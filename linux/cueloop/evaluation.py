"""Provenance-gated, raw-audio-nonretaining classifier evaluation."""

from __future__ import annotations

from array import array
from collections import deque
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys
from typing import Iterable
import wave

from .constants import EVENT_CLASSES, SAMPLE_RATE_HZ, WINDOW_SAMPLES, WINDOW_STRIDE_SAMPLES
from .engine import DEFAULT_POLICIES
from .model import AudioClassifier


ALLOWED_SPLITS = frozenset(("calibration", "validation", "test"))


class DatasetValidationError(ValueError):
    """Raised before inference if a dataset record is unsafe or unreproducible."""


@dataclass(frozen=True, slots=True)
class EvaluationRecord:
    id: str
    path: Path
    labels: frozenset[str]
    split: str
    source: str
    license: str
    sha256: str


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_evaluation_manifest(
    path: str | Path, *, split: str
) -> tuple[str, list[EvaluationRecord]]:
    if split not in ALLOWED_SPLITS:
        raise DatasetValidationError(f"unsupported split {split!r}")
    manifest_path = Path(path).resolve()
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise DatasetValidationError(f"cannot read manifest: {error}") from error
    if manifest.get("schema_version") != 1:
        raise DatasetValidationError("unsupported evaluation-manifest schema")
    dataset_id = manifest.get("dataset_id")
    if not isinstance(dataset_id, str) or not dataset_id.strip():
        raise DatasetValidationError("dataset_id is required")
    raw_records = manifest.get("records")
    if not isinstance(raw_records, list):
        raise DatasetValidationError("records must be an array")

    records: list[EvaluationRecord] = []
    seen_ids: set[str] = set()
    for raw in raw_records:
        if not isinstance(raw, dict):
            raise DatasetValidationError("each record must be an object")
        record_split = raw.get("split")
        if record_split not in ALLOWED_SPLITS:
            raise DatasetValidationError(f"record has unsupported split {record_split!r}")
        record_id = raw.get("id")
        if not isinstance(record_id, str) or not record_id.strip():
            raise DatasetValidationError("record id is required")
        if record_id in seen_ids:
            raise DatasetValidationError(f"duplicate record id {record_id!r}")
        seen_ids.add(record_id)
        if raw.get("consent_confirmed") is not True:
            raise DatasetValidationError(f"{record_id}: consent_confirmed must be true")
        source = raw.get("source")
        license_name = raw.get("license")
        if not isinstance(source, str) or not source.strip():
            raise DatasetValidationError(f"{record_id}: source is required")
        if not isinstance(license_name, str) or not license_name.strip():
            raise DatasetValidationError(f"{record_id}: license is required")
        labels = raw.get("labels")
        if not isinstance(labels, list) or any(
            not isinstance(label, str) or label not in EVENT_CLASSES for label in labels
        ):
            raise DatasetValidationError(f"{record_id}: unsupported labels")
        if len(labels) != len(set(labels)):
            raise DatasetValidationError(f"{record_id}: duplicate labels")
        digest = raw.get("sha256")
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise DatasetValidationError(f"{record_id}: invalid lowercase SHA-256")
        raw_path = raw.get("path")
        if not isinstance(raw_path, str) or not raw_path:
            raise DatasetValidationError(f"{record_id}: path is required")
        audio_path = (manifest_path.parent / raw_path).resolve()
        if audio_path.suffix.lower() != ".wav" or not audio_path.is_file():
            raise DatasetValidationError(f"{record_id}: WAV file not found")
        actual_digest = file_digest(audio_path)
        if actual_digest != digest:
            raise DatasetValidationError(
                f"{record_id}: SHA-256 mismatch; expected {digest}, got {actual_digest}"
            )
        if record_split == split:
            records.append(
                EvaluationRecord(
                    id=record_id,
                    path=audio_path,
                    labels=frozenset(labels),
                    split=split,
                    source=source.strip(),
                    license=license_name.strip(),
                    sha256=digest,
                )
            )
    if not records:
        raise DatasetValidationError(f"manifest has no records in split {split!r}")
    return dataset_id.strip(), records


def read_pcm16_mono(path: Path) -> tuple[tuple[int, ...], float]:
    try:
        with wave.open(str(path), "rb") as source:
            if source.getnchannels() != 1:
                raise DatasetValidationError(f"{path.name}: expected mono WAV")
            if source.getsampwidth() != 2:
                raise DatasetValidationError(f"{path.name}: expected PCM16 WAV")
            if source.getframerate() != SAMPLE_RATE_HZ:
                raise DatasetValidationError(
                    f"{path.name}: expected {SAMPLE_RATE_HZ} Hz WAV"
                )
            if source.getcomptype() != "NONE":
                raise DatasetValidationError(f"{path.name}: compressed WAV unsupported")
            frame_count = source.getnframes()
            if frame_count <= 0:
                raise DatasetValidationError(f"{path.name}: empty WAV")
            raw = source.readframes(frame_count)
    except (OSError, wave.Error) as error:
        raise DatasetValidationError(f"cannot decode {path.name}: {error}") from error
    values = array("h")
    values.frombytes(raw)
    if sys.byteorder != "little":
        values.byteswap()
    return tuple(values), len(values) / SAMPLE_RATE_HZ


