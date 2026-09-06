#!/usr/bin/env python3
"""
publish_sunday_fanvue.py — Uploads and publishes the 3-shot Sunday set immediately on Fanvue.
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
    print("=== PUBLISHING SUNDAY DROP TO FANVUE (sun_sunday_bed) ===")
    
    files = [
        GROWTH_DIR / "schedule_assets" / "sun_sunday_bed.png",
        GROWTH_DIR / "schedule_assets" / "sets" / "sun_sunday_bed" / "02_livingroom_stretch.png",
        GROWTH_DIR / "schedule_assets" / "sets" / "sun_sunday_bed" / "03_balcony_coffee.png"
    ]
    
    for f in files:
        if not f.exists():
            sys.exit(f"Error: Required file not found: {f}")
        print(f"  Found: {f.name} ({f.stat().st_size // 1024} KB)")

    api_key = load_key(GROWTH_DIR)
    client = FanvueClient(api_key)

    media_uuids = []
    for f in files:
        print(f"\n  Uploading {f.name} ({f.stat().st_size // 1024} KB)...")
        uuid = client.upload_media(f, name=f.name)
        if not uuid:
            sys.exit(f"Error: Upload failed for {f.name}")
        media_uuids.append(uuid)
        print(f"  -> Media UUID: {uuid}")

    caption = "sunday. coffee first. leaving bed later... lazy sundays are better shared. chatting in my inbox all afternoon 🖤"
    print(f"\n  Publishing immediate post to Fanvue (subscribers)...")
    res = client.create_post(
        text=caption,
        media_uuids=media_uuids,
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
                    "growth/schedule_assets/sun_sunday_bed.png",
                    "growth/schedule_assets/sets/sun_sunday_bed/02_livingroom_stretch.png",
                    "growth/schedule_assets/sets/sun_sunday_bed/03_balcony_coffee.png"
                ]
                break
        SCHEDULE_FILE.write_text(json.dumps(schedule, indent=2, ensure_ascii=False), encoding="utf-8")
        print("[+] weekly_schedule.json updated successfully!")

if __name__ == "__main__":
    main()
