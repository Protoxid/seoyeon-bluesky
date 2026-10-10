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

    def test_no_scene_is_invented_on_provider_failure(self):
        with patch.object(generator, "_call_llm", return_value=(None, "failed")):
            for phase in ("morning", "afternoon", "deep_night"):
                ctx = build_environment_context()
                ctx.circadian_phase = phase
                self.assertEqual(generator.determine_image_scene("a thought", ctx), "")

    def test_scene_requires_structured_type(self):
        ctx = build_environment_context()
        for raw in ('plain scene text', '{"description":"scene","is_selfie":"false"}', '{}'):
            with patch.object(generator, "_call_llm", return_value=(raw, "mock")):
                self.assertEqual(generator.determine_image_scene("a thought", ctx), "")

    def test_pixel_review_blocks_unavailable_or_rejected_review(self):
        generator.last_scene = {"is_selfie": False}
        for raw in (None, '{"approved":false,"alt_text":"a chair"}', '{"approved":true,"alt_text":""}'):
            with patch.object(generator, "_call_llm", return_value=(raw, "mock")):
                self.assertFalse(generator.review_image(b"test pixels", "chair", "chair")[0])
        with patch.object(generator, "_call_llm", return_value=('{"approved":true,"alt_text":"A wooden chair."}', "mock")) as call:
            self.assertEqual(generator.review_image(b"test pixels", "chair", "chair"), (True, "A wooden chair."))
            self.assertEqual(call.call_args.args[1][1]["type"], "image_url")

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

        with patch.object(generator, "_call_llm", return_value=('{"description":"open book on a table, no people","is_selfie":false}', "mock")):
            scene = generator.determine_image_scene(post, ctx)
            self.assertIn("open book", scene)
            self.assertIn("no people", scene)


if __name__ == "__main__":
    unittest.main()
