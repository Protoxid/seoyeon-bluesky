"""
tests/test_visual_consistency.py — Unit tests for Visual Consistency & Photographic Scene Direction.

Validates that Han Seo-yeon's generated image scenes and prompts:
  1. Correspond meaningfully to their post captions and current scheduled activity.
  2. Adhere strictly to the "Consistency Solution":
     - Deep night (02:00–06:00 KST) is strictly tight in-bed selfies (duvet, messy hair, dim lamp).
     - Daytime/evening prioritizes anonymous outdoor settings (Seongsu red-brick sidewalks, crosswalks, fallen leaves, Line 2 bridge window).
     - POV shots (stray cats, books, tea cups, transit) automatically omit human face references.
     - Strictly forbids wide identifiable indoor flat or gym rooms.
  3. ImageEngine accurately distinguishes between first-person POV environmental shots and face-conditioned selfies.
"""

import unittest
from unittest.mock import patch

from agent.context_engine import WeatherSnapshot, build_environment_context
from agent.generator import generator
from agent.image_engine import ImageEngine


class TestVisualConsistency(unittest.TestCase):
    def setUp(self):
        self.weather_clear = WeatherSnapshot(
            temperature_c=16.0,
            description="clear autumn weather",
            is_raining=False,
            is_snowing=False,
            windspeed_kmh=6.0,
            retrieved_at="2026-10-08T15:00:00Z",
        )
        self.weather_rain = WeatherSnapshot(
            temperature_c=12.0,
            description="overcast with rain showers",
            is_raining=True,
            is_snowing=False,
            windspeed_kmh=12.0,
            retrieved_at="2026-10-08T15:00:00Z",
        )
        self.llm_patcher = patch.object(generator, "_call_llm", return_value=(None, "mock_offline"))
        self.mock_llm = self.llm_patcher.start()

    def tearDown(self):
        self.llm_patcher.stop()

    def test_caption_correspondence_stray_cat_pov(self):
        ctx = build_environment_context()
        ctx.circadian_phase = "afternoon"
        ctx.weather = self.weather_clear
        ctx.scheduled_activity = "errand walk through Seongsu alleys"
        ctx.scheduled_area = "Seongsu-dong"

        post = "met a very calm calico cat sunbathing on a parked scooter."
        scene = generator.determine_image_scene(post, ctx)
        scene_lower = scene.lower()

        self.assertTrue(any(w in scene_lower for w in ("cat", "kitten", "calico")))
        self.assertTrue(any(w in scene_lower for w in ("scooter", "alleyway", "seongsu")))
        self.assertTrue(any(w in scene_lower for w in ("pov", "point-of-view", "no people", "snapshot", "stray cat")))

        # Verify ImageEngine detects it as POV (no face reference)
        engine = ImageEngine(api_key="test_dummy_key")
        _, prompt, _ = engine.generate_image(scene, dry_run=True)
        self.assertIn("35mm film photograph", prompt)
        self.assertNotIn("Candid everyday smartphone selfie", prompt)

    def test_caption_correspondence_transit_line2(self):
        ctx = build_environment_context()
        ctx.circadian_phase = "evening"
        ctx.weather = self.weather_clear
        ctx.scheduled_activity = "subway commute back to Seongsu"
        ctx.scheduled_area = "Line 2 Dangsan-Hapjeong Bridge"

        post = "line 2 train crossing the bridge right when the sun drops behind the river."
        scene = generator.determine_image_scene(post, ctx)
        scene_lower = scene.lower()

        self.assertTrue(any(w in scene_lower for w in ("line 2", "train", "window", "bridge", "river", "han river")))
        self.assertTrue(any(w in scene_lower for w in ("pov", "point-of-view", "no people", "window", "snapshot")))

        # Verify ImageEngine detects it as POV (no face reference)
        engine = ImageEngine(api_key="test_dummy_key")
        _, prompt, _ = engine.generate_image(scene, dry_run=True)
        self.assertIn("35mm film photograph", prompt)
        self.assertNotIn("Candid everyday smartphone selfie", prompt)

    def test_caption_correspondence_reading_monograph_pov(self):
        ctx = build_environment_context()
        ctx.circadian_phase = "afternoon"
        ctx.weather = self.weather_clear
        ctx.scheduled_activity = "quiet reading and tea"
        ctx.scheduled_area = "quiet cafe courtyard"

        post = "reading a secondhand paperback on seoul typography. cold tea on the table."
        scene = generator.determine_image_scene(post, ctx)
        scene_lower = scene.lower()

        self.assertTrue(any(w in scene_lower for w in ("book", "paperback", "cup", "table", "bokeh")))
        self.assertTrue(any(w in scene_lower for w in ("pov", "point-of-view", "no people", "snapshot", "looking down")))

        # Verify ImageEngine detects it as POV (no face reference)
        engine = ImageEngine(api_key="test_dummy_key")
        _, prompt, _ = engine.generate_image(scene, dry_run=True)
        self.assertIn("35mm film photograph", prompt)
        self.assertNotIn("Candid everyday smartphone selfie", prompt)

    def test_weather_correspondence_rainy_day(self):
        ctx = build_environment_context()
        ctx.circadian_phase = "afternoon"
        ctx.weather = self.weather_rain
        ctx.scheduled_activity = "walking back from grocery store"
        ctx.scheduled_area = "Seongsu-dong"

        post = "rain is picking up around yeonmujang-gil crosswalk."
        scene = generator.determine_image_scene(post, ctx)
        scene_lower = scene.lower()

        self.assertTrue(any(w in scene_lower for w in ("umbrella", "rain", "droplets", "overcast")))

    def test_deep_night_in_bed_invariance(self):
        ctx = build_environment_context()
        ctx.circadian_phase = "deep_night"
        ctx.weather = self.weather_clear
        ctx.scheduled_activity = "sleeping in Seongsu flat"
        ctx.scheduled_area = "Seongsu flat bedroom"

        post = "3am and the ceiling is very quiet tonight."
        scene = generator.determine_image_scene(post, ctx)
        scene_lower = scene.lower()

        self.assertTrue(any(w in scene_lower for w in ("bed", "duvet", "pillow", "messy bedhead")))
        self.assertTrue(any(w in scene_lower for w in ("night lamp", "dark", "dim", "sleepy")))

    def test_pilates_activity_enforces_outdoor_walk_and_forbids_wide_gym(self):
        ctx = build_environment_context()
        ctx.circadian_phase = "morning"
        ctx.weather = self.weather_clear
        ctx.scheduled_activity = "morning reformer class"
        ctx.scheduled_area = "studio walk"

        post = "on the way to morning reformer class, cold sidewalk."
        scene = generator.determine_image_scene(post, ctx)
        scene_lower = scene.lower()

        # Must describe walking along sidewalk on the way to class
        self.assertTrue(any(w in scene_lower for w in ("walking", "sidewalk", "outdoor", "on the way")))
        # Strictly forbid wide identifiable indoor rooms
        self.assertNotIn("wide gym interior", scene_lower)
        self.assertNotIn("wide living room", scene_lower)
        self.assertNotIn("full flat interior", scene_lower)

    def test_image_engine_pov_vs_selfie_auto_detection(self):
        engine = ImageEngine(api_key="test_dummy_key")

        # 1. First-person POV environmental scene (no people) -> is_selfie should be False
        pov_scene = (
            "candid 35mm point-of-view photograph looking down at an open paperback book "
            "and ceramic cup on a wooden table in Seongsu, shallow depth of field, no people"
        )
        _, prompt_pov, _ = engine.generate_image(pov_scene, dry_run=True)
        self.assertIn("35mm film photograph", prompt_pov)
        self.assertNotIn("Candid everyday smartphone selfie", prompt_pov)

        # 2. Handheld front-camera selfie -> is_selfie should be True
        selfie_scene = (
            "authentic handheld front-camera outdoor selfie walking along Seongsu red-brick sidewalk, "
            "fallen yellow ginkgo fan-leaves on pavement, natural eye-level phone camera framing"
        )
        _, prompt_selfie, _ = engine.generate_image(selfie_scene, dry_run=True)
        self.assertIn("Candid everyday smartphone selfie of Seo-yeon", prompt_selfie)

    def test_llm_synthesized_scene_integration(self):
        ctx = build_environment_context()
        ctx.circadian_phase = "afternoon"
        ctx.weather = self.weather_clear
        post = "looking down at an open book"

        with patch.object(generator, "_call_llm", return_value=("candid 35mm point-of-view photograph of an open book on outdoor wooden table, no people", "claude-sonnet-5.5")):
            scene = generator.determine_image_scene(post, ctx)
            self.assertIn("open book", scene)
            self.assertIn("no people", scene)


if __name__ == "__main__":
    unittest.main()
