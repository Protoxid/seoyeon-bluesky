"""Bounded, fail-closed publication of the encrypted runtime state.

The only durable state is ``data/vault.enc`` (an encrypted, compressed bundle). It is published as a
single parentless commit on the ``state`` branch, replacing the previous one, so the repository does
not accumulate a new multi-megabyte ciphertext blob for every checkpoint. The replacement is guarded by
``--force-with-lease`` against the exact state commit this run started from: a competing update fails
closed instead of being overwritten. Recovery copies of recent states are kept as workflow artifacts.

No vault imports or state rewrites: also usable by the workflow's final step.
Git stderr is classified, never printed (it may contain authenticated URLs).
"""
import os
from pathlib import Path
import subprocess
import time

STATE_FILE = "vault.enc"
BASE_FILE = Path("data") / ".state_base"


def state_branch():
    return os.environ.get("SEOYEON_STATE_BRANCH", "state")


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


def _run(root, *args, stdin=None):
    try:
        result = subprocess.run(["git", *args], cwd=root, capture_output=True, timeout=60, input=stdin)
    except subprocess.TimeoutExpired:
        return None, "timeout"
    except OSError:
        return None, "git_unavailable"
    return result, _category(result.stderr) if result.returncode else "ok"


def checked_git(root, *args, stdin=None):
    result, category = _run(root, *args, stdin=stdin)
    if result is None or result.returncode:
        raise RuntimeError(f"State checkpoint {args[0]} failed ({category}); outbound work stopped")
    return result.stdout


def _read_base(root):
    path = Path(root) / BASE_FILE
    if not path.exists():
        raise RuntimeError("State checkpoint base unknown (data/.state_base missing); outbound work stopped")
    return path.read_text().strip()


def publish_state(root):
    """Publish data/vault.enc as the new state commit; confirm the remote ref before allowing outbound work.

    The lease is the state commit this run restored (empty = branch must not exist yet). An ambiguous push
    counts as saved only if a fresh remote read shows exactly the new commit.
    """
    root = Path(root)
    encrypted = root / "data" / STATE_FILE
    if not encrypted.exists():
        return
    base = _read_base(root)
    blob = checked_git(root, "hash-object", "-w", str(encrypted)).strip().decode()
    if base:
        published, _ = _run(root, "rev-parse", f"{base}:{STATE_FILE}")
        if published is not None and published.returncode == 0 and published.stdout.strip().decode() == blob:
            return  # Nothing changed since the last published state.
    tree = checked_git(root, "mktree", stdin=f"100644 blob {blob}\t{STATE_FILE}\n".encode()).strip().decode()
    commit = checked_git(root, "commit-tree", tree, "-m", "chore(agent): state checkpoint [skip ci]").strip().decode()
    branch = state_branch()
    ref = f"refs/heads/{branch}"
    category = "unverified_remote"
    for attempt in range(3):
        _, push_category = _run(root, "push", f"--force-with-lease={ref}:{base}", "origin", f"{commit}:{ref}")
        remote, read_category = _run(root, "ls-remote", "--exit-code", "origin", ref)
        if remote is not None and remote.returncode == 0:
            records = [line.split() for line in remote.stdout.splitlines()]
            if records == [[commit.encode(), ref.encode()]]:
                (root / BASE_FILE).write_text(commit)
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
    publish_state(Path(__file__).resolve().parents[1])
