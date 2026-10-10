import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class TestCliIsolation(unittest.TestCase):
    def test_offline_commands_preserve_source_data(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder) / "data"
            data.mkdir()
            (data / "sentinel").write_text("must not change")
            (data / "vault.enc").write_bytes(b"corrupted private vault must not be read by offline CLI")
            def snapshot():
                return {str(p.relative_to(data)): hashlib.sha256(p.read_bytes()).hexdigest() for p in data.rglob("*") if p.is_file()}
            before = snapshot()
            env = dict(os.environ, SEOYEON_DATA_DIR=str(data), ENV="test", SEOYEON_GIT_CHECKPOINT="0")
            for flags in (["--status"], ["--dry-run"]):
                result = subprocess.run([sys.executable, str(root / "agent_runner.py"), *flags], cwd=root,
                    env=env, capture_output=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
                self.assertEqual(snapshot(), before)
