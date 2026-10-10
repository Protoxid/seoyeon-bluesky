"""
tests/test_weekly_planner.py — Unit tests for Weekly Life Planner and Cognitive Scene Synthesis.
"""

import datetime as dt
import unittest
from agent.weekly_planner import WeeklyPlanner, BASELINE_SCHEDULE
from agent.context_engine import EnvironmentContext, WeatherSnapshot
from agent.generator import generator


class TestWeeklyPlanner(unittest.TestCase):
    def setUp(self):
        self.planner = WeeklyPlanner()

    def test_iso_week_id(self):
        d = dt.date(2026, 10, 8)
        week_id = self.planner.get_iso_week_id(d)
        self.assertTrue(week_id.startswith("2026-W"))

    def test_get_current_activity_phases(self):
        # Test morning
        kst_tz = dt.timezone(dt.timedelta(hours=9))
        morning_time = dt.datetime(2026, 10, 8, 9, 30, tzinfo=kst_tz)
        act = self.planner.get_current_activity(morning_time)
        self.assertEqual(act["phase"], "morning")
        self.assertEqual(act["activity"], "")
        self.assertEqual(act["area"], "")

        # Test deep night
        night_time = dt.datetime(2026, 10, 8, 3, 15, tzinfo=kst_tz)
        act_night = self.planner.get_current_activity(night_time)
        self.assertEqual(act_night["phase"], "deep_night")
        self.assertEqual(act_night["area"], "")

    def test_format_schedule_summary(self):
        summary = self.planner.format_schedule_summary()
        self.assertIn("=== Han Seo-yeon Optional Intentions", summary)
        self.assertIn("intentions", summary)
        self.assertNotIn("[SUNDAY]", summary)

    def test_context_read_never_creates_calendar(self):
        from unittest.mock import patch
        with patch.object(self.planner, "_generate_schedule_with_llm", side_effect=AssertionError("read triggered generation")):
            self.assertEqual(self.planner.get_current_activity()["activity"], "")

if __name__ == "__main__":
    unittest.main()
