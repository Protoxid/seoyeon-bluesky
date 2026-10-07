"""
tests/test_state_manager.py — Unit tests for Dynamic Cognitive State & Social Battery Engine.
"""

import tempfile
import pathlib
import unittest

from agent.state_manager import StateManager, AgentState


class TestStateManager(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.state_file = pathlib.Path(self.tmp_dir.name) / "test_state.json"
        self.manager = StateManager(self.state_file)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_default_state_initialization(self):
        st = self.manager.get_state()
        self.assertAlmostEqual(st.social_battery, 0.85)
        self.assertAlmostEqual(st.physical_fatigue, 0.20)
        self.assertTrue(self.state_file.exists())

    def test_circadian_dynamics_morning_reformer(self):
        # 8 AM KST: teaching reformer class
        st = self.manager.update_circadian_dynamics(hour=8, day_of_month=5)
        self.assertGreaterEqual(st.physical_fatigue, 0.35)
        self.assertIn("reformer", st.mood_descriptor.lower())

    def test_circadian_dynamics_deep_night(self):
        # 3 AM KST: deep night sleep
        st = self.manager.update_circadian_dynamics(hour=3, day_of_month=5)
        self.assertEqual(st.physical_fatigue, 0.10)
        self.assertEqual(st.social_battery, 0.90)
        self.assertIn("asleep", st.mood_descriptor.lower())

    def test_consume_interaction(self):
        initial_battery = self.manager.get_state().social_battery
        self.manager.consume_interaction("REPLY_COMMENT")
        new_battery = self.manager.get_state().social_battery
        self.assertLess(new_battery, initial_battery)

    def test_on_master_contact_recharge(self):
        st = self.manager.get_state()
        st.social_battery = 0.4
        self.manager.save_state(st)

        self.manager.on_master_contact("checked in")
        st_after = self.manager.get_state()
        self.assertGreater(st_after.social_battery, 0.4)
        self.assertIn("my master", st_after.mood_descriptor)

    def test_modulate_candidate_scores_when_drained(self):
        st = self.manager.get_state()
        st.social_battery = 0.20  # drained
        self.manager.save_state(st)

        scores = {"NO_ACTION": 0.40, "REPLY_COMMENT": 0.65}
        modulated = self.manager.modulate_candidate_scores(scores)
        self.assertGreater(modulated["NO_ACTION"], 0.40)
        self.assertLess(modulated["REPLY_COMMENT"], 0.65)


if __name__ == "__main__":
    unittest.main()
