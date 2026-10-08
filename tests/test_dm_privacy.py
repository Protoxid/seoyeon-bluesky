"""
tests/test_dm_privacy.py — Tests for Direct Message Privacy Protection.

Verifies:
  1. Private DM reply text is never written to tick_history.jsonl (only character count/metadata).
  2. Private DM text is never committed to user_memory.json.
  3. Daily activity summaries exclude raw DM conversation text.
  4. Console logs do not print raw DM draft contents.
"""

import io
import json
import os
import pathlib
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

import agent.runner as runner_module
from agent.bsky_client import bsky_client
from agent.decision_engine import ActionType, DecisionOutcome
from agent.generator import generator
from agent.memory_store import memory_store
from agent.vault import vault, set_encryption_key_override


class TestDmPrivacy(unittest.TestCase):
    def setUp(self):
        self.test_dir = pathlib.Path(tempfile.mkdtemp())
        self.orig_memory_dir = memory_store.memory_dir
        memory_store.memory_dir = self.test_dir / "data" / "memory"
        memory_store.memory_dir.mkdir(parents=True, exist_ok=True)

        self.logs_dir = self.test_dir / "data" / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.tick_file = self.logs_dir / "tick_history.jsonl"

        self.orig_tick_file = runner_module.TICK_LOG_FILE
        self.orig_logs_dir = runner_module.LOGS_DIR
        runner_module.TICK_LOG_FILE = self.tick_file
        runner_module.LOGS_DIR = self.logs_dir

        self.user_memory_file = memory_store.memory_dir / "user_memory.json"
        self.orig_user_file = memory_store.users_file
        memory_store.users_file = self.user_memory_file

        self.recent_ctx_file = self.test_dir / "recent_context.json"
        self.orig_ctx_file = memory_store.recent_context_file
        memory_store.recent_context_file = self.recent_ctx_file

        self.orig_vault_dir = vault.vault_dir
        self.orig_enc_file = vault.enc_file
        vault.vault_dir = self.test_dir / ".vault"
        vault.enc_file = self.test_dir / "vault.enc"
        set_encryption_key_override("test_dm_privacy_key")

        from agent.config import config
        self.orig_app_pwd = config.bsky_app_password
        self.orig_handle = config.bsky_handle
        config.bsky_app_password = config.bsky_app_password or "test_mock_app_pwd"
        config.bsky_handle = config.bsky_handle or "syeonhn.bsky.social"

    def tearDown(self):
        from agent.config import config
        config.bsky_app_password = self.orig_app_pwd
        config.bsky_handle = self.orig_handle
        runner_module.TICK_LOG_FILE = self.orig_tick_file
        runner_module.LOGS_DIR = self.orig_logs_dir
        memory_store.users_file = self.orig_user_file
        memory_store.memory_dir = self.orig_memory_dir
        memory_store.recent_context_file = self.orig_ctx_file
        vault.vault_dir = self.orig_vault_dir
        vault.enc_file = self.orig_enc_file
        set_encryption_key_override(None)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch.object(bsky_client, "authenticate", return_value=True)
    @patch.object(bsky_client, "get_convo_messages")
    @patch.object(bsky_client, "send_dm")
    @patch.object(bsky_client, "mark_convo_read")
    @patch.object(generator, "generate_dm_reply")
    def test_dm_text_never_written_to_tick_history(
        self,
        mock_gen_dm,
        mock_mark_read,
        mock_send_dm,
        mock_get_msgs,
        mock_auth,
    ):
        secret_reply = "super_secret_private_dm_reply_12345"
        mock_get_msgs.return_value = [{"sender": {"did": "did:plc:other"}, "text": "hey"}]
        mock_gen_dm.return_value = (secret_reply, "claude-sonnet-5.5")
        mock_send_dm.return_value = {"id": "msg_sent_1"}

        fake_outcome = DecisionOutcome(
            selected_action=ActionType.ANSWER_DM,
            reason="Unread DM",
            target_data={
                "convo_id": "convo_priv_1",
                "handle": "confidential_friend",
                "last_message_id": "msg_in_1",
            },
            intent="warm_reply",
            candidate_scores={"ANSWER_DM": 0.85},
            all_candidates=[],
        )

        with patch("agent.runner.decision_engine.evaluate", return_value=fake_outcome), \
             patch("agent.runner.notifier.check_and_send_evening_summary"), \
             patch("agent.runner.notifier.process_master_inbox", return_value=0):
            # Capture stdout to verify console masking
            captured_stdout = io.StringIO()
            with patch("sys.stdout", captured_stdout):
                runner_module.run_tick(dry_run=False)

        # 1. Verify tick_history.jsonl does NOT contain secret DM text
        self.assertTrue(self.tick_file.exists())
        log_content = self.tick_file.read_text(encoding="utf-8")
        self.assertNotIn(secret_reply, log_content)

        # 2. Verify tick entry contains metadata (char_count, to, dm_sent)
        lines = log_content.strip().splitlines()
        self.assertTrue(len(lines) > 0)
        entry = json.loads(lines[-1])
        details = entry.get("details", {})
        self.assertTrue(details.get("dm_sent"))
        self.assertEqual(details.get("to"), "confidential_friend")
        self.assertEqual(details.get("char_count"), len(secret_reply))
        self.assertNotIn("text", details)

        # 3. Verify console logs masked the output
        stdout_text = captured_stdout.getvalue()
        self.assertNotIn(secret_reply, stdout_text)
        self.assertIn("private message generated", stdout_text)

        # 4. Verify user_memory.json does NOT contain raw text
        if self.user_memory_file.exists():
            mem_content = self.user_memory_file.read_text(encoding="utf-8")
            self.assertNotIn(secret_reply, mem_content)
            self.assertIn("[private direct message reply]", mem_content)

    def test_daily_summary_does_not_leak_dm_text(self):
        """Verifies get_daily_activity summary contains char_count rather than text."""
        import datetime as dt
        # Write mock tick entry to tick history
        entry = {
            "ts": "2026-10-09T03:00:00Z",
            "seoul_time": "12:00 KST",
            "action": "ANSWER_DM",
            "reason": "Replied to DM",
            "executed": True,
            "details": {
                "dm_sent": True,
                "to": "alice",
                "char_count": 42,
            },
        }
        self.tick_file.write_text(json.dumps(entry) + "\n", encoding="utf-8")

        summary = memory_store.get_daily_activity_summary(dt.date(2026, 10, 9))
        dms = summary.get("dms", [])
        self.assertEqual(len(dms), 1)
        self.assertEqual(dms[0]["recipient"], "alice")
        self.assertEqual(dms[0]["char_count"], 42)
        self.assertNotIn("text", dms[0])

    def test_did_first_tracking_preserves_profile(self):
        """Verifies DID-first tracking preserves profile history across handle changes."""
        did = "did:plc:abcdef123456789"
        old_handle = "old_user.bsky.social"
        new_handle = "new_user.bsky.social"

        # Record interaction with initial handle
        memory_store.record_user_interaction(
            handle=old_handle,
            incoming_text="hello",
            outgoing_text="chatting about film",
            interaction_type="reply",
            did=did,
        )

        profile = memory_store.get_user_profile(did)
        self.assertEqual(profile.handle, old_handle)
        self.assertEqual(profile.interaction_count, 1)

        # Later, user renamed their handle but has same DID
        memory_store.record_user_interaction(
            handle=new_handle,
            incoming_text="hello again",
            outgoing_text="second chat about photography",
            interaction_type="reply",
            did=did,
        )

        # Look up by new handle or DID
        profile_by_did = memory_store.get_user_profile(did)
        profile_by_new_handle = memory_store.get_user_profile(new_handle)
        self.assertEqual(profile_by_did.interaction_count, 2)
        self.assertEqual(profile_by_new_handle.did, did)
        self.assertEqual(profile_by_new_handle.interaction_count, 2)


if __name__ == "__main__":
    unittest.main()

