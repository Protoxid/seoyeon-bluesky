import json
from pathlib import Path
import tempfile
import unittest
from agent.continuity import ContinuityStore


class TestEvidenceContinuity(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = ContinuityStore(Path(self.temp.name) / "continuity.json")

    def evidence(self, text="I prefer quiet films", scope="public", source="source"):
        return self.store.observe(source, text, kind="user_statement", scope=scope, subject="person")

    def memory(self, source, **changes):
        return {"id": "taste", "kind": "preference", "text": "prefers quiet films",
                "quote": "I prefer quiet films", "confidence": .9, "source_ids": [source], **changes}

    def test_private_memory_is_not_public_or_another_persons(self):
        source = self.evidence(scope="private:person")
        self.store.apply("one", {"memories": [self.memory(source)]}, [source], scope="private:person", subject="person")
        self.assertNotIn("quiet films", self.store.context(subject="person"))
        self.assertNotIn("quiet films", self.store.context(scope="private:other", subject="other"))
        self.assertIn("quiet films", self.store.context(scope="private:person", subject="person"))

    def test_private_evidence_cannot_be_promoted(self):
        source = self.evidence(scope="private:person")
        with self.assertRaises(ValueError):
            self.store.apply("one", {"memories": [self.memory(source)]}, [source], subject="person")
        self.assertEqual(self.store.load()["memories"], {})

    def test_verbatim_evidence_is_required(self):
        source = self.evidence()
        with self.assertRaises(ValueError):
            self.store.apply("one", {"memories": [self.memory(source, quote="I love horror")]}, [source])

    def test_generated_reply_cannot_define_user_preference(self):
        source = self.store.observe("out", "I prefer quiet films", kind="published_statement")
        with self.assertRaises(ValueError):
            self.store.apply("one", {"memories": [self.memory(source)]}, [source])

    def test_unknown_sources_rejected_atomically(self):
        source = self.evidence()
        proposal = {"memories": [self.memory(source), self.memory("invented", id="other")]}
        with self.assertRaises(ValueError):
            self.store.apply("one", proposal, [source])
        self.assertEqual(self.store.load()["memories"], {})

    def test_replay_does_not_duplicate(self):
        source = self.evidence()
        proposal = {"memories": [self.memory(source)]}
        self.assertTrue(self.store.apply("one", proposal, [source], subject="person"))
        self.assertFalse(self.store.apply("one", proposal, [source], subject="person"))
        self.assertEqual(len(self.store.load()["memories"]), 1)

    def test_correction_preserves_reason_and_history(self):
        source = self.evidence()
        self.store.apply("one", {"memories": [self.memory(source)]}, [source], subject="person")
        updated = self.evidence("I prefer loud films now", source="second")
        row = self.memory(updated, text="prefers loud films now", quote="I prefer loud films now", reason="explicit correction")
        self.store.apply("two", {"memories": [row]}, [updated], subject="person")
        result = self.store.load()["memories"]["taste"]
        self.assertEqual(result["text"], "prefers loud films now")
        self.assertEqual(result["history"][0]["text"], "prefers quiet films")

    def test_immutable_evidence_id(self):
        self.evidence()
        with self.assertRaises(ValueError):
            self.evidence("changed")

    def test_oversized_evidence_not_silently_truncated(self):
        with self.assertRaises(ValueError):
            self.evidence("x" * 12001)

    def test_low_confidence_memory_not_saved(self):
        source = self.evidence()
        self.store.apply("one", {"memories": [self.memory(source, confidence=.2)]}, [source])
        self.assertEqual(self.store.load()["memories"], {})

    def test_unrelated_observation_does_not_close_commitment(self):
        source = self.evidence("I'll send the title")
        self.store.apply("one", {"commitments": [{"id": "book", "topic": "send exact title", "status": "open", "source_ids": [source]}]}, [source], subject="person")
        self.evidence("nice weather", source="two")
        self.assertEqual(self.store.load()["commitments"]["book"]["status"], "open")
        with self.assertRaises(ValueError):
            self.store.apply("two", {"commitments": [{"id": "book", "topic": "title", "status": "fulfilled", "source_ids": [source]}]}, [source], subject="person")

    def test_actual_artifact_is_versioned(self):
        source = self.evidence("the lettering looks hand painted")
        artifact = {"id": "essay", "title": "Lettering", "content": "An original study of irregular letterforms.", "source_ids": [source]}
        self.store.apply("one", {"artifact": artifact}, [source], subject="self")
        artifact.update(content="Revised study: irregular spacing can carry rhythm.", reason="developed the observation")
        self.store.apply("two", {"artifact": artifact}, [source], subject="self")
        self.assertEqual(self.store.load()["artifacts"]["essay"]["version"], 2)
        self.assertEqual(len(self.store.load()["artifacts"]["essay"]["history"]), 1)

    def test_claiming_completion_is_not_completion_evidence(self):
        source = self.evidence("I finished a book")
        with self.assertRaises(ValueError):
            self.store.apply("one", {"pursuits": [{"title": "Read book", "status": "completed", "source_ids": [source]}]}, [source])

    def test_fictional_world_is_labeled(self):
        source = self.evidence("thinking about lettering")
        self.store.apply("one", {"world": {"activity": "lettering study", "status": "intended", "source_ids": [source]}}, [source])
        self.assertIn("fictional_state", self.store.context())

    def test_corruption_does_not_reset_memory(self):
        self.store.path.write_text("broken", encoding="utf-8")
        with self.assertRaises(json.JSONDecodeError):
            self.store.load()
        self.assertEqual(self.store.path.read_text(), "broken")