def audio_windows(samples: tuple[int, ...]) -> Iterable[tuple[int, ...]]:
    if len(samples) <= WINDOW_SAMPLES:
        yield samples + (0,) * (WINDOW_SAMPLES - len(samples))
        return
    starts = list(range(0, len(samples) - WINDOW_SAMPLES + 1, WINDOW_STRIDE_SAMPLES))
    final_start = len(samples) - WINDOW_SAMPLES
    if starts[-1] != final_start:
        starts.append(final_start)
    for start in starts:
        yield samples[start : start + WINDOW_SAMPLES]


def temporal_triggers(window_scores: list[dict[str, float]]) -> set[str]:
    triggered: set[str] = set()
    evidence = {label: deque() for label in EVENT_CLASSES}
    stride_seconds = WINDOW_STRIDE_SAMPLES / SAMPLE_RATE_HZ
    for window_index, scores in enumerate(window_scores):
        current = window_index * stride_seconds
        for label in EVENT_CLASSES:
            policy = DEFAULT_POLICIES[label]
            queue = evidence[label]
            cutoff = current - policy.confirmation_seconds
            while queue and queue[0][0] < cutoff:
                queue.popleft()
            score = max(0.0, min(1.0, float(scores.get(label, 0.0))))
            if policy.enabled and score >= policy.observe_threshold:
                queue.append((current, score))
            if len(queue) >= policy.minimum_hits:
                confidence = sum(value for _, value in queue) / len(queue)
                if confidence >= policy.alert_threshold:
                    triggered.add(label)
    return triggered


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _safe_ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def evaluate(
    classifier: AudioClassifier,
    records: list[EvaluationRecord],
    *,
    dataset_id: str,
) -> dict[str, object]:
    counters = {
        label: {"true_positive": 0, "false_positive": 0, "false_negative": 0, "true_negative": 0}
        for label in EVENT_CLASSES
    }
    calibration_pairs: list[tuple[float, int]] = []
    latencies: list[float] = []
    total_seconds = 0.0
    total_windows = 0
    missed = 0
    false_triggers = 0
    model_name = "not-run"
    evidence_tier = "unknown"

    for record in records:
        samples, duration = read_pcm16_mono(record.path)
        total_seconds += duration
        window_results = []
        for window in audio_windows(samples):
            classification = classifier.classify(window, SAMPLE_RATE_HZ)
            model_name = classification.model_name
            evidence_tier = classification.evidence_tier
            latencies.append(classification.inference_ms)
            window_results.append(classification.scores)
            total_windows += 1
        triggered = temporal_triggers(window_results)
        for label in EVENT_CLASSES:
            truth = label in record.labels
            predicted = label in triggered
            key = (
                "true_positive"
                if truth and predicted
                else "false_negative"
                if truth
                else "false_positive"
                if predicted
                else "true_negative"
            )
            counters[label][key] += 1
            if truth and not predicted:
                missed += 1
            if predicted and not truth:
                false_triggers += 1
            clip_score = max(float(scores.get(label, 0.0)) for scores in window_results)
            calibration_pairs.append((max(0.0, min(1.0, clip_score)), int(truth)))

    per_class: dict[str, dict[str, float | int]] = {}
    for label, counts in counters.items():
        tp = counts["true_positive"]
        fp = counts["false_positive"]
        fn = counts["false_negative"]
        precision = _safe_ratio(tp, tp + fp)
        recall = _safe_ratio(tp, tp + fn)
        per_class[label] = {
            **counts,
            "precision": round(precision, 6),
            "recall": round(recall, 6),
            "f1": round(_safe_ratio(2 * precision * recall, precision + recall), 6),
        }

    total_true_events = sum(len(record.labels) for record in records)
    brier = statistics.fmean((score - truth) ** 2 for score, truth in calibration_pairs)
    ece = 0.0
    calibration_bins: list[dict[str, float | int]] = []
    for bin_index in range(10):
        lower = bin_index / 10
        upper = (bin_index + 1) / 10
        members = [
            pair
            for pair in calibration_pairs
            if lower <= pair[0] <= upper and (bin_index == 9 or pair[0] < upper)
        ]
        if not members:
            continue
        confidence = statistics.fmean(score for score, _ in members)
        frequency = statistics.fmean(truth for _, truth in members)
        ece += len(members) / len(calibration_pairs) * abs(confidence - frequency)
        calibration_bins.append(
            {
                "lower": lower,
                "upper": upper,
                "count": len(members),
                "mean_score": round(confidence, 6),
                "positive_frequency": round(frequency, 6),
            }
        )

    return {
        "schema_version": 1,
        "dataset_id": dataset_id,
        "split": records[0].split,
        "evidence_tier": evidence_tier,
        "model": model_name,
        "record_count": len(records),
        "window_count": total_windows,
        "audio_hours": round(total_seconds / 3600.0, 6),
        "temporal_policy": "production defaults; at least two qualifying windows",
        "per_class": per_class,
        "missed_event_rate": round(_safe_ratio(missed, total_true_events), 6),
        "false_triggers_per_audio_hour": round(
            _safe_ratio(false_triggers, total_seconds / 3600.0), 6
        ),
        "calibration": {
            "brier_score": round(brier, 6),
            "expected_calibration_error_10_bin": round(ece, 6),
            "bins": calibration_bins,
        },
        "inference_latency_ms": {
            "mean": round(statistics.fmean(latencies), 3),
            "p50": round(_percentile(latencies, 0.50), 3),
            "p95": round(_percentile(latencies, 0.95), 3),
            "p99": round(_percentile(latencies, 0.99), 3),
            "maximum": round(max(latencies), 3),
        },
        "claim_boundary": (
            "Metrics apply only to the listed manifest records and execution host; "
            "they are not physical CuePod/UNO Q measurements unless separately recorded."
        ),
    }
