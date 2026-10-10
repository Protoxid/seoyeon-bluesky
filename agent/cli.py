"""Establish isolation before importing modules with persistent singletons."""
import json
import os
from pathlib import Path
import shutil
import socket
import sys
import tempfile


def main():
    args = sys.argv[1:]
    offline = "--dry-run" in args or "--status" in args or "--replay" in args
    preview = "--preview" in args
    if offline and preview:
        raise SystemExit("Choose either offline replay or paid preview")
    if offline or preview:
        with tempfile.TemporaryDirectory(prefix="seoyeon-isolated-") as directory:
            source = Path(os.environ.get("SEOYEON_DATA_DIR", str(Path(__file__).resolve().parent.parent / "data")))
            destination = Path(directory) / "data"
            if source.exists():
                shutil.copytree(source, destination, ignore=shutil.ignore_patterns(".vault", "vault.enc", "*.bak", "*.lock"))
            os.environ["SEOYEON_DATA_DIR"] = str(destination)
            os.environ["SEOYEON_MODE"] = "offline" if offline else "preview"
            os.environ["SEOYEON_GIT_CHECKPOINT"] = "0"
            os.environ["DATA_ENCRYPTION_KEY"] = "isolated-disposable-preview-key"
            if offline:
                os.environ["ENV"] = "test"
                for key in ("OPENROUTER_API_KEY", "KIE_API_KEY", "TELEGRAM_BOT_TOKEN", "BSKY_APP_PASSWORD"):
                    os.environ[key] = ""
                def denied(*args, **kwargs):
                    raise RuntimeError("Offline replay attempted a network connection")
                socket.socket.connect = denied
            from .runner import main as run
            return run()
    from .storage import file_lock
    root = Path(os.environ.get("SEOYEON_DATA_DIR", str(Path(__file__).resolve().parent.parent / "data")))
    with file_lock(root / "runtime"):
        from .vault import vault
        if vault.enc_file.exists() and not vault.load_vault():
            return 1
        from .runner import main as run
        try:
            return run()
        finally:
            from .delivery import checkpoint
            checkpoint()
