#!/usr/bin/env python3
"""
campaign_orchestrator.py — Cross-Platform Campaign Orchestration Suite (Fanvue <-> Bluesky).
Guarantees absolute content coherence: A Bluesky teaser post can NEVER be published
unless its corresponding exclusive media post is already live and verified on Fanvue.
"""
import argparse
import datetime as dt
import io
import json
import os
import pathlib
import re
import sys
import time
from typing import Any, Dict, List, Optional
import urllib.request
import urllib.error

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

GROWTH_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = GROWTH_DIR.parent
SCHEDULE_FILE = GROWTH_DIR / "schedule_assets" / "weekly_schedule.json"
LEDGER_FILE = GROWTH_DIR / "ledger.jsonl"
FANVUE_TRACKING_URL = "https://www.fanvue.com/syeon.hn?c=fv-4"

# Add GROWTH_DIR to sys.path for internal imports
if str(GROWTH_DIR) not in sys.path:
    sys.path.insert(0, str(GROWTH_DIR))

try:
    from fanvue_api import FanvueClient, load_key, log_ledger
except ImportError:
    from growth.fanvue_api import FanvueClient, load_key, log_ledger


def load_schedule() -> List[Dict[str, Any]]:
    if not SCHEDULE_FILE.exists():
        sys.exit(f"Schedule file not found: {SCHEDULE_FILE}")
    return json.loads(SCHEDULE_FILE.read_text(encoding="utf-8"))


