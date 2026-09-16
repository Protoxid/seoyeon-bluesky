#!/usr/bin/env python3
"""
update_bsky_profile.py — Update Bluesky profile with 2K header banner
and ensure description has the Fanvue tracking link.
"""
import io
import json
import pathlib
import sys
import urllib.request
import urllib.error
from PIL import Image

GROWTH_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = GROWTH_DIR.parent
CRED_PATH = GROWTH_DIR / "bsky_credentials.json"
BANNER_PATH = PROJECT_ROOT / "personas" / "seoyeon" / "content" / "fanvue" / "fv_banner_bedroom_linen.png"

XRPC_BASE = "https://bsky.social/xrpc"

def main():
    if not CRED_PATH.exists():
        sys.exit(f"Error: Credentials not found at {CRED_PATH}")

    creds = json.loads(CRED_PATH.read_text(encoding="utf-8"))
    handle = creds.get("handle")
    app_pw = creds.get("app_password")

    if not handle or not app_pw:
        sys.exit("Error: Missing handle or app_password in credentials")

    if "." not in handle:
        handle = f"{handle}.bsky.social"

    print(f"=== Updating Bluesky Profile for {handle} ===")

    # 1. Create Session
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
    print(f"  Authenticated DID: {did}")

    # 2. Prepare and Compress Banner
    if not BANNER_PATH.exists():
        sys.exit(f"Error: Banner file not found at {BANNER_PATH}")

    print(f"  Preparing banner: {BANNER_PATH.name}...")
    im = Image.open(BANNER_PATH).convert("RGB")
    # Resize slightly if larger than 3000px
    if max(im.size) > 2500:
        im.thumbnail((2500, 2500), Image.LANCZOS)

    buf = io.BytesIO()
    quality = 90
    im.save(buf, format="JPEG", quality=quality, optimize=True)
    while buf.tell() > 950_000 and quality > 50:
        buf.seek(0)
        buf.truncate(0)
        quality -= 5
        im.save(buf, format="JPEG", quality=quality, optimize=True)

    banner_bytes = buf.getvalue()
    print(f"  Banner compressed to JPEG: {len(banner_bytes) // 1024} KB (Quality: {quality})")

    # 3. Upload Blob
    print("  Uploading banner blob...")
    upload_req = urllib.request.Request(
        f"{XRPC_BASE}/com.atproto.repo.uploadBlob",
        data=banner_bytes,
        headers={"Content-Type": "image/jpeg", "Authorization": f"Bearer {jwt}"},
        method="POST",
    )
    with urllib.request.urlopen(upload_req) as r:
        banner_blob = json.loads(r.read().decode("utf-8")).get("blob")
    print(f"  Uploaded blob ref: {banner_blob.get('ref', {}).get('$link', 'ok')}")

    # 4. Fetch current profile record
    get_req = urllib.request.Request(
        f"{XRPC_BASE}/com.atproto.repo.getRecord?repo={did}&collection=app.bsky.actor.profile&rkey=self",
        headers={"Authorization": f"Bearer {jwt}"},
    )
    with urllib.request.urlopen(get_req) as r:
        current_rec = json.loads(r.read().decode("utf-8"))

    val = current_rec.get("value", {})
    val["banner"] = banner_blob
    val["displayName"] = "Seo-yeon Han (AI)"

    # Pin the hero soft-NSFW teaser post
    val["pinnedPost"] = {
        "uri": f"at://{did}/app.bsky.feed.post/3mvlgqhchiu2t",
        "cid": "bafyreicx5fshsycj7ohngnwvflrpozcxytquw5vaerx7sqk3tbsf7kqaua"
    }

    # High-converting funnel bio with full compliance
    fv_link = "https://www.fanvue.com/syeon.hn?c=fv-4"
    val["description"] = (
        "an ai creator, not a real person\n"
        "seoul, living alone, changing outfits too many times\n"
        "fit checks + what instagram won't take 🖤\n"
        f"{fv_link}"
    )

    # 5. Put updated profile record
    put_data = json.dumps({
        "repo": did,
        "collection": "app.bsky.actor.profile",
        "rkey": "self",
        "record": val,
    }).encode("utf-8")

    put_req = urllib.request.Request(
        f"{XRPC_BASE}/com.atproto.repo.putRecord",
        data=put_data,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {jwt}"},
        method="POST",
    )
    with urllib.request.urlopen(put_req) as r:
        res = json.loads(r.read().decode("utf-8"))
        print(f"  Profile updated successfully! Record CID: {res.get('cid')}")

    print("\n=== Bluesky Profile Successfully Updated with Banner & Fanvue Bio Link ===")

if __name__ == "__main__":
    main()
