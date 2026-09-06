from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CAD = ROOT / "cad"
APPLICATION = ROOT / "submissions" / "autodesk_application"


def load_validator():
    path = CAD / "validate_cad.py"
    spec = importlib.util.spec_from_file_location("cueloop_cad_validator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load CAD validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CadApplicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.parameters = json.loads(
            (CAD / "design_parameters.json").read_text(encoding="utf-8")
        )
        cls.contract = json.loads(
            (CAD / "design_contract.json").read_text(encoding="utf-8")
        )
        cls.validator = load_validator()

    def test_parameter_contract_and_critical_clearances(self) -> None:
        result = self.validator.validate_sources(self.parameters, self.contract)
        self.assertEqual(self.parameters["schema_version"], 2)
        self.assertEqual(self.parameters["units"], "mm")
        self.assertIn("vendor envelopes", self.parameters["evidence"])
        self.assertEqual(result["status"], "pass")
        self.assertGreaterEqual(result["numeric_parameter_count"], 70)
        self.assertEqual(result["manufacturing_component_count"], 6)
        self.assertGreaterEqual(result["wall_mm"], 2.0)
        self.assertGreaterEqual(
            result["boss_radial_web_mm"],
            self.parameters["manufacturing"]["minimum_web"],
        )
        self.assertGreaterEqual(
            result["dock_total_clearance_mm"]["length"],
            2 * self.parameters["manufacturing"]["fit_clearance"],
        )
        self.assertGreaterEqual(
            result["dock_total_clearance_mm"]["width"],
            2 * self.parameters["manufacturing"]["fit_clearance"],
        )
        self.assertGreater(result["xiao_closed_height_margin_mm"], 0)
        self.assertGreater(result["uno_vertical_margin_mm"], 0)

    def test_fusion_generator_is_native_parametric_and_exports_all_formats(self) -> None:
        script_path = CAD / "fusion" / "CueLoopBridgeGenerator.py"
        script = script_path.read_text(encoding="utf-8")
        compile(script, str(script_path), "exec")

        native_markers = (
            "ParametricDesignType",
            "userParameters.add",
            "sketches.add",
            "addTwoPointRectangle",
            "addDiameterDimension",
            "DistanceExtentDefinition.create",
            "setOneSideExtent",
            "extrudeFeatures",
            "filletFeatures",
            "addNewComponent",
            "createFusionArchiveExportOptions",
            "createSTEPExportOptions",
            "createSTLExportOptions",
            "createC3MFExportOptions",
            "export_manager.execute",
            "CueLoop_Bridge_validation.json",
            "CueLoop_Bridge_source_manifest.json",
            "snapshot_authoritative_sources",
            "SHA256SUMS.txt",
        )
        for marker in native_markers:
            self.assertIn(marker, script)
        for forbidden in (
            "ImportManager",
            "importManager",
            "createMeshBody",
            "setDistanceExtent(",
            "TemporaryBRepManager",
        ):
            self.assertNotIn(forbidden, script)

        required_geometry = (
            "CuePod_Microphone_Module",
            "CuePod_Bottom",
            "CuePod_Top",
            "Receiver_Bottom",
            "Receiver_Top",
            "Receiver_Carry_Clip",
            "Reference_UNO_Q",
            "Reference_Support_Electronics",
            "Reference_Microphone_Cartridge",
            "Microphone_Acoustic_Port",
            "USB_C",
            "Button_Opening",
            "Alert_LED_Window",
            "Ventilation_Slot",
            "Battery_Cable_Opening",
            "M2_Boss",
            "M2_Clearance",
            "Dock_Tongue",
            "Dock_Pocket",
            "Dock_Rail",
            "Lid_Lip",
        )
        for marker in required_geometry:
            self.assertIn(marker, script)
        self.assertIn("ESTIMATED_DIMENSIONS_VALIDATE_BEFORE_MANUFACTURE", script)

    def test_reference_generator_and_exports_are_validated(self) -> None:
        script_path = CAD / "reference" / "freecad_reference.py"
        script = script_path.read_text(encoding="utf-8")
        compile(script, str(script_path), "exec")
        for marker in (
            "import FreeCAD as App",
            "import Part",
            "open_shell",
            "Part.export",
            "Part.read",
            "REFERENCE_ONLY_NOT_CONTEST_AUTHORITATIVE",
        ):
            self.assertIn(marker, script)

        result = self.validator.validate_reference_output(
            CAD / "reference_exports", self.parameters, self.contract
        )
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["kind"], "freecad_opencascade_reference")
        self.assertEqual(result["reported_object_count"], 12)
        self.assertEqual(result["reopened_solid_count"], 12)
        self.assertEqual(result["reopened_fcstd_solid_count"], 12)
        self.assertEqual(result["interference_check_count"], 12)
        self.assertEqual(result["verified_file_count"], 17)

        self.assertGreater(
            (CAD / "reference_exports" / "CueLoop_Reference.FCStd").stat().st_size,
            0,
        )

        assembly = CAD / "reference_exports" / "CueLoop_Reference_Assembly.step"
        self.assertTrue(assembly.read_bytes().startswith(b"ISO-10303-21"))
        for component in self.contract["components"]:
            if not component["manufacturing_export"]:
                continue
            stem = component["output_stem"]
            step = CAD / "reference_exports" / "manufacturing" / f"{stem}.step"
            stl = CAD / "reference_exports" / "manufacturing" / f"{stem}.stl"
            self.assertTrue(step.read_bytes().startswith(b"ISO-10303-21"))
            self.assertGreater(stl.stat().st_size, 84)

    def test_fusion_output_bundle_contract_and_tamper_detection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            for relative in self.contract["fusion_outputs"]:
                if relative == "SHA256SUMS.txt":
                    continue
                target = output / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b"placeholder\n")
            for component in self.contract["components"]:
                if not component["manufacturing_export"]:
                    continue
                for suffix in self.contract["manufacturing_formats"]:
                    target = (
                        output
                        / "manufacturing"
                        / f"{component['output_stem']}.{suffix}"
                    )
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(b"manufacturing-placeholder\n")

            # Reproduce a generator snapshot exported by Fusion on Windows.
            generator_payload = (
                (CAD / "fusion" / "CueLoopBridgeGenerator.py")
                .read_bytes()
                .replace(b"\r\n", b"\n")
                .replace(b"\n", b"\r\n")
            )
            self.assertIn(b"\r\n", generator_payload)
            source_payloads = {
                "fusion_generator": (
                    "sources/CueLoopBridgeGenerator.py",
                    generator_payload,
                ),
                "design_parameters": (
                    "sources/design_parameters.json",
                    (CAD / "design_parameters.json").read_bytes(),
                ),
                "design_contract": (
                    "sources/design_contract.json",
                    (CAD / "design_contract.json").read_bytes(),
                ),
            }
            source_records = []
            for role, (relative, payload) in source_payloads.items():
                (output / relative).write_bytes(payload)
                source_records.append(
                    {
                        "role": role,
                        "path": relative,
                        "sha256": hashlib.sha256(payload).hexdigest(),
                        "bytes": len(payload),
                    }
                )
            (output / "CueLoop_Bridge_source_manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "authoritative": True,
                        "generator_version": "test",
                        "sources": source_records,
                    }
                ),
                encoding="utf-8",
            )
            minimum = self.contract["minimum_counts"]
            statistics = {
                "component_count_including_root": minimum["components_including_root"],
                "solid_body_count": minimum["solid_bodies"],
                "sketch_count": minimum["native_sketches"],
                "feature_count": minimum["native_features"],
                "timeline_count": minimum["timeline_entries"],
                "user_parameter_count": minimum["user_parameters"],
                "components": [
                    {"name": component["name"]}
                    for component in self.contract["components"]
                ],
            }
            (output / "CueLoop_Bridge_validation.json").write_text(
                json.dumps({"schema_version": 1, "status": "pass", "statistics": statistics}),
                encoding="utf-8",
            )
            checksum_lines = []
            for path in sorted(candidate for candidate in output.rglob("*") if candidate.is_file()):
                relative = path.relative_to(output).as_posix()
                checksum_lines.append(
                    f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {relative}"
                )
            (output / "SHA256SUMS.txt").write_text(
                "\n".join(checksum_lines) + "\n", encoding="utf-8"
            )

            result = self.validator.validate_fusion_output(
                output, self.parameters, self.contract
            )
            self.assertEqual(result["status"], "pass")
            self.assertEqual(result["kind"], "autodesk_fusion_native")

            with (output / "CueLoop_Bridge_Native.f3d").open("ab") as handle:
                handle.write(b"tamper")
            with self.assertRaises(self.validator.CadValidationError):
                self.validator.validate_fusion_output(
                    output, self.parameters, self.contract
                )

    def test_operator_docs_prove_native_history_and_provenance(self) -> None:
        runbook = (CAD / "FUSION_WINDOWS_RUNBOOK.md").read_text(encoding="utf-8")
        provenance = (CAD / "PROVENANCE.md").read_text(encoding="utf-8")
        dfm = (CAD / "PCBWAY_DFM.md").read_text(encoding="utf-8")
        hardware_tests = (ROOT / "HARDWARE_TESTS.md").read_text(encoding="utf-8")
        for phrase in (
            "Scripts and Add-Ins",
            "CueLoop_Bridge_Native.f3d",
            "Change Parameters",
            "pod_mic_hole_diameter",
            "Mesh Bodies",
            "Section Analysis",
            "WINDOWS_RETURN_HASHES.csv",
            "cad/validate_cad.py",
        ):
            self.assertIn(phrase, runbook)
        self.assertIn("Vendor-derived and estimated references", provenance)
        self.assertIn("No third-party STEP, mesh, BRep", provenance)
        self.assertIn("PCBWay", dfm)
        self.assertIn("boss radial web", dfm)
        for test_id in ("C-101", "C-105", "C-109"):
            self.assertIn(test_id, hardware_tests)

    def test_autodesk_application_has_all_five_answers_and_honest_gates(self) -> None:
        responses = (APPLICATION / "APPLICATION_RESPONSES.md").read_text(
            encoding="utf-8"
        )
        for number in range(1, 6):
            self.assertIn(f"## {number}.", responses)
        self.assertIn("USER ACTION REQUIRED", responses)
        self.assertNotIn("UNAVOIDABLE USER INPUT", responses)
        self.assertNotIn("[profession/role", responses)
        self.assertIn("I am an investment banker", responses)
        self.assertIn("hobbyist hardware and software developer", responses)
        self.assertIn("not a certified alarm", responses)
        self.assertIn("raw audio is discarded after inference by default", responses)
        self.assertIn("preliminary `.f3d`", responses)

        opening = (APPLICATION / "HACKSTER_PROJECT_OPENING.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("What exists at application time", opening)
        self.assertIn("Physical performance will be added only after it is observed", opening)
        checklist = (APPLICATION / "APPLICATION_CHECKLIST.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("September 7, 2026 at 11:59 PM PDT", checklist)
        self.assertIn("genuine native-history `.f3d`", checklist)
        self.assertIn("C-100 through C-109", checklist)


if __name__ == "__main__":
    unittest.main()
