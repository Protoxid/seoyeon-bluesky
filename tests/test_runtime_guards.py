from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock
from agent.budget_manager import BudgetManager
from agent.config import config
from agent.generator import ContentGenerator
from agent.runtime import execution_mode


class TestRuntimeGuards(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "budget.json"
        self.budget = BudgetManager(self.path)

    def test_parallel_reservations_cannot_overbook(self):
        with patch.object(config, "daily_ai_budget", .1):
            def reserve(_):
                return BudgetManager(self.path).reserve(.06)
            with ThreadPoolExecutor(max_workers=8) as pool:
                results = list(pool.map(reserve, range(8)))
        self.assertEqual(sum(bool(r) for r in results), 1)

    def test_submitted_request_does_not_expire(self):
        reservation = self.budget.reserve(.05)
        self.budget.mark_submitted(reservation, "provider-id")
        data = self.budget._load_ledger()
        data["active_reservations"][reservation]["timestamp"] = "2000-01-01T00:00:00+00:00"
        self.budget._save_ledger(data)
        self.assertIn(reservation, BudgetManager(self.path).get_active_reservations())

    def test_reconcile_is_idempotent(self):
        reservation = self.budget.reserve(.05)
        self.budget.reconcile(reservation, .03)
        self.budget.reconcile(reservation, .03)
        self.assertAlmostEqual(self.budget.get_summary()["daily_spend_usd"], .03)

    def test_nonfinite_cost_rejected_without_corruption(self):
        before = self.path.read_bytes()
        for invalid in (float("nan"), float("inf"), -.01):
            with self.assertRaises(ValueError):
                self.budget.reserve(invalid)
            with self.assertRaises(ValueError):
                self.budget.reconcile(None, invalid)
        self.assertEqual(self.path.read_bytes(), before)

    def test_corrupt_budget_does_not_reset_to_zero(self):
        self.path.write_text("invalid", encoding="utf-8")
        with self.assertRaises(RuntimeError):
            self.budget.reserve(.01)

    def test_each_billed_model_attempt_is_accounted(self):
        generator = ContentGenerator()
        def query(model, *args):
            generator.last_usage = {"cost": .01, "prompt_tokens": 1, "completion_tokens": 1}
            return None if model == config.primary_text_model else "a reply"
        with patch("agent.generator.budget_manager", self.budget), patch.object(generator, "_query_openrouter", side_effect=query):
            self.assertEqual(generator._call_llm("system", "user")[0], "a reply")
        self.assertAlmostEqual(self.budget.get_summary()["daily_spend_usd"], .02)
        self.assertEqual(len(self.budget._load_ledger()["history"]), 2)

    def test_offline_never_queries_or_reserves(self):
        generator = ContentGenerator()
        with execution_mode("offline"), patch.object(generator, "_query_openrouter") as request, patch("agent.generator.budget_manager.reserve") as reserve:
            self.assertEqual(generator._call_llm("system", "user"), (None, "offline"))
            request.assert_not_called()
            reserve.assert_not_called()

    def test_preview_cannot_mutate_bluesky(self):
        from agent.bsky_client import BlueskyClient
        client = BlueskyClient()
        with execution_mode("preview"), patch.object(client, "_xrpc_post_raw") as request:
            client.xrpc_post("com.atproto.repo.createRecord", {})
            request.assert_not_called()

    def test_short_promises_are_preserved(self):
        from agent.validator import validator
        for text in ("same", "i'll find the title", "i will check"):
            ok, clean, reason = validator.validate_outgoing_text(text, "reply", False)
            self.assertTrue(ok, reason)
            self.assertEqual(text, clean)

    def test_model_choice_cannot_bypass_daily_cap(self):
        from agent.choice import choose
        from agent.decision_engine import ActionCandidate, ActionType, DecisionOutcome
        from agent.context_engine import build_environment_context
        context = build_environment_context(posts_today=config.max_posts_per_day)
        post = ActionCandidate(ActionType.PUBLISH_TEXT_POST, .9, .9, "post")
        quiet = ActionCandidate(ActionType.NO_ACTION, .4, .9, "quiet")
        outcome = DecisionOutcome(post.action, "", {}, "", {}, [post, quiet])
        with patch("agent.generator.generator._call_llm", return_value=('{"candidate_id":0,"confidence":1}', "mock")):
            self.assertEqual(choose(outcome, context).selected_action, ActionType.NO_ACTION)
