"""CueLoop Protocol v1 encoder and strict decoder.

The fixed-size header is network byte order. PCM payload samples are signed
16-bit little-endian to match the ESP32 capture and common TFLite input path.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, IntFlag
import struct
import zlib

from .constants import SAMPLE_RATE_HZ, SAMPLES_PER_FRAME


MAGIC = b"CLP1"
VERSION = 1
HEADER_WITHOUT_CRC = struct.Struct(">4sBBHIIQIHHHbBI")
HEADER = struct.Struct(">4sBBHIIQIHHHbBII")
ACK_WITHOUT_CRC = struct.Struct(">4sBBHIII")
ACK = struct.Struct(">4sBBHIIII")
STREAM_LENGTH = struct.Struct(">H")
MAX_SAMPLE_COUNT = 640
MAX_STREAM_PAYLOAD_BYTES = HEADER.size + MAX_SAMPLE_COUNT * 2


class MessageType(IntEnum):
    AUDIO_PCM16 = 1
    RECEIVER_ACK = 2


class PacketFlags(IntFlag):
    NONE = 0
    SIMULATED = 1 << 0
    TEST_TONE = 1 << 1
    USB_POWERED = 1 << 2
    BATTERY_VALID = 1 << 3
    STREAM_RESTART = 1 << 4


class PacketError(ValueError):
    """Raised when a packet cannot be safely accepted."""


def encode_stream_frame(payload: bytes) -> bytes:
    """Prefix one protocol payload for transport over a TCP byte stream."""

    if not 1 <= len(payload) <= MAX_STREAM_PAYLOAD_BYTES:
        raise ValueError(
            f"stream payload length must be 1..{MAX_STREAM_PAYLOAD_BYTES} bytes"
        )
    return STREAM_LENGTH.pack(len(payload)) + payload


def decode_stream_length(prefix: bytes) -> int:
    """Validate and decode a TCP stream-frame length prefix."""

    if len(prefix) != STREAM_LENGTH.size:
        raise PacketError(
            f"stream prefix length mismatch: got {len(prefix)}, "
            f"expected {STREAM_LENGTH.size}"
        )
    (length,) = STREAM_LENGTH.unpack(prefix)
    if not 1 <= length <= MAX_STREAM_PAYLOAD_BYTES:
        raise PacketError(f"invalid stream payload length {length}")
    return length


@dataclass(frozen=True, slots=True)
class AudioPacket:
    pod_id: int
    sequence: int
    sample_clock: int
    capture_ms: int
    samples: tuple[int, ...]
    sample_rate: int = SAMPLE_RATE_HZ
    battery_mv: int = 0
    rssi_dbm: int = 0
    flags: PacketFlags = PacketFlags.NONE

    def __post_init__(self) -> None:
        if not 0 <= self.pod_id <= 0xFFFFFFFF:
            raise ValueError("pod_id must fit uint32")
        if not 0 <= self.sequence <= 0xFFFFFFFF:
            raise ValueError("sequence must fit uint32")
        if not 0 <= self.sample_clock <= 0xFFFFFFFFFFFFFFFF:
            raise ValueError("sample_clock must fit uint64")
        if not 0 <= self.capture_ms <= 0xFFFFFFFF:
            raise ValueError("capture_ms must fit uint32")
        if not 1 <= self.sample_rate <= 0xFFFF:
            raise ValueError("sample_rate must fit positive uint16")
        if not 0 <= len(self.samples) <= MAX_SAMPLE_COUNT:
            raise ValueError(f"sample count must be <= {MAX_SAMPLE_COUNT}")
        if not 0 <= self.battery_mv <= 0xFFFF:
            raise ValueError("battery_mv must fit uint16")
        if not -128 <= self.rssi_dbm <= 127:
            raise ValueError("rssi_dbm must fit int8")
        if any(sample < -32768 or sample > 32767 for sample in self.samples):
            raise ValueError("PCM samples must fit int16")


@dataclass(frozen=True, slots=True)
class ReceiverAck:
    pod_id: int
    last_sequence: int
    receiver_uptime_ms: int

    def __post_init__(self) -> None:
        for name, value in (
            ("pod_id", self.pod_id),
            ("last_sequence", self.last_sequence),
            ("receiver_uptime_ms", self.receiver_uptime_ms),
        ):
            if not 0 <= value <= 0xFFFFFFFF:
                raise ValueError(f"{name} must fit uint32")


def encode_audio(packet: AudioPacket) -> bytes:
    sample_count = len(packet.samples)
    payload = struct.pack(f"<{sample_count}h", *packet.samples)
    payload_crc = zlib.crc32(payload) & 0xFFFFFFFF
    header_without_crc = HEADER_WITHOUT_CRC.pack(
        MAGIC,
        VERSION,
        MessageType.AUDIO_PCM16,
        int(packet.flags),
        packet.pod_id,
        packet.sequence,
        packet.sample_clock,
        packet.capture_ms,
        packet.sample_rate,
        sample_count,
        packet.battery_mv,
        packet.rssi_dbm,
        0,
        payload_crc,
    )
    header_crc = zlib.crc32(header_without_crc) & 0xFFFFFFFF
    return header_without_crc + struct.pack(">I", header_crc) + payload


def decode_audio(datagram: bytes) -> AudioPacket:
    if len(datagram) < HEADER.size:
        raise PacketError("truncated header")
    fields = HEADER.unpack_from(datagram)
    (
        magic,
        version,
        message_type,
        flags,
        pod_id,
        sequence,
        sample_clock,
        capture_ms,
        sample_rate,
        sample_count,
        battery_mv,
        rssi_dbm,
        reserved,
        payload_crc,
        header_crc,
    ) = fields
    if magic != MAGIC:
        raise PacketError("bad magic")
    if version != VERSION:
        raise PacketError(f"unsupported version {version}")
    if message_type != MessageType.AUDIO_PCM16:
        raise PacketError(f"unsupported message type {message_type}")
    if reserved != 0:
        raise PacketError("reserved header byte must be zero")
    if flags & ~int(
        PacketFlags.SIMULATED
        | PacketFlags.TEST_TONE
        | PacketFlags.USB_POWERED
        | PacketFlags.BATTERY_VALID
        | PacketFlags.STREAM_RESTART
    ):
        raise PacketError("unknown flag bit")
    if sample_count > MAX_SAMPLE_COUNT:
        raise PacketError("sample count exceeds protocol maximum")
    expected_length = HEADER.size + sample_count * 2
    if len(datagram) != expected_length:
        raise PacketError(
            f"length mismatch: got {len(datagram)}, expected {expected_length}"
        )
    computed_header_crc = zlib.crc32(datagram[: HEADER_WITHOUT_CRC.size]) & 0xFFFFFFFF
    if computed_header_crc != header_crc:
        raise PacketError("header CRC mismatch")
    payload = datagram[HEADER.size :]
    if zlib.crc32(payload) & 0xFFFFFFFF != payload_crc:
        raise PacketError("payload CRC mismatch")
    samples = struct.unpack(f"<{sample_count}h", payload)
    return AudioPacket(
        pod_id=pod_id,
        sequence=sequence,
        sample_clock=sample_clock,
        capture_ms=capture_ms,
        samples=samples,
        sample_rate=sample_rate,
        battery_mv=battery_mv,
        rssi_dbm=rssi_dbm,
        flags=PacketFlags(flags),
    )


def encode_receiver_ack(ack: ReceiverAck) -> bytes:
    without_crc = ACK_WITHOUT_CRC.pack(
        MAGIC,
        VERSION,
        MessageType.RECEIVER_ACK,
        0,
        ack.pod_id,
        ack.last_sequence,
        ack.receiver_uptime_ms,
    )
    checksum = zlib.crc32(without_crc) & 0xFFFFFFFF
    return without_crc + struct.pack(">I", checksum)


def decode_receiver_ack(datagram: bytes) -> ReceiverAck:
    if len(datagram) != ACK.size:
        raise PacketError(f"ACK length mismatch: got {len(datagram)}, expected {ACK.size}")
    magic, version, message_type, flags, pod_id, sequence, uptime_ms, checksum = (
        ACK.unpack(datagram)
    )
    if magic != MAGIC:
        raise PacketError("bad ACK magic")
    if version != VERSION:
        raise PacketError(f"unsupported ACK version {version}")
    if message_type != MessageType.RECEIVER_ACK:
        raise PacketError(f"unsupported ACK message type {message_type}")
    if flags != 0:
        raise PacketError("ACK flags must be zero")
    computed = zlib.crc32(datagram[: ACK_WITHOUT_CRC.size]) & 0xFFFFFFFF
    if computed != checksum:
        raise PacketError("ACK CRC mismatch")
    return ReceiverAck(
        pod_id=pod_id,
        last_sequence=sequence,
        receiver_uptime_ms=uptime_ms,
    )


def nominal_audio_packet(
    *,
    pod_id: int,
    sequence: int,
    sample_clock: int,
    capture_ms: int,
    samples: tuple[int, ...] | None = None,
    flags: PacketFlags = PacketFlags.NONE,
) -> AudioPacket:
    """Convenience factory used by tests and the simulator."""

    if samples is None:
        samples = (0,) * SAMPLES_PER_FRAME
    return AudioPacket(
        pod_id=pod_id,
        sequence=sequence,
        sample_clock=sample_clock,
        capture_ms=capture_ms,
        samples=samples,
        flags=flags,
    )
