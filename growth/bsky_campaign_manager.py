#!/usr/bin/env python3
"""
bsky_campaign_manager.py — Bluesky Content Manager & Funnel Orchestration Suite.
Manages soft-NSFW funnel drops, profile optimization, scheduled queue,
and engagement discovery for Seo-yeon Han (@syeonhn.bsky.social -> Fanvue @syeon.hn).
"""
import argparse
import datetime as dt
import json
import pathlib
import sys
import urllib.request
import urllib.error

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

GROWTH_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = GROWTH_DIR.parent
CRED_PATH = GROWTH_DIR / "bsky_credentials.json"
LEDGER_PATH = GROWTH_DIR / "ledger.jsonl"
FANVUE_TRACKING_URL = "https://www.fanvue.com/syeon.hn?c=fv-4"

DROPS_PIPELINE = [
    {
        "id": "drop-1",
        "title": "Morning Linen Bed Wakeup",
        "image": "personas/seoyeon/content/fanvue/fv_ex_unbuttoned_linen.png",
        "main_text": "woke up slow today in seongsu... linen sheets and warm morning sun ✨",
        "reply_text": f"put together a quiet morning set + video for you on my private feed... come say hi 🖤☕ {FANVUE_TRACKING_URL}",
        "label": "suggestive",
        "status": "LIVE (3musahzizcv2n)"
    },
    {
        "id": "drop-2",
        "title": "Post-Shower Steam & Towel Wrap",
        "image": "personas/seoyeon/content/fanvue/fv_ex_towel_steam.png",
        "main_text": "warm shower after a late night in seoul... steam still on the glass ☁️🫧",
        "reply_text": f"shared the quiet morning moments on my private wall... don't be shy, link is here 🖤🛁 {FANVUE_TRACKING_URL}",
        "label": "suggestive",
        "status": "READY"
    },
    {
        "id": "drop-3",
        "title": "Late Night Black Lace Bedroom Mirror",
        "image": "personas/seoyeon/content/fanvue/fv_ex_lace_mirror.png",
        "main_text": "trying on black lace before bed... how does it look? 🌙🖤",
        "reply_text": f"the full try-on set is waiting for you... plus answering all dms tonight on my page ✨ {FANVUE_TRACKING_URL}",
        "label": "suggestive",
        "status": "READY"
    }
]

def get_profile():
    url = "https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile?actor=syeonhn.bsky.social"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

def list_pipeline():
    print("\n" + "="*65)
    print("  BLUESKY SOFT-NSFW FUNNEL PIPELINE -> FANVUE (c=fv-4)")
    print("="*65)
    for d in DROPS_PIPELINE:
        print(f"\n[ID: {d['id']}] {d['title']}")
        print(f"  Status:    {d['status']}")
        print(f"  Image:     {d['image']}")
        print(f"  Main:      \"{d['main_text']}\"")
        print(f"  Thread CTA:\"{d['reply_text']}\"")
        print(f"  Label:     {d['label']}")
    print("\n" + "="*65 + "\n")

def get_session():
    if not CRED_PATH.exists():
        sys.exit(f"Error: Credentials not found at {CRED_PATH}")
    creds = json.loads(CRED_PATH.read_text(encoding="utf-8"))
    handle = creds.get("handle")
    app_pw = creds.get("app_password")
    if "." not in handle:
        handle = f"{handle}.bsky.social"
    
    sess_data = json.dumps({"identifier": handle, "password": app_pw}).encode("utf-8")
    req = urllib.request.Request(
        "https://bsky.social/xrpc/com.atproto.server.createSession",
        data=sess_data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode("utf-8"))

def show_status():
    prof = get_profile()
    print("\n" + "="*65)
    print("  BLUESKY ACCOUNT & FUNNEL STATUS (@syeonhn.bsky.social)")
    print("="*65)
    if "error" in prof:
        print(f"  Error fetching profile: {prof['error']}")
    else:
        print(f"  Handle:       @{prof.get('handle')}")
        print(f"  DisplayName:  {prof.get('displayName')}")
        print(f"  Followers:    {prof.get('followersCount')}")
        print(f"  Follows:      {prof.get('followsCount')}")
        print(f"  Posts:        {prof.get('postsCount')}")
        print(f"  Bio:\n{prof.get('description')}")
    print("="*65 + "\n")

def show_recent_posts():
    sess = get_session()
    jwt = sess["accessJwt"]
    did = sess["did"]
    url = f"https://bsky.social/xrpc/app.bsky.feed.getAuthorFeed?actor={did}&limit=10"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {jwt}"})
    with urllib.request.urlopen(req) as r:
        feed = json.loads(r.read().decode("utf-8")).get("feed", [])
    
    print("\n" + "="*65)
    print("  RECENT BLUESKY POSTS & THREAD REPLIES")
    print("="*65)
    for idx, item in enumerate(feed, 1):
        post = item.get("post", {})
        rec = post.get("record", {})
        uri = post.get("uri")
        cid = post.get("cid")
        labels = [l.get("val") for l in post.get("labels", [])]
        reply = item.get("reply", {})
        is_reply = bool(reply)
        print(f"\n[{idx}] {'[REPLY]' if is_reply else '[POST]'} {rec.get('createdAt')}")
        print(f"    URI:    {uri}")
        print(f"    Labels: {labels if labels else '(none)'}")
        print(f"    Text:   {rec.get('text')}")
    print("\n" + "="*65 + "\n")

def dispatch_drop(drop_id: str, dry_run: bool = False):
    drop = next((d for d in DROPS_PIPELINE if d["id"] == drop_id), None)
    if not drop:
        print(f"Error: Drop ID '{drop_id}' not recognized. Available: {[d['id'] for d in DROPS_PIPELINE]}")
        return

    from bsky_funnel_post import post_funnel
    print(f"\n[>>>] Triggering Drop: {drop['title']} ({drop_id})...")
    post_funnel(
        image_path=drop["image"],
        post_text=drop["main_text"],
        reply_text=drop["reply_text"],
        dry_run=dry_run
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bluesky Content Manager & Funnel Orchestrator")
    parser.add_argument("--status", action="store_true", help="Display current profile & funnel metrics")
    parser.add_argument("--posts", action="store_true", help="Display recent published posts & replies")
    parser.add_argument("--pipeline", action="store_true", help="List scheduled soft-NSFW drops")
    parser.add_argument("--drop", type=str, help="Dispatch a drop by ID (e.g. drop-1, drop-2, drop-3)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without network calls")
    args = parser.parse_args()

    if args.status:
        show_status()
    elif args.posts:
        show_recent_posts()
    elif args.pipeline:
        list_pipeline()
    elif args.drop:
        dispatch_drop(args.drop, dry_run=args.dry_run)
    else:
        show_status()
        show_recent_posts()
        list_pipeline()
