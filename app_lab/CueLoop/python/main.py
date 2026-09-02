"""CueLoop Arduino App Lab entry point for the UNO Q Linux processor."""

from __future__ import annotations

from pathlib import Path
from threading import Event, Thread
import time

from arduino.app_utils import App, Bridge

from cueloop.api import CueLoopHTTPServer
from cueloop.bridge import BridgeCueSink
from cueloop.constants import DEFAULT_UDP_PORT
from cueloop.pipeline import CueLoopPipeline
from cueloop.service import UDPReceiver
from cueloop.storage import EventStore
from cueloop.yamnet import DEFAULT_YAMNET_SHA256, YamnetClassifier


APP_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = APP_ROOT / "models" / "yamnet-classification-tflite-v1.tflite"
MAPPING_PATH = APP_ROOT / "models" / "class_mapping.json"
DATA_PATH = APP_ROOT / "data" / "cueloop.sqlite3"
HTTP_PORT = 8080


class CueLoopApp:
    def __init__(self) -> None:
        # Missing, incompatible, or modified models intentionally stop startup;
        # the physical App never falls back to synthetic classifications.
        classifier = YamnetClassifier(
            MODEL_PATH,
            MAPPING_PATH,
            expected_sha256=DEFAULT_YAMNET_SHA256,
            num_threads=2,
            evidence_tier="UNO Q",
        )
        self.store = EventStore(str(DATA_PATH))
        self.cue_sink = BridgeCueSink(Bridge, timeout_seconds=1)
        self.pipeline = CueLoopPipeline(
            classifier=classifier,
            store=self.store,
            cue_sink=self.cue_sink,
            location="CuePod monitored space",
        )
        self.receiver = UDPReceiver("0.0.0.0", DEFAULT_UDP_PORT, self.pipeline)
        self.server = CueLoopHTTPServer(("0.0.0.0", HTTP_PORT), self.pipeline)
        self.server_thread = Thread(
            target=self.server.serve_forever,
            kwargs={"poll_interval": 0.25},
            name="cueloop-http",
            daemon=True,
        )
        self.stop_event = Event()
        self.bridge_handlers_registered = Event()
        self.registration_thread = Thread(
            target=self._register_bridge_handlers,
            name="cueloop-bridge-register",
            daemon=True,
        )
        self.started_monotonic = time.monotonic()
        self.last_heartbeat_monotonic = 0.0

    def _handle_ack(self, event_id: object) -> bool:
        if not isinstance(event_id, str) or not 1 <= len(event_id) <= 64:
            return False
        # The MCU already cleared its output before sending this notification;
        # avoid a synchronous Bridge call from inside the Bridge handler.
        return self.pipeline.feedback(
            event_id, "acknowledged", notify_sink=False
        )

    def _register_bridge_handlers(self) -> None:
        while not self.stop_event.is_set():
            try:
                Bridge.provide("cueloop/ack", self._handle_ack)
                Bridge.provide("cueloop/mcu_status", self.cue_sink.record_mcu_status)
            except Exception as error:
                print(f"CueLoop Bridge registration pending: {error}", flush=True)
                self.stop_event.wait(3.0)
                continue
            self.bridge_handlers_registered.set()
            return

    def start(self) -> None:
        self.receiver.start()
        self.server_thread.start()
        self.registration_thread.start()
        print(
            f"CueLoop dashboard: http://<uno-q-address>:{HTTP_PORT}\n"
            f"CueLoop CuePod receiver: UDP {DEFAULT_UDP_PORT}\n"
            "Privacy: raw audio is processed in memory and is not retained.",
            flush=True,
        )

    def loop(self) -> None:
        now = time.monotonic()
        if now - self.last_heartbeat_monotonic >= 2.0:
            self.last_heartbeat_monotonic = now
            self.cue_sink.heartbeat(
                int((now - self.started_monotonic) * 1000)
            )
            if self.cue_sink.consume_resync_required():
                self.pipeline.resync_cue_output()
        time.sleep(0.05)

    def stop(self) -> None:
        self.stop_event.set()
        self.server.shutdown()
        self.server.server_close()
        self.receiver.stop()
        self.server_thread.join(timeout=2.0)
        self.registration_thread.join(timeout=2.0)
        self.store.close()


def main() -> None:
    app = CueLoopApp()
    app.start()
    try:
        App.run(user_loop=app.loop)
    finally:
        app.stop()


if __name__ == "__main__":
    main()
