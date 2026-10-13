import contextlib
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from agent.git_checkpoint import push_checkpoint


class TestCheckpointFailures(unittest.TestCase):
    def run_case(self, push_results, remote_results):
        pushes = iter(push_results)
        remotes = iter(remote_results)
        def run(args, **kwargs):
            if args[1] == "rev-parse":
                return subprocess.CompletedProcess(args, 0, b"abc\n", b"")
            result = next(pushes if args[1] == "push" else remotes)
            if isinstance(result, Exception):
                raise result
            code, stdout, stderr = result
            return subprocess.CompletedProcess(args, code, stdout, stderr)
        with patch("agent.git_checkpoint.subprocess.run", side_effect=run), patch("agent.git_checkpoint.time.sleep"):
            push_checkpoint("unused")

    def test_lost_push_acknowledgment_is_verified_without_replaying_commit(self):
        self.run_case([(1, b"", b"connection reset")], [(0, b"abc\trefs/heads/main\n", b"")])

    def test_transient_push_failure_retries_same_head(self):
        self.run_case([(1, b"", b"503 unavailable"), (0, b"", b"")],
                      [(0, b"old\trefs/heads/main\n", b""), (0, b"abc\trefs/heads/main\n", b"")])

    def test_timeout_retries_and_verifies(self):
        self.run_case([subprocess.TimeoutExpired("git", 30), (0, b"", b"")],
                      [(1, b"", b"connection reset"), (0, b"abc\trefs/heads/main\n", b"")])

    def test_successful_push_without_remote_confirmation_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, "not verified"):
            self.run_case([(0, b"", b"")] * 3, [(1, b"", b"connection reset")] * 3)

    def test_remote_divergence_is_not_overwritten(self):
        with self.assertRaisesRegex(RuntimeError, "remote_changed"):
            self.run_case([(1, b"", b"rejected non-fast-forward")], [(0, b"other\trefs/heads/main\n", b"")])

    def test_failure_diagnostics_do_not_disclose_git_stderr(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), self.assertRaisesRegex(RuntimeError, "authentication") as error:
            self.run_case([(1, b"", b"Authentication failed https://user:secret@example.com/private")],
                          [(1, b"", b"private output")])
        self.assertNotIn("secret", output.getvalue() + str(error.exception))
        self.assertNotIn("example.com", output.getvalue() + str(error.exception))


class TestCheckpointLocalGit(unittest.TestCase):
    def test_already_committed_state_pushes_with_clean_index_and_rejects_competing_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bare, first, other = (root / name for name in ("remote.git", "first", "other"))
            def git(cwd, *args):
                result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, check=True)
                return result.stdout.strip()
            git(root, "init", "--bare", str(bare))
            git(root, "init", "-b", "main", str(first))
            for key, value in (("user.name", "Test"), ("user.email", "test@example.invalid")):
                git(first, "config", key, value)
            git(first, "remote", "add", "origin", str(bare))
            (first / "state").write_text("initial")
            git(first, "add", "state"); git(first, "commit", "-m", "initial")
            push_checkpoint(first)
            git(root, "clone", "-b", "main", str(bare), str(other))
            for key, value in (("user.name", "Test"), ("user.email", "test@example.invalid")):
                git(other, "config", key, value)
            (first / "state").write_text("new local state")
            git(first, "commit", "-am", "saved locally before failed push")
            self.assertEqual(git(first, "status", "--porcelain"), b"")
            push_checkpoint(first)
            saved = git(first, "rev-parse", "HEAD")
            self.assertEqual(git(bare, "rev-parse", "main"), saved)
            (other / "state").write_text("competing state")
            git(other, "commit", "-am", "competing state")
            with self.assertRaisesRegex(RuntimeError, "remote_changed"):
                push_checkpoint(other)
            self.assertEqual(git(bare, "rev-parse", "main"), saved)
            self.assertEqual((other / "state").read_text(), "competing state")
