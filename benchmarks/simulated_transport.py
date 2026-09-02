#!/usr/bin/env python3
"""Benchmark deterministic packet-fault tolerance without claiming RF hardware results."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import random
from pathlib import Path
import statistics
import time

from cueloop.constants import EVENT_CLASSES, FRAME_DURATION_MS, SAMPLE_RATE_HZ
from cueloop.pipeline import CueLoopPipeline
from cueloop.protocol import AudioPacket, PacketFlags, encode_audio
from cueloop.simulator import SyntheticAudio
from cueloop.storage import EventStore


@dataclass(frozen=True, slots=True)
class FaultProfile:
    name: str
    loss_rate: float
    jitter_ms: float
    reorder_rate: float


PROFILES = (
    FaultProfile("clean", 0.0, 0.0, 0.0),
    FaultProfile("moderate", 0.05, 15.0, 0.05),
    FaultProfile("severe", 0.20, 40.0, 0.15),
)


def run_trial(
    *,
    event: str,
    profile: FaultProfile,
    seed: int,
    seconds: float = 4.0,
) -> dict[str, object]:
    if event not in EVENT_CLASSES:
        raise ValueError(f"unsupported event {event!r}")
    if seconds < 2.0:
        raise ValueError("trial must be at least two seconds for temporal confirmation")
    rng = random.Random(seed)
    source = SyntheticAudio(seed=seed)
    store = EventStore()
    pipeline = CueLoopPipeline(store=store, location="Simulated transport benchmark")
    frame_seconds = FRAME_DURATION_MS / 1000.0
    frame_count = int(seconds / frame_seconds)
    base_arrival = time.monotonic()
    last_arrival = base_arrival
    held: bytes | None = None
    sent = 0
    dropped = 0
    reordered = 0
    emitted: list[str] = []

    def deliver(datagram: bytes, arrival: float) -> None:
        nonlocal sent, last_arrival
        last_arrival = max(last_arrival + 0.000001, arrival)
        emitted.extend(
            record.class_name
            for record in pipeline.handle_datagram(
                datagram, arrival_monotonic=last_arrival
            )
        )
        sent += 1

    started = time.perf_counter()
    try:
        for sequence in range(frame_count):
            sample_clock = sequence * int(SAMPLE_RATE_HZ * frame_seconds)
            flags = PacketFlags.SIMULATED
            if sequence == 0:
                flags |= PacketFlags.STREAM_RESTART
            packet = AudioPacket(
                pod_id=0xC0E10001,
                sequence=sequence,
                sample_clock=sample_clock,
                capture_ms=int(sequence * FRAME_DURATION_MS),
                samples=source.frame(event, sample_clock),
                battery_mv=0,
                rssi_dbm=-42,
                flags=flags,
            )
            datagram = encode_audio(packet)
            nominal_arrival = base_arrival + sequence * frame_seconds
            jitter = rng.uniform(-profile.jitter_ms, profile.jitter_ms) / 1000.0
            arrival = nominal_arrival + jitter
            if rng.random() < profile.loss_rate:
                dropped += 1
            elif held is None and rng.random() < profile.reorder_rate:
                held = datagram
            else:
                deliver(datagram, arrival)
                if held is not None:
                    deliver(held, arrival + 0.000001)
                    held = None
                    reordered += 1
        if held is not None:
            deliver(held, last_arrival + frame_seconds)
            reordered += 1
    finally:
        store.close()

    elapsed_ms = (time.perf_counter() - started) * 1000.0
    metrics = pipeline.jitter.metrics.snapshot()
    return {
        "event": event,
        "profile": profile.name,
        "seed": seed,
        "duration_seconds": seconds,
        "frames_generated": frame_count,
        "frames_sent": sent,
        "frames_dropped": dropped,
        "actual_drop_rate": round(dropped / frame_count, 6),
        "reorder_pairs": reordered,
        "target_detected": event in emitted,
        "emitted_classes": emitted,
        "receiver_reported_loss_rate": metrics["loss_rate"],
        "receiver_missing_frames": metrics["missing_frames"],
        "receiver_late_frames": metrics["late_frames"],
        "receiver_jitter_ms": metrics["jitter_ms"],
        "maximum_buffered_samples": pipeline.windows.maximum_buffered_samples,
        "execution_ms": round(elapsed_ms, 3),
        "evidence_tier": "simulated",
    }


def benchmark(*, seeds: list[int], seconds: float) -> dict[str, object]:
    if not seeds:
        raise ValueError("at least one seed is required")
    trials = [
        run_trial(event=event, profile=profile, seed=seed, seconds=seconds)
        for profile in PROFILES
        for event in EVENT_CLASSES
        for seed in seeds
    ]
    summaries: dict[str, dict[str, object]] = {}
    for profile in PROFILES:
        members = [trial for trial in trials if trial["profile"] == profile.name]
        summaries[profile.name] = {
            "profile": asdict(profile),
            "trial_count": len(members),
            "target_detected_count": sum(
                bool(trial["target_detected"]) for trial in members
            ),
            "target_detection_rate": round(
                statistics.fmean(bool(trial["target_detected"]) for trial in members),
                6,
            ),
            "mean_actual_drop_rate": round(
                statistics.fmean(float(trial["actual_drop_rate"]) for trial in members),
                6,
            ),
            "mean_receiver_reported_loss_rate": round(
                statistics.fmean(
                    float(trial["receiver_reported_loss_rate"]) for trial in members
                ),
                6,
            ),
        }
    return {
        "schema_version": 1,
        "evidence_tier": "simulated",
        "workload": (
            "project-authored deterministic acoustic signatures through encoded "
            "Protocol v1 datagrams, bounded receiver, windowing, synthetic classifier, "
            "and temporal policy"
        ),
        "claim_boundary": (
            "Software fault-injection evidence only; not real-audio accuracy, RF/link "
            "performance, UNO Q timing, or physical CuePod validation."
        ),
        "seeds": seeds,
        "seconds_per_trial": seconds,
        "profiles": [asdict(profile) for profile in PROFILES],
        "summaries": summaries,
        "trials": trials,
    }


def parse_seeds(value: str) -> list[int]:
    try:
        seeds = [int(item.strip()) for item in value.split(",") if item.strip()]
    except ValueError as error:
        raise argparse.ArgumentTypeError("seeds must be comma-separated integers") from error
    if not seeds:
        raise argparse.ArgumentTypeError("at least one seed is required")
    return seeds


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seeds", type=parse_seeds, default=parse_seeds("7,17,27,37,47")
    )
    parser.add_argument("--seconds", type=float, default=4.0)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = benchmark(seeds=args.seeds, seconds=args.seconds)
    except ValueError as error:
        parser.error(str(error))
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    if not args.quiet:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
