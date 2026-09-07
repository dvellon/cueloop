from __future__ import annotations

import socket
import time
import unittest

from cueloop.pipeline import CueLoopPipeline
from cueloop.protocol import (
    AudioPacket,
    PacketFlags,
    ReceiverAck,
    STREAM_LENGTH,
    decode_receiver_ack,
    decode_stream_length,
    encode_audio,
    encode_receiver_ack,
    encode_stream_frame,
)
from cueloop.service import TCPReceiver
from cueloop.simulator import drain_acknowledgements, main as simulator_main
from cueloop.storage import EventStore


def receive_exact(connection: socket.socket, length: int) -> bytes:
    result = bytearray()
    while len(result) < length:
        chunk = connection.recv(length - len(result))
        if not chunk:
            raise ConnectionError("receiver closed before the test frame completed")
        result.extend(chunk)
    return bytes(result)


class TCPTransportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = EventStore()
        self.pipeline = CueLoopPipeline(store=self.store, location="TCP test")
        self.receiver = TCPReceiver("127.0.0.1", 0, self.pipeline)
        self.receiver.start()

    def tearDown(self) -> None:
        self.receiver.stop()
        self.store.close()

    @staticmethod
    def packet(sequence: int) -> bytes:
        return encode_audio(
            AudioPacket(
                pod_id=0xC0E10001,
                sequence=sequence,
                sample_clock=sequence * 320,
                capture_ms=sequence * 20,
                samples=(0,) * 320,
                battery_mv=4000,
                rssi_dbm=-42,
                flags=PacketFlags.SIMULATED | PacketFlags.BATTERY_VALID,
            )
        )

    def test_fragmented_and_coalesced_frames_reach_pipeline_and_ack(self) -> None:
        with socket.create_connection(("127.0.0.1", self.receiver.port), timeout=2) as client:
            client.settimeout(2)
            first = encode_stream_frame(self.packet(0))
            second = encode_stream_frame(self.packet(1))
            client.sendall(first[:1])
            client.sendall(first[1:] + second)

            prefix = receive_exact(client, STREAM_LENGTH.size)
            ack = decode_receiver_ack(
                receive_exact(client, decode_stream_length(prefix))
            )
            deadline = time.monotonic() + 1.0
            while (
                self.pipeline.snapshot()["diagnostics"]["datagrams_received"] < 2
                and time.monotonic() < deadline
            ):
                time.sleep(0.01)

        self.assertEqual(ack.pod_id, 0xC0E10001)
        self.assertEqual(ack.last_sequence, 0)
        self.assertEqual(
            self.pipeline.snapshot()["diagnostics"]["datagrams_received"], 2
        )

    def test_simulator_uses_tcp_receiver(self) -> None:
        result = simulator_main(
            [
                "--host",
                "127.0.0.1",
                "--port",
                str(self.receiver.port),
                "--run-seconds",
                "0.08",
                "--loss",
                "0",
                "--jitter-ms",
                "0",
                "--latency-ms",
                "0",
                "--reorder-rate",
                "0",
            ]
        )
        self.assertEqual(result, 0)
        self.assertGreaterEqual(
            self.pipeline.snapshot()["diagnostics"]["datagrams_received"], 3
        )

    def test_simulator_drains_fragmented_acknowledgement(self) -> None:
        sender, receiver = socket.socketpair()
        self.addCleanup(sender.close)
        self.addCleanup(receiver.close)
        framed = encode_stream_frame(
            encode_receiver_ack(
                ReceiverAck(
                    pod_id=0xC0E10001,
                    last_sequence=4,
                    receiver_uptime_ms=100,
                )
            )
        )
        pending = bytearray()
        sender.sendall(framed[:1])
        self.assertEqual(drain_acknowledgements(receiver, pending), 0)
        sender.sendall(framed[1:])
        self.assertEqual(drain_acknowledgements(receiver, pending), 1)
        self.assertEqual(pending, b"")

    def test_receiver_accepts_a_replacement_connection(self) -> None:
        first = socket.create_connection(
            ("127.0.0.1", self.receiver.port), timeout=2
        )
        first.close()

        deadline = time.monotonic() + 1.0
        while time.monotonic() < deadline:
            try:
                with socket.create_connection(
                    ("127.0.0.1", self.receiver.port), timeout=0.2
                ) as second:
                    second.sendall(encode_stream_frame(self.packet(2)))
                break
            except (ConnectionRefusedError, TimeoutError):
                time.sleep(0.01)

        deadline = time.monotonic() + 1.0
        while (
            self.pipeline.snapshot()["diagnostics"]["datagrams_received"] < 1
            and time.monotonic() < deadline
        ):
            time.sleep(0.01)
        self.assertEqual(
            self.pipeline.snapshot()["diagnostics"]["datagrams_received"], 1
        )


if __name__ == "__main__":
    unittest.main()
