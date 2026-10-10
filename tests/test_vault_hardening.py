"""
tests/test_vault_hardening.py — Tests for Vault Encryption, Fallback Security & Data Loss Prevention.

Verifies:
  1. Successful roundtrip encryption/decryption of private journals and DMs.
  2. Production strictness: Missing dedicated key raises RuntimeError in production (no deterministic fallback).
  3. Key mismatch / corrupted ciphertext causes load_vault to fail gracefully without crashing.
  4. Decryption failure sets _load_failed = True, which strictly prohibits save_vault from overwriting.
  5. Automatic creation of safety backup (vault.enc.bak) prior to ciphertext modification.
  6. Runner stops safely with exit code 1 if existing vault cannot be decrypted.
"""

import json
import os
import pathlib
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from agent.vault import PrivateVault, _get_encryption_key, set_encryption_key_override


class TestVaultHardening(unittest.TestCase):
    def setUp(self):
        self.test_dir = pathlib.Path(tempfile.mkdtemp())
        self.vault_dir = self.test_dir / ".vault"
        self.enc_file = self.test_dir / "vault.enc"
        self.vault = PrivateVault(vault_dir=self.vault_dir, enc_file=self.enc_file)
        self.test_key = "test_hardening_secret_key_12345"
        set_encryption_key_override(self.test_key)

    def tearDown(self):
        set_encryption_key_override(None)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_roundtrip_encryption_and_decryption(self):
        """Verifies that private entries are accurately saved, encrypted, and restored."""
        self.vault.append_journal({"date": "2026-10-09", "entry": "private reflection in flat"})
        self.vault.append_private_dm("convo_test", "user1", "hi", "hello there")

        self.assertTrue(self.enc_file.exists())
        self.assertGreater(self.enc_file.stat().st_size, 0)

        # Clear plaintext directory to simulate ephemeral runner reboot
        shutil.rmtree(self.vault_dir)
        self.assertFalse(self.vault_dir.exists())

        # Load fresh vault instance from ciphertext
        new_vault = PrivateVault(vault_dir=self.vault_dir, enc_file=self.enc_file)
        success = new_vault.load_vault()
        self.assertTrue(success)
        self.assertFalse(new_vault._load_failed)

        journals = new_vault.read_journal_entries()
        self.assertEqual(len(journals), 1)
        self.assertEqual(journals[0]["entry"], "private reflection in flat")

    def test_production_strictly_rejects_missing_key_with_no_fallback(self):
        """Verifies that production environment refuses to run without explicit dedicated secret."""
        set_encryption_key_override(None)
        with patch.dict(os.environ, {"ENV": "production", "DATA_ENCRYPTION_KEY": "", "VAULT_KEY": ""}, clear=True):
            with self.assertRaises(RuntimeError) as ctx:
                _get_encryption_key()
            self.assertIn("Dedicated encryption key missing", str(ctx.exception))
            self.assertIn("Deterministic fallback is strictly prohibited in production", str(ctx.exception))

    def test_key_mismatch_flags_load_failure(self):
        """Verifies that loading with incorrect key flags _load_failed = True."""
        # Create vault with valid test key
        self.vault.append_journal({"entry": "secret thought"})
        self.assertTrue(self.enc_file.exists())

        # Attempt to load with wrong key
        wrong_vault = PrivateVault(vault_dir=self.vault_dir, enc_file=self.enc_file)
        set_encryption_key_override("wrong_key_that_cannot_decrypt")
        success = wrong_vault.load_vault()

        self.assertFalse(success)
        self.assertTrue(wrong_vault._load_failed)
        self.assertIsNotNone(wrong_vault._load_error)

    def test_load_failure_blocks_save_and_prevents_data_loss(self):
        """Verifies that save_vault refuses to overwrite existing ciphertext if decryption failed."""
        # Create initial valid vault
        self.vault.append_journal({"entry": "irreplaceable historical memory"})
        orig_bytes = self.enc_file.read_bytes()

        # Simulate second runner where decryption fails
        bad_vault = PrivateVault(vault_dir=self.vault_dir, enc_file=self.enc_file)
        set_encryption_key_override("corrupted_key")
        bad_vault.load_vault()
        self.assertTrue(bad_vault._load_failed)

        # Attempting to save MUST raise RuntimeError and preserve existing file
        with self.assertRaises(RuntimeError) as ctx:
            bad_vault.save_vault()
        self.assertIn("Refusing to save vault: decryption failed on load", str(ctx.exception))

        # Ciphertext on disk must remain untouched
        self.assertEqual(self.enc_file.read_bytes(), orig_bytes)

        # Appending should also be rejected
        with self.assertRaises(RuntimeError):
            bad_vault.append_journal({"entry": "new thought"})

    def test_backup_created_before_ciphertext_update(self):
        """Verifies that saving an updated vault creates a vault.enc.bak copy."""
        self.vault.append_journal({"entry": "entry 1"})
        initial_ciphertext = self.enc_file.read_bytes()

        # Add second entry (triggers re-save)
        self.vault.append_journal({"entry": "entry 2"})
        bak_file = self.enc_file.with_name(f"{self.enc_file.name}.bak")

        self.assertTrue(bak_file.exists())
        self.assertEqual(bak_file.read_bytes(), initial_ciphertext)

    def test_runner_safely_halts_when_vault_decryption_fails(self):
        """Verifies runner.py halts with exit code 1 if vault.enc exists but cannot be decrypted."""
        from agent.runner import run_tick
        import agent.vault as vault_module

        # Point global vault to test enc_file
        orig_vault = vault_module.vault
        test_vault = PrivateVault(vault_dir=self.vault_dir, enc_file=self.enc_file)
        vault_module.vault = test_vault

        try:
            # Write invalid data to vault.enc
            self.enc_file.write_bytes(b"corrupted_garbage_data")

            # Running tick must exit safely with code 1
            exit_code = run_tick(dry_run=False)
            self.assertEqual(exit_code, 1)
        finally:
            vault_module.vault = orig_vault


if __name__ == "__main__":
    unittest.main()
