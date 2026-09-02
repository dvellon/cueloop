"""Optional, checksum-pinned YAMNet LiteRT classifier adapter."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from threading import RLock
import time
from typing import Sequence
from zipfile import BadZipFile, ZipFile

from .constants import EVENT_CLASSES, SAMPLE_RATE_HZ
from .model import Classification


YAMNET_INPUT_SAMPLES = 15_600
YAMNET_LABEL_COUNT = 521
DEFAULT_YAMNET_SHA256 = (
    "10c95ea3eb9a7bb4cb8bddf6feb023250381008177ac162ce169694d05c317de"
)


class ModelConfigurationError(ValueError):
    """Raised when a model or mapping violates the pinned interface contract."""


def file_sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def load_mapping(path: str | Path) -> dict[str, object]:
    mapping_path = Path(path)
    try:
        mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ModelConfigurationError(f"cannot read mapping {mapping_path}: {error}") from error
    if mapping.get("schema_version") != 1:
        raise ModelConfigurationError("unsupported class-mapping schema")
    if mapping.get("label_count") != YAMNET_LABEL_COUNT:
        raise ModelConfigurationError("mapping must declare exactly 521 labels")
    if mapping.get("aggregation") != "max":
        raise ModelConfigurationError("only max aggregation is supported in V1")
    groups = mapping.get("target_groups")
    if not isinstance(groups, dict) or set(groups) != set(EVENT_CLASSES):
        raise ModelConfigurationError("mapping target groups must match CueLoop classes")
    background = mapping.get("background_group")
    if not isinstance(background, list) or not background:
        raise ModelConfigurationError("mapping requires a background group")
    for group_name, entries in [*groups.items(), ("background", background)]:
        if not isinstance(entries, list) or not entries:
            raise ModelConfigurationError(f"mapping group {group_name} is empty")
        for entry in entries:
            if not isinstance(entry, dict):
                raise ModelConfigurationError(f"mapping group {group_name} has invalid entry")
            index = entry.get("index")
            label = entry.get("label")
            if not isinstance(index, int) or not 0 <= index < YAMNET_LABEL_COUNT:
                raise ModelConfigurationError(f"invalid index in mapping group {group_name}")
            if not isinstance(label, str) or not label:
                raise ModelConfigurationError(f"missing label in mapping group {group_name}")
    return mapping


def embedded_labels(model_path: str | Path) -> tuple[str, ...]:
    try:
        with ZipFile(model_path) as archive:
            labels = archive.read("yamnet_label_list.txt").decode("utf-8").splitlines()
    except (OSError, BadZipFile, KeyError, UnicodeDecodeError) as error:
        raise ModelConfigurationError(
            "model does not contain a readable yamnet_label_list.txt"
        ) from error
    if len(labels) != YAMNET_LABEL_COUNT:
        raise ModelConfigurationError(
            f"model contains {len(labels)} labels; expected {YAMNET_LABEL_COUNT}"
        )
    return tuple(labels)


def validate_mapping_labels(
    mapping: dict[str, object], labels: Sequence[str]
) -> None:
    groups = mapping["target_groups"]
    background = mapping["background_group"]
    assert isinstance(groups, dict)
    assert isinstance(background, list)
    for group_name, entries in [*groups.items(), ("background", background)]:
        assert isinstance(entries, list)
        for entry in entries:
            assert isinstance(entry, dict)
            index = int(entry["index"])
            expected = str(entry["label"])
            if labels[index] != expected:
                raise ModelConfigurationError(
                    f"mapping label mismatch for {group_name}[{index}]: "
                    f"expected {expected!r}, model has {labels[index]!r}"
                )


def aggregate_scores(
    raw_scores: Sequence[float], mapping: dict[str, object]
) -> dict[str, float]:
    if len(raw_scores) != YAMNET_LABEL_COUNT:
        raise ModelConfigurationError(
            f"model returned {len(raw_scores)} scores; expected {YAMNET_LABEL_COUNT}"
        )
    groups = mapping["target_groups"]
    background = mapping["background_group"]
    assert isinstance(groups, dict)
    assert isinstance(background, list)

    result: dict[str, float] = {}
    for group_name, entries in groups.items():
        assert isinstance(entries, list)
        result[str(group_name)] = max(
            max(0.0, min(1.0, float(raw_scores[int(entry["index"])])))
            for entry in entries
        )
    background_score = max(
        max(0.0, min(1.0, float(raw_scores[int(entry["index"])])))
        for entry in background
    )
    strongest = max([background_score, *result.values()])
    result["background"] = background_score
    result["unknown"] = max(0.0, 1.0 - strongest)
    return result


class YamnetClassifier:
    """Run the exact fixed-window official YAMNet LiteRT v1 artifact.

    Third-party imports are intentionally delayed until construction so the
    default simulator and its tests retain a zero-dependency path.
    """

    def __init__(
        self,
        model_path: str | Path,
        mapping_path: str | Path,
        *,
        expected_sha256: str = DEFAULT_YAMNET_SHA256,
        num_threads: int = 2,
        evidence_tier: str = "development-computer",
    ) -> None:
        if not 1 <= num_threads <= 16:
            raise ModelConfigurationError("num_threads must be between 1 and 16")
        self.model_path = Path(model_path)
        if not self.model_path.is_file():
            raise ModelConfigurationError(f"model not found: {self.model_path}")
        actual_sha256 = file_sha256(self.model_path)
        if actual_sha256 != expected_sha256.lower():
            raise ModelConfigurationError(
                f"model SHA-256 mismatch: expected {expected_sha256}, got {actual_sha256}"
            )
        self.mapping = load_mapping(mapping_path)
        self.labels = embedded_labels(self.model_path)
        validate_mapping_labels(self.mapping, self.labels)

        try:
            import numpy as np
            from ai_edge_litert.interpreter import Interpreter
        except ImportError as error:
            raise ModelConfigurationError(
                "YAMNet requires requirements-model.txt (ai-edge-litert 2.2.0)"
            ) from error
        self._np = np
        self._interpreter = Interpreter(
            model_path=str(self.model_path), num_threads=num_threads
        )
        self._interpreter.allocate_tensors()
        inputs = self._interpreter.get_input_details()
        outputs = self._interpreter.get_output_details()
        if len(inputs) != 1 or tuple(int(value) for value in inputs[0]["shape"]) != (
            YAMNET_INPUT_SAMPLES,
        ):
            raise ModelConfigurationError("unexpected YAMNet input tensor contract")
        if str(inputs[0]["dtype"]) not in ("<class 'numpy.float32'>", "float32"):
            raise ModelConfigurationError("YAMNet input tensor is not float32")
        if len(outputs) != 1 or tuple(int(value) for value in outputs[0]["shape"]) != (
            1,
            YAMNET_LABEL_COUNT,
        ):
            raise ModelConfigurationError("unexpected YAMNet output tensor contract")
        if str(outputs[0]["dtype"]) not in ("<class 'numpy.float32'>", "float32"):
            raise ModelConfigurationError("YAMNet output tensor is not float32")
        self._input_index = int(inputs[0]["index"])
        self._output_index = int(outputs[0]["index"])
        self.model_name = str(self.mapping["model_id"])
        self.evidence_tier = evidence_tier
        self._lock = RLock()

    def classify(self, samples: tuple[int, ...], sample_rate: int) -> Classification:
        if sample_rate != SAMPLE_RATE_HZ:
            raise ValueError(f"YAMNet requires {SAMPLE_RATE_HZ} Hz input")
        if len(samples) < YAMNET_INPUT_SAMPLES:
            raise ValueError(
                f"YAMNet requires at least {YAMNET_INPUT_SAMPLES} samples; got {len(samples)}"
            )
        crop_start = (len(samples) - YAMNET_INPUT_SAMPLES) // 2
        crop = samples[crop_start : crop_start + YAMNET_INPUT_SAMPLES]
        waveform = self._np.asarray(crop, dtype=self._np.float32) / self._np.float32(
            32768.0
        )
        started = time.perf_counter()
        with self._lock:
            self._interpreter.set_tensor(self._input_index, waveform)
            self._interpreter.invoke()
            raw = self._interpreter.get_tensor(self._output_index).reshape(-1).copy()
        inference_ms = (time.perf_counter() - started) * 1000.0
        return Classification(
            scores=aggregate_scores(raw, self.mapping),
            inference_ms=inference_ms,
            model_name=self.model_name,
            evidence_tier=self.evidence_tier,
        )
