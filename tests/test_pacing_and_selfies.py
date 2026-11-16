import datetime as dt
import json
import unittest
from unittest.mock import Mock, patch

from agent.runtime import execution_mode


class TestPostGap(unittest.TestCase):
    def test_gap_is_floor_plus_stable_per_post_variation(self):
        from agent.choice import required_post_gap
        config = Mock(min_post_gap_hours=3.0, post_gap_jitter_hours=2.0)
        a = [{"created_at": "2026-11-16T01:00:00+00:00"}]
        b = [{"created_at": "2026-11-16T05:30:00+00:00"}]
        gap_a = required_post_gap(a, config)
        self.assertTrue(3.0 <= gap_a <= 5.0)
        self.assertEqual(gap_a, required_post_gap(a, config))  # stable across wakeups
        self.assertNotEqual(gap_a, required_post_gap(b, config))  # varies from post to post
        self.assertEqual(required_post_gap(a, Mock(min_post_gap_hours=3.0, post_gap_jitter_hours=0.0)), 3.0)


class TestNothingNewSkipsModel(unittest.TestCase):
    def test_feed_already_offered_is_not_offered_again_and_costs_no_call(self):
        from agent.choice import choose
        from agent.context_engine import build_environment_context
        from agent.decision_engine import ActionCandidate, ActionType, DecisionOutcome
        from feed_fixtures import fresh_feed_candidate
        feed = fresh_feed_candidate()
        quiet = ActionCandidate(ActionType.NO_ACTION, .4, .9, "")
        reply = '{"candidate_id":0,"confidence":0.9}'
        with execution_mode("live"), patch("agent.generator.generator._call_llm", return_value=(reply, "mock")) as call:
            choose(DecisionOutcome(quiet.action, "", {}, "", {}, [quiet, feed]), build_environment_context())
            self.assertEqual(call.call_count, 1)
            call.reset_mock()
            result = choose(DecisionOutcome(quiet.action, "", {}, "", {}, [quiet, feed]), build_environment_context())
        call.assert_not_called()
        self.assertEqual(result.selected_action, ActionType.NO_ACTION)
        self.assertEqual(result.discussion_diagnostics["selection"], "nothing_new")
        self.assertEqual(result.discussion_diagnostics["offered_excluded"], 1)

    def test_direct_notifications_are_never_filtered_as_already_offered(self):
        from agent.choice import choose
        from agent.context_engine import build_environment_context
        from agent.decision_engine import ActionCandidate, ActionType, DecisionOutcome
        dm = ActionCandidate(ActionType.ANSWER_DM, .5, .9, "", {})
        quiet = ActionCandidate(ActionType.NO_ACTION, .4, .9, "")
        with execution_mode("live"), patch("agent.generator.generator._call_llm",
                                           return_value=('{"candidate_id":0,"confidence":0.9}', "mock")) as call:
            for _ in range(2):
                result = choose(DecisionOutcome(quiet.action, "", {}, "", {}, [dm, quiet]), build_environment_context())
        self.assertEqual(call.call_count, 2)
        self.assertEqual(result.selected_action, ActionType.ANSWER_DM)


class TestSelfieChoice(unittest.TestCase):
    def propose(self, payload):
        from agent.original_ideas import propose
        gen = Mock()
        gen._call_llm.return_value = (payload, "mock")
        return propose(gen, "identity", "context", {}, [], ["text", "image"],
                       pacing={"days_since_last_selfie": None})

    def test_selfie_shot_is_single_photo_and_text_posts_are_never_selfies(self):
        idea, _ = self.propose('{"format":"image","kind":"moment","idea":"mirror after class, hair a mess","shot":"selfie","photos":3}')
        self.assertEqual((idea["shot"], idea["photos"]), ("selfie", 1))
        idea, _ = self.propose('{"format":"text","kind":"moment","idea":"mirror after class, hair a mess","shot":"selfie"}')
        self.assertEqual(idea["shot"], "pov")
        idea, _ = self.propose('{"format":"image","kind":"moment","idea":"rice and kimchi on the table"}')
        self.assertEqual(idea["shot"], "pov")

    def test_days_since_last_selfie(self):
        from agent.choice import _days_since_last_selfie
        two_days = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=2)).isoformat()
        self.assertIsNone(_days_since_last_selfie([{"is_selfie": False, "created_at": two_days}]))
        self.assertEqual(_days_since_last_selfie([{"is_selfie": True, "created_at": two_days}]), 2.0)

    def test_selfie_proposal_reaches_the_image_engine_request(self):
        from agent.choice import choose
        from agent.context_engine import build_environment_context
        from agent.decision_engine import ActionCandidate, ActionType, DecisionOutcome
        image = ActionCandidate(ActionType.PUBLISH_IMAGE_POST, .5, .9, "")
        quiet = ActionCandidate(ActionType.NO_ACTION, .4, .9, "")
        proposal = {"format": "image", "idea": "mirror after class", "kind": "moment", "shot": "selfie", "photos": 1}
        context = build_environment_context()
        context.hours_since_last_post = 12.0
        with execution_mode("live"), patch("agent.original_ideas.propose", return_value=(proposal, "proposed")), \
             patch("agent.life.LifeJournal.prompt_data", return_value={}), \
             patch("agent.generator.generator._call_llm", return_value=("{}", "mock")):
            result = choose(DecisionOutcome(quiet.action, "", {}, "", {}, [image, quiet]), context)
        self.assertEqual(result.selected_action, ActionType.PUBLISH_IMAGE_POST)
        self.assertEqual(result.target_data["image_kind"], "selfie")


class TestReflectionThrottle(unittest.TestCase):
    def test_reflection_runs_at_most_once_per_interval(self):
        import tempfile
        from pathlib import Path
        from agent.continuity import ContinuityStore, reflect
        from agent.context_engine import build_environment_context
        from agent.generator import generator
        with tempfile.TemporaryDirectory() as tmp:
            store = ContinuityStore(Path(tmp) / "continuity.json", checkpoint=lambda: None)
            store.observe("obs:1", "a public observation", kind="external_observation")
            with execution_mode("live"), patch("agent.continuity.ContinuityStore", return_value=store), \
                 patch.object(generator, "_call_llm", return_value=("{}", "mock")) as model:
                reflect(build_environment_context())
                store.observe("obs:2", "another public observation", kind="external_observation")
                reflect(build_environment_context())
            self.assertEqual(model.call_count, 1)
            self.assertIn("last_reflection_at", store.load())


if __name__ == "__main__":
    unittest.main()
