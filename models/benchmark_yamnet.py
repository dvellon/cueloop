#!/usr/bin/env python3
"""Benchmark real YAMNet inference on an explicitly synthetic workload."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from importlib.metadata import version
import json
import math
import os
from pathlib import Path
import platform
import resource
import statistics

from cueloop.simulator import SyntheticAudio
from cueloop.yamnet import DEFAULT_YAMNET_SHA256, YamnetClassifier


ROOT = Path(__file__).resolve().parents[1]


def percentile(values: list[float], quantile: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        type=Path,
        default=ROOT / "models" / "artifacts" / "yamnet-classification-tflite-v1.tflite",
    )
    parser.add_argument(
        "--mapping", type=Path, default=ROOT / "models" / "class_mapping.json"
    )
    parser.add_argument("--model-sha256", default=DEFAULT_YAMNET_SHA256)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--warmup", type=int, default=10)
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.warmup < 1 or args.iterations < 1:
        parser.error("warmup and iterations must be positive")

    classifier = YamnetClassifier(
        args.model,
        args.mapping,
        expected_sha256=args.model_sha256,
        num_threads=args.threads,
        evidence_tier="development-computer",
    )
    events = ("background", "door_knock", "alarm_beep", "dog_bark", "attention_call")
    windows = {event: SyntheticAudio(seed=17).window(event) for event in events}
    for index in range(args.warmup):
        classifier.classify(windows[events[index % len(events)]], 16_000)

    latencies: list[float] = []
    mapped_examples: dict[str, dict[str, float]] = {}
    for index in range(args.iterations):
        event = events[index % len(events)]
        result = classifier.classify(windows[event], 16_000)
        latencies.append(result.inference_ms)
        if event not in mapped_examples:
            mapped_examples[event] = {
                label: round(score, 6)
                for label, score in sorted(
                    result.scores.items(), key=lambda item: item[1], reverse=True
                )[:3]
            }

    result = {
        "schema_version": 1,
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_tier": "development-computer / synthetic workload",
        "accuracy_evaluated": False,
        "claim_boundary": (
            "Measures local LiteRT inference time only. Synthetic tones are not "
            "real-event accuracy, UNO Q performance, or physical CuePod evidence."
        ),
        "host": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "logical_cpus": os.cpu_count(),
        },
        "runtime": {
            "ai-edge-litert": version("ai-edge-litert"),
            "numpy": version("numpy"),
            "threads": args.threads,
        },
        "model": {
            "id": classifier.model_name,
            "sha256": args.model_sha256,
            "bytes": args.model.stat().st_size,
        },
        "workload": {
            "warmup_iterations": args.warmup,
            "measured_iterations": args.iterations,
            "sample_rate_hz": 16_000,
            "pipeline_window_samples": 16_000,
            "model_crop_samples": 15_600,
            "signals": list(events),
            "mapped_examples_not_accuracy": mapped_examples,
        },
        "latency_ms": {
            "minimum": round(min(latencies), 3),
            "mean": round(statistics.fmean(latencies), 3),
            "p50": round(percentile(latencies, 0.50), 3),
            "p95": round(percentile(latencies, 0.95), 3),
            "p99": round(percentile(latencies, 0.99), 3),
            "maximum": round(max(latencies), 3),
        },
        "process_peak_rss_kib_linux": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

