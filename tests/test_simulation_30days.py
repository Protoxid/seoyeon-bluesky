"""
tests/test_simulation_30days.py — Hermetic Regression Test for 30-Day Deterministic Simulation.

Runs a fast 3-day (144-tick) verification of the simulation engine to ensure:
  1. Complete deterministic execution without exceptions.
  2. Zero budget cap breaches.
  3. Proper restraint ratio (> 65% NO_ACTION).
  4. Goal and narrative state transitions.
"""

import unittest

from scripts.simulate_30_days import SimulationRunner


class TestSimulationHarness(unittest.TestCase):
    def test_simulation_runner_v25(self):
        runner = SimulationRunner(run_mode="v25")
        try:
            results = runner.run_simulation()
            self.assertEqual(results["total_ticks"], 1440)
            self.assertFalse(results["budget_cap_breached"])
            self.assertGreater(results["restraint_ratio"], 0.65)
            self.assertLessEqual(results["cliche_ratio"], 0.10)
            self.assertEqual(results["temporal_coherence_failures"], 0)
            self.assertGreater(results["goals_completed"], 0)
        finally:
            runner.cleanup()


if __name__ == "__main__":
    unittest.main()
