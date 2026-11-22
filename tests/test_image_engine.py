"""
tests/test_image_engine.py — Unit tests for Visual Identity & Image Generation.
"""

import json
import unittest
from agent.visual_identity import VISUAL_CANON, build_image_prompt, place_setting
from agent.image_engine import ImageEngine


class TestImageEngine(unittest.TestCase):
    def test_visual_identity_prompt_construction(self):
        scene = "sitting at a quiet corner table in a Seongsu cafe, grey wool coat"
        prompt = build_image_prompt(scene_description=scene, mood="quiet morning")

        # Prompt should be concise, natural, and include scene and mood
        self.assertIn("Seo-yeon", prompt)
        self.assertIn(scene, prompt)
        self.assertIn("quiet morning", prompt)
        self.assertIn("smartphone selfie", prompt)
        # Contract change (2026-11-16): every prompt ends with a setting for the place the scene happens in
        # (her home by default) so images are not generic; the scene-specific part itself stays concise.
        from agent.visual_identity import place_setting
        setting = place_setting()
        self.assertTrue(prompt.endswith(setting))
        self.assertLess(len(prompt) - len(setting), 300)

        # Environmental POV prompt check
        pov_prompt = build_image_prompt("Seongsu-dong red brick street corner at golden hour dusk in autumn", is_selfie=False)
        self.assertIn("35mm film photograph", pov_prompt)
        self.assertIn("Seongsu-dong red brick street corner", pov_prompt)
        self.assertNotIn("Seo-yeon", pov_prompt)
        self.assertTrue(pov_prompt.endswith(setting))
        self.assertLess(len(pov_prompt) - len(setting), 250)

    def test_every_prompt_variant_names_its_place(self):
        from agent.config import config
        for is_selfie in (True, False):
            for location_ref in (True, False):
                home = build_image_prompt("a bowl of rice on a small table", is_selfie=is_selfie, location_ref=location_ref)
                self.assertIn(f"Setting: {config.home_place}", home)
                away = build_image_prompt("a bowl of rice on a small table", is_selfie=is_selfie, location_ref=location_ref,
                                          place="Haeundae, Busan, South Korea")
                self.assertIn("Setting: Haeundae, Busan, South Korea", away)
                self.assertNotIn(config.home_place, away)
                # Contract change (2026-11-22): place anchoring stays concise instead of verbose label instructions.
                self.assertIn("Natural local details", away)
                self.assertIn("no brand logos", away)
                self.assertLess(len(place_setting()), 120)

    def test_scene_planner_requests_simple_unlabeled_prompts_and_caps_length(self):
        from unittest.mock import patch
        from agent.context_engine import build_environment_context
        from agent.generator import generator

        long_desc = ("a kimchi jar on a wooden table in a seongsu restaurant, warm evening light, no people. " * 10).strip()
        reply = json.dumps({"description": long_desc, "is_selfie": False, "location": None, "place": "Seongsu-dong, Seoul, South Korea"})
        with patch.object(generator, "_call_llm", return_value=(reply, "mock")) as mock_llm, \
             patch("agent.image_engine.available_locations", return_value=[]), \
             patch("agent.visual_identity.wardrobe_subset", return_value=[]), \
             patch("agent.life.LifeJournal.prompt_data", return_value={}):
            scene = generator.determine_image_scene("kimchi stew for dinner", build_environment_context())

        sys_prompt = mock_llm.call_args.args[0]
        self.assertIn("short, simple, natural", sys_prompt)
        self.assertIn("do NOT list background clutter", sys_prompt)
        self.assertLessEqual(len(scene), 400)

    def test_scene_place_is_kept_and_bounded(self):
        from unittest.mock import patch
        from agent.context_engine import build_environment_context
        from agent.generator import generator
        reply = '{"description":"a beach boardwalk, no people","is_selfie":false,"location":null,"place":"Haeundae, Busan, South Korea"}'
        with patch.object(generator, "_call_llm", return_value=(reply, "mock")), \
             patch("agent.life.LifeJournal.prompt_data", return_value={}):
            generator.determine_image_scene("visiting mom in busan", build_environment_context())
        self.assertEqual(generator.last_scene["place"], "Haeundae, Busan, South Korea")

    def test_image_engine_auto_detect_pov_vs_selfie(self):
        engine = ImageEngine(api_key="test_key")
        # POV shot with stray cat or no people
        _, prompt_cat, _ = engine.generate_image(
            scene_description="candid 35mm point-of-view photograph of a calm stray calico cat curled up on a parked scooter in Seongsu alley, no people",
            dry_run=True,
        )
        self.assertIn("35mm film photograph", prompt_cat)
        self.assertNotIn("smartphone selfie", prompt_cat)

        # Handheld selfie
        _, prompt_selfie, _ = engine.generate_image(
            scene_description="authentic handheld front-camera outdoor morning selfie walking along Seongsu red-brick sidewalk",
            dry_run=True,
        )
        self.assertIn("smartphone selfie", prompt_selfie)


if __name__ == "__main__":
    unittest.main()
