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
ALLOWED_BACKGROUND_CONDITIONS = frozenset(
    ("quiet", "speech", "television", "music", "fan", "workshop", "other")
)


class DatasetValidationError(ValueError):
    """Raised before inference if a dataset record is unsafe or unreproducible."""


@dataclass(frozen=True, slots=True)
class EventInterval:
    label: str
    start_seconds: float
    end_seconds: float


@dataclass(frozen=True, slots=True)
class EvaluationRecord:
    id: str
    path: Path
    labels: frozenset[str]
    split: str
    source: str
    license: str
    sha256: str
    environment: str
    distance_m: float | None
    closed_door: bool | None
    background_conditions: tuple[str, ...]
    event_intervals: tuple[EventInterval, ...]


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
        environment = raw.get("environment", "unspecified")
        if not isinstance(environment, str) or not environment.strip():
            raise DatasetValidationError(f"{record_id}: environment must be nonempty")
        raw_distance = raw.get("distance_m")
        if raw_distance is None:
            distance_m = None
        elif isinstance(raw_distance, bool) or not isinstance(raw_distance, (int, float)):
            raise DatasetValidationError(f"{record_id}: distance_m must be numeric")
        elif raw_distance < 0:
            raise DatasetValidationError(f"{record_id}: distance_m cannot be negative")
        else:
            distance_m = float(raw_distance)
        closed_door = raw.get("closed_door")
        if closed_door is not None and not isinstance(closed_door, bool):
            raise DatasetValidationError(f"{record_id}: closed_door must be boolean")
        raw_backgrounds = raw.get("background_conditions", [])
        if not isinstance(raw_backgrounds, list) or any(
            not isinstance(condition, str)
            or condition not in ALLOWED_BACKGROUND_CONDITIONS
            for condition in raw_backgrounds
        ):
            raise DatasetValidationError(
                f"{record_id}: unsupported background_conditions"
            )
        if len(raw_backgrounds) != len(set(raw_backgrounds)):
            raise DatasetValidationError(
                f"{record_id}: duplicate background_conditions"
            )
        raw_intervals = raw.get("event_intervals", [])
        if not isinstance(raw_intervals, list):
            raise DatasetValidationError(f"{record_id}: event_intervals must be an array")
        intervals: list[EventInterval] = []
        interval_labels: set[str] = set()
        for raw_interval in raw_intervals:
            if not isinstance(raw_interval, dict):
                raise DatasetValidationError(
                    f"{record_id}: event interval must be an object"
                )
            interval_label = raw_interval.get("label")
            start_seconds = raw_interval.get("start_seconds")
            end_seconds = raw_interval.get("end_seconds")
            if not isinstance(interval_label, str) or interval_label not in labels:
                raise DatasetValidationError(
                    f"{record_id}: interval label must appear in record labels"
                )
            if interval_label in interval_labels:
                raise DatasetValidationError(
                    f"{record_id}: at most one interval per label is supported"
                )
            if (
                isinstance(start_seconds, bool)
                or not isinstance(start_seconds, (int, float))
                or isinstance(end_seconds, bool)
                or not isinstance(end_seconds, (int, float))
                or start_seconds < 0
                or end_seconds <= start_seconds
            ):
                raise DatasetValidationError(
                    f"{record_id}: invalid event interval bounds"
                )
            interval_labels.add(interval_label)
            intervals.append(
                EventInterval(
                    label=interval_label,
                    start_seconds=float(start_seconds),
                    end_seconds=float(end_seconds),
                )
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
                    environment=environment.strip(),
                    distance_m=distance_m,
                    closed_door=closed_door,
                    background_conditions=tuple(raw_backgrounds),
                    event_intervals=tuple(intervals),
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


def temporal_qualifying_times(
    window_scores: list[dict[str, float]],
) -> dict[str, list[float]]:
    qualifying = {label: [] for label in EVENT_CLASSES}
    evidence = {label: deque() for label in EVENT_CLASSES}
    stride_seconds = WINDOW_STRIDE_SAMPLES / SAMPLE_RATE_HZ
    window_seconds = WINDOW_SAMPLES / SAMPLE_RATE_HZ
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
                    qualifying[label].append(current + window_seconds)
    return qualifying


def temporal_triggers(window_scores: list[dict[str, float]]) -> set[str]:
    return {
        label
        for label, times in temporal_qualifying_times(window_scores).items()
        if times
    }


def single_window_trigger_times(
    window_scores: list[dict[str, float]],
) -> dict[str, list[float]]:
    qualifying = {label: [] for label in EVENT_CLASSES}
    stride_seconds = WINDOW_STRIDE_SAMPLES / SAMPLE_RATE_HZ
    window_seconds = WINDOW_SAMPLES / SAMPLE_RATE_HZ
    for window_index, scores in enumerate(window_scores):
        detection_time = window_index * stride_seconds + window_seconds
        for label in EVENT_CLASSES:
            policy = DEFAULT_POLICIES[label]
            score = max(0.0, min(1.0, float(scores.get(label, 0.0))))
            if policy.enabled and score >= policy.alert_threshold:
                qualifying[label].append(detection_time)
    return qualifying


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


def _new_counters() -> dict[str, dict[str, int]]:
    return {
        label: {
            "true_positive": 0,
            "false_positive": 0,
            "false_negative": 0,
            "true_negative": 0,
        }
        for label in EVENT_CLASSES
    }


def _update_counters(
    counters: dict[str, dict[str, int]],
    *,
    truth: frozenset[str],
    predicted: set[str],
) -> None:
    for label in EVENT_CLASSES:
        actual = label in truth
        detected = label in predicted
        key = (
            "true_positive"
            if actual and detected
            else "false_negative"
            if actual
            else "false_positive"
            if detected
            else "true_negative"
        )
        counters[label][key] += 1


def _per_class_metrics(
    counters: dict[str, dict[str, int]],
) -> dict[str, dict[str, object]]:
    metrics: dict[str, dict[str, object]] = {}
    for label, counts in counters.items():
        tp = counts["true_positive"]
        fp = counts["false_positive"]
        fn = counts["false_negative"]
        tn = counts["true_negative"]
        precision = _safe_ratio(tp, tp + fp)
        recall = _safe_ratio(tp, tp + fn)
        metrics[label] = {
            **counts,
            "support": tp + fn,
            "precision": round(precision, 6),
            "recall": round(recall, 6),
            "f1": round(_safe_ratio(2 * precision * recall, precision + recall), 6),
            "confusion_matrix": [[tn, fp], [fn, tp]],
            "confusion_matrix_labels": ["negative", "positive"],
        }
    return metrics


def evaluate(
    classifier: AudioClassifier,
    records: list[EvaluationRecord],
    *,
    dataset_id: str,
) -> dict[str, object]:
    temporal_counters = _new_counters()
    single_window_counters = _new_counters()
    calibration_pairs: list[tuple[float, int]] = []
    latencies: list[float] = []
    annotated_event_latencies_ms: list[float] = []
    annotated_interval_count = 0
    annotated_interval_misses = 0
    condition_accumulators: dict[str, dict[str, float | int]] = {}
    total_seconds = 0.0
    total_windows = 0
    model_name = "not-run"
    evidence_tier = "unknown"

    for record in records:
        samples, duration = read_pcm16_mono(record.path)
        for interval in record.event_intervals:
            if interval.end_seconds > duration:
                raise DatasetValidationError(
                    f"{record.id}: event interval ends after WAV duration"
                )
        total_seconds += duration
        window_results = []
        for window in audio_windows(samples):
            classification = classifier.classify(window, SAMPLE_RATE_HZ)
            model_name = classification.model_name
            evidence_tier = classification.evidence_tier
            latencies.append(classification.inference_ms)
            window_results.append(classification.scores)
            total_windows += 1
        temporal_times = temporal_qualifying_times(window_results)
        single_times = single_window_trigger_times(window_results)
        temporal_triggered = {
            label for label, times in temporal_times.items() if times
        }
        single_triggered = {label for label, times in single_times.items() if times}
        _update_counters(
            temporal_counters,
            truth=record.labels,
            predicted=temporal_triggered,
        )
        _update_counters(
            single_window_counters,
            truth=record.labels,
            predicted=single_triggered,
        )

        record_misses = len(record.labels - temporal_triggered)
        record_false_triggers = len(temporal_triggered - record.labels)
        door_condition = (
            "unspecified"
            if record.closed_door is None
            else "closed"
            if record.closed_door
            else "open"
        )
        distance_condition = (
            "unspecified"
            if record.distance_m is None
            else f"{record.distance_m:.2f}"
        )
        slice_keys = {
            f"environment:{record.environment}",
            f"door:{door_condition}",
            f"distance_m:{distance_condition}",
        }
        backgrounds = record.background_conditions or ("unspecified",)
        slice_keys.update(f"background:{condition}" for condition in backgrounds)
        for key in slice_keys:
            accumulator = condition_accumulators.setdefault(
                key,
                {
                    "record_count": 0,
                    "audio_seconds": 0.0,
                    "true_events": 0,
                    "missed_events": 0,
                    "false_triggers": 0,
                },
            )
            accumulator["record_count"] += 1
            accumulator["audio_seconds"] += duration
            accumulator["true_events"] += len(record.labels)
            accumulator["missed_events"] += record_misses
            accumulator["false_triggers"] += record_false_triggers

        for interval in record.event_intervals:
            annotated_interval_count += 1
            deadline = (
                interval.end_seconds
                + DEFAULT_POLICIES[interval.label].confirmation_seconds
                + WINDOW_SAMPLES / SAMPLE_RATE_HZ
            )
            candidates = [
                timestamp
                for timestamp in temporal_times[interval.label]
                if interval.start_seconds <= timestamp <= deadline
            ]
            if not candidates:
                annotated_interval_misses += 1
            else:
                annotated_event_latencies_ms.append(
                    (candidates[0] - interval.start_seconds) * 1000.0
                )

        for label in EVENT_CLASSES:
            truth = label in record.labels
            clip_score = max(float(scores.get(label, 0.0)) for scores in window_results)
            calibration_pairs.append((max(0.0, min(1.0, clip_score)), int(truth)))

    per_class = _per_class_metrics(temporal_counters)
    single_window_per_class = _per_class_metrics(single_window_counters)
    missed = sum(counts["false_negative"] for counts in temporal_counters.values())
    false_triggers = sum(
        counts["false_positive"] for counts in temporal_counters.values()
    )
    single_missed = sum(
        counts["false_negative"] for counts in single_window_counters.values()
    )
    single_false_triggers = sum(
        counts["false_positive"] for counts in single_window_counters.values()
    )
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

    condition_slices: dict[str, dict[str, float | int]] = {}
    for key, values in sorted(condition_accumulators.items()):
        audio_seconds = float(values["audio_seconds"])
        true_events = int(values["true_events"])
        condition_slices[key] = {
            "record_count": int(values["record_count"]),
            "audio_hours": round(audio_seconds / 3600.0, 6),
            "true_events": true_events,
            "missed_events": int(values["missed_events"]),
            "missed_event_rate": round(
                _safe_ratio(float(values["missed_events"]), true_events), 6
            ),
            "false_triggers": int(values["false_triggers"]),
            "false_triggers_per_audio_hour": round(
                _safe_ratio(float(values["false_triggers"]), audio_seconds / 3600.0),
                6,
            ),
        }

    if annotated_event_latencies_ms:
        annotated_latency: dict[str, object] = {
            "annotated_interval_count": annotated_interval_count,
            "detected_interval_count": len(annotated_event_latencies_ms),
            "missed_interval_count": annotated_interval_misses,
            "mean": round(statistics.fmean(annotated_event_latencies_ms), 3),
            "p50": round(_percentile(annotated_event_latencies_ms, 0.50), 3),
            "p95": round(_percentile(annotated_event_latencies_ms, 0.95), 3),
            "maximum": round(max(annotated_event_latencies_ms), 3),
        }
    else:
        annotated_latency = {
            "annotated_interval_count": annotated_interval_count,
            "detected_interval_count": 0,
            "missed_interval_count": annotated_interval_misses,
            "mean": None,
            "p50": None,
            "p95": None,
            "maximum": None,
        }
    annotated_latency["method"] = (
        "WAV event onset to first temporally qualifying decision window; excludes "
        "CuePod capture, network, target scheduling, Bridge, and physical-output delay"
    )

    return {
        "schema_version": 2,
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
        "confirmation_comparison": {
            "single_window_rule": "one window at the production alert threshold",
            "single_window_per_class": single_window_per_class,
            "temporal": {
                "missed_events": missed,
                "false_triggers": false_triggers,
                "false_triggers_per_audio_hour": round(
                    _safe_ratio(false_triggers, total_seconds / 3600.0), 6
                ),
            },
            "single_window": {
                "missed_events": single_missed,
                "false_triggers": single_false_triggers,
                "false_triggers_per_audio_hour": round(
                    _safe_ratio(single_false_triggers, total_seconds / 3600.0), 6
                ),
            },
            "temporal_minus_single_window": {
                "missed_events": missed - single_missed,
                "false_triggers": false_triggers - single_false_triggers,
            },
        },
        "condition_slices": condition_slices,
        "annotated_audio_to_decision_latency_ms": annotated_latency,
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
