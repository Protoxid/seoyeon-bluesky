#!/usr/bin/env python3
"""
bsky_schedule_worker.py — Robust 24/7 Cloud/Local Bluesky Funnel Worker.
Supports both GitHub Actions (reading secrets from env) and local execution.
Posts soft-NSFW images or videos with 'suggestive' self-label and threaded CTA.
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
import urllib.error
import urllib.parse
import urllib.request
from PIL import Image

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

GROWTH_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = GROWTH_DIR.parent
SCHEDULE_FILE = GROWTH_DIR / "schedule_assets" / "weekly_schedule.json"
CRED_FILE = GROWTH_DIR / "bsky_credentials.json"
LEDGER_FILE = GROWTH_DIR / "ledger.jsonl"
XRPC_BASE = "https://bsky.social/xrpc"

def get_credentials():
    """Reads credentials from Environment Variables (GitHub Secrets) or local file."""
    handle = os.environ.get("BSKY_HANDLE")
    app_pw = os.environ.get("BSKY_APP_PASSWORD")

    if not handle or not app_pw:
        if CRED_FILE.exists():
            try:
                data = json.loads(CRED_FILE.read_text(encoding="utf-8"))
                handle = handle or data.get("handle")
                app_pw = app_pw or data.get("app_password")
            except Exception:
                pass

    if not handle or not app_pw:
        sys.exit("Error: BSKY_HANDLE or BSKY_APP_PASSWORD not set in environment or credentials file.")

    if "." not in handle:
        handle = f"{handle}.bsky.social"

    return handle.strip(), app_pw.strip()

def parse_facets(text: str) -> list[dict]:
    """Detects URLs in text and builds AT Protocol richtext link facets using UTF-8 byte offsets."""
    facets = []
    url_pattern = re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+')
    for match in url_pattern.finditer(text):
        url = match.group(0)
        start_byte = len(text[:match.start()].encode("utf-8"))
        end_byte = len(text[:match.end()].encode("utf-8"))
        full_url = url if url.startswith("http") else f"https://{url}"
        facets.append({
            "index": {"byteStart": start_byte, "byteEnd": end_byte},
            "features": [{
                "$type": "app.bsky.richtext.facet#link",
                "uri": full_url
            }]
        })
    return facets

def create_session(handle: str, app_pw: str) -> tuple[str, str]:
    sess_data = json.dumps({"identifier": handle, "password": app_pw}).encode("utf-8")
    req = urllib.request.Request(
        f"{XRPC_BASE}/com.atproto.server.createSession",
        data=sess_data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        res = json.loads(r.read().decode("utf-8"))
    return res["accessJwt"], res["did"]

def upload_image_blob(img_path: pathlib.Path, jwt: str) -> dict:
    im = Image.open(img_path).convert("RGB")
    if max(im.size) > 2048:
        im.thumbnail((2048, 2048), Image.LANCZOS)

    buf = io.BytesIO()
    quality = 90
    im.save(buf, format="JPEG", quality=quality, optimize=True)
    while buf.tell() > 950_000 and quality > 50:
        buf.seek(0)
        buf.truncate(0)
        quality -= 5
        im.save(buf, format="JPEG", quality=quality, optimize=True)

    img_bytes = buf.getvalue()
    upload_req = urllib.request.Request(
        f"{XRPC_BASE}/com.atproto.repo.uploadBlob",
        data=img_bytes,
        headers={"Content-Type": "image/jpeg", "Authorization": f"Bearer {jwt}"},
        method="POST"
    )
    with urllib.request.urlopen(upload_req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8")).get("blob")

def upload_video_blob(vid_path: pathlib.Path, jwt: str, did: str) -> dict:
    # 1. Obtain scoped service auth token for video.bsky.app
    auth_url = f"{XRPC_BASE}/com.atproto.server.getServiceAuth?aud=did:web:video.bsky.app&lxm=app.bsky.video.uploadVideo"
    auth_req = urllib.request.Request(auth_url, headers={"Authorization": f"Bearer {jwt}"})
    with urllib.request.urlopen(auth_req, timeout=15) as r:
        service_token = json.loads(r.read().decode("utf-8")).get("token")

    # 2. Upload video binary
    vid_bytes = vid_path.read_bytes()
    upload_url = f"https://video.bsky.app/xrpc/app.bsky.video.uploadVideo?did={did}&name={vid_path.name}"
    upload_req = urllib.request.Request(
        upload_url,
        data=vid_bytes,
        headers={"Content-Type": "video/mp4", "Authorization": f"Bearer {service_token}"},
        method="POST"
    )
    with urllib.request.urlopen(upload_req, timeout=60) as resp:
        job = json.loads(resp.read().decode("utf-8"))

    job_id = job.get("jobId")
    if not job_id:
        return job.get("blob")

    # 3. Poll video processing status
    status_url = f"https://video.bsky.app/xrpc/app.bsky.video.getJobStatus?jobId={job_id}"
    for _ in range(30):
        time.sleep(3)
        status_req = urllib.request.Request(status_url, headers={"Authorization": f"Bearer {service_token}"})
        try:
            with urllib.request.urlopen(status_req, timeout=15) as r:
                s = json.loads(r.read().decode("utf-8"))
                state = s.get("jobStatus", {}).get("state")
                if state == "JOB_STATE_COMPLETED":
                    return s.get("jobStatus", {}).get("blob")
                elif state == "JOB_STATE_FAILED":
                    raise RuntimeError(f"Video processing failed: {s}")
        except Exception:
            pass
    raise TimeoutError("Video processing timed out on video.bsky.app")

def dispatch_drop(drop: dict, dry_run: bool = False, force: bool = False):
    # Integrity Invariant: Never tease content on Bluesky that is not live on Fanvue!
    fv_uuid = drop.get("fanvue_post_uuid")
    if not fv_uuid and not dry_run:
        sys.exit(
            f"\n[BLOCKED BY CAMPAIGN POLICY] Drop '{drop.get('id')}' cannot be dispatched to Bluesky!\n"
            f"  Reason: The corresponding Fanvue post does not exist yet (fanvue_post_uuid is null).\n"
            f"  To maintain 100% truth in advertising, run:\n"
            f"    python growth/campaign_orchestrator.py --sync-fanvue\n"
            f"  This will publish the exclusive set to Fanvue first, then unlock Bluesky.\n"
        )

    if drop.get("status") == "published" and not force:
        print(f"\n============================================================")
        print(f"  [SKIPPED] DROP ALREADY PUBLISHED: {drop.get('id')} ({drop.get('day')})")
        print(f"  Bluesky URI: {drop.get('uri')}")
        print(f"  Skipping dispatch to prevent duplicate posting on Bluesky.")
        print(f"  (Use --force if you intentionally wish to republish)")
        print(f"============================================================\n")
        return {"status": "skipped", "reason": "already_published", "uri": drop.get("uri")}

    handle, app_pw = get_credentials()
    media_p = PROJECT_ROOT / drop["media_file"]
    if not media_p.exists():
        media_p = (GROWTH_DIR / drop["media_file"]).resolve()
    if not media_p.exists():
        sys.exit(f"Error: Media asset not found: {drop['media_file']}")

    print(f"\n============================================================")
    print(f"  BLUESKY SCHEDULED FUNNEL DISPATCH -> @{handle}")
    print(f"============================================================")
    print(f"  Drop ID:     {drop['id']} ({drop.get('day', 'Custom')})")
    print(f"  Media:       {media_p.name} ({drop['media_type']})")
    print(f"  Main Post:   {drop['main_text']}")
    print(f"  Thread CTA:  {drop['reply_text']}")
    print(f"  Label:       {drop.get('label', 'suggestive')}")
    print(f"============================================================\n")

    if dry_run:
        print("[DRY RUN] Simulation passed successfully. No network calls sent.")
        return {"dry_run": True}

    print("[1/4] Authenticating with AT Protocol...")
    jwt, did = create_session(handle, app_pw)
    print(f"      Authenticated DID: {did}")

    print(f"[2/4] Uploading {drop['media_type']} blob...")
    if drop["media_type"] == "video":
        blob = upload_video_blob(media_p, jwt, did)
        embed = {"$type": "app.bsky.embed.video", "video": blob}
    else:
        blob = upload_image_blob(media_p, jwt)
        embed = {
            "$type": "app.bsky.embed.images",
            "images": [{"alt": "Seo-yeon candid soft-NSFW snapshot", "image": blob}]
        }

    print("[3/4] Publishing main post with 'suggestive' label...")
    now_iso = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    main_record = {
        "$type": "app.bsky.feed.post",
        "text": drop["main_text"],
        "createdAt": now_iso,
        "labels": {
            "$type": "com.atproto.label.defs#selfLabels",
            "values": [{"val": drop.get("label", "suggestive")}]
        },
        "embed": embed
    }
    main_facets = parse_facets(drop["main_text"])
    if main_facets:
        main_record["facets"] = main_facets

    post_payload = json.dumps({
        "repo": did,
        "collection": "app.bsky.feed.post",
        "record": main_record
    }).encode("utf-8")

    post_req = urllib.request.Request(
        f"{XRPC_BASE}/com.atproto.repo.createRecord",
        data=post_payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {jwt}"},
        method="POST"
    )
    with urllib.request.urlopen(post_req, timeout=20) as resp:
        main_res = json.loads(resp.read().decode("utf-8"))

    main_uri = main_res.get("uri")
    main_cid = main_res.get("cid")
    print(f"[✔] Main post published! URI: {main_uri}")

    if drop.get("reply_text"):
        print("[4/4] Creating threaded conversion reply with Fanvue tracking link...")
        reply_now_iso = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
        reply_record = {
            "$type": "app.bsky.feed.post",
            "text": drop["reply_text"],
            "createdAt": reply_now_iso,
            "reply": {
                "root": {"uri": main_uri, "cid": main_cid},
                "parent": {"uri": main_uri, "cid": main_cid}
            }
        }
        reply_facets = parse_facets(drop["reply_text"])
        if reply_facets:
            reply_record["facets"] = reply_facets

        reply_payload = json.dumps({
            "repo": did,
            "collection": "app.bsky.feed.post",
            "record": reply_record
        }).encode("utf-8")

        reply_req = urllib.request.Request(
            f"{XRPC_BASE}/com.atproto.repo.createRecord",
            data=reply_payload,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {jwt}"},
            method="POST"
        )
        with urllib.request.urlopen(reply_req, timeout=20) as resp:
            reply_res = json.loads(resp.read().decode("utf-8"))
        print(f"[✔] Conversion reply published! URI: {reply_res.get('uri')}")

    # Record to ledger
    entry = {
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
        "surface": "bluesky",
        "action": "scheduled_funnel_post",
        "drop_id": drop["id"],
        "target": main_uri,
        "note": f"Published {drop.get('day')} drop: {drop['main_text'][:40]}..."
    }
    with open(LEDGER_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # Record to schedule file so state is persistent and idempotent
    if SCHEDULE_FILE.exists() and not dry_run:
        try:
            sched = json.loads(SCHEDULE_FILE.read_text(encoding="utf-8"))
            for d in sched:
                if d.get("id") == drop.get("id"):
                    d["status"] = "published"
                    d["uri"] = main_uri
                    d["published_at"] = now_iso
                    break
            SCHEDULE_FILE.write_text(json.dumps(sched, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            print(f"  [Warning] Could not update status in weekly_schedule.json: {e}")

    return {"main_uri": main_uri}

def run_auto(dry_run: bool = False, force: bool = False):
    schedule = json.loads(SCHEDULE_FILE.read_text(encoding="utf-8"))
    # Match current weekday in UTC/KST
    now_utc = dt.datetime.now(dt.timezone.utc)
    # KST is UTC+9
    now_kst = now_utc + dt.timedelta(hours=9)
    current_day = now_kst.strftime("%A")
    print(f"Current KST Day: {current_day} ({now_kst.strftime('%Y-%m-%d %H:%M')})")

    drop = next((d for d in schedule if d["day"].lower() == current_day.lower()), None)
    if not drop:
        print(f"No scheduled drop configured for {current_day}.")
        return

    if drop.get("status") == "published" and not force:
        print(f"\n============================================================")
        print(f"  [SKIPPED] DROP ALREADY PUBLISHED: {drop.get('id')} ({drop.get('day')})")
        print(f"  Bluesky URI: {drop.get('uri')}")
        print(f"  Skipping auto-dispatch to avoid duplicate posting on Bluesky.")
        print(f"============================================================\n")
        return

    dispatch_drop(drop, dry_run=dry_run, force=force)

def main():
    parser = argparse.ArgumentParser(description="Bluesky Automated Funnel Scheduler Worker")
    parser.add_argument("--auto", action="store_true", help="Auto-detect current day and dispatch scheduled drop")
    parser.add_argument("--drop", type=str, help="Dispatch specific drop ID from schedule")
    parser.add_argument("--list", action="store_true", help="List all scheduled drops")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without publishing")
    parser.add_argument("--force", action="store_true", help="Force republish even if already marked as published")
    args = parser.parse_args()

    if not SCHEDULE_FILE.exists():
        sys.exit(f"Error: Schedule file not found at {SCHEDULE_FILE}")

    if args.list:
        schedule = json.loads(SCHEDULE_FILE.read_text(encoding="utf-8"))
        print("\n" + "="*70)
        print("  7-DAY BLUESKY SOFT-NSFW FUNNEL SCHEDULE")
        print("="*70)
        for d in schedule:
            print(f"[{d['day']}] {d['id']} ({d['media_type']}) - {d['time_kst']} KST")
            print(f"  Hook:   \"{d['main_text']}\"")
            print(f"  CTA:    \"{d['reply_text']}\"")
            print(f"  Asset:  {d['media_file']}")
            print(f"  Status: {d.get('status', 'ready')}")
            print("-"*70)
        print()
    elif args.drop:
        schedule = json.loads(SCHEDULE_FILE.read_text(encoding="utf-8"))
        drop = next((d for d in schedule if d["id"] == args.drop), None)
        if not drop:
            sys.exit(f"Error: Drop ID '{args.drop}' not found in schedule.")
        dispatch_drop(drop, dry_run=args.dry_run, force=args.force)
    elif args.auto:
        run_auto(dry_run=args.dry_run, force=args.force)
    else:
        run_auto(dry_run=args.dry_run, force=args.force)

if __name__ == "__main__":
    main()
