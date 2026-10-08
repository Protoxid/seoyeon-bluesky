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
        """Verifies narrative arcs store and append milestones across days."""
        arcs = self.engine.get_active_narrative_arcs()
        self.assertGreaterEqual(len(arcs), 1)
        persimmon_arc = arcs[0]

        # Add a new milestone
        success = self.engine.add_narrative_milestone(
            arc_id=persimmon_arc.arc_id,
            note="Persimmons are beginning to wrinkle slightly; skin feels leathery.",
        )
        self.assertTrue(success)

        context_str = self.engine.format_narrative_arcs_context()
        self.assertIn("wrinkle slightly", context_str)

    def test_temporal_coherence_validation(self):
        """Verifies temporal validator blocks claiming evening/night activities during morning hours."""
        # 09:00 KST (morning): Cannot claim to have finished dinner
        ok, reason = self.engine.validate_temporal_statement("just finished dinner with radish soup.", current_hour_kst=9)
        self.assertFalse(ok)
        self.assertIn("Temporal inconsistency", reason)

        # 09:00 KST: Ordinary morning observation is completely valid
        ok, reason = self.engine.validate_temporal_statement("morning light through the kitchen blind is cold.", current_hour_kst=9)
        self.assertTrue(ok)
        self.assertIsNone(reason)

        # 15:00 KST (afternoon): Cannot claim midnight activities
        ok, reason = self.engine.validate_temporal_statement("midnight walk along the silent bridge was freezing.", current_hour_kst=15)
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
