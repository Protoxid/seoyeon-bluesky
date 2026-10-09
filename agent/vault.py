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

Security & Invariants:
  - Production REQUIRES dedicated secret (DATA_ENCRYPTION_KEY or VAULT_KEY).
  - Deterministic fallback is strictly prohibited in production.
  - If decryption of an existing vault.enc fails, execution halts and save_vault()
    refuses to overwrite to prevent catastrophic data loss.
  - An atomic backup (vault.enc.bak) is created prior to updating ciphertext.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import pathlib
import shutil
import sys
from typing import Any, Dict, List, Optional

from .config import DATA_DIR, config

VAULT_DIR = DATA_DIR / ".vault"
VAULT_ENC_FILE = DATA_DIR / "vault.enc"

_OVERRIDE_KEY: Optional[str] = None


def set_encryption_key_override(key: Optional[str]) -> None:
    """Used in unit tests to explicitly configure or clear test encryption keys."""
    global _OVERRIDE_KEY
    _OVERRIDE_KEY = key


def _is_test_environment() -> bool:
    """Detects whether code is running under an automated unit test suite."""
    if os.environ.get("ENV") == "production":
        return False
    return (
        os.environ.get("ENV") == "test"
        or os.environ.get("SEOYEON_TEST_MODE") == "1"
        or "unittest" in sys.modules
        or "pytest" in sys.modules
    )


def _get_encryption_key(key_override: Optional[str] = None) -> bytes:
    """
    Retrieves or derives a 32-byte urlsafe-base64 key suitable for Fernet.
    Priority:
      1. Explicit key parameter or programmatic override
      2. DATA_ENCRYPTION_KEY or VAULT_KEY environment variable
    In production (ENV == 'production' or GITHUB_ACTIONS == 'true'):
      Raises RuntimeError if dedicated secret is missing. Deterministic fallback is prohibited.
    In local development:
      Derives from BSKY_APP_PASSWORD if present.
    In automated test environments without credentials:
      Uses isolated test key.
    Otherwise:
      Raises RuntimeError when no credentials are configured.
    """
    explicit = key_override or _OVERRIDE_KEY or os.environ.get("DATA_ENCRYPTION_KEY") or os.environ.get("VAULT_KEY")
    if explicit and explicit.strip():
        raw = hashlib.sha256(explicit.strip().encode("utf-8")).digest()
        return base64.urlsafe_b64encode(raw)

    is_production = os.environ.get("ENV") == "production" or os.environ.get("GITHUB_ACTIONS") == "true"
    if is_production:
        raise RuntimeError(
            "Dedicated encryption key missing! Set DATA_ENCRYPTION_KEY or VAULT_KEY environment variable. "
            "Deterministic fallback is strictly prohibited in production."
        )

    # Local development credential derivation
    if config.bsky_app_password:
        seed = f"{config.bsky_app_password}:{config.bsky_handle}:seoyeon_vault_v2"
        raw = hashlib.sha256(seed.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(raw)

    # Automated test environments only
    if _is_test_environment():
        test_seed = os.environ.get("TEST_VAULT_KEY", "seoyeon_dev_test_vault_key_2026")
        raw = hashlib.sha256(test_seed.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(raw)

    raise RuntimeError(
        "Dedicated encryption key missing! Set DATA_ENCRYPTION_KEY or VAULT_KEY environment variable. "
        "Deterministic fallback is strictly prohibited."
    )


class PrivateVault:
    def __init__(self, vault_dir: pathlib.Path = VAULT_DIR, enc_file: pathlib.Path = VAULT_ENC_FILE):
        self.vault_dir = vault_dir
        self.enc_file = enc_file
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        self._load_failed: bool = False
        self._load_error: Optional[str] = None

    def load_vault(self, key_override: Optional[str] = None) -> bool:
        """
        Decrypts data/vault.enc into data/.vault/ if it exists.
        If decryption fails, flags _load_failed = True to prevent destructive overwrites.
        """
        if not self.enc_file.exists():
            self._load_failed = False
            self._load_error = None
            return False

        try:
            from cryptography.fernet import Fernet, InvalidToken
            key = _get_encryption_key(key_override=key_override)
            fernet = Fernet(key)
            encrypted_data = self.enc_file.read_bytes()
            try:
                decrypted_bytes = fernet.decrypt(encrypted_data)
            except InvalidToken:
                # If explicit key was configured but existing vault was encrypted
                # with credential derivation, seamlessly fallback to credential key
                if config.bsky_app_password and config.bsky_handle:
                    seed = f"{config.bsky_app_password}:{config.bsky_handle}:seoyeon_vault_v2"
                    cred_key = base64.urlsafe_b64encode(hashlib.sha256(seed.encode("utf-8")).digest())
                    decrypted_bytes = Fernet(cred_key).decrypt(encrypted_data)
                else:
                    raise
            bundle: Dict[str, str] = json.loads(decrypted_bytes.decode("utf-8"))

            self.vault_dir.mkdir(parents=True, exist_ok=True)
            for filename, content in bundle.items():
                target_path = self.vault_dir / filename
                target_path.write_text(content, encoding="utf-8")
            self._load_failed = False
            self._load_error = None
            return True
        except Exception as e:
            self._load_failed = True
            self._load_error = str(e)
            print(f"[PrivateVault] CRITICAL: Decryption failed for {self.enc_file}: {e}")
            return False

    def save_vault(self, key_override: Optional[str] = None) -> bool:
        """
        Packages all files in data/.vault/ and encrypts them into data/vault.enc.
        Strictly refuses to overwrite if previous load/decryption failed (_load_failed == True).
        Creates atomic backup (vault.enc.bak) before modifying existing ciphertext.
        """
        if self._load_failed:
            raise RuntimeError(
                f"Refusing to save vault: decryption failed on load ({self._load_error}). "
                "Saving would permanently overwrite and destroy existing encrypted vault data."
            )

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
            key = _get_encryption_key(key_override=key_override)
            fernet = Fernet(key)
            encrypted_bytes = fernet.encrypt(raw_json.encode("utf-8"))

            self.enc_file.parent.mkdir(parents=True, exist_ok=True)

            # 1. Create safety backup of existing ciphertext
            if self.enc_file.exists() and self.enc_file.stat().st_size > 0:
                bak_file = self.enc_file.with_name(f"{self.enc_file.name}.bak")
                shutil.copy2(self.enc_file, bak_file)

            # 2. Atomic write using temporary file + replace
            tmp_file = self.enc_file.with_suffix(".tmp")
            tmp_file.write_bytes(encrypted_bytes)
            os.replace(tmp_file, self.enc_file)
            return True
        except Exception as e:
            print(f"[PrivateVault] Warning: Failed to save/encrypt vault: {e}")
            raise

    def append_journal(self, entry: Dict[str, Any]) -> None:
        """Appends a private journal entry inside the secure vault."""
        if self._load_failed:
            raise RuntimeError(
                f"Cannot append to journal: vault decryption failed on load ({self._load_error})."
            )
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
        if self._load_failed:
            raise RuntimeError(
                f"Cannot append DM: vault decryption failed on load ({self._load_error})."
            )
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
