from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from cueloop.constants import EVENT_CLASSES
from cueloop.yamnet import (
    ModelConfigurationError,
    aggregate_scores,
    load_mapping,
    validate_mapping_labels,
)


ROOT = Path(__file__).resolve().parents[1]
MAPPING_PATH = ROOT / "models" / "class_mapping.json"


class YamnetMappingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mapping = load_mapping(MAPPING_PATH)

    def test_mapping_has_exact_product_classes(self) -> None:
        self.assertEqual(
            set(self.mapping["target_groups"]),
            set(EVENT_CLASSES),
        )

    def test_group_max_and_unknown_are_bounded(self) -> None:
        raw = [0.0] * 521
        raw[353] = 0.81
        raw[70] = 0.62
        raw[494] = 0.10
        scores = aggregate_scores(raw, self.mapping)
        self.assertEqual(scores["door_knock"], 0.81)
        self.assertEqual(scores["dog_bark"], 0.62)
        self.assertAlmostEqual(scores["unknown"], 0.19)
        self.assertTrue(all(0.0 <= value <= 1.0 for value in scores.values()))

    def test_generic_speech_is_not_an_attention_trigger(self) -> None:
        raw = [0.0] * 521
        raw[0] = 0.99
        scores = aggregate_scores(raw, self.mapping)
        self.assertEqual(scores["attention_call"], 0.0)

    def test_mapping_label_validation_detects_drift(self) -> None:
        labels = [f"label-{index}" for index in range(521)]
        for entries in self.mapping["target_groups"].values():
            for entry in entries:
                labels[entry["index"]] = entry["label"]
        for entry in self.mapping["background_group"]:
            labels[entry["index"]] = entry["label"]
        validate_mapping_labels(self.mapping, labels)
        labels[353] = "Unexpected"
        with self.assertRaises(ModelConfigurationError):
            validate_mapping_labels(self.mapping, labels)

    def test_invalid_mapping_is_rejected(self) -> None:
        invalid = dict(self.mapping)
        invalid["aggregation"] = "mean"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mapping.json"
            path.write_text(json.dumps(invalid), encoding="utf-8")
            with self.assertRaises(ModelConfigurationError):
                load_mapping(path)


if __name__ == "__main__":
    unittest.main()

