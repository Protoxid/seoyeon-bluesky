"""
tests/test_dm_reliability.py — Unit tests for Direct Message Reliability, Deduplication & Disclosure.

Verifies:
  1. Deduplication survives separate runner executions via recent_context.json.
  2. Messages are marked handled ONLY after verified successful delivery.
  3. Uncertain delivery outcomes are resolved without sending duplicate messages.
  4. Truthful AI disclosure in DMs and replies is consistently accepted by validator and generator prompts.
"""

import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from agent.bsky_client import bsky_client
from agent.decision_engine import ActionCandidate, ActionType, DecisionOutcome
from agent.generator import generator
from agent.memory_store import MemoryStore, UserProfile, memory_store
from agent.runner import run_tick
from agent.validator import validator


class TestDmReliability(unittest.TestCase):
    def setUp(self):
        self.test_dir = pathlib.Path(tempfile.mkdtemp())
        self.recent_ctx_file = self.test_dir / "recent_context.json"
        self.orig_ctx_file = memory_store.recent_context_file
        memory_store.recent_context_file = self.recent_ctx_file

        self.users_file = self.test_dir / "user_memory.json"
        self.orig_users_file = memory_store.users_file
        memory_store.users_file = self.users_file

        import agent.runner as runner_module
        self.orig_tick_file = runner_module.TICK_LOG_FILE
        runner_module.TICK_LOG_FILE = self.test_dir / "tick_history.jsonl"

        from agent.vault import vault, set_encryption_key_override
        self.orig_vault_dir = vault.vault_dir
        self.orig_enc_file = vault.enc_file
        vault.vault_dir = self.test_dir / ".vault"
        vault.enc_file = self.test_dir / "vault.enc"
        vault._load_failed = False
        vault._load_error = None
        set_encryption_key_override("test_dm_reliability_key")

        from agent.config import config
        self.orig_app_pwd = config.bsky_app_password
        self.orig_handle = config.bsky_handle
        config.bsky_app_password = config.bsky_app_password or "test_mock_app_pwd"
        config.bsky_handle = config.bsky_handle or "syeonhn.bsky.social"

    def tearDown(self):
        from agent.config import config
        config.bsky_app_password = self.orig_app_pwd
        config.bsky_handle = self.orig_handle
        memory_store.recent_context_file = self.orig_ctx_file
        memory_store.users_file = self.orig_users_file
        import agent.runner as runner_module
        runner_module.TICK_LOG_FILE = self.orig_tick_file
        from agent.vault import vault, set_encryption_key_override
        vault.vault_dir = self.orig_vault_dir
        vault.enc_file = self.orig_enc_file
        vault._load_failed = False
        vault._load_error = None
        set_encryption_key_override(None)
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_dm_deduplication_survives_separate_runner_executions(self):
        msg_id = "test_msg_9999"
        self.assertFalse(memory_store.has_replied_to_dm(msg_id))

        # Runner 1: Mark DM handled
        memory_store.mark_dm_handled(msg_id)
        self.assertTrue(memory_store.has_replied_to_dm(msg_id))

        # Runner 2 (new fresh MemoryStore instance pointing to same file)
        fresh_store = MemoryStore()
        fresh_store.recent_context_file = self.recent_ctx_file
        self.assertTrue(fresh_store.has_replied_to_dm(msg_id))

    def test_dm_not_marked_handled_on_delivery_failure(self):
        target_msg_id = "msg_fail_1"
        fake_outcome = DecisionOutcome(
            selected_action=ActionType.ANSWER_DM,
            reason="Unread DM",
            target_data={
                "convo_id": "convo_1",
                "handle": "test_user.bsky.social",
                "last_message_id": target_msg_id,
            },
            intent="warm_reply",
            candidate_scores={"ANSWER_DM": 0.8},
            all_candidates=[],
        )

        with patch("agent.runner.decision_engine.evaluate", return_value=fake_outcome), \
             patch("agent.runner.notifier.check_and_send_evening_summary"), \
             patch("agent.runner.notifier.process_master_inbox", return_value=0), \
             patch.object(bsky_client, "authenticate", return_value=True), \
             patch.object(bsky_client, "get_convo_messages", return_value=[]), \
             patch.object(generator, "generate_dm_reply", return_value=("hello.", "mock")), \
             patch.object(bsky_client, "send_dm", return_value={}):  # Delivery fails!

            run_tick(dry_run=False)

        # Since delivery failed, target_msg_id must NOT be marked handled
        self.assertFalse(memory_store.has_replied_to_dm(target_msg_id))

    def test_dm_marked_handled_on_verified_delivery(self):
        target_msg_id = "msg_success_1"
        fake_outcome = DecisionOutcome(
            selected_action=ActionType.ANSWER_DM,
            reason="Unread DM",
            target_data={
                "convo_id": "convo_2",
                "handle": "test_user.bsky.social",
                "last_message_id": target_msg_id,
            },
            intent="warm_reply",
            candidate_scores={"ANSWER_DM": 0.8},
            all_candidates=[],
        )

        with patch("agent.runner.decision_engine.evaluate", return_value=fake_outcome), \
             patch("agent.runner.notifier.check_and_send_evening_summary"), \
             patch("agent.runner.notifier.process_master_inbox", return_value=0), \
             patch.object(bsky_client, "authenticate", return_value=True), \
             patch.object(bsky_client, "get_convo_messages", return_value=[]), \
             patch.object(generator, "generate_dm_reply", return_value=("hello.", "mock")), \
             patch.object(bsky_client, "send_dm", return_value={"id": "sent_123"}), \
             patch.object(bsky_client, "mark_convo_read"):

            run_tick(dry_run=False)

        # Since delivery succeeded, target_msg_id MUST be marked handled
        self.assertTrue(memory_store.has_replied_to_dm(target_msg_id))
        self.assertTrue(memory_store.has_replied_to_dm("sent_123"))

    def test_uncertain_delivery_resolved_via_thread_check(self):
        target_msg_id = "msg_timeout_1"
        reply_body = "tea is steeping now."
        fake_outcome = DecisionOutcome(
            selected_action=ActionType.ANSWER_DM,
            reason="Unread DM",
            target_data={
                "convo_id": "convo_3",
                "handle": "test_user.bsky.social",
                "last_message_id": target_msg_id,
            },
            intent="warm_reply",
            candidate_scores={"ANSWER_DM": 0.8},
            all_candidates=[],
        )

        # send_dm returns {} (e.g. timeout), but thread check sees it did arrive on server
        delivered_thread = [
            {"id": "msg_timeout_1", "text": "how are you?", "sender": {"did": "did:plc:other"}},
            {"id": "landed_msg_456", "text": reply_body, "sender": {"did": bsky_client.did}},
        ]

        with patch("agent.runner.decision_engine.evaluate", return_value=fake_outcome), \
             patch("agent.runner.notifier.check_and_send_evening_summary"), \
             patch("agent.runner.notifier.process_master_inbox", return_value=0), \
             patch.object(bsky_client, "authenticate", return_value=True), \
             patch.object(generator, "generate_dm_reply", return_value=(reply_body, "mock")), \
             patch.object(bsky_client, "send_dm", return_value={}), \
             patch.object(bsky_client, "get_convo_messages", side_effect=[[], delivered_thread]), \
             patch.object(bsky_client, "mark_convo_read"):

            run_tick(dry_run=False)

        # Verified through uncertain delivery reconciliation
        self.assertTrue(memory_store.has_replied_to_dm(target_msg_id))

    def test_truthful_ai_disclosure_in_replies_and_dms(self):
        # Truthful plain disclosure in a reply must pass validation
        reply_disclosure = "yes, i am an ai fictional persona created by my human operator. living through seongsu observations."
        is_valid, cleaned, reason = validator.validate_outgoing_text(reply_disclosure, content_type="reply")
        self.assertTrue(is_valid, f"Validation failed: {reason}")

        # Truthful plain disclosure in a DM must pass validation
        dm_disclosure = "i am an ai persona, not a physical human. my operator runs this account from seoul."
        is_valid_dm, cleaned_dm, reason_dm = validator.validate_outgoing_text(dm_disclosure, content_type="dm")
        self.assertTrue(is_valid_dm, f"DM Validation failed: {reason_dm}")

        # But generic corporate assistant jargon must be rejected
        jargon = "as an ai language model, i am programmed to assist you."
        is_valid_jargon, _, reason_jargon = validator.validate_outgoing_text(jargon, content_type="reply")
        self.assertFalse(is_valid_jargon)
        self.assertIn("assistant jargon", reason_jargon.lower())


if __name__ == "__main__":
    unittest.main()
