#!/usr/bin/env python3
"""
publish_queue.py — post anything in the queue whose time has come.

    python publish_queue.py --list            what is queued, what is due
    python publish_queue.py --add clips/r4_fit_door.mp4 --at "2026-09-05 18:40" \
        --caption-file caps/r4.txt
    python publish_queue.py --due             post everything due (the scheduled call)
    python publish_queue.py --due --dry-run   free

THE QUEUE IS THE CONSENT. Nothing in this project publishes by itself. A clip
is posted because a human put it in this file, having looked at it; the
schedule only decides WHEN, never WHETHER. That is the whole reason this is a
queue and not a rule that posts whatever is newest in clips/ -- 82% of what
this pipeline generates gets discarded, and a scheduler pointed at a folder
would publish the discards.

ONE ENTRY PER LINE, JSON, APPEND-ONLY (queue.jsonl):
    {"video": "clips/r4_fit_door.mp4", "caption_file": "caps/r4.txt",
     "at": "2026-09-05T18:40", "trial": true}
A posted entry is REWRITTEN with "posted" and the media id rather than deleted,
so the file is also the record of what went out and when. Deleting the history
is how you end up reposting something by accident.

TIMES ARE LOCAL AND NAIVE, on purpose: the operator writes "2026-09-05 18:40"
meaning their own clock, the machine runs on that clock, and a timezone
conversion between the two is a bug waiting for a clock change.
"""
from __future__ import annotations
import argparse, datetime as dt, io, json, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent
Q = ROOT / "queue.jsonl"


def load() -> list[dict]:
    if not Q.is_file():
        return []
    out = []
    for i, line in enumerate(Q.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError as e:
            # LOUD, NOT SKIPPED. A malformed line quietly dropped means a post
            # that never happens and nobody notices until the slot is gone.
            sys.exit(f"  ! queue.jsonl line {i} is not valid JSON: {e}")
    return out


def save(rows: list[dict]) -> None:
    io.open(Q, "w", encoding="utf-8", newline="\n").write(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))


def when(r: dict) -> dt.datetime:
    return dt.datetime.fromisoformat(r["at"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--add")
    ap.add_argument("--at", help='"2026-09-05 18:40", local time')
    ap.add_argument("--caption-file")
    ap.add_argument("--caption")
    ap.add_argument("--no-trial", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--due", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    rows = load()

    if a.add:
        if not a.at:
            print("  ! --add needs --at")
            return 1
        vid = ROOT / a.add
        if not vid.is_file():
            print(f"  ! {a.add} not found — nothing queued")
            return 2
        at = dt.datetime.fromisoformat(a.at.replace(" ", "T"))
        if at < dt.datetime.now():
            print(f"  ! {at} is in the past")
            return 1
        rows.append({"video": a.add, "caption_file": a.caption_file,
                     "caption": a.caption, "at": at.isoformat(timespec="minutes"),
                     "trial": not a.no_trial, "posted": None})
        save(rows)
        print(f"  queued  {a.add}  for {at:%a %d %b %H:%M}"
              + ("  (trial reel)" if not a.no_trial else "  (straight to grid)"))
        return 0

    if a.list or not (a.due or a.add):
        if not rows:
            print("  queue is empty — nothing will be posted")
            return 0
        now = dt.datetime.now()
        for r in rows:
            state = ("posted " + str(r["posted"])) if r.get("posted") else (
                "DUE" if when(r) <= now else "waiting")
            print(f"  {when(r):%a %d %b %H:%M}  {state:<28} {r['video']}")
        return 0

    now = dt.datetime.now()
    due = [r for r in rows if not r.get("posted") and when(r) <= now]
    if not due:
        print("  nothing due")
        return 0
    for r in due:
        cmd = [sys.executable, str(ROOT / "ig_publish.py"),
               "--video", r["video"]]
        if r.get("caption_file"):
            cmd += ["--caption-file", r["caption_file"]]
        elif r.get("caption"):
            cmd += ["--caption", r["caption"]]
        if r.get("anchor") is not None:
            cmd += ["--anchor", str(r["anchor"])]
        if r.get("i_picked_this"):
            cmd.append("--i-picked-this")
        if r.get("force"):
            cmd.append("--force")
        if not r.get("trial", True):
            cmd.append("--no-trial")
        if a.dry_run:
            cmd.append("--dry-run")
        print(f"\n  === {r['video']}  (was due {when(r):%H:%M}) ===")
        env = {**os.environ, "PYTHONUTF8": "1"}
        p = subprocess.run(cmd, text=True, encoding="utf-8", errors="replace", env=env)
        if a.dry_run:
            continue
        if p.returncode == 0:
            r["posted"] = dt.datetime.now().isoformat(timespec="minutes")
            save(rows)                # SAVE AFTER EACH ONE, not at the end:
                                      # a crash on item two must not re-post
                                      # item one on the next run.
        else:
            print(f"  ! {r['video']} failed — left in the queue, will retry")
    return 0


if __name__ == "__main__":
    sys.exit(main())
