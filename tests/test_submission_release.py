from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
SUBMISSION = ROOT / "submissions" / "app_lab"


class SubmissionReleaseTests(unittest.TestCase):
    def test_submission_package_has_all_required_material(self) -> None:
        required = {
            "LICENSES_AND_ATTRIBUTION.md",
            "PHOTO_SHOT_LIST.md",
            "PROJECT_ARTICLE.md",
            "README.md",
            "RUBRIC_REVIEW.md",
            "SOURCE_GUIDE.md",
            "SUBMISSION_CHECKLIST.md",
            "SUBMISSION_METADATA.md",
            "TEST_RESULTS.md",
            "TROUBLESHOOTING.md",
            "VIDEO_PACKAGE.md",
        }
        self.assertEqual(
            {path.name for path in SUBMISSION.glob("*.md")}, required
        )
        article = (SUBMISSION / "PROJECT_ARTICLE.md").read_text(encoding="utf-8")
        self.assertIn("What has actually been measured", article)
        self.assertIn("not a certified alarm", article)
        self.assertIn("unencrypted and unauthenticated", article)
        rubric = (SUBMISSION / "RUBRIC_REVIEW.md").read_text(encoding="utf-8")
        for phrase in (
            "Documentation — 30 points",
            "Bill of materials — 20 points",
            "Schematics — 15 points",
            "Code and contribution — 15 points",
            "Creativity — 20 points",
        ):
            self.assertIn(phrase, rubric)

    def test_video_has_complete_timeline_and_simulation_fallback_label(self) -> None:
        video = (SUBMISSION / "VIDEO_PACKAGE.md").read_text(encoding="utf-8")
        self.assertIn("0:00–0:10", video)
        self.assertIn("2:55–3:00", video)
        self.assertIn("SIMULATED PIPELINE — HARDWARE RESULT PENDING", video)
        self.assertIn("not a certified alarm", video)

    def test_source_archive_is_deterministic_and_sanitized(self) -> None:
        if not (ROOT / ".git").is_dir():
            self.skipTest("source packaging requires Git metadata and runs before export")
        command = [
            sys.executable,
            "scripts/package_source_release.py",
            "--version",
            "test",
            "--allow-dirty",
        ]
        first = subprocess.run(
            command, cwd=ROOT, capture_output=True, text=True, check=False
        )
        self.assertEqual(first.returncode, 0, first.stderr)
        archive = ROOT / "packages" / "CueLoop-Source-vtest.zip"
        first_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
        second = subprocess.run(
            command, cwd=ROOT, capture_output=True, text=True, check=False
        )
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), first_hash)

        with ZipFile(archive) as bundle:
            names = bundle.namelist()
            prefix = "CueLoop-Source-vtest/"
            self.assertIn(f"{prefix}README.md", names)
            self.assertIn(f"{prefix}SOURCE_MANIFEST.json", names)
            self.assertNotIn(f"{prefix}PROJECT_PROMPT.md", names)
            forbidden_suffixes = (".tflite", ".sqlite3", ".wav", ".pem", ".key")
            self.assertFalse(any(name.endswith(forbidden_suffixes) for name in names))
            manifest = json.loads(bundle.read(f"{prefix}SOURCE_MANIFEST.json"))
            self.assertFalse(manifest["raw_audio_included"])
            self.assertFalse(manifest["runtime_model_included"])
            self.assertEqual(manifest["excluded_tracked_paths"], ["PROJECT_PROMPT.md"])


if __name__ == "__main__":
    unittest.main()
