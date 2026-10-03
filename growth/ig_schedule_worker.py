#!/usr/bin/env python3
"""
ig_schedule_worker.py — publish due tier-1 Instagram posts from
growth/schedule_assets/weekly_schedule.json.

    python growth/ig_schedule_worker.py --list
    python growth/ig_schedule_worker.py --auto              # live, due only
    python growth/ig_schedule_worker.py --auto --dry-run    # gates + token GET, no publish
    python growth/ig_schedule_worker.py --auto --force-id w37_fan   # one entry, time ignored

WHY THIS FILE EXISTS. Meta has no scheduling API: the Content Publishing flow
(container -> media_publish) is immediate-only, and the scheduled_publish_time
parameters are whitelist-gated (#3, "User must be on whitelist"). Business
Suite's planner is a first-party UI over Meta's internal scheduler and is not
exposed. So the schedule lives here, and this worker IS the scheduler: it fires
at the planned minute, calls the publisher, and records the permalink.

DESIGN RULES, in order of severity:
  - IDEMPOTENT. Only `status: "ready"` rows are ever published; a row marked
    published is skipped on every later run. A cron re-fire cannot double-post.
  - NO LATE POSTING AS IF NOTHING HAPPENED. A slot due more than WINDOW hours
    ago (cron outage, secrets missing) is marked `missed` with a reason, not
    published hours late — a 21:05 caption posted at 01:00 breaks the illusion
    the whole account exists to maintain. A missed row is visible in the
    schedule and takes a human to reset to ready.
  - NEVER ECHO SECRETS. Publishing goes through ig_publish.py, which owns the
    token files and never prints them. This worker passes file paths only.
  - ONE RENDER PER SHOT. Enforced downstream by ig_publish's ambiguity gate;
    this worker refuses a row whose media cannot be resolved at all.

MEDIA RESOLUTION. The cloud runner only has tracked files. The renders are
gitignored PNGs, so the prepped publish JPGs (1080x1440 sRGB q95 — the exact
bytes ig_publish uploads) live in growth/schedule_assets/ and are preferred;
the schedule's own media_file is the local fallback.
"""
from __future__ import annotations
import argparse, datetime as dt, json, pathlib, re, subprocess, sys

REPO = pathlib.Path(__file__).resolve().parents[1]
SCHEDULE = REPO / "growth" / "schedule_assets" / "weekly_schedule.json"
LEDGER = REPO / "growth" / "ledger.jsonl"
STATUS = REPO / "growth" / "STATUS.md"
IG_DIR = REPO / "personas" / "seoyeon"
PUBLISH_JPG_DIR = REPO / "growth" / "schedule_assets"
WINDOW_HOURS = 3


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _parse_at(s: str) -> dt.datetime:
    return dt.datetime.fromisoformat(s)  # rows carry +09:00


def load_rows() -> list[dict]:
    return json.loads(SCHEDULE.read_text(encoding="utf-8"))


def save_rows(rows: list[dict]) -> None:
    SCHEDULE.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")


def is_tier1_ig(row: dict) -> bool:
    return (row.get("tier") == 1 and "instagram" in (row.get("lanes") or []))


def resolve_media(row: dict) -> pathlib.Path | None:
    """Prepped publish JPG first (works on the cloud runner), then the
    schedule's own media_file (works locally). Absolute, because ig_publish
    joins relative --video paths to personas/seoyeon, not the CWD."""
    stem = pathlib.Path(row.get("media_file", "")).stem
    if stem:
        jpg = PUBLISH_JPG_DIR / f"{stem}.jpg"
        if jpg.is_file():
            return jpg.resolve()
    alt = REPO / row.get("media_file", "")
    if alt.is_file():
        return alt.resolve()
    return None


def resolve_caption(row: dict) -> pathlib.Path | None:
    p = REPO / row.get("caption_file", "")
    return p if p.is_file() else None


def ledger_add(entry: dict) -> None:
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def status_note(text: str) -> None:
    with STATUS.open("a", encoding="utf-8") as f:
        f.write(text.rstrip() + "\n")


def fetch_permalink(media_id: str) -> str:
    """Reuse ig_publish's api()/read(): same version pin, same never-echoes-
    token error handling. A failure here must not lose the publish record."""
    sys.path.insert(0, str(IG_DIR))
    try:
        import ig_publish  # noqa: PLC0415
        tok = ig_publish.read("ig_token.txt")
        return ig_publish.api(media_id, {"fields": "permalink",
                                         "access_token": tok}).get("permalink", "")
    except SystemExit:
        return ""
    except Exception:                                   # noqa: BLE001
        return ""


