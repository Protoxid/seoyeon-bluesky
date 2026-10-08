"""
tests/test_budget_hardening.py — Tests for Atomic Budget Reservations & Single-Entry Accounting.

Verifies:
  1. Atomic reservations hold estimated funds and prevent concurrent overages.
  2. Reconcile commits actual costs and frees reserved funds.
  3. Release frees reserved funds without charging the ledger.
  4. Daily budget exhaustion blocks subsequent reservations and stops LLM calls.
  5. Single-entry accounting: text posts and replies are charged strictly once.
"""

import json
import os
import pathlib
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from agent.budget_manager import BudgetManager
from agent.config import config
from agent.generator import ContentGenerator


class TestBudgetHardening(unittest.TestCase):
    def setUp(self):
        self.test_dir = pathlib.Path(tempfile.mkdtemp())
        self.ledger_file = self.test_dir / "budget_ledger.json"
        self.budget_mgr = BudgetManager(ledger_file=self.ledger_file)

        from agent.memory_store import memory_store
        self.orig_ctx_file = memory_store.recent_context_file
        self.orig_users_file = memory_store.users_file
        memory_store.recent_context_file = self.test_dir / "recent_context.json"
        memory_store.users_file = self.test_dir / "user_memory.json"

        import agent.runner as runner_module
        self.orig_tick_file = runner_module.TICK_LOG_FILE
        runner_module.TICK_LOG_FILE = self.test_dir / "tick_history.jsonl"

        from agent.vault import vault, set_encryption_key_override
        self.orig_vault_dir = vault.vault_dir
        self.orig_enc_file = vault.enc_file
        vault.vault_dir = self.test_dir / ".vault"
        vault.enc_file = self.test_dir / "vault.enc"
        vault._load_failed = False
        vault._load_error = None
        set_encryption_key_override("test_budget_hardening_key")

    def tearDown(self):
        from agent.memory_store import memory_store
        memory_store.recent_context_file = self.orig_ctx_file
        memory_store.users_file = self.orig_users_file
        import agent.runner as runner_module
        runner_module.TICK_LOG_FILE = self.orig_tick_file
        from agent.vault import vault, set_encryption_key_override
        vault.vault_dir = self.orig_vault_dir
        vault.enc_file = self.orig_enc_file
        vault._load_failed = False
        vault._load_error = None
        set_encryption_key_override(None)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_reservation_and_reconciliation_lifecycle(self):
        """Verifies reservation hold -> reconciliation commit flow."""
        self.assertEqual(self.budget_mgr.get_reserved_amount(), 0.0)

        # 1. Reserve $0.010
        res_id = self.budget_mgr.reserve(amount_usd=0.010, action_type="test_action")
        self.assertIsNotNone(res_id)
        self.assertEqual(self.budget_mgr.get_reserved_amount(), 0.010)

        # 2. Reconcile with actual cost $0.0035
        actual_cost = self.budget_mgr.reconcile(
            reservation_id=res_id,
            actual_cost_usd=0.0035,
            model="anthropic/claude-sonnet-5.5",
            prompt_tokens=500,
            completion_tokens=100,
        )
        self.assertEqual(actual_cost, 0.0035)

        # 3. Reservation should be cleared and spend committed
        self.assertEqual(self.budget_mgr.get_reserved_amount(), 0.0)
        summary = self.budget_mgr.get_summary()
        self.assertAlmostEqual(summary["daily_spend_usd"], 0.0035, places=4)
        self.assertEqual(summary["daily_tokens"], 600)

    def test_reservation_release_on_failure(self):
        """Verifies failed calls release reserved funds without ledger charges."""
        res_id = self.budget_mgr.reserve(amount_usd=0.025, action_type="test_failure")
        self.assertIsNotNone(res_id)
        self.assertEqual(self.budget_mgr.get_reserved_amount(), 0.025)

        # Release reservation
        self.budget_mgr.release(res_id)
        self.assertEqual(self.budget_mgr.get_reserved_amount(), 0.0)

        summary = self.budget_mgr.get_summary()
        self.assertEqual(summary["daily_spend_usd"], 0.0)

    def test_budget_exhaustion_blocks_reservations(self):
        """Verifies that exceeding daily budget prevents new reservations."""
        # Set daily budget to $0.02 for test
        with patch.object(config, "daily_ai_budget", 0.02):
            # First reservation consumes $0.015
            res_id_1 = self.budget_mgr.reserve(amount_usd=0.015)
            self.assertIsNotNone(res_id_1)

            # Second reservation of $0.010 would exceed $0.02 ($0.015 + $0.010 = $0.025 > $0.02)
            res_id_2 = self.budget_mgr.reserve(amount_usd=0.010)
            self.assertIsNone(res_id_2)

            # Release first reservation -> subsequent reservation now succeeds
            self.budget_mgr.release(res_id_1)
            res_id_3 = self.budget_mgr.reserve(amount_usd=0.010)
            self.assertIsNotNone(res_id_3)

    def test_generator_atomic_reservation_blocks_when_exhausted(self):
        """Verifies generator._call_llm returns budget_exceeded when reservation denied."""
        gen = ContentGenerator()
        with patch("agent.generator.budget_manager.reserve", return_value=None):
            text, model = gen._call_llm("sys", "user")
            self.assertIsNone(text)
            self.assertEqual(model, "budget_exceeded")

    def test_single_accounting_no_double_billing(self):
        """Verifies generator and runner together charge costs exactly once."""
        import agent.runner as runner_module
        from agent.bsky_client import bsky_client
        from agent.decision_engine import ActionType, DecisionOutcome

        orig_budget_mgr = runner_module.budget_manager
        runner_module.budget_manager = self.budget_mgr

        try:
            # Mock LLM generation to return text with 200 tokens
            fake_outcome = DecisionOutcome(
                selected_action=ActionType.PUBLISH_TEXT_POST,
                reason="Thoughtful reflection",
                target_data={},
                intent="dry_thought",
                candidate_scores={"PUBLISH_TEXT_POST": 0.8},
                all_candidates=[],
            )
            with patch("agent.generator.budget_manager", self.budget_mgr), \
                 patch.object(bsky_client, "authenticate", return_value=True), \
                 patch.object(bsky_client, "publish_text_post", return_value={"uri": "at://test/post/1"}), \
                 patch("agent.generator.generator._query_openrouter", return_value="spontaneous evening thought in my flat."), \
                 patch("agent.generator.validator.validate_outgoing_text", return_value=(True, "spontaneous evening thought in my flat.", None)), \
                 patch("agent.weekly_planner.weekly_planner.get_current_activity", return_value={"activity": "reading", "area": "Seongsu", "vibe": "quiet", "phase": "deep_night", "day": "friday"}), \
                 patch("agent.runner.decision_engine.evaluate", return_value=fake_outcome), \
                 patch("agent.runner.notifier.check_and_send_evening_summary"), \
                 patch("agent.runner.notifier.process_master_inbox", return_value=0):

                # Set fake usage
                from agent.generator import generator as global_gen
                global_gen.last_usage = {"prompt_tokens": 150, "completion_tokens": 50}

                # Run live tick
                runner_module.run_tick(dry_run=False)

                # Check total recorded charges in ledger
                data = self.budget_mgr._load_ledger()
                history = data.get("history", [])

                # There should be EXACTLY ONE cost entry from llm_generation (NO duplicate text_post entry)
                self.assertEqual(len(history), 1, f"Expected 1 entry, got {len(history)}: {history}")
                self.assertEqual(history[0]["action_type"], "llm_generation")
                self.assertNotEqual(history[0]["action_type"], "text_post")
        finally:
            runner_module.budget_manager = orig_budget_mgr


if __name__ == "__main__":
    unittest.main()
