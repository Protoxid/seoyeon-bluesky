import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock
from agent.migration import migrate_legacy_state


class TestLegacyMigration(unittest.TestCase):
    def test_private_excerpt_removed_only_after_encrypted_backup(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            log = root / "episodic_memory.jsonl"
            log.write_text(json.dumps({"details": {"journal_excerpt": "PRIVATE_MARKER", "count": 2}}), encoding="utf-8")
            vault = Mock(vault_dir=root / "private")
            vault.save_vault.return_value = False
            with self.assertRaises(RuntimeError):
                migrate_legacy_state(root, vault)
            self.assertIn("PRIVATE_MARKER", log.read_text())
            vault.save_vault.return_value = True
            migrate_legacy_state(root, vault)
            self.assertNotIn("PRIVATE_MARKER", log.read_text())
            self.assertEqual(json.loads(log.read_text())["details"]["count"], 2)
            self.assertIn("PRIVATE_MARKER", (vault.vault_dir / "legacy_unscoped.json").read_text())
            before = log.read_bytes()
            migrate_legacy_state(root, vault)
            self.assertEqual(log.read_bytes(), before)
