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

# Runtime state that used to be committed as plaintext. It now travels inside the encrypted bundle
# under STATE_PREFIX and is restored to data/ on the first load of a process. Authored identity
# (memory/identity_memory.json) stays in the repository and is never overwritten from the bundle.
STATE_PREFIX = "__state__/"
STATE_DIRS = ("memory", "historical")
STATE_FILES = ("logs/tick_history.jsonl", "budget_ledger.json")
STATE_EXCLUDE = {"memory/identity_memory.json"}
TICK_HISTORY_KEEP = 3000
COMPRESSED_MAGIC = b"zlib1:"

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
    def __init__(self, vault_dir: pathlib.Path = VAULT_DIR, enc_file: pathlib.Path = VAULT_ENC_FILE,
                 data_dir: Optional[pathlib.Path] = None):
        self.vault_dir = vault_dir
        self.enc_file = enc_file
        self.data_dir = data_dir or enc_file.parent
        self.digest_file = self.data_dir / ".vault.digest"
        self._state_restored = False
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
            # No credential-derived fallback: the vault is encrypted only with the dedicated key.
            decrypted_bytes = fernet.decrypt(encrypted_data)
            if decrypted_bytes.startswith(COMPRESSED_MAGIC):
                import zlib
                decrypted_bytes = zlib.decompress(decrypted_bytes[len(COMPRESSED_MAGIC):])
            bundle: Dict[str, str] = json.loads(decrypted_bytes.decode("utf-8"))
            state = {k[len(STATE_PREFIX):]: v for k, v in bundle.items() if k.startswith(STATE_PREFIX)}
            bundle = {k: v for k, v in bundle.items() if not k.startswith(STATE_PREFIX)}

            self.vault_dir.mkdir(parents=True, exist_ok=True)
            for relative, content in state.items():
                if self._state_target(relative) is None or not isinstance(content, str):
                    raise ValueError("Unsafe vault state member")
            if not self._state_restored:
                # Only the first load restores runtime state; a later reload in the same process must not
                # roll back files (e.g. tick history) written since the last save.
                for relative, content in state.items():
                    target = self._state_target(relative)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(content, encoding="utf-8")
                self._state_restored = True
            for filename, content in bundle.items():
                if pathlib.Path(filename).name != filename or "/" in filename or "\\" in filename or filename in {".", ".."}:
                    raise ValueError("Unsafe vault member name")
                if not isinstance(content, str):
                    raise ValueError("Invalid vault member content")
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
                if item.is_file() and item.suffix not in {".lock", ".tmp"}:
                    bundle[item.name] = item.read_text(encoding="utf-8")
            bundle.update(self._collect_state())

            if not bundle and not self.enc_file.exists():
                return False

            import zlib
            raw_json = json.dumps(bundle, ensure_ascii=False, sort_keys=True).encode("utf-8")
            digest = hashlib.sha256(raw_json).hexdigest()
            if self.enc_file.exists() and self.digest_file.exists() and self.digest_file.read_text().strip() == digest:
                return True  # Unchanged content: keep the existing ciphertext so nothing new is published.
            key = _get_encryption_key(key_override=key_override)
            fernet = Fernet(key)
            encrypted_bytes = fernet.encrypt(COMPRESSED_MAGIC + zlib.compress(raw_json, 9))

            self.enc_file.parent.mkdir(parents=True, exist_ok=True)

            # 1. Create safety backup of existing ciphertext
            if self.enc_file.exists() and self.enc_file.stat().st_size > 0:
                bak_file = self.enc_file.with_name(f"{self.enc_file.name}.bak")
                shutil.copy2(self.enc_file, bak_file)

            # 2. Atomic write using temporary file + replace
            tmp_file = self.enc_file.with_suffix(".tmp")
            tmp_file.write_bytes(encrypted_bytes)
            os.replace(tmp_file, self.enc_file)
            self.digest_file.write_text(digest)
            return True
        except Exception as e:
            print(f"[PrivateVault] Warning: Failed to save/encrypt vault: {e}")
            raise

    def _state_target(self, relative: str) -> Optional[pathlib.Path]:
        """Map a bundled state path to data/, accepting only the known state locations."""
        parts = pathlib.PurePosixPath(relative).parts
        if not parts or any(p in {"", ".", ".."} for p in parts) or "\\" in relative or relative in STATE_EXCLUDE:
            return None
        if not (relative in STATE_FILES or (len(parts) == 2 and parts[0] in STATE_DIRS)):
            return None
        return self.data_dir.joinpath(*parts)

    def _collect_state(self) -> Dict[str, str]:
        state: Dict[str, str] = {}
        candidates = [self.data_dir / f for f in STATE_FILES]
        for directory in STATE_DIRS:
            folder = self.data_dir / directory
            if folder.is_dir():
                candidates += sorted(p for p in folder.iterdir() if p.is_file())
        for path in candidates:
            if not path.is_file() or path.suffix in {".lock", ".tmp", ".bak"}:
                continue
            relative = path.relative_to(self.data_dir).as_posix()
            if self._state_target(relative) is None:
                continue
            text = path.read_text(encoding="utf-8")
            if relative == "logs/tick_history.jsonl":
                lines = text.splitlines(keepends=True)
                text = "".join(lines[-TICK_HISTORY_KEEP:])
            state[STATE_PREFIX + relative] = text
        return state

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
