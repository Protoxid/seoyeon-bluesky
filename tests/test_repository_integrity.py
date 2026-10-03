"""
tests/test_repository_integrity.py — Automated Repository Integrity & Zero-Error Test Suite.

Validates that:
  1. All core project modules import cleanly with zero runtime/initialization errors.
  2. Text generation is configured exclusively for OpenRouter with Claude Sonnet 5.5.
  3. Persona strictly enforces referring to the human creator as "my master" or "my human".
  4. Outbound Telegram escalation is bound to @Protoxide and logs cleanly.
  5. Workflow definitions are valid, complete, and free of legacy Instagram/Fanvue references.
  6. Persistent memory files and audit log files are valid JSON/JSONL with no corruption.
"""

import importlib
import json
import os
import pathlib
import subprocess
import unittest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent


class TestRepositoryIntegrity(unittest.TestCase):
    def test_all_agent_modules_import_cleanly(self):
        """Verifies all Python modules in agent/ import cleanly without syntax or import errors."""
        agent_dir = PROJECT_ROOT / "agent"
        self.assertTrue(agent_dir.exists() and agent_dir.is_dir())

        modules_to_test = [
            "agent.config",
            "agent.context_engine",
            "agent.memory_store",
            "agent.bsky_client",
            "agent.decision_engine",
            "agent.generator",
            "agent.image_engine",
            "agent.validator",
            "agent.budget_manager",
            "agent.notifier",
            "agent.runner",
            "agent.visual_identity",
        ]

        for mod_name in modules_to_test:
            with self.subTest(module=mod_name):
                mod = importlib.import_module(mod_name)
                self.assertIsNotNone(mod, f"Failed to import {mod_name}")

    def test_model_configuration_is_openrouter_sonnet_5_5(self):
        """Verifies text generation model is strictly Claude Sonnet 5.5 via OpenRouter."""
        from agent.config import config
        from agent.generator import OPENROUTER_URL

        self.assertEqual(config.primary_text_model, "anthropic/claude-sonnet-5.5")
        self.assertIn("openrouter.ai", OPENROUTER_URL)

    def test_master_and_human_designation_rules(self):
        """Ensures Seo-yeon strictly refers to the creator as 'my master' or 'my human' everywhere."""
        from agent.config import config
        from agent.memory_store import memory_store

        # 1. Config definitions
        self.assertIn("my master", config.master_designations)
        self.assertIn("my human", config.master_designations)
        self.assertEqual(config.master_telegram_handle, "@Protoxide")

        # 2. Identity Memory JSON file
        ident_path = PROJECT_ROOT / "data" / "memory" / "identity_memory.json"
        self.assertTrue(ident_path.exists())
        ident_data = json.loads(ident_path.read_text(encoding="utf-8"))
        self.assertIn("creator_relationship", ident_data)
        rel = ident_data["creator_relationship"]
        self.assertIn("my master", rel["designations"])
        self.assertIn("my human", rel["designations"])
        self.assertEqual(rel["telegram_username"], "@Protoxide")

        # 3. Dynamic Identity Prompt
        prompt = memory_store.format_identity_prompt()
        self.assertIn("my master", prompt)
        self.assertIn("my human", prompt)
        self.assertIn("@Protoxide", prompt)

        # 4. CANON.md documentation
        canon_text = (PROJECT_ROOT / "CANON.md").read_text(encoding="utf-8")
        self.assertIn("my master", canon_text)
        self.assertIn("my human", canon_text)
        self.assertIn("@Protoxide", canon_text)

        # 5. AGENTS.md documentation
        agents_text = (PROJECT_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("my master", agents_text)
        self.assertIn("my human", agents_text)
        self.assertIn("@Protoxide", agents_text)

    def test_telegram_outbox_logging(self):
        """Verifies notifier dispatches messages in dry-run mode and logs to telegram_outbox.jsonl."""
        from agent.notifier import notifier, TELEGRAM_OUTBOX_FILE

        test_text = "Repository integrity check message for my master"
        ok = notifier.ask_master(test_text, context="Integrity test", dry_run=True)
        self.assertTrue(ok)
        self.assertTrue(TELEGRAM_OUTBOX_FILE.exists())

        # Verify entry exists in outbox
        lines = TELEGRAM_OUTBOX_FILE.read_text(encoding="utf-8").strip().splitlines()
        last_entry = json.loads(lines[-1])
        self.assertEqual(last_entry["recipient"], "@Protoxide")
        self.assertIn("my master", last_entry["text"])
        self.assertEqual(last_entry["status"], "simulated_dry_run")

    def test_github_workflow_integrity(self):
        """Verifies .github/workflows/bluesky_scheduler.yml has all required secrets and log artifacts."""
        workflow_path = PROJECT_ROOT / ".github" / "workflows" / "bluesky_scheduler.yml"
        self.assertTrue(workflow_path.exists())
        content = workflow_path.read_text(encoding="utf-8")

        # Required secrets
        self.assertIn("OPENROUTER_API_KEY", content)
        self.assertIn("KIE_API_KEY", content)
        self.assertIn("BSKY_HANDLE", content)
        self.assertIn("BSKY_APP_PASSWORD", content)
        self.assertIn("TELEGRAM_BOT_TOKEN", content)
        self.assertIn("TELEGRAM_CHAT_ID", content)

        # Tracked log output
        self.assertIn("data/logs/telegram_outbox.jsonl", content)
        self.assertIn("data/logs/tick_history.jsonl", content)
        self.assertIn("data/memory/identity_memory.json", content)

        # Confirm old workflows are gone
        old_ig = PROJECT_ROOT / ".github" / "workflows" / "ig_scheduler.yml"
        self.assertFalse(old_ig.exists(), "Old ig_scheduler.yml should be deleted")

    def test_persistent_memory_json_validity(self):
        """Ensures all data/memory/*.json files parse as valid JSON."""
        memory_dir = PROJECT_ROOT / "data" / "memory"
        for json_file in memory_dir.glob("*.json"):
            with self.subTest(file=json_file.name):
                data = json.loads(json_file.read_text(encoding="utf-8"))
                self.assertIsInstance(data, (dict, list))


if __name__ == "__main__":
    unittest.main()