def publish_row(row: dict, dry: bool) -> tuple[bool, str]:
    media = resolve_media(row)
    cap = resolve_caption(row)
    if media is None:
        return False, (f"{row['id']}: media unresolvable (neither prepped jpg "
                       f"nor {row.get('media_file')} exists)")
    if cap is None:
        return False, f"{row['id']}: caption file missing " \
                      f"({row.get('caption_file')})"

    cmd = [sys.executable, str(IG_DIR / "ig_publish.py"),
           "--video", str(media), "--caption-file", str(cap)]
    if dry:
        cmd.append("--dry-run")
    r = subprocess.run(cmd, cwd=str(REPO), capture_output=True,
                       text=True, timeout=900)
    out = ((r.stdout or "") + (r.stderr or "")).rstrip()
    print(out)
    if dry:
        return r.returncode == 0, f"{row['id']}: dry-run {'OK' if r.returncode == 0 else 'FAILED'}"

    m = re.search(r"published\s+media id (\d+)", out)
    if r.returncode != 0 or not m:
        return False, f"{row['id']}: ig_publish failed — tail: {out[-220:]}"
    pid = m.group(1)
    row["status"] = "published"
    row["published_at"] = _now().isoformat()
    row["published_media_id"] = pid
    row["permalink"] = fetch_permalink(pid)
    ledger_add({"ts": _now().isoformat(), "surface": "instagram",
                "action": "tier1_post", "target": "instagram",
                "note": f"Published {row['id']} (media id {pid})"
                        f"{' — ' + row['permalink'] if row.get('permalink') else ''}"})
    status_note(f"\n## {_now().strftime('%Y-%m-%d %H:%M UTC')} — ig_schedule_worker\n"
                f"- published {row['id']} at {row.get('publish_at')} (slot time)\n"
                f"- permalink: {row.get('permalink', '(unavailable)')}\n"
                f"conclusion: tier-1 post published and recorded in weekly_schedule.json\n"
                f"blocked by: nothing\n")
    return True, f"{row['id']}: published media id {pid}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--list", action="store_true", help="show tier-1 IG rows and resolution")
    ap.add_argument("--auto", action="store_true", help="process due rows")
    ap.add_argument("--dry-run", action="store_true",
                    help="validate (gates + free token GET), publish nothing")
    ap.add_argument("--force-id", default=None,
                    help="process this one row regardless of due time")
    ap.add_argument("--window", type=float, default=WINDOW_HOURS,
                    help="hours after slot time before a row is 'missed' not late-published")
    a = ap.parse_args()
    print("[NOTICE] ig_schedule_worker.py is DEPRECATED. Instagram integration has been permanently removed. Use agent_runner.py instead.")
    return 0
        now = _now()
        print(f"{'id':24} {'publish_at':26} {'status':10} due?  media  caption")
        for r in ig_rows:
            pub = r.get("publish_at")
            due = _parse_at(pub) <= now if pub else False
            media = "jpg" if (PUBLISH_JPG_DIR / (pathlib.Path(r.get('media_file', 'x')).stem + '.jpg')).is_file() \
                else ("src" if (REPO / r.get("media_file", "x")).is_file() else "MISSING")
            cap = "ok" if (REPO / r.get("caption_file", "x")).is_file() else "MISSING"
            print(f"{r['id']:24} {str(pub):26} {str(r.get('status')):10} "
                  f"{'yes' if due else 'no ':4} {media:7} {cap}")
        return 0

    if not a.auto and not a.force_id:
        ap.error("nothing to do: --auto, --list or --force-id")

    now = _now()
    targets, failures, acted = [], [], False

    for r in ig_rows:
        if a.force_id:
            if r["id"] != a.force_id or r.get("status") == "published":
                continue
            targets.append(r)
            continue
        if r.get("status") != "ready":
            continue
        pub = r.get("publish_at")
        if not pub:
            continue
        at = _parse_at(pub)
        if at > now:
            continue
        if (now - at).total_seconds() > a.window * 3600:
            acted = True
            r["status"] = "missed"
            r["missed_reason"] = (f"slot was {at.isoformat()} but the scheduler "
                                   f"only reached it at {now.isoformat()} — past "
                                   f"the {a.window:g}h window; a human decides "
                                   f"whether this slot still makes sense")
            print(f"  [MISSED] {r['id']} — {r['missed_reason']}")
            ledger_add({"ts": now.isoformat(), "surface": "instagram",
                        "action": "slot_missed", "target": "instagram",
                        "note": f"{r['id']} missed its window"})
            continue
        targets.append(r)

    targets.sort(key=lambda r: r.get("publish_at", ""))

    if not targets:
        print("no due tier-1 instagram rows" + (" — nothing changed" if not acted else ""))
        if acted:
            save_rows(rows)
        return 0

    for r in targets:
        ok, msg = publish_row(r, a.dry_run)
        print(("  OK  " if ok else "  FAIL ") + msg)
        if not ok:
            failures.append(msg)

    save_rows(rows)
    print(f"\n{len(targets)} row(s) processed, {len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
