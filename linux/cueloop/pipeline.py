"""Audio datagram to confirmed-event orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
import time
from typing import Protocol

from .buffering import JitterBuffer, WindowAccumulator
from .constants import POD_TIMEOUT_SECONDS, SAMPLE_RATE_HZ, SAMPLES_PER_FRAME
from .engine import EventEngine, EventRecord
from .model import AudioClassifier, SignatureClassifier
from .protocol import PacketError, PacketFlags, decode_audio
from .storage import EventStore


class CueSink(Protocol):
    def alert(self, event: EventRecord) -> None:
        ...

    def feedback(self, event_id: str, action: str) -> None:
        ...


@dataclass(slots=True)
class NullCueSink:
    """Safe desktop sink; records the last compact command for diagnostics."""

    last_command: dict[str, object] | None = None

    def alert(self, event: EventRecord) -> None:
        self.last_command = {
            "command": "alert",
            "event_id": event.id,
            "class_name": event.class_name,
            "priority": event.priority,
        }

    def feedback(self, event_id: str, action: str) -> None:
        self.last_command = {
            "command": action,
            "event_id": event_id,
        }


class CueLoopPipeline:
    def __init__(
        self,
        *,
        classifier: AudioClassifier | None = None,
        engine: EventEngine | None = None,
        store: EventStore | None = None,
        cue_sink: CueSink | None = None,
        location: str = "Simulated workshop",
    ) -> None:
        self.classifier = SignatureClassifier() if classifier is None else classifier
        self.engine = EventEngine() if engine is None else engine
        self.store = EventStore() if store is None else store
        self.cue_sink = NullCueSink() if cue_sink is None else cue_sink
        self.location = location[:48]
        self.jitter = JitterBuffer()
        self.windows = WindowAccumulator()
        self._lock = RLock()
        self._active_pod_id: int | None = None
        self._last_packet_flags = PacketFlags.NONE
        self._last_battery_mv = 0
        self._last_rssi_dbm = 0
        self._last_model_name = "not-run"
        self._last_inference_ms: float | None = None
        self._last_error: str | None = None
        self._current_event: EventRecord | None = None
        self._events_emitted = 0

    def handle_datagram(
        self,
        datagram: bytes,
        *,
        arrival_monotonic: float | None = None,
    ) -> list[EventRecord]:
        now = time.monotonic() if arrival_monotonic is None else arrival_monotonic
        try:
            packet = decode_audio(datagram)
        except PacketError as error:
            self.jitter.mark_bad_packet()
            with self._lock:
                self._last_error = str(error)
            return []
        if packet.sample_rate != SAMPLE_RATE_HZ:
            self.jitter.metrics.sample_rate_mismatches += 1
            with self._lock:
                self._last_error = f"unsupported sample rate {packet.sample_rate}"
            return []
        if len(packet.samples) != SAMPLES_PER_FRAME:
            self.jitter.metrics.frame_size_mismatches += 1
            with self._lock:
                self._last_error = (
                    f"unsupported frame size {len(packet.samples)}; "
                    f"expected {SAMPLES_PER_FRAME}"
                )
            return []
        if packet.flags & PacketFlags.STREAM_RESTART:
            self.windows.reset()
        if self._active_pod_id is not None and packet.pod_id != self._active_pod_id:
            self.windows.reset()
        self._active_pod_id = packet.pod_id
        with self._lock:
            self._last_packet_flags = packet.flags
            self._last_battery_mv = packet.battery_mv
            self._last_rssi_dbm = packet.rssi_dbm
            self._last_error = None

        events: list[EventRecord] = []
        for released in self.jitter.push(packet, arrival_monotonic=now):
            for samples, window_completed in self.windows.append(
                released.samples,
                arrival_monotonic=released.arrival_monotonic,
            ):
                classification = self.classifier.classify(samples, SAMPLE_RATE_HZ)
                processing_ms = (time.monotonic() - window_completed) * 1000.0
                evidence_tier = (
                    "simulated"
                    if packet.flags & (PacketFlags.SIMULATED | PacketFlags.TEST_TONE)
                    else classification.evidence_tier
                )
                event = self.engine.process(
                    classification.scores,
                    pod_id=packet.pod_id,
                    location=self.location,
                    evidence_tier=evidence_tier,
                    packet_loss_rate=self.jitter.metrics.loss_rate,
                    pipeline_latency_ms=processing_ms,
                )
                with self._lock:
                    self._last_model_name = classification.model_name
                    self._last_inference_ms = classification.inference_ms
                if event is not None:
                    self.store.add(event)
                    self.cue_sink.alert(event)
                    with self._lock:
                        self._current_event = event
                        self._events_emitted += 1
                    events.append(event)
        return events

    def feedback(self, event_id: str, action: str) -> bool:
        changed = self.store.set_action(event_id, action)
        if changed:
            self.cue_sink.feedback(event_id, action)
            with self._lock:
                if self._current_event and self._current_event.id == event_id:
                    self._current_event.user_action = action
        return changed

    def clear_history(self) -> None:
        self.store.clear()
        with self._lock:
            self._current_event = None

    def snapshot(self, *, now: float | None = None) -> dict[str, object]:
        current = time.monotonic() if now is None else now
        last_packet = self.jitter.metrics.last_packet_monotonic
        connected = last_packet is not None and current - last_packet <= POD_TIMEOUT_SECONDS
        with self._lock:
            return {
                "service": "healthy" if self._last_error is None else "degraded",
                "connection": "connected" if connected else "disconnected",
                "pod_id": self._active_pod_id,
                "location": self.location,
                "input_mode": (
                    "none"
                    if last_packet is None
                    else "simulated"
                    if self._last_packet_flags & PacketFlags.SIMULATED
                    else "test-tone"
                    if self._last_packet_flags & PacketFlags.TEST_TONE
                    else "physical"
                ),
                "battery_mv": (
                    self._last_battery_mv
                    if self._last_packet_flags & PacketFlags.BATTERY_VALID
                    else None
                ),
                "rssi_dbm": self._last_rssi_dbm or None,
                "privacy": {
                    "raw_audio_retained": False,
                    "cloud_connected": False,
                    "transport_security": "trusted-LAN UDP; not encrypted",
                },
                "decision": self.engine.state_snapshot(),
                "current_event": (
                    None if self._current_event is None else self._current_event.as_dict()
                ),
                "diagnostics": {
                    **self.jitter.metrics.snapshot(),
                    "buffered_samples": self.windows.buffered_samples,
                    "model": self._last_model_name,
                    "inference_ms": (
                        None
                        if self._last_inference_ms is None
                        else round(self._last_inference_ms, 3)
                    ),
                    "events_emitted": self._events_emitted,
                    "last_error": self._last_error,
                },
            }
