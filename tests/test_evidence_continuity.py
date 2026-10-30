import json
from pathlib import Path
import tempfile
import unittest
from agent.continuity import ContinuityStore


class TestEvidenceContinuity(unittest.TestCase):
    def test_own_artifact_does_not_retrigger_reflection(self):
        from unittest.mock import patch
        from agent.continuity import reflect
        from agent.runtime import execution_mode
        from agent.context_engine import build_environment_context
        from agent.generator import generator
        source=self.evidence("an external observation")
        with execution_mode("live"), patch("agent.continuity.ContinuityStore",return_value=self.store), patch.object(generator,"_call_llm",return_value=('{}','mock')) as model:
            reflect(build_environment_context())
            self.store.apply("artifact", {"artifact":{"title":"new work","content":"An original piece of digital work.","source_ids":[source]}}, [source],subject="self")
            reflect(build_environment_context())
        model.assert_called_once()

    def test_kept_drafts_retrieved_but_private_and_discarded_drafts_excluded(self):
        source=self.evidence("a public observation")
        self.store.apply("draft", {"draft":{"id":"kept","text":"a thought about a film","status":"kept","source_ids":[source]}}, [source], subject="self")
        self.store.apply("discard", {"draft":{"id":"discarded","text":"discarded words","status":"discarded","source_ids":[source]}}, [source], subject="self")
        private=self.evidence("private words",scope="operator",source="private")
        self.store.apply("private", {"draft":{"id":"private","text":"secret proposal","status":"kept","source_ids":[private]}}, [private], scope="operator",subject="self")
        for result in (self.store.context(subject="self"),json.dumps(self.store.public_post_material())):
            self.assertIn("a thought about a film",result)
            self.assertNotIn("secret proposal",result)
            self.assertNotIn("discarded words",result)
        packet=self.store.public_post_material()
        self.assertEqual([r['id'] for r in packet['observations']],[source])

    def test_paused_pursuit_is_not_default_material_but_remains_searchable(self):
        source=self.evidence("lettering study")
        self.store.apply("paused", {"pursuits":[{"id":"study","title":"lettering study","status":"paused","source_ids":[source]}]}, [source],subject="self")
        self.assertNotIn("lettering study", self.store.context(subject="self"))
        self.assertIn("lettering study", self.store.context("lettering",subject="self"))

    def test_current_topic_outranks_unrelated_self_project(self):
        source=self.evidence("a film observation")
        self.store.apply("film", {"artifact":{"id":"film","title":"film observation","content":"A considered film observation with concrete detail.","source_ids":[source]}}, [source],subject="other")
        self.store.apply("study", {"pursuits":[{"id":"study","title":"lettering study","status":"active","source_ids":[source]}]}, [source],subject="self")
        result=json.loads(self.store.context("film",subject="self",limit=1))
        self.assertEqual(result[0]['id'],'film')

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

    def test_own_expressed_taste_can_be_retained_as_scoped_opinion(self):
        source = self.store.observe("out", "I prefer quiet films", kind="published_statement", scope="private:person")
        self.store.apply("one", {"memories": [self.memory(source, kind="opinion")]}, [source], scope="private:person", subject="person")
        memory = self.store.load()["memories"]["taste"]
        self.assertEqual(memory["subject"], "self")
        self.assertNotIn("quiet films", self.store.context(subject="self"))

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

    def test_malformed_model_collections_are_rejected(self):
        source = self.evidence()
        for proposal in ({"memories": "not a list"}, {"world": []}, {"memories": [None]}):
            with self.assertRaises(ValueError):
                self.store.apply("bad", proposal, [source])
        self.assertEqual(self.store.load()["memories"], {})

    def test_prompt_preview_preserves_full_artifact_on_disk(self):
        source = self.evidence()
        content = "original work " * 300
        self.store.apply("one", {"artifact": {"id": "work", "title": "Study", "content": content, "source_ids": [source]}}, [source])
        self.assertEqual(self.store.load()["artifacts"]["work"]["content"], content)
        prompt = self.store.context()
        self.assertIn("preview_truncated", prompt)
        self.assertLess(len(prompt), len(content))
