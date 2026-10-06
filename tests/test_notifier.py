"""
tests/test_notifier.py — Unit Tests for Telegram Master Escalation & OpenRouter Integration.
"""

import json
import unittest
from unittest.mock import patch, MagicMock

from agent.config import config
from agent.generator import ContentGenerator, generator
from agent.memory_store import memory_store
from agent.notifier import MasterNotifier, notifier


class TestTelegramNotifier(unittest.TestCase):
    def setUp(self):
        self.notifier = MasterNotifier()

    def test_dry_run_telegram_message(self):
        """Dry-run should cleanly append to outbox without network errors."""
        test_msg = "test message to my master"
        success = self.notifier.send_telegram_message(test_msg, dry_run=True)
        self.assertTrue(success)

    def test_ask_master_formatting(self):
        """ask_master must address the human as 'my master' and target @Protoxide."""
        with patch.object(self.notifier, "send_telegram_message", return_value=True) as mock_send:
            res = self.notifier.ask_master(
                question="Should I accept this invitation, my master?",
                context="Inbound Bluesky DM from unknown user",
                dry_run=True,
            )
            self.assertTrue(res)
            mock_send.assert_called_once()
            called_msg = mock_send.call_args[0][0]
            self.assertIn("my master", called_msg)
            self.assertIn("@Protoxide", called_msg)
            self.assertIn("Should I accept this invitation", called_msg)

    def test_sensitive_escalation_detection(self):
        """Sensitive queries (meetup, phone number, money) must trigger Telegram escalation to master."""
        with patch.object(notifier, "ask_master", return_value=True) as mock_ask:
            # Sensitive query: meetup
            triggered = generator.check_sensitive_escalation(
                "hey let's meet up in person in seoul for coffee",
                author_handle="stranger_user",
                context_summary="Bluesky DM",
            )
            self.assertTrue(triggered)
            mock_ask.assert_called_once()

        with patch.object(notifier, "ask_master", return_value=True) as mock_ask:
            # Sensitive query: phone number / whatsapp
            triggered2 = generator.check_sensitive_escalation(
                "give me your phone number or whatsapp",
                author_handle="stranger_user",
                context_summary="Bluesky Reply",
            )
            self.assertTrue(triggered2)
            mock_ask.assert_called_once()

        with patch.object(notifier, "ask_master", return_value=True) as mock_ask:
            # Innocent ordinary chat should NOT trigger escalation
            triggered_innocent = generator.check_sensitive_escalation(
                "that movie was really interesting, i liked the soundtrack",
                author_handle="regular_user",
                context_summary="Bluesky Reply",
            )
            self.assertFalse(triggered_innocent)
            mock_ask.assert_not_called()

    def test_identity_prompt_contains_master_designations(self):
        """Identity prompt must enforce referring to creator as 'my master' or 'my human'."""
        prompt = memory_store.format_identity_prompt()
        self.assertIn("my master", prompt)
        self.assertIn("my human", prompt)
        self.assertIn("@Protoxide", prompt)

    def test_config_model_is_sonnet_5_5(self):
        """Config primary text model must default to Claude Sonnet 5.5 on OpenRouter."""
        self.assertEqual(config.primary_text_model, "anthropic/claude-sonnet-5.5")

    def test_send_daily_summary(self):
        """send_daily_summary must deliver formatted message to master and record episodic memory."""
        with patch.object(self.notifier, "send_telegram_message", return_value=True) as mock_send:
            summary_data = {
                "date": "2026-10-06",
                "posts_count": 1,
                "replies_count": 2,
                "likes_count": 3,
                "dms_count": 0,
            }
            summary_text = "my master, wrapping up for the day. posted once about the cold studio floor, answered two comments, liked three posts on the feed. going to sleep."
            success = self.notifier.send_daily_summary(summary_text, summary_data, dry_run=True)
            self.assertTrue(success)
            mock_send.assert_called_once()
            called_msg = mock_send.call_args[0][0]
            self.assertIn("my master", called_msg)
            self.assertIn("@Protoxide", called_msg)
            self.assertIn("Late Evening Check-in", called_msg)
            self.assertIn("cold studio floor", called_msg)

    def test_generate_daily_report_fallback(self):
        """generate_daily_report must return an in-character message adhering to persona rules."""
        from agent.context_engine import build_environment_context
        ctx = build_environment_context()
        summary_data = {
            "date": "2026-10-06",
            "posts_count": 1,
            "posts": [{"text": "cold studio floor in the morning."}],
            "replies_count": 1,
            "replies": [{"reply_text": "fair point on that."}],
            "likes_count": 2,
            "dms_count": 0,
        }
        # Mock _call_llm to None to test the persona fallback
        with patch.object(generator, "_call_llm", return_value=(None, "fallback")):
            text, model = generator.generate_daily_report(summary_data, ctx)
            self.assertEqual(model, "fallback")
            self.assertIn("my master", text)
            self.assertNotIn("!", text)  # Zero exclamation marks
            self.assertIn("bluesky", text.lower())

    def test_get_daily_activity_summary(self):
        """get_daily_activity_summary must return structured dict with all activity keys."""
        summary = memory_store.get_daily_activity_summary()
        self.assertIn("date", summary)
        self.assertIn("posts_count", summary)
        self.assertIn("replies_count", summary)
        self.assertIn("likes_count", summary)
        self.assertIn("dms_count", summary)
        self.assertIn("spend_usd", summary)


if __name__ == "__main__":
    unittest.main()
