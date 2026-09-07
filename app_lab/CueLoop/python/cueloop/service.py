"""CueLoop receiver/API service entry point."""

from __future__ import annotations

import argparse
from pathlib import Path
import signal
import socket
from threading import Event, Thread
import time

from .api import CueLoopHTTPServer
from .constants import (
    DEFAULT_HTTP_HOST,
    DEFAULT_HTTP_PORT,
    DEFAULT_TCP_HOST,
    DEFAULT_TCP_PORT,
    POD_TIMEOUT_SECONDS,
)
from .pipeline import CueLoopPipeline
from .protocol import (
    PacketError,
    ReceiverAck,
    STREAM_LENGTH,
    decode_audio,
    decode_stream_length,
    encode_receiver_ack,
    encode_stream_frame,
)
from .storage import EventStore
from .yamnet import DEFAULT_YAMNET_SHA256, ModelConfigurationError, YamnetClassifier


class TCPReceiver:
    def __init__(self, host: str, port: int, pipeline: CueLoopPipeline) -> None:
        self.host = host
        self.port = port
        self.pipeline = pipeline
        self._stop = Event()
        self._thread: Thread | None = None
        self._listener: socket.socket | None = None
        self._client: socket.socket | None = None
        self._started_monotonic = time.monotonic()
        self._last_ack_monotonic = 0.0

    def start(self) -> None:
        if self._thread is not None:
            raise RuntimeError("receiver already started")
        self._listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._listener.bind((self.host, self.port))
        self.port = int(self._listener.getsockname()[1])
        self._listener.listen(1)
        self._listener.settimeout(0.5)
        self._thread = Thread(target=self._run, name="cueloop-tcp", daemon=True)
        self._thread.start()

    def _receive_exact(self, client: socket.socket, length: int) -> bytes:
        payload = bytearray()
        while len(payload) < length and not self._stop.is_set():
            chunk = client.recv(length - len(payload))
            if not chunk:
                raise ConnectionError("CuePod disconnected")
            payload.extend(chunk)
        if len(payload) != length:
            raise ConnectionError("receiver stopped")
        return bytes(payload)

    def _serve_client(self, client: socket.socket) -> None:
        client.settimeout(POD_TIMEOUT_SECONDS)
        self._last_ack_monotonic = 0.0
        while not self._stop.is_set():
            prefix = self._receive_exact(client, STREAM_LENGTH.size)
            payload = self._receive_exact(client, decode_stream_length(prefix))
            self.pipeline.handle_datagram(payload)
            now = time.monotonic()
            if now - self._last_ack_monotonic < 1.0:
                continue
            try:
                packet = decode_audio(payload)
            except PacketError:
                continue
            ack = ReceiverAck(
                pod_id=packet.pod_id,
                last_sequence=packet.sequence,
                receiver_uptime_ms=int(
                    (now - self._started_monotonic) * 1000
                )
                & 0xFFFFFFFF,
            )
            client.sendall(encode_stream_frame(encode_receiver_ack(ack)))
            self._last_ack_monotonic = now

    def _run(self) -> None:
        assert self._listener is not None
        while not self._stop.is_set():
            try:
                client, _address = self._listener.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            self._client = client
            try:
                client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self._serve_client(client)
            except (ConnectionError, PacketError, socket.timeout, OSError):
                pass
            finally:
                try:
                    client.close()
                except OSError:
                    pass
                self._client = None

    def stop(self) -> None:
        self._stop.set()
        for active_socket in (self._client, self._listener):
            if active_socket is not None:
                try:
                    active_socket.close()
                except OSError:
                    pass
        if self._thread is not None:
            self._thread.join(timeout=2.0)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CueLoop local receiver and dashboard")
    parser.add_argument("--tcp-host", default=DEFAULT_TCP_HOST)
    parser.add_argument("--tcp-port", type=int, default=DEFAULT_TCP_PORT)
    parser.add_argument("--http-host", default=DEFAULT_HTTP_HOST)
    parser.add_argument("--http-port", type=int, default=DEFAULT_HTTP_PORT)
    parser.add_argument("--db", default="data/cueloop.sqlite3")
    parser.add_argument("--location", default="Simulated workshop")
    parser.add_argument(
        "--classifier",
        choices=("synthetic", "yamnet"),
        default="synthetic",
        help="synthetic is the safe default and never represents real audio quality",
    )
    parser.add_argument("--model", type=Path, help="pinned YAMNet .tflite artifact")
    parser.add_argument(
        "--mapping", type=Path, default=Path("models/class_mapping.json")
    )
    parser.add_argument("--model-sha256", default=DEFAULT_YAMNET_SHA256)
    parser.add_argument("--inference-threads", type=int, default=2)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    classifier = None
    if args.classifier == "yamnet":
        if args.model is None:
            parser.error("--model is required with --classifier yamnet")
        try:
            classifier = YamnetClassifier(
                args.model,
                args.mapping,
                expected_sha256=args.model_sha256,
                num_threads=args.inference_threads,
            )
        except ModelConfigurationError as error:
            parser.error(str(error))
    store = EventStore(args.db)
    pipeline = CueLoopPipeline(
        classifier=classifier, store=store, location=args.location
    )
    receiver = TCPReceiver(args.tcp_host, args.tcp_port, pipeline)
    server = CueLoopHTTPServer((args.http_host, args.http_port), pipeline)

    stopping = Event()

    def request_stop(_signum: int, _frame: object) -> None:
        if stopping.is_set():
            return
        stopping.set()
        Thread(target=server.shutdown, daemon=True).start()

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)
    receiver.start()
    print(
        f"CueLoop TCP receiver: {args.tcp_host}:{args.tcp_port}\n"
        f"CueLoop dashboard: http://{args.http_host}:{args.http_port}\n"
        f"Classifier: {args.classifier}\n"
        "Privacy: raw audio is memory-only and not retained.",
        flush=True,
    )
    try:
        server.serve_forever(poll_interval=0.25)
    finally:
        server.server_close()
        receiver.stop()
        store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
