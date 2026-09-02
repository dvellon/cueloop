from __future__ import annotations

from datetime import datetime, timezone
import sqlite3
import tempfile
import unittest

from cueloop.engine import EventEngine
from cueloop.model import SignatureClassifier
from cueloop.simulator import SyntheticAudio
from cueloop.storage import EventStore


class ModelEngineStorageTests(unittest.TestCase):
    def test_synthetic_signatures_map_to_expected_classes(self) -> None:
        source = SyntheticAudio(seed=2)
        classifier = SignatureClassifier()
        for expected in ("door_knock", "alarm_beep", "dog_bark", "attention_call"):
            with self.subTest(expected=expected):
                result = classifier.classify(source.window(expected), 16000)
                predicted = max(
                    (label for label in result.scores if label not in ("background", "unknown")),
                    key=result.scores.get,
                )
                self.assertEqual(predicted, expected)
                self.assertGreater(result.scores[expected], 0.74)
                self.assertEqual(result.evidence_tier, "simulated")

    def test_temporal_confirmation_cooldown_and_mute(self) -> None:
        engine = EventEngine()
        common = dict(
            pod_id=7,
            location="test",
            evidence_tier="simulated",
            packet_loss_rate=0.0,
            pipeline_latency_ms=8.5,
            wall_time=datetime(2026, 9, 1, tzinfo=timezone.utc),
        )
        self.assertIsNone(engine.process({"door_knock": 0.80}, now=1.0, **common))
        event = engine.process({"door_knock": 0.84}, now=1.5, **common)
        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event.evidence_windows, 2)
        self.assertEqual(event.decision_state, "confirmed")
        self.assertIsNone(engine.process({"door_knock": 0.90}, now=2.0, **common))
        self.assertIsNone(engine.process({"door_knock": 0.90}, now=2.5, **common))
        self.assertEqual(engine.state_snapshot()["state"], "cooldown")
        engine.mute(10, now=20.0)
        self.assertIsNone(engine.process({"alarm_beep": 0.99}, now=21.0, **common))
        self.assertEqual(engine.state_snapshot()["state"], "muted")

    def test_ambiguous_evidence_does_not_alert(self) -> None:
        engine = EventEngine()
        kwargs = dict(
            pod_id=1,
            location="test",
            evidence_tier="simulated",
            packet_loss_rate=0.0,
            pipeline_latency_ms=None,
        )
        self.assertIsNone(engine.process({"door_knock": 0.55}, now=1.0, **kwargs))
        self.assertIsNone(engine.process({"door_knock": 0.58}, now=1.5, **kwargs))
        self.assertEqual(engine.state_snapshot()["state"], "confirming")

    def test_store_schema_contains_metadata_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = f"{directory}/events.sqlite3"
            store = EventStore(path)
            engine = EventEngine()
            kwargs = dict(
                pod_id=1,
                location="test",
                evidence_tier="simulated",
                packet_loss_rate=0.02,
                pipeline_latency_ms=12.0,
            )
            engine.process({"alarm_beep": 0.9}, now=1.0, **kwargs)
            event = engine.process({"alarm_beep": 0.9}, now=1.5, **kwargs)
            assert event is not None
            store.add(event)
            row = store.list()[0]
            self.assertNotIn("samples", row)
            self.assertNotIn("audio", row)
            self.assertTrue(store.set_action(event.id, "dismissed"))
            self.assertEqual(store.list()[0]["user_action"], "dismissed")
            store.close()
            connection = sqlite3.connect(path)
            columns = [row[1] for row in connection.execute("PRAGMA table_info(events)")]
            connection.close()
            self.assertFalse({"audio", "samples", "payload"} & set(columns))


if __name__ == "__main__":
    unittest.main()
