"""Bounded, fail-closed publication of already committed runtime state.

No vault imports or state rewrites: also usable by the workflow's final step.
Git stderr is classified, never printed (it may contain authenticated URLs).
"""
from pathlib import Path
import subprocess
import time


def _category(stderr):
    text = stderr.decode("utf-8", errors="replace").lower()
    for category, markers in (
        ("remote_changed", ("non-fast-forward", "fetch first", "stale info")),
        ("authentication", ("authentication failed", "could not read username", "permission denied", "403")),
        ("remote_policy", ("protected branch", "repository rule", "gh013", "gh006")),
        ("network", ("could not resolve", "connection", "timed out", "502", "503", "504")),
    ):
        if any(marker in text for marker in markers):
            return category
    return "git_failure"


def _run(root, *args):
    try:
        result = subprocess.run(["git", *args], cwd=root, capture_output=True, timeout=30)
    except subprocess.TimeoutExpired:
        return None, "timeout"
    except OSError:
        return None, "git_unavailable"
    return result, _category(result.stderr) if result.returncode else "ok"


def checked_git(root, *args):
    result, category = _run(root, *args)
    if result is None or result.returncode:
        raise RuntimeError(f"State checkpoint {args[0]} failed ({category}); outbound work stopped")
    return result.stdout


def push_checkpoint(root):
    """Retry the same commit; confirm origin/main before allowing outbound work.

    Never force push, pull, rebase, or resolve a competing state update here.
    An ambiguous push counts as saved only if a fresh remote read matches HEAD.
    """
    expected = checked_git(root, "rev-parse", "HEAD").strip()
    category = "unverified_remote"
    for attempt in range(3):
        _, push_category = _run(root, "push", "origin", "HEAD:main")
        remote, read_category = _run(root, "ls-remote", "--exit-code", "origin", "refs/heads/main")
        if remote is not None and remote.returncode == 0:
            records = [line.split() for line in remote.stdout.splitlines()]
            if records == [[expected, b"refs/heads/main"]]:
                return
            category = push_category if push_category != "ok" else "remote_changed"
        else:
            category = read_category if push_category == "ok" else push_category
        print(f"[Checkpoint] attempt={attempt + 1}/3 status={category}")
        if category in {"remote_changed", "authentication", "remote_policy", "git_unavailable"}:
            break
        if attempt < 2:
            time.sleep(2 ** attempt)
    raise RuntimeError(f"State checkpoint push not verified ({category}); outbound work stopped")


if __name__ == "__main__":
    push_checkpoint(Path(__file__).resolve().parents[1])
