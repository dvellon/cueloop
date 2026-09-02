from __future__ import annotations

import unittest

from benchmarks.simulated_transport import FaultProfile, benchmark, run_trial


class SimulatedTransportBenchmarkTests(unittest.TestCase):
    def test_clean_trial_detects_owned_signature_with_bounded_buffer(self) -> None:
        result = run_trial(
            event="door_knock",
            profile=FaultProfile("test-clean", 0.0, 0.0, 0.0),
            seed=7,
            seconds=3.0,
        )
        self.assertTrue(result["target_detected"])
        self.assertEqual(result["actual_drop_rate"], 0.0)
        self.assertEqual(result["evidence_tier"], "simulated")
        self.assertLessEqual(result["maximum_buffered_samples"], 24_000)

    def test_benchmark_keeps_fault_profiles_and_claim_boundary(self) -> None:
        result = benchmark(seeds=[7], seconds=3.0)
        self.assertEqual(result["schema_version"], 1)
        self.assertEqual(result["evidence_tier"], "simulated")
        self.assertIn("not real-audio accuracy", result["claim_boundary"])
        self.assertEqual(set(result["summaries"]), {"clean", "moderate", "severe"})
        self.assertEqual(len(result["trials"]), 12)


if __name__ == "__main__":
    unittest.main()
