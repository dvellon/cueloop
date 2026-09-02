"""CueLoop receiver/API service entry point."""

from __future__ import annotations

import argparse
import signal
import socket
from threading import Event, Thread

from .api import CueLoopHTTPServer
from .constants import (
    DEFAULT_HTTP_HOST,
    DEFAULT_HTTP_PORT,
    DEFAULT_UDP_HOST,
    DEFAULT_UDP_PORT,
)
from .pipeline import CueLoopPipeline
from .storage import EventStore


class UDPReceiver:
    def __init__(self, host: str, port: int, pipeline: CueLoopPipeline) -> None:
        self.host = host
        self.port = port
        self.pipeline = pipeline
        self._stop = Event()
        self._thread: Thread | None = None
        self._socket: socket.socket | None = None

    def start(self) -> None:
        if self._thread is not None:
            raise RuntimeError("receiver already started")
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((self.host, self.port))
        self._socket.settimeout(0.5)
        self._thread = Thread(target=self._run, name="cueloop-udp", daemon=True)
        self._thread.start()

    def _run(self) -> None:
        assert self._socket is not None
        while not self._stop.is_set():
            try:
                datagram, _address = self._socket.recvfrom(2048)
            except socket.timeout:
                continue
            except OSError:
                break
            self.pipeline.handle_datagram(datagram)

    def stop(self) -> None:
        self._stop.set()
        if self._socket is not None:
            self._socket.close()
        if self._thread is not None:
            self._thread.join(timeout=2.0)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CueLoop local receiver and dashboard")
    parser.add_argument("--udp-host", default=DEFAULT_UDP_HOST)
    parser.add_argument("--udp-port", type=int, default=DEFAULT_UDP_PORT)
    parser.add_argument("--http-host", default=DEFAULT_HTTP_HOST)
    parser.add_argument("--http-port", type=int, default=DEFAULT_HTTP_PORT)
    parser.add_argument("--db", default="data/cueloop.sqlite3")
    parser.add_argument("--location", default="Simulated workshop")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    store = EventStore(args.db)
    pipeline = CueLoopPipeline(store=store, location=args.location)
    receiver = UDPReceiver(args.udp_host, args.udp_port, pipeline)
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
        f"CueLoop UDP receiver: {args.udp_host}:{args.udp_port}\n"
        f"CueLoop dashboard: http://{args.http_host}:{args.http_port}\n"
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
