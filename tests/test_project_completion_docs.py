from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ProjectCompletionDocumentationTests(unittest.TestCase):
    def test_authoritative_hardware_tests_cover_windows_safety_and_all_gates(self) -> None:
        content = (ROOT / "HARDWARE_TESTS.md").read_text(encoding="utf-8")
        for test_id in (
            "W-001",
            "W-101",
            "W-109",
            "H-001",
            "H-010",
            "H-101",
            "H-108",
            "H-301",
            "H-313",
        ):
            self.assertIn(test_id, content)
        for phrase in (
            "Get-FileHash",
            "XIAO_ESP32S3",
            "ai-edge-litert==2.2.0",
            "Never solder with USB or the LiPo connected",
            "Never solder directly to a LiPo cell",
            "Never trust wire color",
            "Do not proceed if either digest differs",
            "No physical test records exist yet",
        ):
            self.assertIn(phrase, content)
        self.assertIn("Append completed blocks immediately below", content)
        self.assertIn("copy only reviewed", content.lower())

    def test_autodesk_final_workspace_tracks_every_required_v2_delta(self) -> None:
        directory = ROOT / "submissions" / "autodesk_final"
        expected = {
            "EVIDENCE_MATRIX.md",
            "FINAL_ARTICLE_OUTLINE.md",
            "MANUFACTURING_PLAN.md",
            "README.md",
            "SUBMISSION_CHECKLIST.md",
            "V2_DEVELOPMENT_PLAN.md",
        }
        self.assertEqual({path.name for path in directory.glob("*.md")}, expected)
        combined = "\n".join(
            (directory / name).read_text(encoding="utf-8") for name in expected
        )
        for phrase in (
            "New hardware",
            "New interactions",
            "New CAD",
            "New manufacturing",
            "New testing",
            "Autodesk-user workflow",
            "Eligibility differentiation",
            "approximately 750 units",
            "PCBWay",
            "Fusion Electronics",
        ):
            self.assertIn(phrase, combined)
        self.assertIn("not yet proven", combined)

    def test_experiment_registry_and_example_follow_the_schema_contract(self) -> None:
        schema = json.loads(
            (ROOT / "experiments" / "experiment.schema.json").read_text(
                encoding="utf-8"
            )
        )
        example = json.loads(
            (ROOT / "experiments" / "experiment.example.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(schema["properties"]["schema_version"]["const"], 1)
        self.assertEqual(set(schema["required"]), set(example))
        self.assertRegex(example["experiment_id"], r"^EXP-[0-9]{3}$")
        self.assertEqual(example["status"], "planned")
        registry = (ROOT / "experiments" / "README.md").read_text(encoding="utf-8")
        self.assertIn("EXP-001", registry)
        self.assertIn("HARDWARE_TESTS.md", registry)
        self.assertIn("A failure remains a result", registry)


if __name__ == "__main__":
    unittest.main()
