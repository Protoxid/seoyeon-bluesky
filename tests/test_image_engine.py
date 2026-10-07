"""
tests/test_image_engine.py — Unit tests for Visual Identity & Image Generation.
"""

import unittest
from agent.visual_identity import VISUAL_CANON, build_image_prompt
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
        # Verify prompt is kept concise (under 250 characters instead of a huge paragraph)
        self.assertLess(len(prompt), 300)

        # Environmental POV prompt check
        pov_prompt = build_image_prompt("Seongsu-dong red brick street corner at golden hour dusk in autumn", is_selfie=False)
        self.assertIn("35mm film photograph", pov_prompt)
        self.assertIn("Seongsu-dong red brick street corner", pov_prompt)
        self.assertNotIn("Seo-yeon", pov_prompt)
        self.assertLess(len(pov_prompt), 250)

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
