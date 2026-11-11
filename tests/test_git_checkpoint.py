import contextlib
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from agent.git_checkpoint import publish_state


def _workdir(tmp, base=""):
    root = Path(tmp) / "work"
    (root / "data").mkdir(parents=True)
    (root / "data" / "vault.enc").write_bytes(b"ciphertext")
    (root / "data" / ".state_base").write_text(base)
    return root


class TestCheckpointFailures(unittest.TestCase):
    def run_case(self, push_results, remote_results):
        pushes = iter(push_results)
        remotes = iter(remote_results)
        def run(args, **kwargs):
            if args[1] in {"hash-object", "mktree", "rev-parse"}:
                return subprocess.CompletedProcess(args, 0, b"obj\n", b"")
            if args[1] == "commit-tree":
                return subprocess.CompletedProcess(args, 0, b"abc\n", b"")
            result = next(pushes if args[1] == "push" else remotes)
            if isinstance(result, Exception):
                raise result
            code, stdout, stderr = result
            return subprocess.CompletedProcess(args, code, stdout, stderr)
        with tempfile.TemporaryDirectory() as tmp:
            root = _workdir(tmp)
            with patch("agent.git_checkpoint.subprocess.run", side_effect=run), patch("agent.git_checkpoint.time.sleep"):
                publish_state(root)
            return (root / "data" / ".state_base").read_text()

    def test_lost_push_acknowledgment_is_verified_without_replaying_commit(self):
        base = self.run_case([(1, b"", b"connection reset")], [(0, b"abc\trefs/heads/state\n", b"")])
        self.assertEqual(base, "abc")

    def test_transient_push_failure_retries_same_commit(self):
        self.run_case([(1, b"", b"503 unavailable"), (0, b"", b"")],
                      [(0, b"old\trefs/heads/state\n", b""), (0, b"abc\trefs/heads/state\n", b"")])

    def test_timeout_retries_and_verifies(self):
        self.run_case([subprocess.TimeoutExpired("git", 30), (0, b"", b"")],
                      [(1, b"", b"connection reset"), (0, b"abc\trefs/heads/state\n", b"")])

    def test_successful_push_without_remote_confirmation_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, "not verified"):
            self.run_case([(0, b"", b"")] * 3, [(1, b"", b"connection reset")] * 3)

    def test_remote_divergence_is_not_overwritten(self):
        with self.assertRaisesRegex(RuntimeError, "remote_changed"):
            self.run_case([(1, b"", b"rejected (stale info)")], [(0, b"other\trefs/heads/state\n", b"")])

    def test_failure_diagnostics_do_not_disclose_git_stderr(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), self.assertRaisesRegex(RuntimeError, "authentication") as error:
            self.run_case([(1, b"", b"Authentication failed https://user:secret@example.com/private")],
                          [(1, b"", b"private output")])
        self.assertNotIn("secret", output.getvalue() + str(error.exception))
        self.assertNotIn("example.com", output.getvalue() + str(error.exception))

    def test_missing_base_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _workdir(tmp)
            (root / "data" / ".state_base").unlink()
            with self.assertRaisesRegex(RuntimeError, "base unknown"):
                publish_state(root)


class TestCheckpointLocalGit(unittest.TestCase):
    def test_state_branch_is_replaced_not_grown_and_competing_state_is_kept(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bare = root / "remote.git"
            def git(cwd, *args):
                return subprocess.run(["git", *args], cwd=cwd, capture_output=True, check=True).stdout.strip()
            git(root, "init", "--bare", str(bare))
            def workspace(name, base):
                work = root / name
                (work / "data").mkdir(parents=True)
                git(work, "init", "-b", "main")
                for key, value in (("user.name", "Test"), ("user.email", "test@example.invalid")):
                    git(work, "config", key, value)
                git(work, "remote", "add", "origin", str(bare))
                (work / "data" / ".state_base").write_text(base)
                return work

            first = workspace("first", "")
            (first / "data" / "vault.enc").write_bytes(b"state one")
            publish_state(first)
            one = git(bare, "rev-parse", "state")
            self.assertEqual((first / "data" / ".state_base").read_text(), one.decode())

            # A second run restores from the published commit.
            second = workspace("second", one.decode())
            git(second, "fetch", "origin", "state")
            (second / "data" / "vault.enc").write_bytes(b"state two")
            publish_state(second)
            two = git(bare, "rev-parse", "state")
            self.assertNotEqual(one, two)
            self.assertEqual(git(bare, "rev-list", "--count", "state"), b"1")  # parentless: no growing history

            # Unchanged content publishes nothing.
            publish_state(second)
            self.assertEqual(git(bare, "rev-parse", "state"), two)

            # The first workspace still holds the stale lease: it must not overwrite newer state.
            (first / "data" / "vault.enc").write_bytes(b"stale competing state")
            with self.assertRaisesRegex(RuntimeError, "remote_changed"):
                publish_state(first)
            self.assertEqual(git(bare, "rev-parse", "state"), two)
            self.assertEqual(git(bare, "show", "state:vault.enc"), b"state two")