def save_schedule(schedule: List[Dict[str, Any]]) -> None:
    SCHEDULE_FILE.write_text(json.dumps(schedule, indent=2, ensure_ascii=False), encoding="utf-8")
    # Also sync to mirrored directories if running
    mirror_file = pathlib.Path(r"c:\AI-Project\growth\schedule_assets\weekly_schedule.json")
    if mirror_file.resolve() != SCHEDULE_FILE.resolve() and mirror_file.parent.exists():
        try:
            mirror_file.write_text(json.dumps(schedule, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass


def calculate_target_publish_at(day_name: str, time_kst_str: str, ref_now: Optional[dt.datetime] = None) -> str:
    """
    Computes the upcoming ISO 8601 UTC timestamp for a given day of the week and KST time.
    e.g., 'Tuesday' + '20:00' -> '2026-09-08T11:00:00.000Z'
    """
    kst_tz = dt.timezone(dt.timedelta(hours=9))
    now_kst = (ref_now or dt.datetime.now(dt.timezone.utc)).astimezone(kst_tz)
    
    days_map = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6
    }
    target_weekday = days_map.get(day_name.lower().strip())
    if target_weekday is None:
        return ""

    try:
        parts = time_kst_str.strip().split(":", 1)
        hour, minute = int(parts[0]), int(parts[1])
    except Exception:
        hour, minute = 20, 0

    days_ahead = (target_weekday - now_kst.weekday()) % 7
    target_dt_kst = now_kst.replace(hour=hour, minute=minute, second=0, microsecond=0) + dt.timedelta(days=days_ahead)
    
    # If the slot is in the past or within 10 minutes, schedule for next week's occurrence
    if target_dt_kst <= now_kst + dt.timedelta(minutes=10):
        target_dt_kst += dt.timedelta(days=7)
        
    target_utc = target_dt_kst.astimezone(dt.timezone.utc)
    return target_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def get_fanvue_client() -> Optional[FanvueClient]:
    try:
        key = load_key()
        return FanvueClient(key)
    except SystemExit:
        return None
    except Exception:
        return None


def get_fanvue_live_posts(client: Optional[FanvueClient]) -> Dict[str, Dict[str, Any]]:
    """Retrieves all published/scheduled posts from Fanvue and indexes by UUID."""
    if not client:
        return {}
    try:
        res = client.request("GET", "/posts")
        posts = res.get("data", []) if isinstance(res, dict) else []
        return {p.get("uuid") or p.get("id"): p for p in posts if p.get("uuid") or p.get("id")}
    except Exception as e:
        print(f"  [Warning] Could not fetch live Fanvue posts: {e}")
        return {}


def is_bluesky_fanvue_drop(d: Dict[str, Any]) -> bool:
    """Returns True if the drop is part of the Bluesky <-> Fanvue growth funnel."""
    platforms = d.get("platforms") or d.get("lanes") or []
    if any(p in platforms for p in ("bluesky", "fanvue")):
        return True
    return d.get("tier") in (2, 3) and bool(d.get("day"))


def print_campaign_matrix() -> None:
    """Displays the side-by-side Fanvue <-> Bluesky campaign coherence matrix."""
    schedule = load_schedule()
    client = get_fanvue_client()
    live_fanvue_posts = get_fanvue_live_posts(client)

    print("\n" + "=" * 90)
    print("  SEOYEON HAN — CROSS-PLATFORM CAMPAIGN COHERENCE MATRIX (FANVUE <-> BLUESKY)")
    print("=" * 90)
    print(f"{'DAY / SLOT':<16} | {'FANVUE POST STATUS':<30} | {'BLUESKY TEASER STATUS':<24} | {'INTEGRITY'}")
    print("-" * 90)

    for drop in schedule:
        if not is_bluesky_fanvue_drop(drop):
            continue
        drop_id = drop.get("id", "unknown")
        day_slot = f"{drop.get('day', '')} ({drop.get('time_kst', '')})"
        fv_uuid = drop.get("fanvue_post_uuid")
        fv_status = drop.get("fanvue_status", "ready")
        bsky_status = drop.get("status", "ready")

        # Verify against live Fanvue API or local scheduled record
        is_live_on_fanvue = fv_uuid in live_fanvue_posts if fv_uuid else False
        if is_live_on_fanvue:
            p_data = live_fanvue_posts[fv_uuid]
            p_pub = p_data.get("publishAt")
            if p_pub and not p_data.get("publishedAt"):
                fv_display = f"SCHEDULED ({fv_uuid[:8]}... @ {p_pub[5:16]})"
            else:
                fv_display = f"LIVE ({fv_uuid[:8]}...)"
        elif fv_uuid:
            fv_pub = drop.get("fanvue_publish_at", "")
            if fv_pub:
                fv_display = f"SCHEDULED ({fv_uuid[:8]}... @ {fv_pub[5:16]})"
            else:
                fv_display = f"RECORDED ({fv_uuid[:8]}...)"
        else:
            fv_display = "PENDING UPLOAD"

        bsky_display = bsky_status.upper()
        if bsky_status == "published":
            bsky_uri = drop.get("uri", "")
            rkey = bsky_uri.split("/")[-1] if "/" in bsky_uri else "live"
            bsky_display = f"LIVE ({rkey[:8]})"

        # Integrity check: Bluesky CANNOT be live or ready without Fanvue!
        if bsky_status == "published" and not fv_uuid:
            integrity = "[CRITICAL] BROKEN FUNNEL"
        elif bsky_status == "ready" and not fv_uuid:
            integrity = "[BLOCKED] Awaiting Fanvue"
        elif is_live_on_fanvue or fv_uuid:
            integrity = "[VERIFIED] Coherent"
        else:
            integrity = "[PENDING]"

        print(f"{day_slot:<16} | {fv_display:<30} | {bsky_display:<24} | {integrity}")

    print("=" * 90)
    print("  Rule: Bluesky teasers are locked until the matching Fanvue post is live.\n")


def sync_fanvue_drop(client: FanvueClient, drop: Dict[str, Any], dry_run: bool = False, schedule_future: bool = True) -> str:
    """Uploads media (single or multi-image full set gallery) to Fanvue and creates/schedules the subscriber post."""
    drop_id = drop["id"]
    gallery_rel = drop.get("fanvue_gallery_files") or [drop.get("media_file", "")]
    
    media_paths = []
    for rel in gallery_rel:
        p = (PROJECT_ROOT / rel if not pathlib.Path(rel).is_absolute() else pathlib.Path(rel)).resolve()
        if not p.exists():
            alt_p = pathlib.Path(r"c:\AI-Project") / rel
            if alt_p.exists():
                p = alt_p
            else:
                raise FileNotFoundError(f"Media file not found for drop {drop_id}: {rel}")
        media_paths.append(p)

    caption = drop.get("fanvue_text") or (
        f"something a little more private for you today... {drop.get('main_text', '')} 🖤"
    )
    audience = drop.get("fanvue_audience", "subscribers")
    price_cents = drop.get("fanvue_price_cents")

    # Determine server-side scheduling target (publishAt)
    publish_at = None
    if schedule_future:
        publish_at = drop.get("fanvue_publish_at")
        if not publish_at and drop.get("day") and drop.get("time_kst"):
            publish_at = calculate_target_publish_at(drop["day"], drop["time_kst"])

    print(f"\n[Fanvue Sync] Processing drop '{drop_id}' ({drop.get('day')}) — Full Set Gallery ({len(media_paths)} items)...")
    for i, mp in enumerate(media_paths, 1):
        print(f"  [{i}/{len(media_paths)}] {mp.name} ({mp.stat().st_size // 1024} KB)")
    print(f"  Audience:    {audience}")
    print(f"  Target Post: {'SCHEDULED for ' + publish_at if publish_at else 'IMMEDIATE PUBLISH'}")
    print(f"  Caption:     \"{caption[:60]}...\"")

    if dry_run:
        print(f"  [DRY-RUN] Would upload {len(media_paths)} media files and create 1 subscriber gallery post.")
        return "simulated-fanvue-uuid"

    # 1. Upload all media files
    media_uuids = []
    for i, mp in enumerate(media_paths, 1):
        print(f"  Uploading asset {i}/{len(media_paths)}: {mp.name}...")
        muuid = client.upload_media(mp, name=f"{drop_id}_{i:02d}")
        if not muuid:
            raise RuntimeError(f"Failed to upload media {mp.name} to Fanvue for drop {drop_id}")
        media_uuids.append(muuid)

    # 2. Create multi-image post (with native publishAt if scheduled)
    post_res = client.create_post(
        text=caption,
        media_uuids=media_uuids,
        audience=audience,
        price_cents=price_cents,
        publish_at=publish_at,
        dry_run=dry_run
    )
    post_uuid = post_res.get("id") or post_res.get("uuid") or post_res.get("data", {}).get("id")
    if not post_uuid:
        raise RuntimeError(f"Post created but no UUID returned: {post_res}")

    if publish_at:
        drop["fanvue_publish_at"] = publish_at
        drop["fanvue_status"] = "scheduled"
        print(f"  [SUCCESS] Fanvue full set gallery ({len(media_uuids)} items) SCHEDULED! UUID: {post_uuid} (Release: {publish_at})")
    else:
        drop["fanvue_status"] = "published"
        print(f"  [SUCCESS] Fanvue full set gallery ({len(media_uuids)} items) published! UUID: {post_uuid}")

    log_ledger("fanvue_campaign_sync", drop_id, f"Post {post_uuid} with {len(media_uuids)} media items (publishAt={publish_at})")
    return post_uuid


def sync_all_fanvue(dry_run: bool = False, schedule_future: bool = True) -> None:
    """Ensures all 7 days of scheduled content exist on Fanvue before Bluesky drops."""
    schedule = load_schedule()
    client = get_fanvue_client()
    if not client:
        sys.exit("  ! Fanvue credentials not available. Run: python growth/fanvue_auth.py --start")
    live_posts = get_fanvue_live_posts(client)
    updated = False

    for drop in schedule:
        if not is_bluesky_fanvue_drop(drop):
            continue
        drop_id = drop["id"]
        current_uuid = drop.get("fanvue_post_uuid")

        # If already recorded and verified live/scheduled, skip
        if current_uuid and current_uuid in live_posts:
            continue

        # If not on Fanvue, upload and schedule/publish now
        try:
            new_uuid = sync_fanvue_drop(client, drop, dry_run=dry_run, schedule_future=schedule_future)
            drop["fanvue_post_uuid"] = new_uuid
            updated = True
            time.sleep(2)  # Respect rate limits
        except Exception as e:
            print(f"  [ERROR] Failed to sync drop '{drop_id}' to Fanvue: {e}")

    if updated and not dry_run:
        save_schedule(schedule)
        print("\n[SUCCESS] Weekly schedule updated with all live Fanvue post UUIDs.")


def dispatch_drop(drop_id: str, dry_run: bool = False, force: bool = False) -> None:
    """Dispatches a synchronized drop: guarantees Fanvue existence, then posts to Bluesky."""
    schedule = load_schedule()
    
    target_drop = None
    for d in schedule:
        if d["id"] == drop_id:
            target_drop = d
            break

    if not target_drop:
        sys.exit(f"Drop ID '{drop_id}' not found in schedule.")

    # Guardrail: Check if already published on Bluesky
    if target_drop.get("status") == "published" and not force:
        print(f"\n============================================================")
        print(f"  [SKIPPED] DROP ALREADY PUBLISHED: {drop_id} ({target_drop.get('day')})")
        print(f"  Bluesky URI: {target_drop.get('uri')}")
        print(f"  Skipping dispatch to prevent duplicate posting on Bluesky.")
        print(f"  (Use --force if you intentionally wish to republish)")
        print(f"============================================================\n")
        return

    # 1. Guarantee Fanvue existence (either pre-scheduled or already live)
    fv_uuid = target_drop.get("fanvue_post_uuid")
    if not fv_uuid:
        print(f"\n[Pre-flight Check] Fanvue post does not exist yet for drop '{drop_id}'.")
        client = get_fanvue_client()
        if not client:
            print("  [ERROR] Cannot sync to Fanvue: No active Fanvue OAuth session on this runner.")
            print("  [BLOCKED] In automated cloud runners, Fanvue posts must be pre-scheduled in advance!")
            sys.exit(1)
        print("  -> Uploading and scheduling on Fanvue FIRST to maintain truth in advertising...")
        new_uuid = sync_fanvue_drop(client, target_drop, dry_run=dry_run, schedule_future=False)
        target_drop["fanvue_post_uuid"] = new_uuid
        target_drop["fanvue_status"] = "published"
        save_schedule(schedule)
    else:
        print(f"\n[Pre-flight Check] Fanvue post verified in schedule ({fv_uuid}). Ready for Bluesky teaser.")

    # 2. Dispatch to Bluesky using the existing schedule worker
    print(f"\n[Bluesky Dispatch] Launching Bluesky teaser for '{drop_id}'...")
    import subprocess
    cmd = [sys.executable, str(GROWTH_DIR / "bsky_schedule_worker.py"), "--drop", drop_id]
    if dry_run:
        cmd.append("--dry-run")
    if force:
        cmd.append("--force")
    
    res = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(res.stdout)
    if res.returncode != 0:
        print(res.stderr)
        sys.exit(f"Bluesky dispatch failed with code {res.returncode}")


def select_auto_drop(schedule: List[Dict[str, Any]], now_kst: Optional[dt.datetime] = None, force: bool = False) -> tuple[Optional[Dict[str, Any]], str]:
    """
    Selects the due drop for auto-dispatch with runner queue delay resilience.
    Returns (target_drop, status_or_reason).
    """
    if now_kst is None:
        now_utc = dt.datetime.now(dt.timezone.utc)
        now_kst = now_utc + dt.timedelta(hours=9)

    today_str = now_kst.strftime("%Y-%m-%d")
    yesterday_str = (now_kst - dt.timedelta(days=1)).strftime("%Y-%m-%d")
    current_day = now_kst.strftime("%A")
    current_hour = now_kst.hour

    # 1. Overdue Drops Recovery (catch-up for missed/delayed runs from current week):
    # If any past drop in the schedule is still 'ready' and has a live/scheduled Fanvue post,
    # recover it during daytime/evening hours (07:00 - 01:00 KST) so it does not get dropped.
    if not force:
        # Don't dispatch catch-ups in the dead of night (01:00 - 07:00 KST)
        if not (1 <= current_hour < 7):
            overdue_drops = [
                d for d in schedule
                if d.get("date") and d.get("date") < today_str
                and d.get("status") == "ready"
                and is_bluesky_fanvue_drop(d)
                and (d.get("fanvue_post_uuid") or d.get("fanvue_status") in ("published", "scheduled"))
            ]
            if overdue_drops:
                # Sort by date ascending to catch up oldest first
                overdue_drops.sort(key=lambda x: x.get("date", ""))
                target = overdue_drops[0]
                return target, f"Overdue drop recovery from {target.get('day')} ({target.get('date')})"

    # 2. Match by exact date for today
    today_drops = [
        d for d in schedule
        if d.get("date") == today_str and is_bluesky_fanvue_drop(d)
    ]
    if today_drops:
        ready_today = [d for d in today_drops if d.get("status") == "ready"]
        if not ready_today and not force:
            return None, f"All drops for today ({today_str}) are already published or completed."

        target = ready_today[0] if ready_today else today_drops[0]
        if target.get("status") == "published" and not force:
            return None, f"[SKIPPED] Drop '{target['id']}' already published ({target.get('uri')})."

        # Check slot time
        time_kst_str = target.get("time_kst") or "20:00"
        try:
            parts = [int(p) for p in time_kst_str.split(":", 1)]
            target_time = now_kst.replace(hour=parts[0], minute=parts[1], second=0, microsecond=0)
        except Exception:
            target_time = now_kst

        # Allow dispatch within 30 minutes before slot time, but gate if hours early
        if not force and now_kst < target_time - dt.timedelta(minutes=30):
            return None, (
                f"[TIME-GATE] Today's drop '{target['id']}' is scheduled for {target.get('slot')} "
                f"({time_kst_str} KST). Current KST time is {now_kst.strftime('%H:%M')}. Skipping until slot window."
            )

        return target, f"Scheduled drop for today ({today_str})"

    # 3. Fallback: match by day-of-week for undated drops or current date (ignoring future-dated drops)
    day_drops = [
        d for d in schedule
        if d.get("day") and str(d.get("day")).lower() == current_day.lower()
        and (d.get("date") is None or d.get("date") <= today_str)
        and is_bluesky_fanvue_drop(d)
    ]
    ready_day = [d for d in day_drops if d.get("status") == "ready"]
    if ready_day:
        target = ready_day[0]
        time_kst_str = target.get("time_kst") or "20:00"
        try:
            parts = [int(p) for p in time_kst_str.split(":", 1)]
            target_time = now_kst.replace(hour=parts[0], minute=parts[1], second=0, microsecond=0)
        except Exception:
            target_time = now_kst

        if not force and now_kst < target_time - dt.timedelta(minutes=30):
            return None, (
                f"[TIME-GATE] Drop '{target['id']}' is scheduled for {target.get('slot')} "
                f"({time_kst_str} KST). Current KST time is {now_kst.strftime('%H:%M')}. Skipping until slot window."
            )

        return target, f"Ready drop for {current_day}"

    if day_drops:
        return None, f"All configured drops for {current_day} are already published or completed."

    return None, f"No scheduled drop configured for {current_day} ({today_str})."


def dispatch_auto(dry_run: bool = False, force: bool = False) -> None:
    """Auto-detects today's scheduled drop, guarantees Fanvue existence, and dispatches."""
    schedule = load_schedule()
    now_utc = dt.datetime.now(dt.timezone.utc)
    now_kst = now_utc + dt.timedelta(hours=9)
    current_day = now_kst.strftime("%A")
    print(f"Current KST Time: {now_kst.strftime('%Y-%m-%d %H:%M')} ({current_day})")

    drop, reason = select_auto_drop(schedule, now_kst=now_kst, force=force)
    if not drop:
        print(f"\n============================================================")
        print(f"  [AUTO-DISPATCH STATUS] {reason}")
        print(f"============================================================\n")
        return

    print(f"\n[AUTO-DISPATCH MATCH] Selected '{drop['id']}' ({drop.get('day')}) — Reason: {reason}")
    dispatch_drop(drop["id"], dry_run=dry_run, force=force)


def main():
    print("[NOTICE] campaign_orchestrator.py is DEPRECATED. Fanvue integration and synchronized drops have been permanently removed. Use agent_runner.py instead.")
    return

    if args.sync_drop:
        schedule = load_schedule()
        client = get_fanvue_client()
        drop = next((d for d in schedule if d["id"] == args.sync_drop), None)
        if not drop:
            sys.exit(f"Drop '{args.sync_drop}' not found.")
        post_uuid = sync_fanvue_drop(client, drop, dry_run=args.dry_run)
        if not args.dry_run:
            drop["fanvue_post_uuid"] = post_uuid
            drop["fanvue_status"] = "published"
            save_schedule(schedule)
        print_campaign_matrix()
    elif args.status or len(sys.argv) == 1:
        print_campaign_matrix()
    elif args.sync_fanvue:
        sync_all_fanvue(dry_run=args.dry_run)
        print_campaign_matrix()
    elif args.dispatch:
        dispatch_drop(args.dispatch, dry_run=args.dry_run, force=args.force)
    elif args.auto:
        dispatch_auto(dry_run=args.dry_run, force=args.force)


if __name__ == "__main__":
    main()
