"""
tests/test_narrative_engine.py — Unit Tests for Narrative Continuity & Conversational Loops.

Verifies:
  1. Opening, tracking, and resolving conversational loops with users.
  2. Formatting loop context into generator prompt instructions.
  3. Multi-day narrative arcs and milestone progression.
  4. Temporal statement validation against current Seoul circadian hour.
"""

import pathlib
import shutil
import tempfile
import unittest

from agent.narrative_engine import (
    ConversationalLoop,
    LoopStatus,
    NarrativeContinuityEngine,
)


class TestNarrativeEngine(unittest.TestCase):
    def setUp(self):
        self.test_dir = pathlib.Path(tempfile.mkdtemp())
        self.state_file = self.test_dir / "narrative_state.json"
        self.engine = NarrativeContinuityEngine(storage_file=self.state_file)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_open_and_retrieve_conversational_loop(self):
        """Verifies opening a conversational loop and retrieving by DID or handle."""
        did = "did:plc:cinema_fan_123"
        handle = "cinema_fan.bsky.social"

        loop = self.engine.open_loop(
            partner_identifier=did,
            partner_handle=handle,
            topic="Wim Wenders' Perfect Days",
            loop_type="recommendation_received",
            context_note="User recommended watching the public bathroom architecture scenes.",
        )
        self.assertIsNotNone(loop)
        self.assertEqual(loop.status, LoopStatus.OPEN.value)

        # Retrieve by DID
        loops_by_did = self.engine.get_open_loops_for_user(did)
        self.assertEqual(len(loops_by_did), 1)
        self.assertEqual(loops_by_did[0].topic, "Wim Wenders' Perfect Days")

        # Retrieve by handle
        loops_by_handle = self.engine.get_open_loops_for_user("", partner_handle=handle)
        self.assertEqual(len(loops_by_handle), 1)
        self.assertEqual(loops_by_handle[0].topic, "Wim Wenders' Perfect Days")

    def test_resolve_conversational_loop(self):
        """Verifies resolving a conversational loop removes it from open list."""
        did = "did:plc:book_friend"
        loop = self.engine.open_loop(
            partner_identifier=did,
            partner_handle="book_friend",
            topic="Calvino's Invisible Cities",
            loop_type="promise_to_check",
            context_note="Promised to look for the translation at secondhand bookstall.",
        )

        success = self.engine.resolve_loop(
            loop.loop_id,
            resolution_note="Found the Minumsa edition near Ttukseom yesterday.",
        )
        self.assertTrue(success)

        # Now get_open_loops_for_user should be empty
        active = self.engine.get_open_loops_for_user(did)
        self.assertEqual(len(active), 0)

    def test_format_loops_for_user_prompt(self):
        """Verifies formatted loop prompt contains topic and context."""
        did = "did:plc:design_mutual"
        self.engine.open_loop(
            partner_identifier=did,
            partner_handle="design_mutual",
            topic="Euljiro print shops",
            loop_type="shared_question",
            context_note="Wondering if the risograph studio is still open on Saturdays.",
        )

        prompt_str = self.engine.format_loops_for_user_prompt(did, "design_mutual")
        self.assertIn("Past conversation threads", prompt_str)
        self.assertIn("Euljiro print shops", prompt_str)
        self.assertIn("risograph studio", prompt_str)

    def test_narrative_arcs_and_milestones(self):
        self.assertEqual(self.engine.get_active_narrative_arcs(), [])
        self.assertEqual(self.engine.advance_arcs_daily(30), [])

    def test_temporal_coherence_validation(self):
        for text in ("yesterday dinner was good", "midnight walk was freezing", "dinner after a night shift"):
            self.assertTrue(self.engine.validate_temporal_statement(text, 9)[0])
        self.assertFalse(self.engine.validate_temporal_statement("finished", 9, {"completed_at": "2099-01-01T00:00:00+09:00"})[0])


if __name__ == "__main__":
    unittest.main()
