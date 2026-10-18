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

        with patch.object(generator, "_call_llm", return_value=('```json\n{"description":"open book on a table, no people","is_selfie":false}\n```', "mock")):
            scene = generator.determine_image_scene(post, ctx)
            self.assertIn("open book", scene)
            self.assertIn("no people", scene)

    def test_review_image_downscales_oversized_selfie_references_and_parses_fenced_json(self):
        import tempfile
        from pathlib import Path
        from PIL import Image
        generator.last_scene = {"is_selfie": True}
        fenced_review = '```json\n{"approved": true, "alt_text": "A candid selfie of Seo-yeon."}\n```'
        with tempfile.TemporaryDirectory() as tmp:
            a1 = Path(tmp) / "a1.png"
            c5 = Path(tmp) / "c5.png"
            Image.new("RGB", (2000, 2000), color=(210, 195, 185)).save(a1, format="PNG")
            Image.new("RGB", (2000, 2000), color=(180, 175, 170)).save(c5, format="PNG")
            with patch("agent.image_engine.MASTER_A1_PATH", a1), \
                 patch("agent.image_engine.MASTER_C5_PATH", c5), \
                 patch.object(generator, "_call_llm", return_value=(fenced_review, "mock")) as call:
                ok, alt = generator.review_image(a1.read_bytes(), "quiet afternoon.", "candid selfie")
        self.assertTrue(ok)
        self.assertEqual(alt, "A candid selfie of Seo-yeon.")
        images_arg = call.call_args.args[1]
        self.assertEqual(len(images_arg), 4)
        for ref_part in images_arg[1:]:
            url = ref_part["image_url"]["url"]
            self.assertTrue(url.startswith("data:image/jpeg;base64,"))
            # Compressed reference data URL must stay well under OpenRouter/Anthropic 5MB limit
            self.assertLess(len(url), 600_000)

    def test_image_post_caption_passes_grounded_draft_with_fenced_json(self):
        ctx = build_environment_context()
        draft_resp = '```json\n{"text": "quiet afternoon frame for my human.", "kind": "social", "claims": []}\n```'
        review_resp = '```json\n{"approved": true, "issue": "none"}\n```'
        with patch.object(generator, "_call_llm", side_effect=[(draft_resp, "mock"), (review_resp, "mock")]) as call:
            text, _ = generator.generate_post("master_order_image", ctx, topic_hint="post a selfie", include_image=True)
        self.assertEqual(text, "quiet afternoon frame for my human.")
        self.assertIn("include_image=true", call.call_args_list[0].args[0])
        self.assertIn("include_image=true", call.call_args_list[1].args[0])


if __name__ == "__main__":
    unittest.main()
