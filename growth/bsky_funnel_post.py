#!/usr/bin/env python3
"""
bsky_funnel_post.py — High-converting Bluesky soft-NSFW funnel publisher.
Posts soft-NSFW hero frame with 'suggestive' self-label, then automatically
creates a threaded self-reply with the direct Fanvue tracking link (c=fv-4).
"""
import io
import json
import pathlib
import sys
import re
import datetime as dt
import urllib.request
import urllib.error
from PIL import Image

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

GROWTH_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = GROWTH_DIR.parent
CRED_PATH = GROWTH_DIR / "bsky_credentials.json"
XRPC_BASE = "https://bsky.social/xrpc"
TRACKING_LINK = "https://www.fanvue.com/syeon.hn?c=fv-4"

def parse_facets(text: str) -> list[dict]:
    """Detects URLs and Hashtags in text and builds AT Protocol richtext link & tag facets using UTF-8 byte offsets."""
    facets = []
    # 1. Parse Links
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
    # 2. Parse Hashtags
    tag_pattern = re.compile(r'(?:^|\s)(#([^\s#.,!?:;()\[\]{}"\'<>]+))')
    for match in tag_pattern.finditer(text):
        tag_val = match.group(2)
        start_char = match.start(1)
        end_char = match.end(1)
        start_byte = len(text[:start_char].encode("utf-8"))
        end_byte = len(text[:end_char].encode("utf-8"))
        facets.append({
            "index": {"byteStart": start_byte, "byteEnd": end_byte},
            "features": [{
                "$type": "app.bsky.richtext.facet#tag",
                "tag": tag_val
            }]
        })
    return facets

def post_funnel(image_path: str, post_text: str, reply_text: str = "", dry_run: bool = False):
    img_p = pathlib.Path(image_path)
    if not img_p.is_absolute():
        img_p = (PROJECT_ROOT / img_p if (PROJECT_ROOT / img_p).exists() else img_p).resolve()

    if not img_p.exists():
        sys.exit(f"Error: Image not found at {img_p}")

    if not CRED_PATH.exists():
        sys.exit(f"Error: Credentials not found at {CRED_PATH}")

    creds = json.loads(CRED_PATH.read_text(encoding="utf-8"))
    handle = creds.get("handle")
    app_pw = creds.get("app_password")

    if not handle or not app_pw:
        sys.exit("Error: Missing handle or app_password in credentials")

    if "." not in handle:
        handle = f"{handle}.bsky.social"

    print(f"\n============================================================")
    print(f"  BLUESKY SOFT-NSFW FUNNEL DISPATCH -> @{handle}")
    print(f"============================================================")
    print(f"  Image:       {img_p.name} ({img_p.stat().st_size // 1024} KB)")
    print(f"  Main Post:   {post_text}")
    print(f"  Thread Reply:{reply_text if reply_text else '(none)'}")
    print(f"  Label:       suggestive (soft-NSFW compliant)")
    print(f"============================================================\n")

    if dry_run:
        print("[DRY RUN] Simulation complete. No network requests sent.")
        return {"dry_run": True}

    # 1. Create AT Protocol Session
    print("[1/4] Authenticating with AT Protocol...")
    sess_data = json.dumps({"identifier": handle, "password": app_pw}).encode("utf-8")
    req = urllib.request.Request(
        f"{XRPC_BASE}/com.atproto.server.createSession",
        data=sess_data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as r:
        sess = json.loads(r.read().decode("utf-8"))

    jwt = sess["accessJwt"]
    did = sess["did"]
    print(f"      Authenticated DID: {did}")

    # 2. Compress and Upload Image Blob (< 950KB for AT Proto)
    print(f"[2/4] Compressing and uploading blob: {img_p.name}...")
    im = Image.open(img_p).convert("RGB")
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
    print(f"      Optimized JPEG size: {len(img_bytes) // 1024} KB (quality: {quality})")

    upload_req = urllib.request.Request(
        f"{XRPC_BASE}/com.atproto.repo.uploadBlob",
        data=img_bytes,
        headers={"Content-Type": "image/jpeg", "Authorization": f"Bearer {jwt}"},
        method="POST",
    )
    with urllib.request.urlopen(upload_req) as resp:
        blob_obj = json.loads(resp.read().decode("utf-8")).get("blob")

    # 3. Publish Main Post with 'suggestive' Self-Label
    print("[3/4] Creating main soft-NSFW post with self-label 'suggestive'...")
    now_iso = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    
    main_record = {
        "$type": "app.bsky.feed.post",
        "text": post_text,
        "createdAt": now_iso,
        "langs": ["ko", "en"],
        "labels": {
            "$type": "com.atproto.label.defs#selfLabels",
            "values": [{"val": "suggestive"}]
        },
        "embed": {
            "$type": "app.bsky.embed.images",
            "images": [{"alt": "Seo-yeon candid morning in Seongsu", "image": blob_obj}],
        }
    }
    main_facets = parse_facets(post_text)
    if main_facets:
        main_record["facets"] = main_facets

    post_payload = json.dumps({
        "repo": did,
        "collection": "app.bsky.feed.post",
        "record": main_record,
    }).encode("utf-8")

    post_req = urllib.request.Request(
        f"{XRPC_BASE}/com.atproto.repo.createRecord",
        data=post_payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {jwt}"},
        method="POST",
    )
    with urllib.request.urlopen(post_req) as resp:
        main_res = json.loads(resp.read().decode("utf-8"))

    main_uri = main_res.get("uri")
    main_cid = main_res.get("cid")
    print(f"[✔] Main post published! URI: {main_uri}")

    # 4. Publish Conversion Reply Thread (if specified)
    if reply_text:
        print("[4/4] Creating conversion reply in thread with Fanvue tracking link...")
        reply_now_iso = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
        reply_record = {
            "$type": "app.bsky.feed.post",
            "text": reply_text,
            "createdAt": reply_now_iso,
            "langs": ["ko", "en"],
            "reply": {
                "root": {"uri": main_uri, "cid": main_cid},
                "parent": {"uri": main_uri, "cid": main_cid}
            }
        }
        reply_facets = parse_facets(reply_text)
        if reply_facets:
            reply_record["facets"] = reply_facets

        reply_payload = json.dumps({
            "repo": did,
            "collection": "app.bsky.feed.post",
            "record": reply_record,
        }).encode("utf-8")

        reply_req = urllib.request.Request(
            f"{XRPC_BASE}/com.atproto.repo.createRecord",
            data=reply_payload,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {jwt}"},
            method="POST",
        )
        with urllib.request.urlopen(reply_req) as resp:
            reply_res = json.loads(resp.read().decode("utf-8"))
        print(f"[✔] Conversion reply published! URI: {reply_res.get('uri')}")

    # Log to ledger
    ledger_path = GROWTH_DIR / "ledger.jsonl"
    entry = {
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
        "surface": "bluesky",
        "action": "funnel_post",
        "target": main_uri,
        "note": f"Published soft-NSFW funnel post with reply hook: {post_text[:30]}..."
    }
    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print("\n[+] Funnel post sequence completed and recorded in ledger.")
    return {"main_uri": main_uri}

if __name__ == "__main__":
    print("[NOTICE] bsky_funnel_post.py is DEPRECATED. Fanvue tracking funnels have been permanently removed. Use agent_runner.py instead.")
    sys.exit(0)

