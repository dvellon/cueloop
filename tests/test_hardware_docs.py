from __future__ import annotations

import json
from pathlib import Path
import unittest
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]


class HardwareDocumentationTests(unittest.TestCase):
    def test_netlist_has_safe_minimum_connections(self) -> None:
        netlist = json.loads(
            (
                ROOT / "hardware" / "schematics" / "cueloop_v1.netlist.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(netlist["schema_version"], 1)
        nets = {net["name"]: net for net in netlist["nets"]}
        self.assertEqual(
            nets["BAT_POS"]["endpoints"],
            ["B1.POS", "J1.MEASURED_POS", "U1.BAT_POS"],
        )
        self.assertEqual(
            nets["BAT_NEG"]["endpoints"],
            ["B1.NEG", "J1.MEASURED_NEG", "U1.BAT_NEG"],
        )
        self.assertEqual(
            nets["TRUSTED_LAN_WIFI"]["type"], "wireless-logical"
        )
        electrical_endpoints = {
            endpoint
            for net in netlist["nets"]
            if net["type"].startswith("electrical")
            for endpoint in net["endpoints"]
        }
        self.assertFalse(
            any(endpoint.startswith("U2") for endpoint in nets["BAT_POS"]["endpoints"])
        )
        self.assertNotIn("U1.GND", electrical_endpoints)
        self.assertIn("Qwiic to CuePod battery", netlist["explicitly_not_connected"])

    def test_schematic_svg_is_well_formed_and_accessible(self) -> None:
        path = ROOT / "hardware" / "schematics" / "cueloop_v1.svg"
        tree = ElementTree.parse(path)
        root = tree.getroot()
        self.assertTrue(root.tag.endswith("svg"))
        self.assertEqual(root.attrib["role"], "img")
        content = path.read_text(encoding="utf-8")
        self.assertIn("<title", content)
        self.assertIn("<desc", content)
        self.assertIn("Battery detached", content)

    def test_bom_and_bringup_preserve_safety_gates(self) -> None:
        content = "\n".join(
            (ROOT / path).read_text(encoding="utf-8")
            for path in (
                "hardware/BOM.md",
                "hardware/WIRING.md",
                "hardware/ASSEMBLY.md",
                "HARDWARE_TESTS.md",
                "user_checklists/HARDWARE_BRINGUP.md",
            )
        ).lower()
        self.assertIn("never solder", content)
        self.assertIn("battery detached", content)
        self.assertIn("qwiic", content)
        self.assertIn("measured polarity", content)
        self.assertIn("abx00173", content)
        self.assertIn("113991115", content)
        self.assertIn("adafruit product 1578", content)
        self.assertIn("adafruit product 261", content)


if __name__ == "__main__":
    unittest.main()
