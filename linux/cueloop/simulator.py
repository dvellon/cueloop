"""Simulated CuePod sender with WAV replay and network fault injection."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import math
import random
import select
import socket
import time
import wave

from .constants import DEFAULT_TCP_PORT, SAMPLE_RATE_HZ, SAMPLES_PER_FRAME
from .protocol import (
    AudioPacket,
    PacketFlags,
    STREAM_LENGTH,
    decode_receiver_ack,
    decode_stream_length,
    encode_audio,
    encode_stream_frame,
)


SYNTHETIC_EVENTS = (
    "background",
    "door_knock",
    "alarm_beep",
    "dog_bark",
    "attention_call",
)


@dataclass(slots=True)
class SequenceItem:
    event: str
    seconds: float


def parse_sequence(value: str) -> list[SequenceItem]:
    result: list[SequenceItem] = []
    for item in value.split(","):
        try:
            event, duration_text = item.strip().split(":", 1)
            duration = float(duration_text)
        except ValueError as error:
            raise argparse.ArgumentTypeError(
                "sequence must use event:seconds,event:seconds"
            ) from error
        if event not in SYNTHETIC_EVENTS or duration <= 0:
            raise argparse.ArgumentTypeError(f"invalid sequence item {item!r}")
        result.append(SequenceItem(event, duration))
    if not result:
        raise argparse.ArgumentTypeError("sequence cannot be empty")
    return result


class SyntheticAudio:
    """Generate owned deterministic test signatures—not real-world evidence."""

    def __init__(self, *, seed: int = 7) -> None:
        self.random = random.Random(seed)

    @staticmethod
    def _carrier(frequency: float, seconds: float) -> float:
        return math.sin(2.0 * math.pi * frequency * seconds)

    def sample(self, event: str, event_sample: int) -> int:
        seconds = event_sample / SAMPLE_RATE_HZ
        noise = self.random.uniform(-0.006, 0.006)
        value = noise
        if event == "background":
            value += 0.003 * self._carrier(83.0, seconds)
        elif event == "alarm_beep":
            phase = seconds % 0.9
            gate = 1.0 if phase < 0.62 else 0.0
            value += 0.58 * gate * self._carrier(1400.0, seconds)
        elif event == "attention_call":
            phase = seconds % 1.1
            gate = math.sin(math.pi * phase / 0.72) ** 2 if phase < 0.72 else 0.0
            value += 0.50 * gate * self._carrier(900.0, seconds)
        elif event == "dog_bark":
            phase = seconds % 0.72
            gate = math.sin(math.pi * phase / 0.30) ** 2 if phase < 0.30 else 0.0
            value += 0.65 * gate * self._carrier(650.0, seconds)
        elif event == "door_knock":
            phase = seconds % 0.95
            envelope = 0.0
            for onset in (0.08, 0.32):
                elapsed = phase - onset
                if 0 <= elapsed < 0.18:
                    envelope += math.exp(-elapsed * 17.0)
            value += 0.90 * envelope * self._carrier(280.0, seconds)
        else:
            raise ValueError(f"unknown synthetic event {event}")
        return int(max(-1.0, min(0.999969, value)) * 32768)

    def frame(self, event: str, event_sample: int) -> tuple[int, ...]:
        return tuple(
            self.sample(event, event_sample + offset)
            for offset in range(SAMPLES_PER_FRAME)
        )

    def window(self, event: str) -> tuple[int, ...]:
        return tuple(self.sample(event, index) for index in range(SAMPLE_RATE_HZ))


class WavFrames:
    def __init__(self, path: str) -> None:
        self._wave = wave.open(path, "rb")
        if (
            self._wave.getnchannels() != 1
            or self._wave.getsampwidth() != 2
            or self._wave.getframerate() != SAMPLE_RATE_HZ
        ):
            self._wave.close()
            raise ValueError("WAV replay requires mono, signed PCM16, 16000 Hz")

    def frame(self) -> tuple[int, ...] | None:
        import struct

        raw = self._wave.readframes(SAMPLES_PER_FRAME)
        if not raw:
            return None
        count = len(raw) // 2
        samples = struct.unpack(f"<{count}h", raw)
        if count < SAMPLES_PER_FRAME:
            samples += (0,) * (SAMPLES_PER_FRAME - count)
        return samples

    def close(self) -> None:
        self._wave.close()


def drain_acknowledgements(sock: socket.socket, pending: bytearray) -> int:
    """Consume and validate any complete receiver ACKs without blocking sends."""

    while select.select([sock], [], [], 0)[0]:
        chunk = sock.recv(4096)
        if not chunk:
            raise ConnectionError("CueLoop receiver closed the TCP connection")
        pending.extend(chunk)

    accepted = 0
    while len(pending) >= STREAM_LENGTH.size:
        payload_length = decode_stream_length(bytes(pending[: STREAM_LENGTH.size]))
        frame_length = STREAM_LENGTH.size + payload_length
        if len(pending) < frame_length:
            break
        decode_receiver_ack(bytes(pending[STREAM_LENGTH.size : frame_length]))
        del pending[:frame_length]
        accepted += 1
    return accepted


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Simulated CueLoop CuePod")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=DEFAULT_TCP_PORT)
    parser.add_argument("--connect-timeout", type=float, default=5.0)
    parser.add_argument("--pod-id", type=int, default=0xC0E10001)
    parser.add_argument(
        "--sequence",
        type=parse_sequence,
        default=parse_sequence(
            "background:2,door_knock:4,background:2,alarm_beep:4,"
            "background:2,dog_bark:4,background:2,attention_call:4"
        ),
    )
    parser.add_argument("--wav", help="Replay a mono PCM16 16 kHz WAV instead")
    parser.add_argument("--loss", type=float, default=0.0, help="0..1 packet drop rate")
    parser.add_argument("--jitter-ms", type=float, default=0.0)
    parser.add_argument("--latency-ms", type=float, default=0.0)
    parser.add_argument("--reorder-rate", type=float, default=0.0)
    parser.add_argument("--restart-interval", type=float, default=0.0)
    parser.add_argument("--run-seconds", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--battery-mv", type=int, default=3950)
    return parser


def validate_faults(args: argparse.Namespace) -> None:
    if not 0 <= args.loss <= 1 or not 0 <= args.reorder_rate <= 1:
        raise ValueError("loss and reorder-rate must be between 0 and 1")
    if args.jitter_ms < 0 or args.latency_ms < 0 or args.restart_interval < 0:
        raise ValueError("timing fault values cannot be negative")
    if args.connect_timeout <= 0:
        raise ValueError("connect-timeout must be positive")
    if not 0 <= args.battery_mv <= 0xFFFF:
        raise ValueError("battery-mv must fit uint16")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    validate_faults(args)
    rng = random.Random(args.seed)
    source = SyntheticAudio(seed=args.seed)
    wav_source = WavFrames(args.wav) if args.wav else None
    destination = (args.host, args.port)
    sock = socket.create_connection(destination, timeout=args.connect_timeout)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sock.settimeout(None)
    started = time.monotonic()
    next_send = started + args.latency_ms / 1000.0
    next_restart = (
        started + args.restart_interval if args.restart_interval > 0 else float("inf")
    )
    sequence = 0
    sample_clock = 0
    event_index = 0
    event_sample = 0
    restart_flag = True
    held: bytes | None = None
    sent = 0
    dropped = 0
    reordered = 0
    acknowledgements = 0
    ack_buffer = bytearray()
    current_name = "WAV replay" if wav_source else args.sequence[0].event
    print(
        f"Simulated CuePod -> tcp://{args.host}:{args.port}\n"
        f"Input: {current_name}; loss={args.loss:.1%}, jitter={args.jitter_ms:.1f} ms, "
        f"latency={args.latency_ms:.1f} ms. Press Ctrl+C to stop."
    )
    try:
        while args.run_seconds <= 0 or time.monotonic() - started < args.run_seconds:
            now = time.monotonic()
            if now >= next_restart:
                sequence = 0
                sample_clock = 0
                restart_flag = True
                next_restart += args.restart_interval
                print("[simulator] injected stream restart")

            if wav_source is not None:
                samples = wav_source.frame()
                if samples is None:
                    break
            else:
                item = args.sequence[event_index]
                samples = source.frame(item.event, event_sample)
                event_sample += SAMPLES_PER_FRAME
                if event_sample >= int(item.seconds * SAMPLE_RATE_HZ):
                    event_index = (event_index + 1) % len(args.sequence)
                    event_sample = 0
                    print(f"[simulator] event -> {args.sequence[event_index].event}")

            flags = PacketFlags.SIMULATED | PacketFlags.BATTERY_VALID
            if restart_flag:
                flags |= PacketFlags.STREAM_RESTART
                restart_flag = False
            packet = AudioPacket(
                pod_id=args.pod_id,
                sequence=sequence,
                sample_clock=sample_clock,
                capture_ms=(sample_clock * 1000 // SAMPLE_RATE_HZ) & 0xFFFFFFFF,
                samples=samples,
                battery_mv=args.battery_mv,
                rssi_dbm=-42,
                flags=flags,
            )
            framed_packet = encode_stream_frame(encode_audio(packet))
            if rng.random() < args.loss:
                dropped += 1
            elif held is None and rng.random() < args.reorder_rate:
                held = framed_packet
            else:
                sock.sendall(framed_packet)
                sent += 1
                if held is not None:
                    sock.sendall(held)
                    sent += 1
                    reordered += 1
                    held = None

            acknowledgements += drain_acknowledgements(sock, ack_buffer)

            sequence = (sequence + 1) & 0xFFFFFFFF
            sample_clock += len(samples)
            jitter = rng.uniform(-args.jitter_ms, args.jitter_ms) / 1000.0
            next_send += len(samples) / SAMPLE_RATE_HZ
            sleep_until = max(time.monotonic(), next_send + jitter)
            time.sleep(max(0.0, sleep_until - time.monotonic()))
    except KeyboardInterrupt:
        pass
    finally:
        if held is not None:
            sock.sendall(held)
            sent += 1
        if wav_source is not None:
            wav_source.close()
        sock.close()
    print(
        f"[simulator] stopped: sent={sent}, dropped={dropped}, "
        f"reordered={reordered}, acknowledgements={acknowledgements}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
