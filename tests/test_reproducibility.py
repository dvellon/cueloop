from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ReproducibilityContractTests(unittest.TestCase):
    def test_firmware_builder_normalizes_time_paths_and_intermediates(self) -> None:
        builder = (ROOT / "scripts" / "build_firmware.sh").read_text(
            encoding="utf-8"
        )
        for token in (
            "SOURCE_DATE_EPOCH=1788307200",
            "-ffile-prefix-map=",
            "-fdebug-prefix-map=",
            "--clean",
            "esp32:esp32:XIAO_ESP32S3",
            "arduino:zephyr:unoq",
            "--profile uno_q",
        ):
            self.assertIn(token, builder)
        self.assertGreaterEqual(builder.count("cmp "), 2)

    def test_clean_checkout_verifier_covers_release_surfaces(self) -> None:
        verifier = (ROOT / "scripts" / "verify_clean_checkout.sh").read_text(
            encoding="utf-8"
        )
        for token in (
            "git clone --quiet --no-hardlinks --local",
            "./scripts/test.sh",
            "npx --yes pyright@1.1.413",
            "./scripts/build_firmware.sh",
            "scripts/package_source_release.py",
            "scripts/package_app_lab.py",
        ):
            self.assertIn(token, verifier)

    def test_static_analysis_targets_minimum_supported_python(self) -> None:
        config = json.loads((ROOT / "pyrightconfig.json").read_text(encoding="utf-8"))
        self.assertEqual(config["pythonVersion"], "3.11")
        self.assertNotIn("venv", config)
        self.assertNotIn("venvPath", config)


if __name__ == "__main__":
    unittest.main()
