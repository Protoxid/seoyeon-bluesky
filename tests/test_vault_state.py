import json
import tempfile
import unittest
from pathlib import Path

from agent import vault as vault_module
from agent.vault import PrivateVault, STATE_PREFIX, TICK_HISTORY_KEEP


class TestVaultRuntimeState(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data = Path(self.tmp.name) / "data"
        (self.data / "memory").mkdir(parents=True)
        (self.data / "logs").mkdir()
        vault_module.set_encryption_key_override("vault-state-test-key")

    def tearDown(self):
        vault_module.set_encryption_key_override(None)
        self.tmp.cleanup()

    def make(self):
        return PrivateVault(self.data / ".vault", self.data / "vault.enc")

    def test_plaintext_runtime_state_travels_encrypted_and_restores(self):
        (self.data / "memory" / "user_memory.json").write_text('{"handle": "someone"}', encoding="utf-8")
        (self.data / "memory" / "identity_memory.json").write_text('{"authored": 1}', encoding="utf-8")
        (self.data / "budget_ledger.json").write_text('{"spend": 1}', encoding="utf-8")
        writer = self.make()
        (writer.vault_dir / "continuity.json").write_text("{}", encoding="utf-8")
        self.assertTrue(writer.save_vault())
        self.assertNotIn(b"someone", (self.data / "vault.enc").read_bytes())

        # A fresh checkout: runtime files absent, authored identity from the repository.
        (self.data / "memory" / "user_memory.json").unlink()
        (self.data / "budget_ledger.json").unlink()
        (self.data / "memory" / "identity_memory.json").write_text('{"authored": 2}', encoding="utf-8")
        reader = self.make()
        self.assertTrue(reader.load_vault())
        self.assertEqual(json.loads((self.data / "memory" / "user_memory.json").read_text())["handle"], "someone")
        self.assertEqual(json.loads((self.data / "budget_ledger.json").read_text())["spend"], 1)
        self.assertEqual(json.loads((self.data / "memory" / "identity_memory.json").read_text())["authored"], 2)

    def test_reload_in_same_process_does_not_roll_back_state(self):
        log = self.data / "logs" / "tick_history.jsonl"
        log.write_text('{"n": 1}\n', encoding="utf-8")
        v = self.make()
        v.save_vault()
        self.assertTrue(v.load_vault())
        log.write_text('{"n": 1}\n{"n": 2}\n', encoding="utf-8")
        self.assertTrue(v.load_vault())
        self.assertIn('"n": 2', log.read_text())

    def test_unchanged_content_keeps_ciphertext(self):
        (self.data / "memory" / "recent_context.json").write_text("{}", encoding="utf-8")
        v = self.make()
        v.save_vault()
        first = (self.data / "vault.enc").read_bytes()
        v.save_vault()
        self.assertEqual((self.data / "vault.enc").read_bytes(), first)
        (self.data / "memory" / "recent_context.json").write_text('{"x": 1}', encoding="utf-8")
        v.save_vault()
        self.assertNotEqual((self.data / "vault.enc").read_bytes(), first)

    def test_tick_history_is_bounded_in_bundle(self):
        log = self.data / "logs" / "tick_history.jsonl"
        log.write_text("".join(f'{{"n": {i}}}\n' for i in range(TICK_HISTORY_KEEP + 50)), encoding="utf-8")
        state = self.make()._collect_state()
        lines = state[STATE_PREFIX + "logs/tick_history.jsonl"].splitlines()
        self.assertEqual(len(lines), TICK_HISTORY_KEEP)
        self.assertEqual(lines[-1], f'{{"n": {TICK_HISTORY_KEEP + 49}}}')

    def test_unsafe_state_member_rejected(self):
        from cryptography.fernet import Fernet
        key = vault_module._get_encryption_key()
        bundle = {STATE_PREFIX + "../../outside.txt": "x"}
        (self.data / "vault.enc").write_bytes(Fernet(key).encrypt(json.dumps(bundle).encode()))
        v = self.make()
        self.assertFalse(v.load_vault())
        self.assertFalse((Path(self.tmp.name) / "outside.txt").exists())
        for bad in ("memory/identity_memory.json", "agent/runner.py", "memory/sub/dir.json"):
            self.assertIsNone(v._state_target(bad))

    def test_legacy_uncompressed_bundle_still_loads(self):
        from cryptography.fernet import Fernet
        key = vault_module._get_encryption_key()
        (self.data / "vault.enc").write_bytes(Fernet(key).encrypt(json.dumps({"continuity.json": "{}"}).encode()))
        v = self.make()
        self.assertTrue(v.load_vault())
        self.assertTrue((v.vault_dir / "continuity.json").exists())


if __name__ == "__main__":
    unittest.main()
