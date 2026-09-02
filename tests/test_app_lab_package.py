from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app_lab" / "CueLoop"


class AppLabPackageTests(unittest.TestCase):
    def test_required_app_structure_and_metadata(self) -> None:
        for relative in (
            "app.yaml",
            "README.md",
            "python/main.py",
            "python/requirements.txt",
            "sketch/sketch.ino",
            "sketch/sketch.yaml",
        ):
            self.assertTrue((APP / relative).is_file(), relative)
        descriptor = (APP / "app.yaml").read_text(encoding="utf-8")
        self.assertIn("name: CueLoop", descriptor)
        self.assertIn("  - 8080", descriptor)
        self.assertNotIn("password", descriptor.lower())

    def test_python_entry_point_has_valid_syntax(self) -> None:
        path = APP / "python" / "main.py"
        compile(path.read_text(encoding="utf-8"), str(path), "exec")

    def test_pinned_runtime_and_sketch_profile(self) -> None:
        requirements = (APP / "python" / "requirements.txt").read_text(
            encoding="utf-8"
        )
        self.assertIn("ai-edge-litert==2.2.0", requirements)
        profile = (APP / "sketch" / "sketch.yaml").read_text(encoding="utf-8")
        self.assertIn("fqbn: arduino:zephyr:unoq", profile)
        self.assertIn("platform: arduino:zephyr (0.90.0)", profile)
        self.assertIn("Arduino_RouterBridge (0.4.3)", profile)

    def test_vendored_sources_have_no_drift(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/sync_app_lab.py", "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_local_model_matches_manifest_when_present(self) -> None:
        model = APP / "models" / "yamnet-classification-tflite-v1.tflite"
        if not model.exists():
            self.skipTest("ignored model is installed only in packaged working copies")
        manifest = json.loads(
            (APP / "models" / "model_manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(model.stat().st_size, manifest["expected_bytes"])
        self.assertEqual(hashlib.sha256(model.read_bytes()).hexdigest(), manifest["sha256"])


if __name__ == "__main__":
    unittest.main()
