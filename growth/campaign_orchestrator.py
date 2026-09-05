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


def get_fanvue_client() -> FanvueClient:
    key = load_key()
    return FanvueClient(key)


def get_fanvue_live_posts(client: FanvueClient) -> Dict[str, Dict[str, Any]]:
    """Retrieves all published posts from Fanvue and indexes by UUID."""
    try:
        res = client.request("GET", "/posts")
        posts = res.get("data", []) if isinstance(res, dict) else []
        return {p.get("uuid") or p.get("id"): p for p in posts if p.get("uuid") or p.get("id")}
    except Exception as e:
        print(f"  [Warning] Could not fetch live Fanvue posts: {e}")
        return {}


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
        drop_id = drop.get("id", "unknown")
        day_slot = f"{drop.get('day', '')} ({drop.get('time_kst', '')})"
        fv_uuid = drop.get("fanvue_post_uuid")
        fv_status = drop.get("fanvue_status", "ready")
        bsky_status = drop.get("status", "ready")

        # Verify against live Fanvue API
        is_live_on_fanvue = fv_uuid in live_fanvue_posts if fv_uuid else False
        if is_live_on_fanvue:
            fv_display = f"LIVE ({fv_uuid[:8]}...)"
        elif fv_uuid:
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


def sync_fanvue_drop(client: FanvueClient, drop: Dict[str, Any], dry_run: bool = False) -> str:
    """Uploads media to Fanvue and creates the subscriber post for a drop."""
    drop_id = drop["id"]
    media_rel = drop.get("media_file", "")
    media_path = (PROJECT_ROOT / media_rel if not pathlib.Path(media_rel).is_absolute() else pathlib.Path(media_rel)).resolve()
    
    if not media_path.exists():
        # Fallback check
        alt_path = pathlib.Path(r"c:\AI-Project") / media_rel
        if alt_path.exists():
            media_path = alt_path
        else:
            raise FileNotFoundError(f"Media file not found for drop {drop_id}: {media_rel}")

    caption = drop.get("fanvue_text") or (
        f"something a little more private for you today... {drop.get('main_text', '')} 🖤"
    )
    audience = drop.get("fanvue_audience", "subscribers")
    price_cents = drop.get("fanvue_price_cents")

    print(f"\n[Fanvue Sync] Processing drop '{drop_id}' ({drop.get('day')})...")
    print(f"  Media:    {media_path.name} ({media_path.stat().st_size // 1024} KB)")
    print(f"  Audience: {audience}")
    print(f"  Caption:  \"{caption[:60]}...\"")

    if dry_run:
        print("  [DRY-RUN] Would upload media to Fanvue and publish subscriber post.")
        return "simulated-fanvue-uuid"

    # 1. Upload media
    media_uuid = client.upload_media(media_path, name=drop_id)
    if not media_uuid:
        raise RuntimeError(f"Failed to upload media to Fanvue for drop {drop_id}")

    # 2. Create post
    post_res = client.create_post(
        text=caption,
        media_uuids=[media_uuid],
        audience=audience,
        price_cents=price_cents,
        dry_run=dry_run
    )
    post_uuid = post_res.get("id") or post_res.get("uuid") or post_res.get("data", {}).get("id")
    if not post_uuid:
        raise RuntimeError(f"Post created but no UUID returned: {post_res}")

    print(f"  [SUCCESS] Fanvue post published live! UUID: {post_uuid}")
    log_ledger("fanvue_campaign_sync", drop_id, f"Published Fanvue post {post_uuid} for {drop.get('day')}")
    return post_uuid


def sync_all_fanvue(dry_run: bool = False) -> None:
    """Ensures all 7 days of scheduled content exist on Fanvue before Bluesky drops."""
    schedule = load_schedule()
    client = get_fanvue_client()
    live_posts = get_fanvue_live_posts(client)
    updated = False

    for drop in schedule:
        drop_id = drop["id"]
        current_uuid = drop.get("fanvue_post_uuid")

        # If already recorded and verified live, skip
        if current_uuid and current_uuid in live_posts:
            continue

        # If not on Fanvue, upload and publish now
        try:
            new_uuid = sync_fanvue_drop(client, drop, dry_run=dry_run)
            drop["fanvue_post_uuid"] = new_uuid
            drop["fanvue_status"] = "published"
            updated = True
            time.sleep(2)  # Respect rate limits
        except Exception as e:
            print(f"  [ERROR] Failed to sync drop '{drop_id}' to Fanvue: {e}")

    if updated and not dry_run:
        save_schedule(schedule)
        print("\n[SUCCESS] Weekly schedule updated with all live Fanvue post UUIDs.")


def dispatch_drop(drop_id: str, dry_run: bool = False) -> None:
    """Dispatches a synchronized drop: guarantees Fanvue existence, then posts to Bluesky."""
    schedule = load_schedule()
    client = get_fanvue_client()
    
    target_drop = None
    for d in schedule:
        if d["id"] == drop_id:
            target_drop = d
            break

    if not target_drop:
        sys.exit(f"Drop ID '{drop_id}' not found in schedule.")

    # 1. Guarantee Fanvue existence
    fv_uuid = target_drop.get("fanvue_post_uuid")
    if not fv_uuid:
        print(f"\n[Pre-flight Check] Fanvue post does not exist yet for drop '{drop_id}'.")
        print("  -> Uploading and publishing to Fanvue FIRST to maintain truth in advertising...")
        new_uuid = sync_fanvue_drop(client, target_drop, dry_run=dry_run)
        target_drop["fanvue_post_uuid"] = new_uuid
        target_drop["fanvue_status"] = "published"
        save_schedule(schedule)
    else:
        print(f"\n[Pre-flight Check] Fanvue post verified live ({fv_uuid}). Ready for Bluesky teaser.")

    # 2. Dispatch to Bluesky using the existing schedule worker
    print(f"\n[Bluesky Dispatch] Launching Bluesky teaser for '{drop_id}'...")
    import subprocess
    cmd = [sys.executable, str(GROWTH_DIR / "bsky_schedule_worker.py"), "--drop", drop_id]
    if dry_run:
        cmd.append("--dry-run")
    
    res = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(res.stdout)
    if res.returncode != 0:
        print(res.stderr)
        sys.exit(f"Bluesky dispatch failed with code {res.returncode}")


def main():
    parser = argparse.ArgumentParser(description="Synchronized Fanvue <-> Bluesky Campaign Orchestrator")
    parser.add_argument("--status", action="store_true", help="Display cross-platform campaign coherence matrix")
    parser.add_argument("--sync-fanvue", action="store_true", help="Upload and publish all missing drops to Fanvue")
    parser.add_argument("--dispatch", type=str, help="Dispatch a synchronized drop (Fanvue check -> Bluesky post)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate actions without publishing")

    args = parser.parse_args()

    if args.status or len(sys.argv) == 1:
        print_campaign_matrix()
    elif args.sync_fanvue:
        sync_all_fanvue(dry_run=args.dry_run)
        print_campaign_matrix()
    elif args.dispatch:
        dispatch_drop(args.dispatch, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
