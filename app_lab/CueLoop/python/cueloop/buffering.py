"""Bounded packet reordering and audio window accumulation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from threading import RLock
import time

from .constants import SAMPLES_PER_FRAME, WINDOW_SAMPLES, WINDOW_STRIDE_SAMPLES
from .protocol import AudioPacket, PacketFlags


UINT32_MASK = 0xFFFFFFFF
UINT32_HALF = 0x80000000


def sequence_distance(sequence: int, reference: int) -> int:
    """Return signed modulo-2^32 distance from reference to sequence."""

    distance = (sequence - reference) & UINT32_MASK
    return distance if distance < UINT32_HALF else distance - (UINT32_MASK + 1)


@dataclass(slots=True)
class StreamMetrics:
    datagrams_received: int = 0
    frames_emitted: int = 0
    missing_frames: int = 0
    duplicate_frames: int = 0
    late_frames: int = 0
    stream_restarts: int = 0
    bad_packets: int = 0
    sample_rate_mismatches: int = 0
    frame_size_mismatches: int = 0
    jitter_ms: float = 0.0
    last_sequence: int | None = None
    last_packet_monotonic: float | None = None

    @property
    def expected_frames(self) -> int:
        return self.frames_emitted + self.missing_frames

    @property
    def loss_rate(self) -> float:
        return self.missing_frames / max(1, self.expected_frames)

    def snapshot(self) -> dict[str, int | float | None]:
        result = asdict(self)
        result["loss_rate"] = round(self.loss_rate, 6)
        result["jitter_ms"] = round(self.jitter_ms, 3)
        return result


@dataclass(frozen=True, slots=True)
class ReleasedFrame:
    samples: tuple[int, ...]
    packet: AudioPacket | None
    synthetic_gap: bool
    arrival_monotonic: float


class JitterBuffer:
    """Small bounded packet reorder buffer with explicit zero-gap release."""

    def __init__(self, *, reorder_depth: int = 3, max_packets: int = 16) -> None:
        if reorder_depth < 1 or max_packets <= reorder_depth:
            raise ValueError("require max_packets > reorder_depth >= 1")
        self.reorder_depth = reorder_depth
        self.max_packets = max_packets
        self.metrics = StreamMetrics()
        self._pending: dict[int, tuple[AudioPacket, float]] = {}
        self._expected: int | None = None
        self._pod_id: int | None = None
        self._nominal_samples = SAMPLES_PER_FRAME
        self._previous_transit: float | None = None
        self._lock = RLock()

    def reset(self, *, count_restart: bool = False) -> None:
        with self._lock:
            self._pending.clear()
            self._expected = None
            self._pod_id = None
            self._previous_transit = None
            if count_restart:
                self.metrics.stream_restarts += 1

    def mark_bad_packet(self) -> None:
        with self._lock:
            self.metrics.bad_packets += 1

    def push(
        self,
        packet: AudioPacket,
        *,
        arrival_monotonic: float | None = None,
    ) -> list[ReleasedFrame]:
        now = time.monotonic() if arrival_monotonic is None else arrival_monotonic
        with self._lock:
            self.metrics.datagrams_received += 1
            self.metrics.last_packet_monotonic = now
            if packet.flags & PacketFlags.STREAM_RESTART:
                self.reset(count_restart=True)
                self.metrics.last_packet_monotonic = now
            if self._pod_id is not None and packet.pod_id != self._pod_id:
                # V1 receiver accepts one active pod. A new ID begins a new stream.
                self.reset(count_restart=True)
                self.metrics.last_packet_monotonic = now
            self._pod_id = packet.pod_id
            self._nominal_samples = len(packet.samples) or self._nominal_samples
            self._update_jitter(packet, now)

            if self._expected is None:
                self._expected = packet.sequence
            distance = sequence_distance(packet.sequence, self._expected)
            if distance < 0:
                self.metrics.late_frames += 1
                return []
            if packet.sequence in self._pending:
                self.metrics.duplicate_frames += 1
                return []
            self._pending[packet.sequence] = (packet, now)
            return self._drain(now)

    def _update_jitter(self, packet: AudioPacket, arrival: float) -> None:
        sender_seconds = packet.sample_clock / max(1, packet.sample_rate)
        transit = arrival - sender_seconds
        if self._previous_transit is not None:
            delta = abs(transit - self._previous_transit)
            self.metrics.jitter_ms += (
                delta * 1000.0 - self.metrics.jitter_ms
            ) / 16.0
        self._previous_transit = transit

    def _drain(self, now: float) -> list[ReleasedFrame]:
        released: list[ReleasedFrame] = []
        while self._expected is not None:
            current = self._pending.pop(self._expected, None)
            if current is not None:
                packet, arrival = current
                released.append(
                    ReleasedFrame(
                        samples=packet.samples,
                        packet=packet,
                        synthetic_gap=False,
                        arrival_monotonic=arrival,
                    )
                )
                self.metrics.frames_emitted += 1
                self.metrics.last_sequence = packet.sequence
                self._expected = (self._expected + 1) & UINT32_MASK
                continue

            if len(self._pending) < self.reorder_depth:
                break
            closest = min(
                sequence_distance(sequence, self._expected)
                for sequence in self._pending
            )
            if closest <= 0:
                break
            if closest > self.max_packets:
                # A huge forward jump is a stream discontinuity, not a request
                # to allocate/emit millions of silence frames. Account for the
                # reported gap in O(1), release one silence marker, and resume.
                self.metrics.missing_frames += closest
                self._expected = (self._expected + closest) & UINT32_MASK
                released.append(
                    ReleasedFrame(
                        samples=(0,) * self._nominal_samples,
                        packet=None,
                        synthetic_gap=True,
                        arrival_monotonic=now,
                    )
                )
                continue
            # Release one missing position per pass. This preserves exact loss
            # accounting even for a multi-packet gap and cannot grow memory.
            released.append(
                ReleasedFrame(
                    samples=(0,) * self._nominal_samples,
                    packet=None,
                    synthetic_gap=True,
                    arrival_monotonic=now,
                )
            )
            self.metrics.missing_frames += 1
            self._expected = (self._expected + 1) & UINT32_MASK

        return released


class WindowAccumulator:
    """Create fixed overlapping windows while enforcing a hard memory bound."""

    def __init__(
        self,
        *,
        window_samples: int = WINDOW_SAMPLES,
        stride_samples: int = WINDOW_STRIDE_SAMPLES,
    ) -> None:
        if not 0 < stride_samples <= window_samples:
            raise ValueError("require 0 < stride <= window")
        self.window_samples = window_samples
        self.stride_samples = stride_samples
        self._samples: list[int] = []
        self._first_sample_monotonic: float | None = None
        self._lock = RLock()

    @property
    def buffered_samples(self) -> int:
        with self._lock:
            return len(self._samples)

    @property
    def maximum_buffered_samples(self) -> int:
        return self.window_samples + self.stride_samples

    def reset(self) -> None:
        with self._lock:
            self._samples.clear()
            self._first_sample_monotonic = None

    def append(
        self,
        samples: tuple[int, ...],
        *,
        arrival_monotonic: float,
    ) -> list[tuple[tuple[int, ...], float]]:
        with self._lock:
            if self._first_sample_monotonic is None:
                self._first_sample_monotonic = arrival_monotonic
            self._samples.extend(samples)
            windows: list[tuple[tuple[int, ...], float]] = []
            while len(self._samples) >= self.window_samples:
                completed_at = arrival_monotonic
                windows.append(
                    (tuple(self._samples[: self.window_samples]), completed_at)
                )
                del self._samples[: self.stride_samples]
                self._first_sample_monotonic = arrival_monotonic
            # Defensive eviction: malformed inputs still cannot grow without bound.
            maximum = self.maximum_buffered_samples
            if len(self._samples) > maximum:
                del self._samples[: len(self._samples) - maximum]
            return windows
