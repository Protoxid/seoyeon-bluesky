import json
import pathlib
import random
import tempfile
import unittest
from unittest.mock import patch

from agent import image_engine as ie
from agent.bsky_client import BlueskyClient
from agent.context_engine import build_environment_context
from agent.generator import generator
from agent.image_engine import ImageEngine
from agent.visual_identity import wardrobe_subset


def _png(path: pathlib.Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\x89PNG fake")


class TestLocationReferences(unittest.TestCase):
    def test_missing_files_handled(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            self.assertEqual(ie.available_locations(root), [])
            self.assertIsNone(ie.normalize_location("cafe", root))
            self.assertIsNone(ie.location_reference_path("cafe", root))
        self.assertIsNone(ie.location_reference_path("nowhere"))

    def test_only_known_existing_names_accepted(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            _png(root / "cafe" / "cafe_01.png")
            _png(root / "rooftop" / "rooftop_02.png")
            self.assertEqual(ie.available_locations(root), ["cafe", "rooftop"])
            self.assertEqual(ie.normalize_location(" Cafe ", root), "cafe")
            for bad in ("../cafe", "gym", None, 3, "kitchen"):
                self.assertIsNone(ie.normalize_location(bad, root))
            self.assertEqual(ie.location_reference_path("rooftop", root, rng=random.Random(1)).name, "rooftop_02.png")

    def test_scene_location_parsing(self):
        ctx = build_environment_context()
        def run(raw, avail):
            with patch.object(generator, "_call_llm", return_value=(raw, "m")), \
                 patch("agent.image_engine.available_locations", return_value=avail), \
                 patch("agent.image_engine._location_files", side_effect=lambda n, root=None: [pathlib.Path(n + "_01.png")] if n in avail else []):
                return generator.determine_image_scene("post", ctx), dict(generator.last_scene)
        _, scene = run('{"description":"a table, no people","is_selfie":false,"location":"kitchen"}', ["kitchen"])
        self.assertEqual(scene["location"], "kitchen")
        _, scene = run('{"description":"x","is_selfie":false,"location":"narnia"}', ["kitchen"])
        self.assertIsNone(scene["location"])
        _, scene = run('{"description":"x","is_selfie":false}', ["kitchen"])
        self.assertIsNone(scene["location"])
        _, scene = run('{"description":"x","is_selfie":false,"location":"cafe"}', [])
        self.assertIsNone(scene["location"])

    def test_pov_with_location_uses_i2i_and_only_location_ref(self):
        engine = ImageEngine(api_key="k")
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            _png(root / "kitchen" / "kitchen_01.png")
            with patch.object(ie, "LOCATIONS_DIR", root), \
                 patch("agent.image_engine.get_or_upload_master_reference", return_value="https://x/kitchen") as up, \
                 patch("agent.image_engine.urllib.request.urlopen", side_effect=RuntimeError("stop")) as req:
                engine.generate_image("bowl on table", is_selfie=False, dry_run=False, location="kitchen")
        up.assert_called_once()
        payload = json.loads(req.call_args.args[0].data)
        self.assertIn("image-to-image", payload["model"])
        self.assertEqual(payload["input"]["input_urls"], ["https://x/kitchen"])

    def test_selfie_with_location_adds_third_ref(self):
        engine = ImageEngine(api_key="k")
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            _png(root / "studio" / "studio_01.png")
            with patch.object(ie, "LOCATIONS_DIR", root), \
                 patch("agent.image_engine.get_or_upload_master_reference", side_effect=["u1", "u2", "u3"]), \
                 patch("agent.image_engine.urllib.request.urlopen", side_effect=RuntimeError("stop")) as req:
                engine.generate_image("selfie", is_selfie=True, dry_run=False, location="studio")
        self.assertEqual(json.loads(req.call_args.args[0].data)["input"]["input_urls"], ["u1", "u2", "u3"])

    def test_location_upload_failure_falls_back_to_text_pov(self):
        engine = ImageEngine(api_key="k")
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            _png(root / "kitchen" / "kitchen_01.png")
            with patch.object(ie, "LOCATIONS_DIR", root), \
                 patch("agent.image_engine.get_or_upload_master_reference", return_value=None), \
                 patch("agent.image_engine.urllib.request.urlopen", side_effect=RuntimeError("stop")) as req:
                engine.generate_image("bowl", is_selfie=False, dry_run=False, location="kitchen")
        payload = json.loads(req.call_args.args[0].data)
        self.assertNotIn("input_urls", payload["input"])
        self.assertIn("text-to-image", payload["model"])

    def test_unavailable_location_is_ignored_in_dry_run(self):
        with tempfile.TemporaryDirectory() as d, patch.object(ie, "LOCATIONS_DIR", pathlib.Path(d)):
            img, _, err = ImageEngine(api_key="k").generate_image("bowl", is_selfie=False, dry_run=True, location="kitchen")
        self.assertIsNotNone(img)
        self.assertIsNone(err)


class TestWardrobe(unittest.TestCase):
    def test_season_filter_and_missing_file(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "w.json"
            p.write_text(json.dumps({"outfits": {
                "a": {"name": "A", "description": "wool coat", "season": ["winter"], "vibe": "v"},
                "b": {"name": "B", "description": "linen shirt", "season": ["summer", "spring"]},
                "c": {"name": "C", "description": "hoodie", "season": ["winter", "autumn"]},
            }}), encoding="utf-8")
            self.assertEqual({o["description"] for o in wardrobe_subset("winter", path=p)}, {"wool coat", "hoodie"})
            self.assertEqual(len(wardrobe_subset("winter", limit=1, path=p)), 1)
            self.assertEqual([o["description"] for o in wardrobe_subset("summer", path=p)], ["linen shirt"])
            self.assertEqual(wardrobe_subset("monsoon", path=p), [])
            self.assertEqual(wardrobe_subset("winter", path=pathlib.Path(d) / "missing.json"), [])


class TestMultiImagePublish(unittest.TestCase):
    def _client(self):
        c = BlueskyClient()
        c.dry_run = True
        return c

    def test_multi_image_payload(self):
        c = self._client()
        with patch.object(c, "ensure_session", return_value=True):
            res = c.publish_image_post("hi", [b"1", b"2", b"3", b"4", b"5"], alt_text=["a", "b", "c", "d", "e"])
        self.assertTrue(res.get("uri"))
        images = c.last_dry_run_record["embed"]["images"]
        self.assertEqual([i["alt"] for i in images], ["a", "b", "c", "d"])

    def test_single_image_backward_compatible(self):
        c = self._client()
        with patch.object(c, "ensure_session", return_value=True):
            c.publish_image_post("hi", b"bytes", alt_text="scene")
        images = c.last_dry_run_record["embed"]["images"]
        self.assertEqual(len(images), 1)
        self.assertEqual(images[0]["alt"], "scene")

    def test_any_blob_failure_aborts(self):
        c = self._client()
        with patch.object(c, "upload_image_blob", side_effect=[{"ref": 1}, None]):
            self.assertEqual(c.publish_image_post("hi", [b"1", b"2"], alt_text=["a", "b"]), {})


if __name__ == "__main__":
    unittest.main()
