from __future__ import annotations

import unittest

from cueloop.buffering import JitterBuffer, WindowAccumulator, sequence_distance
from cueloop.protocol import PacketFlags, nominal_audio_packet


def packet(sequence: int, *, flags: PacketFlags = PacketFlags.NONE):
    return nominal_audio_packet(
        pod_id=1,
        sequence=sequence,
        sample_clock=sequence * 320,
        capture_ms=sequence * 20,
        flags=flags,
    )


class BufferingTests(unittest.TestCase):
    def test_sequence_wrap_distance(self) -> None:
        self.assertEqual(sequence_distance(0, 0xFFFFFFFF), 1)
        self.assertEqual(sequence_distance(0xFFFFFFFF, 0), -1)

    def test_reorders_without_loss(self) -> None:
        jitter = JitterBuffer(reorder_depth=3, max_packets=8)
        self.assertEqual([f.packet.sequence for f in jitter.push(packet(10), arrival_monotonic=1.0)], [10])
        self.assertEqual(jitter.push(packet(12), arrival_monotonic=1.02), [])
        released = jitter.push(packet(11), arrival_monotonic=1.04)
        self.assertEqual([f.packet.sequence for f in released], [11, 12])
        self.assertEqual(jitter.metrics.missing_frames, 0)

    def test_missing_frame_becomes_silence(self) -> None:
        jitter = JitterBuffer(reorder_depth=3, max_packets=8)
        jitter.push(packet(0), arrival_monotonic=1.0)
        jitter.push(packet(2), arrival_monotonic=1.02)
        jitter.push(packet(3), arrival_monotonic=1.04)
        released = jitter.push(packet(4), arrival_monotonic=1.06)
        self.assertTrue(released[0].synthetic_gap)
        self.assertEqual([f.packet.sequence for f in released[1:]], [2, 3, 4])
        self.assertEqual(jitter.metrics.missing_frames, 1)

    def test_duplicate_and_restart(self) -> None:
        jitter = JitterBuffer(reorder_depth=2, max_packets=5)
        jitter.push(packet(4), arrival_monotonic=1.0)
        self.assertEqual(jitter.push(packet(4), arrival_monotonic=1.01), [])
        self.assertEqual(jitter.metrics.late_frames, 1)
        released = jitter.push(
            packet(0, flags=PacketFlags.STREAM_RESTART),
            arrival_monotonic=2.0,
        )
        self.assertEqual(released[0].packet.sequence, 0)
        self.assertEqual(jitter.metrics.stream_restarts, 1)

    def test_huge_sequence_jump_is_constant_work(self) -> None:
        jitter = JitterBuffer(reorder_depth=3, max_packets=8)
        jitter.push(packet(0), arrival_monotonic=1.0)
        jitter.push(packet(1_000_000), arrival_monotonic=1.1)
        jitter.push(packet(1_000_001), arrival_monotonic=1.2)
        released = jitter.push(packet(1_000_002), arrival_monotonic=1.3)
        self.assertTrue(released[0].synthetic_gap)
        self.assertEqual(
            [frame.packet.sequence for frame in released[1:]],
            [1_000_000, 1_000_001, 1_000_002],
        )
        self.assertEqual(jitter.metrics.missing_frames, 999_999)

    def test_window_buffer_is_bounded_and_overlapping(self) -> None:
        accumulator = WindowAccumulator(window_samples=8, stride_samples=4)
        windows = accumulator.append(tuple(range(20)), arrival_monotonic=1.0)
        self.assertEqual([window for window, _ in windows], [tuple(range(8)), tuple(range(4, 12)), tuple(range(8, 16)), tuple(range(12, 20))])
        self.assertLessEqual(accumulator.buffered_samples, accumulator.maximum_buffered_samples)


if __name__ == "__main__":
    unittest.main()
