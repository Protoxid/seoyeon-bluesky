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
        self.assertTrue(len(act["activity"]) > 0)
        self.assertTrue(len(act["area"]) > 0)

        # Test deep night
        night_time = dt.datetime(2026, 10, 8, 3, 15, tzinfo=kst_tz)
        act_night = self.planner.get_current_activity(night_time)
        self.assertEqual(act_night["phase"], "deep_night")
        self.assertIn("bed", act_night["area"].lower())

    def test_format_schedule_summary(self):
        summary = self.planner.format_schedule_summary()
        self.assertIn("=== Han Seo-yeon Weekly Life Itinerary", summary)
        self.assertIn("[MONDAY]", summary)
        self.assertIn("[SUNDAY]", summary)

    def test_cognitive_scene_synthesis_deep_night(self):
        weather = WeatherSnapshot(
            temperature_c=14.0,
            description="clear sky",
            is_raining=False,
            is_snowing=False,
            windspeed_kmh=7.0,
            retrieved_at="2026-10-08T03:30:00Z",
        )
        ctx = EnvironmentContext(
            seoul_time_iso="2026-10-08T03:30:00+09:00",
            seoul_time_display="03:30 KST",
            date_display="2026-10-08",
            day_of_week="Thursday",
            is_weekend=False,
            circadian_phase="deep_night",
            season="autumn",
            holiday_note=None,
            weather=weather,
            hours_since_last_post=2.0,
            hours_since_last_action=2.0,
            posts_today=1,
            replies_today=0,
            dms_today=0,
            scheduled_activity="in bed half-asleep",
            scheduled_area="bed in bedroom",
        )
        scene = generator.determine_image_scene("test requested by my human", ctx)
        self.assertIn("bed", scene.lower())
        self.assertIn("duvet", scene.lower())

    def test_cognitive_scene_synthesis_stray_cat(self):
        weather = WeatherSnapshot(
            temperature_c=18.0,
            description="sunny",
            is_raining=False,
            is_snowing=False,
            windspeed_kmh=5.0,
            retrieved_at="2026-10-08T10:30:00Z",
        )
        ctx = EnvironmentContext(
            seoul_time_iso="2026-10-08T10:30:00+09:00",
            seoul_time_display="10:30 KST",
            date_display="2026-10-08",
            day_of_week="Thursday",
            is_weekend=False,
            circadian_phase="morning",
            season="autumn",
            holiday_note=None,
            weather=weather,
            hours_since_last_post=3.0,
            hours_since_last_action=3.0,
            posts_today=0,
            replies_today=0,
            dms_today=0,
            scheduled_activity="walking to studio",
            scheduled_area="Seongsu street",
        )
        scene = generator.determine_image_scene("met a stray cat on the way to the studio", ctx)
        self.assertIn("cat", scene.lower())
        self.assertTrue(len(scene) > 20)


if __name__ == "__main__":
    unittest.main()
