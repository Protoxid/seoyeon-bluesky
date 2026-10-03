"""
tests/test_budget_manager.py — Unit tests for Cost Tracking & Budget Guardrails.
"""

import shutil
import tempfile
import unittest
import pathlib

from agent.budget_manager import BudgetManager
from agent.config import config


class TestBudgetManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = pathlib.Path(tempfile.mkdtemp())
        self.ledger_file = self.test_dir / "test_budget.json"
        self.mgr = BudgetManager(ledger_file=self.ledger_file)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_daily_budget_limit(self):
        # Should be within budget initially
        can_spend, _ = self.mgr.can_spend(0.10)
        self.assertTrue(can_spend)

        # Spend up to the limit
        self.mgr.record_spend(config.daily_ai_budget - 0.01, "test_action")
        can_spend_small, _ = self.mgr.can_spend(0.005)
        self.assertTrue(can_spend_small)

        # Exceed limit
        can_spend_large, reason = self.mgr.can_spend(0.05)
        self.assertFalse(can_spend_large)
        self.assertIn("Daily budget reached", reason)

    def test_daily_image_limit(self):
        # Check initial image permission
        can_img, _ = self.mgr.can_generate_image()
        self.assertTrue(can_img)

        # Exhaust images
        for _ in range(config.max_images_per_day):
            self.mgr.record_spend(0.045, "image_generation")

        can_img_now, reason = self.mgr.can_generate_image()
        self.assertFalse(can_img_now)
        self.assertIn("Daily image limit reached", reason)


if __name__ == "__main__":
    unittest.main()
