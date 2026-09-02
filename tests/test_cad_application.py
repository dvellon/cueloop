from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CAD = ROOT / "cad"
APPLICATION = ROOT / "submissions" / "autodesk_application"


class CadApplicationTests(unittest.TestCase):
    def test_fusion_generator_and_parameter_contract(self) -> None:
        script_path = CAD / "fusion" / "CueLoopBridgeGenerator.py"
        script = script_path.read_text(encoding="utf-8")
        compile(script, str(script_path), "exec")
        parameters = json.loads(
            (CAD / "design_parameters.json").read_text(encoding="utf-8")
        )
        self.assertEqual(parameters["schema_version"], 1)
        self.assertEqual(parameters["units"], "mm")
        self.assertIn("preliminary", parameters["evidence"])
        self.assertIn("caliper validation pending", parameters["evidence"])

        glob = parameters["global"]
        pod = parameters["pod"]
        receiver = parameters["receiver"]
        hardware = parameters["source_hardware"]
        for group in (glob, pod, receiver):
            for name, value in group.items():
                self.assertGreater(value, 0, name)

        pod_inner_length = pod["outer_length"] - 2 * glob["wall"]
        pod_inner_width = pod["outer_width"] - 2 * glob["wall"]
        self.assertGreaterEqual(pod_inner_length, hardware["lipo_500"]["length"])
        self.assertGreaterEqual(pod_inner_width, hardware["lipo_500"]["width"])
        self.assertGreaterEqual(pod_inner_length, hardware["xiao_sense"]["length"])
        self.assertGreaterEqual(pod_inner_width, hardware["xiao_sense"]["width"])

        receiver_inner_length = receiver["outer_length"] - 2 * glob["wall"]
        receiver_inner_width = receiver["outer_width"] - 2 * glob["wall"]
        self.assertGreaterEqual(receiver_inner_length, hardware["uno_q"]["length"])
        self.assertGreaterEqual(receiver_inner_width, hardware["uno_q"]["width"])
        self.assertLess(receiver["dock_length"], receiver["outer_length"])
        self.assertLess(receiver["dock_width"], receiver["outer_width"])

        for component in (
            "CuePod_Base",
            "CuePod_Lid",
            "Receiver_Base",
            "Receiver_Lid",
            "Alert_Diffuser",
            "Clip_Stand",
        ):
            self.assertIn(f'"{component}"', script)
        self.assertIn("ESTIMATED_DIMENSIONS_VALIDATE_BEFORE_MANUFACTURE", script)

    def test_autodesk_application_has_all_five_answers_and_honest_gates(self) -> None:
        responses = (APPLICATION / "APPLICATION_RESPONSES.md").read_text(
            encoding="utf-8"
        )
        for number in range(1, 6):
            self.assertIn(f"## {number}.", responses)
        self.assertIn("USER ACTION REQUIRED", responses)
        self.assertIn("UNAVOIDABLE USER INPUT", responses)
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
        self.assertIn("save the preliminary `.f3d`", checklist)


if __name__ == "__main__":
    unittest.main()
