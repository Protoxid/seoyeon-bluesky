"""
tests/test_context_engine.py — Unit tests for the Seoul Environment Context Engine.
"""

import datetime as dt
import unittest
from agent.context_engine import (
    build_environment_context,
    check_korean_holidays,
    get_circadian_phase,
    get_season,
    get_seoul_datetime,
)


class TestContextEngine(unittest.TestCase):
    def test_seoul_timezone(self):
        kst_dt = get_seoul_datetime()
        # UTC offset for KST must be +9 hours
        self.assertEqual(kst_dt.utcoffset(), dt.timedelta(hours=9))

    def test_circadian_phases(self):
        self.assertEqual(get_circadian_phase(6), "dawn")
        self.assertEqual(get_circadian_phase(9), "morning")
        self.assertEqual(get_circadian_phase(13), "midday")
        self.assertEqual(get_circadian_phase(15), "afternoon")
        self.assertEqual(get_circadian_phase(20), "evening")
        self.assertEqual(get_circadian_phase(23), "night")
        self.assertEqual(get_circadian_phase(2), "deep_night")

    def test_seasons(self):
        self.assertEqual(get_season(4), "spring")
        self.assertEqual(get_season(7), "summer")
        self.assertEqual(get_season(10), "autumn")
        self.assertEqual(get_season(1), "winter")

    def test_korean_holidays(self):
        h_oct3 = check_korean_holidays(dt.date(2026, 10, 3))
        self.assertIsNotNone(h_oct3)
        self.assertIn("개천절", h_oct3)

        h_xmas = check_korean_holidays(dt.date(2026, 12, 25))
        self.assertIsNotNone(h_xmas)
        self.assertIn("Christmas", h_xmas)

    def test_environment_context_builder(self):
        ctx = build_environment_context(
            hours_since_last_post=5.0,
            hours_since_last_action=2.0,
            posts_today=1,
            replies_today=3,
            dms_today=1,
        )
        self.assertIn("KST", ctx.seoul_time_display)
        self.assertEqual(ctx.posts_today, 1)
        self.assertEqual(ctx.replies_today, 3)

        prompt_str = ctx.to_prompt_context()
        self.assertIn("Seoul Time:", prompt_str)
        self.assertIn("Weather in Seoul:", prompt_str)


if __name__ == "__main__":
    unittest.main()
