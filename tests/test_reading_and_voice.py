import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from agent.reading import public_reading
from agent.runtime import execution_mode
from agent.original_ideas import propose


class TestReadingAndVoice(unittest.TestCase):
    def test_choice_keeps_source_when_model_shortens_original_idea(self):
        from agent.choice import choose
        from agent.decision_engine import ActionCandidate, ActionType, DecisionOutcome
        from agent.context_engine import build_environment_context
        post = ActionCandidate(ActionType.PUBLISH_TEXT_POST, .5, .9, "")
        quiet = ActionCandidate(ActionType.NO_ACTION, .5, .9, "")
        outcome = DecisionOutcome(quiet.action, "", {}, "", {}, [post, quiet])
        url = "https://www.bfi.org.uk/features/example"
        proposal = {"format": "text", "idea": "a particular reading of this excerpt\n" + url, "source_url": url}
        with execution_mode("live"), patch("agent.original_ideas.propose", return_value=(proposal, "proposed")), patch("agent.reading.public_reading", return_value=[]), patch("agent.generator.generator._call_llm", return_value=('{"candidate_id":0,"confidence":0.9,"contribution":"a shorter reading idea"}', "mock")):
            result = choose(outcome, build_environment_context())
        self.assertEqual(result.target_data["topic_hint"], "a shorter reading idea\n" + url)

    def test_reading_is_offline_isolated_and_ignores_unsafe_links(self):
        with execution_mode("offline"), patch("agent.discussion.source_packet") as fetch:
            self.assertEqual(public_reading([{"post": {"embed": {"external": {"uri": "https://www.bfi.org.uk/a"}}}}]), [])
            fetch.assert_not_called()
        with execution_mode("live"), patch("agent.discussion.source_packet") as fetch:
            self.assertEqual(public_reading([{"post": {"embed": {"external": {"uri": "http://127.0.0.1/private"}}}}]), [])
            fetch.assert_not_called()

    def test_only_observed_allowed_links_and_bounded_excerpts_reach_planning(self):
        url = "https://www.bfi.org.uk/features/example"
        source = {"id": "source", "url": url, "text": "x" * 4000, "retrieved_at": "today"}
        feed = [{"post": {"embed": {"external": {"uri": url}}}}]
        with execution_mode("live"), patch("agent.discussion.source_packet", return_value=[source]) as fetch:
            result = public_reading(feed)
        fetch.assert_called_once_with(url)
        self.assertEqual(result[0]["url"], url)
        self.assertEqual(len(result[0]["text"]), 1800)
        self.assertTrue(result[0]["partial"])

    def test_article_proposal_preserves_exact_source_and_rejects_invented_url(self):
        gen = Mock()
        url = "https://www.bfi.org.uk/features/example"
        material = {"web_reading": [{"url": url, "text": "a partial excerpt"}]}
        gen._call_llm.return_value = '{"format":"text","idea":"an interpretation of this excerpt","source_url":"' + url + '"}', "mock"
        idea, status = propose(gen, "Pilates retraining", "context", material, [], ["text"])
        self.assertEqual(status, "proposed")
        self.assertIn(url, idea["idea"])
        self.assertEqual(idea["source_url"], url)
        gen._call_llm.return_value = '{"format":"text","idea":"an interesting article","source_url":"https://invented.example/article"}', "mock"
        self.assertEqual(propose(gen, "identity", "context", material, [], ["text"])[1], "invalid")

    def test_shared_voice_reaches_generation_and_independent_review(self):
        from agent.generator import ContentGenerator
        from agent.context_engine import build_environment_context
        from agent.discussion import grounded_draft
        from agent.voice import VOICE
        self.assertIn(VOICE, ContentGenerator()._build_system_prompt(build_environment_context()))
        gen = Mock()
        gen._call_llm.side_effect = [('{"text":"a short thought","kind":"social","claims":[]}', "mock"), ('{"approved":true,"issue":"none"}', "mock")]
        with patch("agent.discussion.source_packet", return_value=[]), patch("agent.discussion.ReferenceLibrary"), patch("agent.validator.validator.validate_outgoing_text", return_value=(True, "a short thought", "")):
            grounded_draft(gen, "identity", "a small opinion", content_type="post")
        for call in gen._call_llm.call_args_list:
            self.assertIn(VOICE, call.args[0])

    def test_atomic_write_retries_only_transient_windows_failure(self):
        from agent.storage import write_json, read_json
        import os
        original = os.replace
        transient = PermissionError("busy")
        transient.winerror = 32
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "state.json"
            write_json(path, {"old": True})
            calls = []
            def retry_then_replace(source, destination):
                calls.append(source)
                if len(calls) == 1:
                    raise transient
                return original(source, destination)
            with patch("agent.storage.os.replace", side_effect=retry_then_replace) as replace, patch("time.sleep"):
                write_json(path, {"new": True})
            self.assertEqual(replace.call_count, 2)
            self.assertEqual(read_json(path, {}), {"new": True})
            with patch("agent.storage.os.replace", side_effect=PermissionError("permanent")) as replace:
                with self.assertRaises(PermissionError):
                    write_json(path, {"new": True})
            replace.assert_called_once()
