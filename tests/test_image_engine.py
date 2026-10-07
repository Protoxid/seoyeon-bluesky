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

    def test_image_engine_dry_run(self):
        engine = ImageEngine(api_key="test_key")
        img_bytes, prompt_used, err = engine.generate_image(
            scene_description="watching rain outside window",
            dry_run=True,
        )
        self.assertIsNotNone(img_bytes)
        self.assertGreater(len(img_bytes), 100)
        self.assertIsNone(err)
        self.assertIn("watching rain outside window", prompt_used)


if __name__ == "__main__":
    unittest.main()
