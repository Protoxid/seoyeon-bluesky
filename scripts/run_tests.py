"""Run tests in a disposable checkout with no credentials or network access."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def main():
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="seoyeon-tests-") as temporary:
        target = Path(temporary)
        for name in ("agent", "tests", "scripts", "data/memory", ".github", ".agents"):
            shutil.copytree(root / name, target / name, ignore=shutil.ignore_patterns("__pycache__", "*.lock"))
        for name in ("CANON.md", "AGENTS.md", "README.md", "agent_runner.py"):
            shutil.copy2(root / name, target / name)
        # Preserve identity only. Never use real interaction history as test fixtures.
        for path in (target / "data/memory").iterdir():
            if path.is_file() and path.name != "identity_memory.json":
                path.unlink()
        env = dict(os.environ, ENV="test", SEOYEON_TEST_MODE="1", SEOYEON_GIT_CHECKPOINT="0",
                   SEOYEON_DATA_DIR=str(target / "data"), DATA_ENCRYPTION_KEY="isolated-test-key",
                   BSKY_APP_PASSWORD="", OPENROUTER_API_KEY="", KIE_API_KEY="", TELEGRAM_BOT_TOKEN="")
        env.pop("SEOYEON_MODE", None)
        bootstrap = '''import socket, unittest, sys
def denied(*args, **kwargs): raise RuntimeError("Tests may not access the network")
socket.socket.connect = denied
suite = unittest.defaultTestLoader.discover("tests", pattern="test_*.py")
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(not result.wasSuccessful())
'''
        return subprocess.call([sys.executable, "-c", bootstrap], cwd=target, env=env)


if __name__ == "__main__":
    sys.exit(main())
