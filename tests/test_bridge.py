from __future__ import annotations

from datetime import datetime, timezone
import unittest

from cueloop.bridge import BridgeCueSink
from cueloop.engine import EventRecord


class FakeBridge:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...], int]] = []
        self.failure: Exception | None = None

    def call(
        self, method_name: str, *params: object, timeout: int = 10
    ) -> object:
        self.calls.append((method_name, params, timeout))
        if self.failure is not None:
            raise self.failure
        return True


def event() -> EventRecord:
    return EventRecord(
        id="event-123",
        class_name="alarm_beep",
        confidence=0.8764,
        detected_at=datetime.now(timezone.utc).isoformat(),
        pod_id=1,
        location="Test room",
        priority=3,
        decision_state="confirmed",
        evidence_windows=2,
        evidence_tier="simulated",
        packet_loss_rate=0.0,
        pipeline_latency_ms=4.2,
    )


class BridgeCueSinkTests(unittest.TestCase):
    def test_translates_commands_to_bounded_rpc_contract(self) -> None:
        bridge = FakeBridge()
        sink = BridgeCueSink(bridge)
        sink.alert(event())
        sink.feedback("event-123", "acknowledged")
        sink.set_muted(True)
        sink.heartbeat(0x1_0000_0001)
        self.assertEqual(
            bridge.calls,
            [
                ("cueloop/cue", ("event-123", 2, 3, 876), 1),
                ("cueloop/clear", ("event-123",), 1),
                ("cueloop/mute", (True,), 1),
                ("cueloop/heartbeat", (1,), 1),
            ],
        )
        status = sink.snapshot()
        self.assertEqual(status["connection"], "connected")
        self.assertEqual(status["failures"], 0)

    def test_router_failure_is_contained_and_reported(self) -> None:
        bridge = FakeBridge()
        bridge.failure = TimeoutError("router did not answer")
        sink = BridgeCueSink(bridge)
        sink.alert(event())
        status = sink.snapshot()
        self.assertEqual(status["connection"], "unknown")
        self.assertEqual(status["failures"], 1)
        self.assertIn("TimeoutError", str(status["last_error"]))

    def test_mcu_status_notification_is_bounded_and_copied(self) -> None:
        sink = BridgeCueSink(FakeBridge())
        self.assertTrue(sink.consume_resync_required())
        self.assertFalse(sink.consume_resync_required())
        sink.record_mcu_status(200, True, True, False, 8, 1, 2)
        status = sink.snapshot()
        self.assertEqual(
            status["mcu"],
            {
                "uptime_ms": 200,
                "linux_healthy": True,
                "active": True,
                "muted": False,
                "accepted_cues": 8,
                "rejected_cues": 1,
                "button_acknowledgements": 2,
            },
        )

        sink.record_mcu_status(10, True, False, False, 0, 0, 0)
        self.assertTrue(sink.consume_resync_required())
        self.assertEqual(sink.snapshot()["mcu_restarts"], 1)


if __name__ == "__main__":
    unittest.main()
