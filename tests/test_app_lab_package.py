from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app_lab" / "CueLoop"


class AppLabPackageTests(unittest.TestCase):
    def test_release_packager_rejects_uncommitted_input(self) -> None:
        probe = APP / "UNCOMMITTED_PACKAGE_PROBE.txt"
        probe.write_text("test-only packaging drift\n", encoding="utf-8")
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/package_app_lab.py",
                    "--version",
                    "dirty-probe",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
        finally:
            probe.unlink(missing_ok=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("packaging inputs differ from HEAD", result.stderr)
        self.assertIn(probe.name, result.stderr)

    def test_required_app_structure_and_metadata(self) -> None:
        for relative in (
            "app.yaml",
            "README.md",
            "python/main.py",
            "python/requirements.txt",
            "sketch/sketch.ino",
            "sketch/sketch.yaml",
            "models/requirements-unoq-cp313.lock",
            "models/unoq_runtime_manifest.json",
        ):
            self.assertTrue((APP / relative).is_file(), relative)
        descriptor = (APP / "app.yaml").read_text(encoding="utf-8")
        self.assertIn("name: CueLoop", descriptor)
        self.assertIn("  - 8080", descriptor)
        self.assertNotIn("password", descriptor.lower())
        entry_point = (APP / "python/main.py").read_text(encoding="utf-8")
        self.assertIn("CueLoop runtime: Python", entry_point)
        self.assertIn('version("ai-edge-litert")', entry_point)

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

    def test_release_archive_is_deterministic_and_excludes_runtime_data(self) -> None:
        model = APP / "models" / "yamnet-classification-tflite-v1.tflite"
        if not model.exists():
            self.skipTest("ignored model is required for a complete release archive")
        command = [
            sys.executable,
            "scripts/package_app_lab.py",
            "--version",
            "test",
            "--allow-dirty",
        ]
        first = subprocess.run(
            command, cwd=ROOT, capture_output=True, text=True, check=False
        )
        self.assertEqual(first.returncode, 0, first.stderr)
        archive = ROOT / "packages" / "CueLoop-App-Lab-vtest.zip"
        first_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
        second = subprocess.run(
            command, cwd=ROOT, capture_output=True, text=True, check=False
        )
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), first_hash)
        with ZipFile(archive) as bundle:
            names = bundle.namelist()
            self.assertIn("CueLoop/PACKAGE_MANIFEST.json", names)
            self.assertIn(
                "CueLoop/models/yamnet-classification-tflite-v1.tflite", names
            )
            self.assertFalse(any(name.endswith(".sqlite3") for name in names))
            self.assertFalse(any(name.endswith(".whl") for name in names))
            self.assertFalse(any("__pycache__" in name for name in names))
            package_manifest = json.loads(
                bundle.read("CueLoop/PACKAGE_MANIFEST.json")
            )
            source_commit = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
            self.assertEqual(package_manifest["source_commit"], source_commit)
            self.assertIsInstance(package_manifest["source_tree_clean"], bool)
            self.assertFalse(package_manifest["raw_audio_included"])
            self.assertFalse(package_manifest["runtime_data_included"])


if __name__ == "__main__":
    unittest.main()
