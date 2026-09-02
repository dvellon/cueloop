"""Fault-contained Arduino Router Bridge output adapter.

The Arduino App SDK is intentionally injected at runtime. Importing the core
package on a development computer therefore never requires App Lab modules or
an UNO Q router socket.
"""

from __future__ import annotations

from threading import RLock
import time
from typing import Protocol

from .engine import EventRecord


CLASS_CODES = {
    "door_knock": 1,
    "alarm_beep": 2,
    "dog_bark": 3,
    "attention_call": 4,
}


class BridgeClient(Protocol):
    def call(
        self, method_name: str, *params: object, timeout: int = 10
    ) -> object:
        ...


class BridgeCueSink:
    """Translate confirmed events to the MCU without failing audio ingestion."""

    def __init__(self, bridge: BridgeClient, *, timeout_seconds: int = 1) -> None:
        if not 1 <= timeout_seconds <= 10:
            raise ValueError("Bridge timeout must be between 1 and 10 seconds")
        self._bridge = bridge
        self._timeout_seconds = timeout_seconds
        self._lock = RLock()
        self._last_command: str | None = None
        self._last_error: str | None = None
        self._last_success_monotonic: float | None = None
        self._last_mcu_status: dict[str, object] | None = None
        self._last_mcu_uptime_ms: int | None = None
        self._mcu_restarts = 0
        self._resync_required = True
        self._calls = 0
        self._failures = 0

    def _call(self, method_name: str, *params: object) -> object | None:
        command = method_name.removeprefix("cueloop/")
        with self._lock:
            self._calls += 1
            self._last_command = command
        try:
            result = self._bridge.call(
                method_name, *params, timeout=self._timeout_seconds
            )
        except Exception as error:  # Router failures must not stop detection.
            with self._lock:
                self._failures += 1
                self._last_error = f"{type(error).__name__}: {error}"[:240]
            return None
        with self._lock:
            self._last_error = None
            self._last_success_monotonic = time.monotonic()
        return result

    def alert(self, event: EventRecord) -> None:
        self._call(
            "cueloop/cue",
            event.id,
            CLASS_CODES[event.class_name],
            event.priority,
            int(round(event.confidence * 1000)),
        )

    def feedback(self, event_id: str, _action: str) -> None:
        self._call("cueloop/clear", event_id)

    def set_muted(self, muted: bool) -> None:
        self._call("cueloop/mute", muted)

    def heartbeat(self, uptime_ms: int) -> None:
        self._call("cueloop/heartbeat", uptime_ms & 0xFFFFFFFF)

    def record_mcu_status(
        self,
        uptime_ms: object,
        linux_healthy: object,
        active: object,
        muted: object,
        accepted_cues: object,
        rejected_cues: object,
        button_acknowledgements: object,
    ) -> None:
        """Record the MCU's bounded periodic status notification."""

        raw_counters = (
            uptime_ms,
            accepted_cues,
            rejected_cues,
            button_acknowledgements,
        )
        if any(
            isinstance(value, bool) or not isinstance(value, (int, float, str))
            for value in raw_counters
        ):
            raise ValueError("MCU status counters must be numeric")
        assert isinstance(uptime_ms, (int, float, str))
        assert isinstance(accepted_cues, (int, float, str))
        assert isinstance(rejected_cues, (int, float, str))
        assert isinstance(button_acknowledgements, (int, float, str))

        current_uptime_ms = max(0, int(uptime_ms))
        status = {
            "uptime_ms": current_uptime_ms,
            "linux_healthy": bool(linux_healthy),
            "active": bool(active),
            "muted": bool(muted),
            "accepted_cues": max(0, int(accepted_cues)),
            "rejected_cues": max(0, int(rejected_cues)),
            "button_acknowledgements": max(0, int(button_acknowledgements)),
        }
        with self._lock:
            previous_uptime = self._last_mcu_uptime_ms
            if previous_uptime is not None and current_uptime_ms < previous_uptime:
                self._mcu_restarts += 1
                self._resync_required = True
            self._last_mcu_status = status
            self._last_mcu_uptime_ms = current_uptime_ms

    def consume_resync_required(self) -> bool:
        with self._lock:
            required = self._resync_required
            self._resync_required = False
            return required

    def snapshot(self, *, now: float | None = None) -> dict[str, object]:
        current = time.monotonic() if now is None else now
        with self._lock:
            success_age = (
                None
                if self._last_success_monotonic is None
                else max(0.0, current - self._last_success_monotonic)
            )
            return {
                "type": "arduino-router-bridge",
                "connection": (
                    "unknown"
                    if success_age is None
                    else "connected"
                    if success_age <= 6.0
                    else "stale"
                ),
                "last_success_age_seconds": (
                    None if success_age is None else round(success_age, 2)
                ),
                "last_command": self._last_command,
                "calls": self._calls,
                "failures": self._failures,
                "mcu_restarts": self._mcu_restarts,
                "last_error": self._last_error,
                "mcu": (
                    None
                    if self._last_mcu_status is None
                    else dict(self._last_mcu_status)
                ),
            }
