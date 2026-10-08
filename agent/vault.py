"""
agent/vault.py — Secure, Encrypted Private Storage Manager.

Protects sensitive character and user state (private nightly journal reflections,
raw direct message logs) across ephemeral cloud runners without committing
plaintext to the public Git repository.

Persistence Model:
  1. Plaintext files reside in data/.vault/ (strictly git-ignored).
  2. At tick startup, load_vault() decrypts data/vault.enc into data/.vault/.
  3. Private journals and raw DM transcripts are written to data/.vault/.
  4. At tick completion, save_vault() encrypts data/.vault/ into data/vault.enc.
  5. The public GitHub repository only commits data/vault.enc (encrypted ciphertext).
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import pathlib
from typing import Any, Dict, List, Optional

from .config import DATA_DIR, config

VAULT_DIR = DATA_DIR / ".vault"
VAULT_ENC_FILE = DATA_DIR / "vault.enc"


def _get_encryption_key() -> bytes:
    """
    Retrieves or derives a 32-byte urlsafe-base64 key suitable for Fernet.
    Priority:
      1. DATA_ENCRYPTION_KEY or VAULT_KEY env var
      2. Deterministic derivation from BSKY_APP_PASSWORD + BSKY_HANDLE
      3. Stable fallback for local test execution
    """
    explicit = os.environ.get("DATA_ENCRYPTION_KEY") or os.environ.get("VAULT_KEY")
    if explicit:
        raw = hashlib.sha256(explicit.strip().encode("utf-8")).digest()
        return base64.urlsafe_b64encode(raw)

    if config.bsky_app_password:
        seed = f"{config.bsky_app_password}:{config.bsky_handle}:seoyeon_vault_v2"
        raw = hashlib.sha256(seed.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(raw)

    # Deterministic development/test fallback
    test_seed = "seoyeon_dev_test_vault_key_2026"
    raw = hashlib.sha256(test_seed.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(raw)


class PrivateVault:
    def __init__(self, vault_dir: pathlib.Path = VAULT_DIR, enc_file: pathlib.Path = VAULT_ENC_FILE):
        self.vault_dir = vault_dir
        self.enc_file = enc_file
        self.vault_dir.mkdir(parents=True, exist_ok=True)

    def load_vault(self) -> bool:
        """Decrypts data/vault.enc into data/.vault/ if it exists."""
        if not self.enc_file.exists():
            return False

        try:
            from cryptography.fernet import Fernet
            key = _get_encryption_key()
            fernet = Fernet(key)
            encrypted_data = self.enc_file.read_bytes()
            decrypted_bytes = fernet.decrypt(encrypted_data)
            bundle: Dict[str, str] = json.loads(decrypted_bytes.decode("utf-8"))

            self.vault_dir.mkdir(parents=True, exist_ok=True)
            for filename, content in bundle.items():
                target_path = self.vault_dir / filename
                target_path.write_text(content, encoding="utf-8")
            return True
        except Exception as e:
            print(f"[PrivateVault] Warning: Failed to load/decrypt vault: {e}")
            return False

    def save_vault(self) -> bool:
        """Packages all files in data/.vault/ and encrypts them into data/vault.enc."""
        if not self.vault_dir.exists():
            return False

        try:
            from cryptography.fernet import Fernet
            bundle: Dict[str, str] = {}
            for item in self.vault_dir.iterdir():
                if item.is_file():
                    bundle[item.name] = item.read_text(encoding="utf-8")

            if not bundle and not self.enc_file.exists():
                return False

            raw_json = json.dumps(bundle, ensure_ascii=False)
            key = _get_encryption_key()
            fernet = Fernet(key)
            encrypted_bytes = fernet.encrypt(raw_json.encode("utf-8"))

            self.enc_file.parent.mkdir(parents=True, exist_ok=True)
            self.enc_file.write_bytes(encrypted_bytes)
            return True
        except Exception as e:
            print(f"[PrivateVault] Warning: Failed to save/encrypt vault: {e}")
            return False

    def append_journal(self, entry: Dict[str, Any]) -> None:
        """Appends a private journal entry inside the secure vault."""
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        journal_path = self.vault_dir / "private_journal.jsonl"
        with open(journal_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self.save_vault()

    def read_journal_entries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Reads recent journal entries from the secure vault."""
        journal_path = self.vault_dir / "private_journal.jsonl"
        if not journal_path.exists():
            return []
        entries: List[Dict[str, Any]] = []
        try:
            for line in journal_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    entries.append(json.loads(line))
        except Exception:
            pass
        return entries[-limit:]

    def append_private_dm(self, convo_id: str, handle: str, incoming: str, outgoing: str) -> None:
        """Records raw private DM transcript in the secure vault."""
        import datetime as dt
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        dms_path = self.vault_dir / "private_dms.jsonl"
        entry = {
            "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
            "convo_id": convo_id,
            "handle": handle,
            "incoming": incoming,
            "outgoing": outgoing,
        }
        with open(dms_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self.save_vault()


vault = PrivateVault()
