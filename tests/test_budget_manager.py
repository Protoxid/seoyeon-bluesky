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

    def test_calculate_token_cost(self):
        # Claude Sonnet 5.5: $3.00/M prompt, $15.00/M completion
        # 1,000 prompt tokens = $0.003, 1,000 completion tokens = $0.015 -> $0.018
        cost = self.mgr.calculate_token_cost("anthropic/claude-sonnet-5.5", 1000, 1000)
        self.assertAlmostEqual(cost, 0.018, places=5)

        # DeepSeek Flash: $0.14/M prompt, $0.28/M completion
        # 10,000 prompt tokens = $0.0014, 10,000 completion tokens = $0.0028 -> $0.0042
        cost_ds = self.mgr.calculate_token_cost("deepseek-v4.1-flash", 10000, 10000)
        self.assertAlmostEqual(cost_ds, 0.0042, places=5)

    def test_record_token_usage(self):
        cost = self.mgr.record_token_usage(
            model="anthropic/claude-sonnet-5.5",
            prompt_tokens=500,
            completion_tokens=100,
            action_type="post_text",
            details="test post generation",
        )
        self.assertGreater(cost, 0.0)

        summary = self.mgr.get_summary()
        self.assertGreater(summary["daily_spend_usd"], 0.0)
        self.assertEqual(summary["daily_tokens"], 600)
        self.assertEqual(summary["monthly_tokens"], 600)

    def test_record_image_spend(self):
        cost = self.mgr.record_image_spend(model="gpt-image-2-5-sunburst", details="street selfie")
        self.assertEqual(cost, 0.045)
        summary = self.mgr.get_summary()
        self.assertEqual(summary["daily_images_count"], 1)


if __name__ == "__main__":
    unittest.main()
