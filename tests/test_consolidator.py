"""
tests/test_consolidator.py — Unit tests for Nightly Cognitive Memory Consolidation.
"""

import tempfile
import pathlib
import unittest
from unittest.mock import patch, MagicMock

from agent.consolidator import MemoryConsolidator
from agent.memory_store import UserProfile, memory_store
from agent.state_manager import state_manager
from agent.goal_manager import goal_manager
from agent.narrative_engine import narrative_engine


class TestConsolidator(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.journal_file = pathlib.Path(self.tmp_dir.name) / "private_journal.jsonl"
        self.orig_users_file = memory_store.users_file
        self.orig_episodic_file = memory_store.episodic_file
        self.test_users_file = pathlib.Path(self.tmp_dir.name) / "user_memory.json"
        self.test_episodic_file = pathlib.Path(self.tmp_dir.name) / "episodic_memory.jsonl"
        memory_store.users_file = self.test_users_file
        memory_store.episodic_file = self.test_episodic_file

        self.orig_state_file = state_manager.state_file
        self.test_state_file = pathlib.Path(self.tmp_dir.name) / "agent_state.json"
        state_manager.state_file = self.test_state_file

        self.orig_goals_file = goal_manager.goals_file
        self.test_goals_file = pathlib.Path(self.tmp_dir.name) / "active_goals.json"
        goal_manager.goals_file = self.test_goals_file

        self.orig_narrative_file = narrative_engine.state_file
        self.test_narrative_file = pathlib.Path(self.tmp_dir.name) / "narrative_state.json"
        narrative_engine.state_file = self.test_narrative_file

        self.consolidator = MemoryConsolidator(
            goal_mgr=goal_manager,
            narrative_eng=narrative_engine,
            state_mgr=state_manager,
            mem_store=memory_store,
        )
        self.consolidator.journal_file = self.journal_file

    def tearDown(self):
        memory_store.users_file = self.orig_users_file
        memory_store.episodic_file = self.orig_episodic_file
        state_manager.state_file = self.orig_state_file
        goal_manager.goals_file = self.orig_goals_file
        narrative_engine.state_file = self.orig_narrative_file
        self.tmp_dir.cleanup()

    def test_read_empty_journal(self):
        entries = self.consolidator.read_recent_journal_entries()
        self.assertEqual(entries, [])

    def test_journal_appending(self):
        entry = {"date": "2026-10-06", "entry": "autumn air was brisk on line 2."}
        self.consolidator._append_journal(entry)
        entries = self.consolidator.read_recent_journal_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["entry"], "autumn air was brisk on line 2.")

    def test_consolidation_evolution_and_reset(self):
        # Create a user profile with 10 interactions as a stranger
        test_handle = "test_regular_mutual.bsky.social"
        prof = UserProfile(
            handle=test_handle,
            relationship="stranger",
            interaction_count=10,
        )
        memory_store.save_user_profile(prof)

        # Run consolidation with dry_run=False and mocked LLM
        with patch("agent.generator.generator._call_llm", return_value=("quiet evening in seongsu flat.", "mock")):
            res = self.consolidator.consolidate(dry_run=False, force=True)
            self.assertEqual(res["status"], "success")

        # Verify relationship evolved to regular
        updated_prof = memory_store.get_user_profile(test_handle)
        self.assertEqual(updated_prof.relationship, "regular")

        # Verify social battery was restored
        st = state_manager.get_state()
        self.assertEqual(st.social_battery, 0.90)
        self.assertEqual(st.physical_fatigue, 0.15)

        # Verify journal entry was written
        entries = self.consolidator.read_recent_journal_entries()
        self.assertGreaterEqual(len(entries), 1)
        last_entry = entries[-1]
        self.assertNotIn("!", last_entry["entry"])  # Zero exclamation marks


if __name__ == "__main__":
    unittest.main()
