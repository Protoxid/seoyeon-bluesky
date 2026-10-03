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

        # Identity markers must be present
        self.assertIn("Han Seo-yeon", prompt)
        self.assertIn("Korean woman", prompt)
        self.assertIn("26 years old", prompt)
        self.assertIn("165 cm", prompt)
        self.assertIn("balayage", prompt)
        self.assertIn("aegyo-sal", prompt)
        self.assertIn("freckles", prompt)

        # Scene details must be included
        self.assertIn(scene, prompt)
        self.assertIn("quiet morning", prompt)

        # Negative constraints
        self.assertIn("NO other people or men in frame", prompt)
        self.assertIn("NO visible commercial logos", prompt)

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
