from __future__ import annotations

import json
from threading import Thread
import time
import unittest
from urllib.request import Request, urlopen

from cueloop.api import CueLoopHTTPServer
from cueloop.constants import SAMPLE_RATE_HZ, SAMPLES_PER_FRAME
from cueloop.pipeline import CueLoopPipeline
from cueloop.protocol import AudioPacket, PacketFlags, encode_audio
from cueloop.simulator import SyntheticAudio
from cueloop.storage import EventStore


class PipelineApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = EventStore()
        self.pipeline = CueLoopPipeline(store=self.store, location="Test room")

    def tearDown(self) -> None:
        self.store.close()

    def feed_event(self, label: str, seconds: float = 3.0) -> list[object]:
        source = SyntheticAudio(seed=3)
        events: list[object] = []
        frame_count = int(seconds * SAMPLE_RATE_HZ / SAMPLES_PER_FRAME)
        for sequence in range(frame_count):
            samples = source.frame(label, sequence * SAMPLES_PER_FRAME)
            packet = AudioPacket(
                pod_id=44,
                sequence=sequence,
                sample_clock=sequence * SAMPLES_PER_FRAME,
                capture_ms=sequence * 20,
                samples=samples,
                battery_mv=3900,
                rssi_dbm=-48,
                flags=(
                    PacketFlags.SIMULATED
                    | PacketFlags.BATTERY_VALID
                    | (PacketFlags.STREAM_RESTART if sequence == 0 else PacketFlags.NONE)
                ),
            )
            events.extend(
                self.pipeline.handle_datagram(
                    encode_audio(packet),
                    arrival_monotonic=100.0 + sequence * 0.02,
                )
            )
        return events

    def test_end_to_end_simulated_event(self) -> None:
        events = self.feed_event("alarm_beep")
        self.assertGreaterEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event.class_name, "alarm_beep")
        self.assertEqual(event.evidence_tier, "simulated")
        status = self.pipeline.snapshot(now=103.0)
        self.assertEqual(status["connection"], "connected")
        self.assertFalse(status["privacy"]["raw_audio_retained"])
        self.assertLessEqual(
            status["diagnostics"]["buffered_samples"],
            self.pipeline.windows.maximum_buffered_samples,
        )

    def test_bad_packet_degrades_without_crashing(self) -> None:
        self.assertEqual(self.pipeline.handle_datagram(b"not a packet"), [])
        status = self.pipeline.snapshot()
        self.assertEqual(status["service"], "degraded")
        self.assertEqual(status["diagnostics"]["bad_packets"], 1)

    def test_non_nominal_frame_is_rejected(self) -> None:
        packet = AudioPacket(
            pod_id=1,
            sequence=0,
            sample_clock=0,
            capture_ms=0,
            samples=(0,) * 12,
            flags=PacketFlags.SIMULATED,
        )
        self.assertEqual(self.pipeline.handle_datagram(encode_audio(packet)), [])
        status = self.pipeline.snapshot()
        self.assertEqual(status["diagnostics"]["frame_size_mismatches"], 1)

    def test_api_status_config_and_feedback(self) -> None:
        events = self.feed_event("door_knock")
        self.assertTrue(events)
        event_id = events[0].id
        server = CueLoopHTTPServer(("127.0.0.1", 0), self.pipeline)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_address[1]}"
        try:
            with urlopen(f"{base}/api/status", timeout=2) as response:
                status = json.load(response)
            self.assertFalse(status["privacy"]["raw_audio_retained"])
            request = Request(
                f"{base}/api/config/dog_bark",
                data=json.dumps({"enabled": False}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=2) as response:
                result = json.load(response)
            self.assertFalse(result["policy"]["enabled"])
            request = Request(
                f"{base}/api/events/{event_id}/acknowledge",
                data=b"{}",
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=2) as response:
                result = json.load(response)
            self.assertTrue(result["updated"])
            self.assertEqual(self.store.list()[0]["user_action"], "acknowledged")
            with urlopen(f"{base}/", timeout=2) as response:
                page = response.read().decode()
            self.assertIn("Local · no recordings", page)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
