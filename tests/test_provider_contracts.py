import json
import unittest
from unittest.mock import patch, MagicMock
from agent.image_engine import ImageEngine
from agent.generator import ContentGenerator


def response(value):
    result = MagicMock()
    result.__enter__.return_value = result
    result.read.return_value = json.dumps(value).encode()
    return result


class TestProviderContracts(unittest.TestCase):
    def test_pov_uses_exact_documented_route_without_faces(self):
        engine = ImageEngine(api_key="dummy")
        with patch("agent.image_engine.urllib.request.urlopen", return_value=response({"code": 422, "data": {}})) as request:
            image, _, error = engine.generate_image("a chair", is_selfie=False, dry_run=False)
        payload = json.loads(request.call_args.args[0].data)
        self.assertEqual(payload["model"], "gpt-image-2-5-sunburst-text-to-image")
        self.assertNotIn("input_urls", payload["input"])
        self.assertEqual(payload["input"]["background"], "opaque")
        self.assertIsNone(image)
        self.assertEqual(engine.last_outcome, "rejected")

    def test_missing_reference_blocks_selfie_before_task_creation(self):
        engine = ImageEngine(api_key="dummy")
        with patch("agent.image_engine.get_or_upload_master_reference", side_effect=["https://example.com/a", None]), patch("agent.image_engine.urllib.request.urlopen") as request:
            image, _, error = engine.generate_image("selfie", is_selfie=True, dry_run=False)
        self.assertIsNone(image)
        self.assertIn("references", error)
        request.assert_not_called()

    def test_completed_image_billed_even_without_download_url(self):
        engine = ImageEngine(api_key="dummy")
        engine.reservation_id = "hold"
        replies = [response({"code": 200, "data": {"taskId": "task"}}), response({"code": 200, "data": {"state": "success", "resultJson": "{}"}})]
        with patch("agent.image_engine.urllib.request.urlopen", side_effect=replies), patch("agent.image_engine.time.sleep"), patch("agent.budget_manager.budget_manager.mark_submitted"), patch("agent.budget_manager.budget_manager.reconcile") as bill:
            image, _, error = engine.generate_image("chair", is_selfie=False, dry_run=False)
        self.assertIsNone(image)
        bill.assert_called_once()
        self.assertEqual(engine.last_task_id, "task")
        self.assertEqual(engine.last_outcome, "completed")

    def test_truncated_text_is_not_published_but_usage_survives(self):
        generator = ContentGenerator()
        generator.openrouter_key = "dummy"
        body = {"id": "request1", "choices": [{"message": {"content": "cut off"}, "finish_reason": "length"}], "usage": {"cost": .01, "completion_tokens": 700}}
        with patch("agent.generator.urllib.request.urlopen", return_value=response(body)):
            self.assertIsNone(generator._query_openrouter("model", "system", "user", 100))
        self.assertEqual(generator.last_usage["cost"], .01)
        self.assertEqual(generator.last_usage["request_id"], "request1")

    def test_deepseek_fallback_bounds_reasoning_effort(self):
        generator = ContentGenerator()
        generator.openrouter_key = "dummy"
        body = {"id": "req-ds", "choices": [{"message": {"content": "quiet reply"}, "finish_reason": "stop"}], "usage": {"cost": .0002, "prompt_tokens": 50, "completion_tokens": 12}}
        with patch("agent.generator.urllib.request.urlopen", return_value=response(body)) as request:
            text = generator._query_openrouter("deepseek-v4.1-flash", "system", "user", 150)
        payload = json.loads(request.call_args.args[0].data)
        self.assertEqual(text, "quiet reply")
        self.assertEqual(payload.get("reasoning"), {"effort": "low"})

    def test_publish_image_post_fails_closed_when_blob_upload_fails(self):
        from agent.bsky_client import BlueskyClient
        client = BlueskyClient()
        with patch.object(client, "upload_image_blob", return_value=None), \
             patch.object(client, "publish_text_post") as text_fallback:
            res = client.publish_image_post("caption written for image", b"bytes", alt_text="scene")
        self.assertEqual(res, {})
        text_fallback.assert_not_called()
