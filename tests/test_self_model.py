import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from agent.runtime import execution_mode
from agent.self_model import SelfModel, CORE_MINIMUM, WEIGHT_STEP


class TestSelfModelBounds(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.model = SelfModel(Path(self.tmp.name) / "self_model.json")
        self.ids = {"p1", "p2", "p3"}

    def tearDown(self):
        self.tmp.cleanup()

    def test_changes_need_two_cited_posts(self):
        applied = self.model.apply([{"field": "interest", "topic": "culture", "delta": .3, "evidence": ["p1"]}], "", self.ids)
        self.assertEqual(applied, [])
        applied = self.model.apply([{"field": "interest", "topic": "culture", "delta": .3, "evidence": ["p1", "p9"]}], "", self.ids)
        self.assertEqual(applied, [])  # p9 was not supplied
        applied = self.model.apply([{"field": "interest", "topic": "culture", "delta": .3, "evidence": ["p1", "p2"]}], "", self.ids)
        self.assertEqual(applied[0]["to"], 1.3)

    def test_steps_and_core_minimum_are_enforced(self):
        self.model.apply([{"field": "interest", "topic": "money", "delta": 5, "evidence": ["p1", "p2"]}], "", self.ids)
        self.assertEqual(self.model.load()["interests"]["money"], 1.0 + WEIGHT_STEP)
        for _ in range(5):
            self.model.apply([{"field": "interest", "topic": "pilates", "delta": -.4, "evidence": ["p1", "p2"]}], "", self.ids)
        self.assertEqual(self.model.load()["interests"]["pilates"], CORE_MINIMUM["pilates"])
        self.model.apply([{"field": "interest", "topic": "politics", "delta": .4, "evidence": ["p1", "p2"]}], "", self.ids)
        self.assertNotIn("politics", self.model.load()["interests"])

    def test_rhythm_moves_one_step_within_config(self):
        from agent.config import config
        self.model.apply([{"field": "posts_per_day", "value": 1, "evidence": ["p1", "p2"]}], "", self.ids)
        self.assertEqual(self.model.load()["rhythm"]["posts_per_day"], config.max_posts_per_day - 1)
        self.model.apply([{"field": "posts_per_day", "value": 99, "evidence": ["p1", "p2"]}], "", self.ids)
        self.assertEqual(self.model.post_cap(config), config.max_posts_per_day)
        self.model.apply([{"field": "min_gap_hours", "value": 99, "evidence": ["p1", "p2"]}], "", self.ids)
        self.assertEqual(self.model.load()["rhythm"]["min_gap_hours"], config.min_post_gap_hours + 1.5)
        self.model.apply([{"field": "min_gap_hours", "value": 0, "evidence": ["p1", "p2"]}], "", self.ids)
        self.assertEqual(self.model.min_gap_hours(config), config.min_post_gap_hours)

    def test_undo_pause_resume_and_status(self):
        self.model.apply([{"field": "interest", "topic": "culture", "delta": .4, "evidence": ["p1", "p2"]}], "more films", self.ids)
        self.assertIn("culture 1.4", self.model.command("status"))
        self.assertIn("undone", self.model.command("undo"))
        self.assertEqual(self.model.load()["interests"]["culture"], 1.0)
        self.assertEqual(self.model.command("undo"), "nothing to undo.")
        self.model.command("pause")
        self.assertFalse(self.model.due())
        self.model.command("resume")
        self.assertFalse(self.model.due())  # a review just ran (apply records the time); next one is days away


class TestReview(unittest.TestCase):
    def test_review_uses_engagement_and_is_spaced_out(self):
        from agent.memory_store import memory_store
        with tempfile.TemporaryDirectory() as tmp:
            model = SelfModel(Path(tmp) / "self_model.json")
            now = dt.datetime.now(dt.timezone.utc).isoformat()
            posts = [{"post_id": f"at://me/{i}", "text": f"post {i}", "created_at": now} for i in range(5)]
            gen = Mock()
            gen._call_llm.return_value = (json.dumps({"changes": [
                {"field": "interest", "topic": "culture", "delta": .2, "evidence": ["p1", "p2"], "why": "film posts got replies"}],
                "summary": "i'll talk about films a bit more."}), "mock")
            with execution_mode("live"), patch.object(memory_store, "get_recent_context", return_value={"posts": posts}), \
                 patch("agent.self_model.fetch_engagement", return_value={"at://me/0": {"replyCount": 3}}):
                applied = model.maybe_review(Mock(), generator=gen, notify=False)
                again = model.maybe_review(Mock(), generator=gen, notify=False)
            self.assertEqual(applied[0]["topic"], "culture")
            self.assertEqual(again, [])
            self.assertEqual(gen._call_llm.call_count, 1)
            supplied = json.loads(gen._call_llm.call_args.args[1])["recent_posts"]
            self.assertEqual(supplied[0]["replies"], 3)

    def test_no_review_offline_or_with_few_posts(self):
        from agent.memory_store import memory_store
        with tempfile.TemporaryDirectory() as tmp:
            model = SelfModel(Path(tmp) / "self_model.json")
            gen = Mock()
            with execution_mode("offline"):
                self.assertEqual(model.maybe_review(Mock(), generator=gen, notify=False), [])
            with execution_mode("live"), patch.object(memory_store, "get_recent_context", return_value={"posts": []}):
                self.assertEqual(model.maybe_review(Mock(), generator=gen, notify=False), [])
            gen._call_llm.assert_not_called()


class TestLearnedHabitsReachDecisions(unittest.TestCase):
    def test_learned_cap_blocks_own_posts(self):
        from agent.choice import choose
        from agent.context_engine import build_environment_context
        from agent.decision_engine import ActionCandidate, ActionType, DecisionOutcome
        post = ActionCandidate(ActionType.PUBLISH_TEXT_POST, .9, .9, "")
        quiet = ActionCandidate(ActionType.NO_ACTION, .4, .9, "")
        context = build_environment_context(posts_today=1)
        with patch("agent.choice._learned", return_value=(1, 3.0, {})), \
             patch("agent.original_ideas.propose") as propose, \
             patch("agent.generator.generator._call_llm", return_value=('{"candidate_id":0,"confidence":1}', "mock")):
            result = choose(DecisionOutcome(post.action, "", {}, "", {}, [post, quiet]), context)
        propose.assert_not_called()
        self.assertEqual(result.selected_action, ActionType.NO_ACTION)

    def test_learning_command_parses(self):
        from agent.generator import generator
        self.assertEqual(generator.parse_master_directive("/learning undo")["action_type"], "LEARNING")
        self.assertEqual(generator.parse_master_directive("/learning")["topic_hint"], "status")
        self.assertTrue(generator.parse_master_directive("/learning forget everything")["needs_clarification"])


if __name__ == "__main__":
    unittest.main()
