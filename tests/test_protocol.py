from __future__ import annotations

import unittest

from cueloop.constants import SAMPLES_PER_FRAME
from cueloop.protocol import (
    ACK,
    AudioPacket,
    HEADER,
    PacketError,
    PacketFlags,
    ReceiverAck,
    decode_audio,
    decode_receiver_ack,
    encode_audio,
    encode_receiver_ack,
)


class ProtocolTests(unittest.TestCase):
    def make_packet(self) -> AudioPacket:
        return AudioPacket(
            pod_id=0xC0E10001,
            sequence=0xFFFFFFFE,
            sample_clock=123456789,
            capture_ms=4321,
            samples=tuple(range(-160, 160)),
            battery_mv=3975,
            rssi_dbm=-51,
            flags=PacketFlags.SIMULATED | PacketFlags.BATTERY_VALID,
        )

    def test_round_trip(self) -> None:
        packet = self.make_packet()
        encoded = encode_audio(packet)
        self.assertEqual(len(encoded), HEADER.size + SAMPLES_PER_FRAME * 2)
        self.assertEqual(decode_audio(encoded), packet)

    def test_payload_corruption_rejected(self) -> None:
        encoded = bytearray(encode_audio(self.make_packet()))
        encoded[-1] ^= 0x7F
        with self.assertRaisesRegex(PacketError, "payload CRC"):
            decode_audio(bytes(encoded))

    def test_header_corruption_rejected(self) -> None:
        encoded = bytearray(encode_audio(self.make_packet()))
        encoded[14] ^= 0x01
        with self.assertRaisesRegex(PacketError, "header CRC"):
            decode_audio(bytes(encoded))

    def test_length_mismatch_rejected(self) -> None:
        with self.assertRaisesRegex(PacketError, "length mismatch"):
            decode_audio(encode_audio(self.make_packet())[:-2])

    def test_sample_range_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "int16"):
            AudioPacket(1, 1, 1, 1, (32768,))

    def test_receiver_ack_round_trip(self) -> None:
        ack = ReceiverAck(0xC0E10001, 0xFFFFFFFF, 123_456)
        encoded = encode_receiver_ack(ack)
        self.assertEqual(len(encoded), ACK.size)
        self.assertEqual(decode_receiver_ack(encoded), ack)

    def test_receiver_ack_corruption_rejected(self) -> None:
        encoded = bytearray(encode_receiver_ack(ReceiverAck(1, 2, 3)))
        encoded[12] ^= 0x40
        with self.assertRaisesRegex(PacketError, "ACK CRC"):
            decode_receiver_ack(bytes(encoded))


if __name__ == "__main__":
    unittest.main()
