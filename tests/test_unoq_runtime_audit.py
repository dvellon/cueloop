from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "models"
APP_MODELS = ROOT / "app_lab" / "CueLoop" / "models"
WHEEL_DIR = ROOT / "tmp" / "unoq-wheel-audit-cp313"


class UnoQRuntimeAuditTests(unittest.TestCase):
    def test_target_manifest_lock_and_app_evidence_are_consistent(self) -> None:
        manifest_path = MODELS / "unoq_runtime_manifest.json"
        lock_path = MODELS / "requirements-unoq-cp313.lock"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        lock = lock_path.read_text(encoding="utf-8")
        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(manifest["target"]["python_version"], "3.13")
        self.assertEqual(manifest["target"]["official_container_platform"], "linux/arm64")
        self.assertEqual(manifest["target"]["pip_platform"], "manylinux_2_27_aarch64")
        self.assertEqual(manifest["target"]["abi"], "cp313")
        self.assertEqual(manifest["native_validation"]["elf_machine_id"], 183)
        self.assertEqual(len(manifest["files"]), 8)
        app_requirements = (APP_MODELS.parent / "python" / "requirements.txt").read_text(
            encoding="utf-8"
        )
        for record in manifest["files"]:
            requirement = f'{record["distribution"]}=={record["version"]}'
            self.assertIn(requirement, lock)
            self.assertIn(requirement, app_requirements)
            self.assertIn(f'sha256:{record["sha256"]}', lock)
        self.assertEqual(
            (APP_MODELS / manifest_path.name).read_bytes(), manifest_path.read_bytes()
        )
        self.assertEqual(
            (APP_MODELS / lock_path.name).read_bytes(), lock_path.read_bytes()
        )

    def test_downloaded_target_wheels_pass_native_audit_when_present(self) -> None:
        if len(list(WHEEL_DIR.glob("*.whl"))) != 8:
            self.skipTest("hash-locked target wheels are fetched by the release verifier")
        result = subprocess.run(
            [
                sys.executable,
                "scripts/audit_unoq_runtime.py",
                "--wheel-dir",
                str(WHEEL_DIR),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["litert"]["version"], "2.2.0")
        self.assertEqual(report["litert"]["license"], "Apache 2.0")
        self.assertEqual(report["litert"]["shared_object_count"], 16)
        self.assertEqual(report["litert"]["shared_object_machine"], "AArch64")


if __name__ == "__main__":
    unittest.main()
