#!/usr/bin/env python3
"""
publish_sunday_fanvue.py — Uploads and publishes only Shot 02 on Fanvue for Sunday.
"""
import json
import pathlib
import sys

GROWTH_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = GROWTH_DIR.parent
SCHEDULE_FILE = GROWTH_DIR / "schedule_assets" / "weekly_schedule.json"

sys.path.insert(0, str(GROWTH_DIR))
from fanvue_api import FanvueClient, load_key, log_ledger

def main():
    print("=== PUBLISHING SUNDAY DROP TO FANVUE (ONLY SHOT 02) ===")
    
    shot_02 = GROWTH_DIR / "schedule_assets" / "sets" / "sun_sunday_bed" / "02_livingroom_stretch.png"
    if not shot_02.exists():
        sys.exit(f"Error: Required file not found: {shot_02}")
    print(f"  Found: {shot_02.name} ({shot_02.stat().st_size // 1024} KB)")

    api_key = load_key(GROWTH_DIR)
    client = FanvueClient(api_key)

    print(f"\n  Uploading {shot_02.name} ({shot_02.stat().st_size // 1024} KB)...")
    uuid = client.upload_media(shot_02, name=shot_02.name)
    if not uuid:
        sys.exit(f"Error: Upload failed for {shot_02.name}")
    print(f"  -> Media UUID: {uuid}")

    caption = "sunday. coffee first. leaving bed later... lazy sundays are better shared. chatting in my inbox all afternoon 🖤"
    print(f"\n  Publishing immediate post to Fanvue (subscribers)...")
    res = client.create_post(
        text=caption,
        media_uuids=[uuid],
        audience="subscribers"
    )
    post_uuid = res.get("id") or res.get("uuid") or res.get("data", {}).get("id")
    print(f"\n[SUCCESS] Sunday Fanvue post published! ID: {post_uuid}")

    # Update weekly_schedule.json
    if SCHEDULE_FILE.exists():
        schedule = json.loads(SCHEDULE_FILE.read_text(encoding="utf-8"))
        for item in schedule:
            if item.get("id") == "sun_sunday_bed":
                item["fanvue_post_uuid"] = post_uuid
                item["fanvue_status"] = "published"
                item["fanvue_gallery_files"] = [
                    "growth/schedule_assets/sets/sun_sunday_bed/02_livingroom_stretch.png"
                ]
                break
        SCHEDULE_FILE.write_text(json.dumps(schedule, indent=2, ensure_ascii=False), encoding="utf-8")
        print("[+] weekly_schedule.json updated successfully!")

if __name__ == "__main__":
    main()
