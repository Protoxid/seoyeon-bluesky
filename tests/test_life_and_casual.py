import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from agent.life import LifeJournal, MAX_LOG
from agent.runtime import execution_mode


def _context(date="2026-11-11"):
    ctx = Mock()
    ctx.date_display = date
    ctx.day_of_week = "Wednesday"
    ctx.season = "autumn"
    ctx.circadian_phase = "afternoon"
    ctx.weather.summary.return_value = "clear, 9C"
    return ctx


class TestLifeJournal(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.journal = LifeJournal(Path(self.tmp.name) / "life.json")

    def tearDown(self):
        self.tmp.cleanup()

    def test_offline_day_sketch_is_empty_and_makes_no_call(self):
        gen = Mock()
        with execution_mode("offline"):
            self.assertEqual(self.journal.today(_context(), gen), {})
        gen._call_llm.assert_not_called()

    def test_day_sketch_generated_once_per_date_and_threads_progress(self):
        gen = Mock()
        gen._call_llm.return_value = (json.dumps({
            "moments": [{"when": "morning", "what": "anatomy flashcards on the bus"}],
            "mood": "tired but fine",
            "thread_notes": [{"id": "pilates", "note": "started the spine module"}, {"id": "unknown", "note": "ignored"}]}), "mock")
        with execution_mode("live"):
            first = self.journal.today(_context(), gen)
            second = self.journal.today(_context(), gen)
        self.assertEqual(first, second)
        self.assertEqual(gen._call_llm.call_count, 1)
        threads = {t["id"]: t for t in self.journal.load()["threads"]}
        self.assertIn("spine module", threads["pilates"]["notes"][-1])
        self.assertNotIn("unknown", threads)

    def test_invalid_sketch_is_not_stored(self):
        gen = Mock()
        gen._call_llm.return_value = ("not json", "mock")
        with execution_mode("live"):
            self.assertEqual(self.journal.today(_context(), gen), {})
        self.assertEqual(self.journal.load()["days"], {})

    def test_log_is_bounded_and_feeds_consistency(self):
        for i in range(MAX_LOG + 5):
            self.journal.record("2099-01-01", f"post {i}")
        log = self.journal.load()["log"]
        self.assertEqual(len(log), MAX_LOG)
        self.assertEqual(log[-1]["text"], f"post {MAX_LOG + 4}")


class TestCasualDraft(unittest.TestCase):
    def _gen(self, *responses):
        gen = Mock()
        gen._call_llm.side_effect = [(r, "mock") for r in responses]
        return gen

    def test_plain_text_draft_is_validated_and_reviewed(self):
        from agent.discussion import casual_draft
        gen = self._gen("legs are dead after reformer today", '{"approved":true,"issue":"none"}')
        with patch("agent.validator.validator.validate_outgoing_text", return_value=(True, "legs are dead after reformer today", None)):
            text, _ = casual_draft(gen, "system", "prompt", life={"today": {}})
        self.assertEqual(text, "legs are dead after reformer today")
        self.assertEqual(gen.last_discussion_status, "approved_casual")
        self.assertEqual(gen._call_llm.call_count, 2)

    def test_review_rejection_blocks_publication(self):
        from agent.discussion import casual_draft
        gen = self._gen("a draft", '{"approved":false,"issue":"inconsistent"}')
        with patch("agent.validator.validator.validate_outgoing_text", return_value=(True, "a draft", None)):
            text, status = casual_draft(gen, "system", "prompt")
        self.assertEqual((text, status), ("", "failed"))
        self.assertEqual(gen.last_discussion_status, "review_rejected")

    def test_links_never_take_the_casual_path(self):
        from agent.discussion import casual_draft
        gen = self._gen("look at this https://example.com")
        text, _ = casual_draft(gen, "system", "prompt")
        self.assertEqual(text, "")
        self.assertEqual(gen._call_llm.call_count, 1)

    def test_unavailable_review_fails_closed(self):
        from agent.discussion import casual_draft
        gen = self._gen("a draft", None)
        with patch("agent.validator.validator.validate_outgoing_text", return_value=(True, "a draft", None)):
            self.assertEqual(casual_draft(gen, "system", "prompt")[0], "")


class TestProposalPacing(unittest.TestCase):
    def test_pacing_and_life_reach_the_proposal_prompt(self):
        from agent.original_ideas import propose
        gen = Mock()
        gen._call_llm.return_value = ('{"format":"image","kind":"moment","idea":"cold kimbap on the counter after class"}', "mock")
        idea, status = propose(gen, "identity", "context", {}, [], ["text", "image"],
                               pacing={"hours_since_last_post": 6.5}, life={"today": {"mood": "tired"}})
        self.assertEqual(status, "proposed")
        self.assertEqual(idea["kind"], "moment")
        payload = json.loads(gen._call_llm.call_args.args[1])
        self.assertEqual(payload["pacing"]["hours_since_last_post"], 6.5)
        self.assertEqual(payload["life"]["today"]["mood"], "tired")

    def test_unknown_kind_defaults_to_thought(self):
        from agent.original_ideas import propose
        gen = Mock()
        gen._call_llm.return_value = ('{"format":"text","kind":"essay","idea":"a specific ordinary opinion"}', "mock")
        idea, _ = propose(gen, "identity", "context", {}, [], ["text"])
        self.assertEqual(idea["kind"], "thought")


if __name__ == "__main__":
    unittest.main()
