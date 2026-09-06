#!/usr/bin/env python3
"""
fanvue_api.py — Thin, verified client for the Fanvue API.
Modeled on kie_api.py: pinned constants, explicit budget cap, sliding-window
rate limiting, dry-run on writes, and append-only ledger logging.

Documentation & Compliance facts (5 Sep 2026):
  - Base URL: https://api.fanvue.com
  - Auth header: X-Fanvue-API-Key (also sends Authorization: Bearer <key>)
  - Version header: X-Fanvue-API-Version (YYYY-MM-DD)
  - Rate limit: 100 requests per 60 seconds per API key (sliding window)
  - Only one active API key per user at a time
"""
from __future__ import annotations
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import argparse
import collections
import datetime
import json
import os
import pathlib
import threading
import time
from typing import Any, Dict, Optional

import requests

ROOT = pathlib.Path(__file__).resolve().parent
# If executed inside growth/, parent is the project root; otherwise ROOT is project root
PROJECT_ROOT = ROOT if (ROOT / "personas").exists() else ROOT.parent
GROWTH_DIR = ROOT if ROOT.name == "growth" else PROJECT_ROOT / "growth"

API_BASE = "https://api.fanvue.com"

# BUMPING API_VERSION IS A DELIBERATE ACT, NEVER A DEFAULT.
# Fanvue enforces date-based API versioning (YYYY-MM-DD).
# Verified supported version from Fanvue developer docs is 2025-06-26.
API_VERSION = "2025-06-26"

RATE_LIMIT_CALLS = 100
RATE_LIMIT_WINDOW_SECS = 60.0

PLACEHOLDER_KEYS = {
    "", "your_key_here", "placeholder", "xxx", "none", "null", "<fanvue_api_key>"
}


def load_key(key_dir: Optional[pathlib.Path] = None) -> str:
    """
    Finds the Fanvue API key or OAuth access token and returns it. Never prints the key.
    Refuses on placeholder or empty values.
    """
    # 0. Check for environment variable (e.g. GitHub Secrets in automated cloud actions)
    env_key = os.environ.get("FANVUE_API_KEY")
    if env_key and env_key.strip() and env_key.lower() not in PLACEHOLDER_KEYS:
        return env_key.strip()

    # 1. Check for active OAuth 2.0 token from fanvue_tokens.json
    try:
        try:
            import fanvue_auth
        except ImportError:
            from growth import fanvue_auth
        tok_file = (key_dir or GROWTH_DIR) / "fanvue_tokens.json"
        if tok_file.is_file() or (ROOT / "fanvue_tokens.json").is_file():
            return fanvue_auth.token()
    except Exception:
        pass

    candidates = [
        (key_dir or GROWTH_DIR) / "fanvue_key.txt",
        PROJECT_ROOT / "growth" / "fanvue_key.txt",
        ROOT / "fanvue_key.txt",
    ]
    key_file = None
    for c in candidates:
        if c.is_file():
            key_file = c
            break

    if not key_file:
        sys.exit(
            "  ! Fanvue API key or OAuth token not found.\n"
            f"    Expected location: {(GROWTH_DIR / 'fanvue_tokens.json').resolve()}\n"
            "    Run: python growth/fanvue_auth.py --start to authenticate."
        )

    content = key_file.read_text(encoding="utf-8-sig").strip()
    for line in content.splitlines():
        line = line.strip().strip('"').strip("'")
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            if "KEY" in k.upper():
                val = v.strip().strip('"').strip("'")
                if val.lower() in PLACEHOLDER_KEYS:
                    sys.exit(f"  ! Placeholder key detected in {key_file.name}. Refusing to run.")
                return val
        else:
            if line.lower() in PLACEHOLDER_KEYS:
                sys.exit(f"  ! Placeholder key detected in {key_file.name}. Refusing to run.")
            return line

    sys.exit(f"  ! No valid key found in {key_file.name}. File is empty or commented out.")


def log_ledger(action: str, target: str, note: str, surface: str = "fanvue") -> None:
    """
    Append an audit record to growth/ledger.jsonl:
    {ts, surface, action, target, note}
    """
    GROWTH_DIR.mkdir(parents=True, exist_ok=True)
    ledger_path = GROWTH_DIR / "ledger.jsonl"
    entry = {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "surface": surface,
        "action": action,
        "target": target,
        "note": note,
    }
    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


class SlidingWindowRateLimiter:
    """
    Thread-safe sliding window rate limiter enforcing max_calls per window_seconds.
    Guarantees we never exceed Fanvue's 100 calls / 60s hard ceiling.
    """
    def __init__(self, max_calls: int = 100, window_secs: float = 60.0):
        self.max_calls = max_calls
        self.window_secs = window_secs
        self.timestamps: collections.deque[float] = collections.deque()
        self.lock = threading.Lock()

    def acquire(self) -> None:
        with self.lock:
            now = time.time()
            # Prune timestamps outside window
            while self.timestamps and self.timestamps[0] <= now - self.window_secs:
                self.timestamps.popleft()

            if len(self.timestamps) >= self.max_calls:
                sleep_duration = self.window_secs - (now - self.timestamps[0]) + 0.05
                if sleep_duration > 0:
                    time.sleep(sleep_duration)
                now = time.time()
                while self.timestamps and self.timestamps[0] <= now - self.window_secs:
                    self.timestamps.popleft()

            self.timestamps.append(time.time())


class FanvueClient:
    def __init__(self, api_key: str, timeout: float = 30.0):
        self.key = api_key
        self.timeout = timeout
        self.limiter = SlidingWindowRateLimiter(RATE_LIMIT_CALLS, RATE_LIMIT_WINDOW_SECS)
        self.session = requests.Session()
        self.session.headers.update({
            "X-Fanvue-API-Key": self.key,
            "Authorization": f"Bearer {self.key}",
            "X-Fanvue-API-Version": API_VERSION,
            "Content-Type": "application/json",
            "User-Agent": "SeoyeonGrowth/1.0",
        })

    def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        dry_run: bool = False,
        raise_for_status: bool = True,
    ) -> Dict[str, Any]:
        """
        Executes an API request with rate limiting and dry-run protection on writes.
        """
        method = method.upper()
        url = f"{API_BASE.rstrip('/')}/{path.lstrip('/')}"
        is_write = method in ("POST", "PUT", "PATCH", "DELETE")

        if is_write and dry_run:
            print(f"  [DRY-RUN] {method} {url}")
            if params:
                print(f"            params: {json.dumps(params, ensure_ascii=False)}")
            if data:
                print(f"            body:   {json.dumps(data, ensure_ascii=False)}")
            return {"dry_run": True, "status": "simulated"}

        self.limiter.acquire()
        try:
            resp = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data if data else None,
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            sys.exit(f"  ! Network error contacting Fanvue API: {e}")

        if not resp.ok:
            if not raise_for_status:
                return {"_status_code": resp.status_code, "_error": resp.text}
            if resp.status_code == 401:
                sys.exit(
                    "  ! HTTP 401 Unauthorized: The Fanvue API key was rejected by the server.\n"
                    "    Check that the key in growth/fanvue_key.txt is active and not revoked.\n"
                    "    Do not retry in a loop."
                )
            if resp.status_code == 403:
                sys.exit(
                    f"  ! HTTP 403 Forbidden on {path}: {resp.text[:300]}\n"
                    "    Required OAuth scope or KYC level may be missing."
                )
            if resp.status_code == 429:
                sys.exit("  ! HTTP 429 Too Many Requests: Rate limit reached on server.")
            sys.exit(f"  ! HTTP {resp.status_code} on {path}: {resp.text[:400]}")

        try:
            return resp.json() if resp.text else {}
        except json.JSONDecodeError:
            return {"raw": resp.text}

    def whoami(self) -> Dict[str, Any]:
        """
        Read-only inspection of the authenticated creator account.
        Queries /users/me and /insights / /creators/me to retrieve handle,
        subscriber count, and balance.
        """
        print("  Querying Fanvue creator identity (/users/me)...")
        user_data = self.request("GET", "/users/me")

        handle = (
            user_data.get("handle")
            or user_data.get("username")
            or user_data.get("data", {}).get("handle")
            or user_data.get("data", {}).get("username")
            or "unknown"
        )
        display_name = user_data.get("name") or user_data.get("data", {}).get("name") or ""
        user_id = user_data.get("id") or user_data.get("uuid") or user_data.get("data", {}).get("id")

        # Inquire stats/insights if available
        subs_count = (
            user_data.get("subscriberCount")
            or user_data.get("subscribers_count")
            or user_data.get("data", {}).get("subscriberCount")
            or 0
        )
        balance = (
            user_data.get("balance")
            or user_data.get("walletBalance")
            or user_data.get("data", {}).get("balance")
            or 0.0
        )

        # If insights endpoint is supported, attempt read
        try:
            insights = self.request("GET", "/insights")
            if isinstance(insights, dict):
                subs_count = insights.get("subscriberCount", subs_count)
                balance = insights.get("currentBalance", balance)
        except SystemExit:
            pass

        print("\n  ========================================")
        print("  FANVUE CREATOR IDENTITY")
        print("  ========================================")
        print(f"  Handle:       @{handle}")
        if display_name:
            print(f"  Display Name: {display_name}")
        if user_id:
            print(f"  User ID:      {user_id}")
        print(f"  Subscribers:  {subs_count}")
        print(f"  Balance:      €{balance:.2f}" if isinstance(balance, (int, float)) else f"  Balance:      {balance}")
        print("  Status:       ACTIVE (API connection verified)")
        print("  ========================================\n")

        return user_data

    def make_links(self, dry_run: bool = False) -> Dict[str, str]:
        """
        Creates or discovers one tracking link per required traffic source:
        instagram, x, bluesky, threads, reddit, youtube.
        Writes all 6 to growth/links.json.
        """
        sources = {
            "instagram": "instagram",
            "x": "twitter",
            "bluesky": "other",
            "threads": "other",
            "reddit": "reddit",
            "youtube": "youtube",
        }
        links: Dict[str, str] = {}

        print("  Checking existing tracking links on Fanvue (GET /tracking-links)...")
        existing = self.request("GET", "/tracking-links")
        items = existing.get("data", []) if isinstance(existing, dict) else []

        existing_map = {}
        for item in items:
            name = (item.get("name") or "").lower().strip()
            code = item.get("linkUrl") or item.get("code")
            url = f"https://www.fanvue.com/syeon.hn?c={code}" if code else item.get("url")
            if name and url:
                existing_map[name] = url

        for s, platform in sources.items():
            if s in existing_map:
                links[s] = existing_map[s]
                print(f"    found existing: {s:10} -> {links[s]}")
            else:
                if dry_run:
                    simulated = f"https://www.fanvue.com/syeon.hn?c={s}"
                    links[s] = simulated
                    print(f"    [DRY-RUN] Would create: {s:10} (platform={platform}) -> {simulated}")
                else:
                    print(f"    creating: {s} (platform={platform})...")
                    res = self.request(
                        "POST",
                        "/tracking-links",
                        data={"name": s, "externalSocialPlatform": platform},
                    )
                    code = res.get("linkUrl") or res.get("code")
                    created_url = f"https://www.fanvue.com/syeon.hn?c={code}" if code else res.get("url")
                    links[s] = created_url
                    log_ledger("create_tracking_link", s, f"Created tracking link {created_url}")
                    print(f"    created:        {s:10} -> {created_url}")

        # Save to links.json
        GROWTH_DIR.mkdir(parents=True, exist_ok=True)
        links_file = GROWTH_DIR / "links.json"
        links_file.write_text(json.dumps(links, indent=2), encoding="utf-8")
        print(f"\n  Saved {len(links)} links to {links_file.resolve()}")

        print("\n  ========================================")
        print("  FANVUE TRACKING LINKS")
        print("  ========================================")
        for s in sources:
            print(f"  {s:10} : {links.get(s, 'NOT CREATED')}")
        print("  ========================================\n")
        return links

    def get_subscribers(self) -> list[Dict[str, Any]]:
        """
        Fetches all current subscribers from smart list
        GET /v1/chats/lists/smart/subscribers with cursor pagination.
        """
        subscribers: list[Dict[str, Any]] = []
        cursor: Optional[str] = None
        while True:
            params: Dict[str, Any] = {"size": 50}
            if cursor:
                params["cursor"] = cursor
            res = self.request("GET", "/v1/chats/lists/smart/subscribers", params=params)
            items = res.get("data", []) if isinstance(res, dict) else []
            subscribers.extend(items)
            cursor = res.get("nextCursor")
            if not cursor:
                break
        return subscribers

    def send_dm(self, user_uuid: str, text: str, dry_run: bool = False) -> Dict[str, Any]:
        """
        Sends a direct message to a user.
        Ensures chat exists first (POST /v1/chats), then posts to /v1/chats/{userUuid}/message.
        """
        if dry_run:
            print(f"  [DRY-RUN] Would send DM to user {user_uuid}:")
            print(f"            text: {json.dumps(text, ensure_ascii=False)}")
            return {"dry_run": True, "status": "simulated"}

        # Ensure chat exists
        self.request("POST", "/v1/chats", data={"userUuid": user_uuid}, raise_for_status=False)
        # Send message
        return self.request("POST", f"/v1/chats/{user_uuid}/message", data={"text": text})



    def upload_media(
        self,
        file_path: pathlib.Path,
        name: str = "",
        dry_run: bool = False,
    ) -> Optional[str]:
        """
        Uploads a media file (image/video) to Fanvue via the official multipart S3 flow:
          1. POST /media/uploads -> returns uploadId, mediaUuid, partSize
          2. For each part: GET /media/uploads/{uploadId}/parts/{partNumber}/url
          3. PUT chunk to S3 presigned URL, capture ETag
          4. PATCH /media/uploads/{uploadId} with {"parts": [{"PartNumber": n, "ETag": ...}]}
        Returns mediaUuid.
        """
        p = pathlib.Path(file_path).resolve()
        if not p.is_file():
            sys.exit(f"  ! Media file not found: {p}")

        file_size = p.stat().st_size
        filename = p.name
        name = name or p.stem
        is_video = p.suffix.lower() in (".mp4", ".mov", ".webm")
        media_type = "video" if is_video else "image"

        if dry_run:
            print(f"  [DRY-RUN] Fanvue Media Upload: {filename} ({file_size // 1024} KB, {media_type})")
            return "simulated-media-uuid"

        print(f"  [1/3] Initializing upload session for {filename} ({file_size // 1024} KB)...")
        session_res = self.request("POST", "/media/uploads", data={
            "name": name,
            "filename": filename,
            "mediaType": media_type,
            "sizeBytes": file_size,
        })

        media_uuid = session_res.get("mediaUuid")
        upload_id = session_res.get("uploadId")
        part_size = session_res.get("partSize", 6291456)
        total_parts = session_res.get("totalParts") or ((file_size + part_size - 1) // part_size)

        if not upload_id or not media_uuid:
            raise RuntimeError(f"Failed to initialize upload session: {session_res}")

        print(f"  [2/3] Uploading {total_parts} part(s) to S3...")
        completed_parts = []
        with open(p, "rb") as f:
            for part_num in range(1, total_parts + 1):
                chunk = f.read(part_size)
                part_res = self.request("GET", f"/media/uploads/{upload_id}/parts/{part_num}/url")
                upload_url = part_res.get("raw") if isinstance(part_res, dict) and "raw" in part_res else str(part_res).strip('"')
                if not upload_url or not upload_url.startswith("http"):
                    raise RuntimeError(f"Invalid part URL for part {part_num}: {part_res}")

                s3_resp = requests.put(upload_url, data=chunk, timeout=180)
                if not s3_resp.ok:
                    raise RuntimeError(f"S3 PUT chunk failed: {s3_resp.status_code} {s3_resp.text[:200]}")
                etag = s3_resp.headers.get("ETag", "").strip('"')
                if not etag:
                    raise RuntimeError(f"S3 did not return ETag for part {part_num}")
                completed_parts.append({"PartNumber": part_num, "ETag": etag})
                print(f"        Part {part_num}/{total_parts} uploaded (ETag: {etag[:10]}...)")

        print(f"  [3/3] Finalizing upload session on Fanvue...")
        self.request("PATCH", f"/media/uploads/{upload_id}", data={"parts": completed_parts})
        log_ledger("media_upload", "fanvue", f"Uploaded media {filename} -> {media_uuid}")
        print(f"  Media ready! UUID: {media_uuid}")
        return media_uuid

    def create_post(
        self,
        text: str,
        media_uuids: Optional[list[str]] = None,
        audience: str = "subscribers",
        price_cents: Optional[int] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Creates a new post on Fanvue (POST /posts).
        Audience can be 'subscribers' or 'followers-and-subscribers'.
        If price_cents is set (>=300), post is Pay-Per-View.
        """
        payload: Dict[str, Any] = {
            "text": text,
            "audience": audience,
        }
        if media_uuids:
            payload["mediaUuids"] = media_uuids
        if price_cents:
            payload["price"] = price_cents

        if dry_run:
            print(f"  [DRY-RUN] POST /posts")
            print(f"            audience: {audience}")
            if price_cents:
                print(f"            price:    €{price_cents / 100:.2f}")
            print(f"            media:    {media_uuids or 'none'}")
            print(f"            text:     {repr(text)}")
            return {"dry_run": True, "status": "simulated"}

        print(f"  Publishing post to Fanvue ({audience})...")
        res = self.request("POST", "/posts", data=payload)
        post_uuid = res.get("id") or res.get("uuid") or res.get("data", {}).get("id") or "ok"
        log_ledger("create_post", "fanvue", f"Created post {post_uuid} ({audience})")
        print(f"  Post published! ID: {post_uuid}")
        return res

    def set_subscription_price(
        self,
        price_cents: int,
        force_opt_in: bool = False,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Updates the monthly subscription price in USD cents (between 399 and 10000).
        """
        if not 399 <= price_cents <= 10000:
            raise ValueError(f"Price {price_cents} cents must be between 399 ($3.99) and 10000 ($100.00)")
        payload = {"subscriptionPrice": price_cents, "forceOptIn": force_opt_in}
        if dry_run:
            print(f"  [DRY-RUN] PATCH /users/me/subscription-price: ${price_cents/100:.2f}")
            return {"dry_run": True, "status": "simulated"}
        print(f"  Setting subscription price to ${price_cents/100:.2f} ({price_cents} cents)...")
        res = self.request("PATCH", "/users/me/subscription-price", data=payload)
        log_ledger("set_subscription_price", "fanvue", f"Set subscription price to {price_cents} cents")
        return res

    def create_promotion(
        self,
        discount_percent: int,
        available_to_group: str = "new_subscribers",
        max_usages: Optional[int] = None,
        message: str = "",
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Creates a promotional discount (1-100%) for subscribers.
        """
        payload: Dict[str, Any] = {
            "discountPercent": discount_percent,
            "availableToGroup": available_to_group,
        }
        if max_usages:
            payload["maxUsages"] = max_usages
        if message:
            payload["message"] = message
        if dry_run:
            print(f"  [DRY-RUN] POST /promotions: {discount_percent}% off for {available_to_group}")
            return {"dry_run": True, "status": "simulated"}
        print(f"  Creating promotion: {discount_percent}% discount for {available_to_group}...")
        res = self.request("POST", "/promotions", data=payload)
        log_ledger("create_promotion", "fanvue", f"Created {discount_percent}% promo for {available_to_group}")
        return res

    def get_automated_messages(self) -> list[Dict[str, Any]]:
        """
        Lists all 7 automated message trigger configurations.
        """
        res = self.request("GET", "/chats/automated-messages")
        return res.get("data", []) if isinstance(res, dict) else []

    def set_automated_message(
        self,
        trigger: str,
        text: str,
        price: Optional[int] = None,
        media_uuids: Optional[list[str]] = None,
        media_preview_uuid: Optional[str] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Sets or updates an automated message trigger:
        new_subscriber, new_follower, subscription_canceled, re_subscribed, renewed, new_purchase, first_message_reply.
        """
        valid_triggers = [
            "new_subscriber", "new_follower", "subscription_canceled",
            "re_subscribed", "renewed", "new_purchase", "first_message_reply"
        ]
        if trigger not in valid_triggers:
            raise ValueError(f"Invalid trigger: {trigger}. Valid: {valid_triggers}")

        payload: Dict[str, Any] = {"text": text}
        if price is not None:
            payload["price"] = price
        if media_uuids:
            payload["mediaUuids"] = media_uuids
        if media_preview_uuid:
            payload["mediaPreviewUuid"] = media_preview_uuid

        if dry_run:
            print(f"  [DRY-RUN] PUT /chats/automated-messages/{trigger}:")
            print(f"            text: {repr(text)}")
            if price:
                print(f"            price: €{price/100:.2f}")
            if media_uuids:
                print(f"            media: {media_uuids}")
            return {"dry_run": True, "status": "simulated"}

        print(f"  Configuring automated message for '{trigger}'...")
        res = self.request("PUT", f"/chats/automated-messages/{trigger}", data=payload)
        log_ledger("set_automated_message", trigger, f"Configured automated message for {trigger}")
        print(f"  Automated message '{trigger}' configured successfully!")
        return res


def main() -> int:
    ap = argparse.ArgumentParser(description="Fanvue API client for persona operations.")
    ap.add_argument("--whoami", action="store_true", help="Read-only check of authenticated creator account")
    ap.add_argument("--make-links", action="store_true", help="Create or fetch tracking links for all 6 traffic sources")
    ap.add_argument("--post", action="store_true", help="Create a post on Fanvue")
    ap.add_argument("--text", type=str, help="Text caption for post")
    ap.add_argument("--image", type=str, help="Path to image media file to upload and attach")
    ap.add_argument("--audience", choices=["subscribers", "followers-and-subscribers"], default="subscribers", help="Target audience")
    ap.add_argument("--price-cents", type=int, default=None, help="PPV unlock price in cents (e.g. 500 = €5.00)")
    ap.add_argument("--list-automated", action="store_true", help="List all 7 automated message triggers")
    ap.add_argument("--setup-automated", action="store_true", help="Configure recommended in-character automated message triggers")
    ap.add_argument("--set-price", type=int, default=None, help="Set monthly subscription price in cents (e.g. 999 = $9.99)")
    ap.add_argument("--create-promo", type=int, default=None, help="Create a first-month discount promo percentage (e.g. 30 for 30% off)")
    ap.add_argument("--promo-group", choices=["new_subscribers", "expired_subscribers", "all", "followers"], default="new_subscribers", help="Target group for promo")
    ap.add_argument("--dry-run", action="store_true", help="Simulate write calls without modifying remote state")
    args = ap.parse_args()

    if not (args.whoami or args.make_links or args.post or args.list_automated or args.setup_automated or args.set_price or args.create_promo):
        ap.print_help()
        return 1

    key = load_key()
    client = FanvueClient(api_key=key)

    if args.whoami:
        client.whoami()

    if args.make_links:
        client.make_links(dry_run=args.dry_run)

    if args.set_price:
        client.set_subscription_price(price_cents=args.set_price, dry_run=args.dry_run)

    if args.create_promo:
        client.create_promotion(
            discount_percent=args.create_promo,
            available_to_group=args.promo_group,
            max_usages=100,
            message="welcome offer 🖤",
            dry_run=args.dry_run,
        )

    if args.list_automated:
        msgs = client.get_automated_messages()
        print("\n  ========================================")
        print("  FANVUE AUTOMATED MESSAGES")
        print("  ========================================")
        for m in msgs:
            trig = m.get("trigger")
            en = "ENABLED" if m.get("enabled") else "DISABLED"
            pr = f"€{m.get('price')/100:.2f}" if m.get("price") else "FREE"
            txt = (m.get("text") or "").replace("\n", " ")[:60]
            print(f"  {trig:<22} [{en:<8}] ({pr}) {txt}")
        print("  ========================================\n")

    if args.setup_automated:
        # Default in-character triggers
        templates = {
            "new_subscriber": (
                "hey, thank you for subscribing. i'm usually either at the studio in seongsu or drinking cold brew at my desk in my flat. i post the quieter, more personal side of things here that doesn't go on instagram.\n\nwhat time is it where you are right now?"
            ),
            "new_follower": (
                "hey, thanks for following 🤍 i'm seoyeon, teaching pilates in seongsu and sharing my daily life here in seoul. my main public feed is chill, but my subscriber feed has the more candid, private moments that stay off instagram. feel free to say hi anytime ✨"
            ),
            "renewed": (
                "thank you so much for staying with me another month 🖤 it really means a lot having you in my private circle. more quiet mornings, studio sets, and unreleased moments coming your way xx"
            ),
            "subscription_canceled": (
                "hey, saw you canceled... no worries at all, just wanted to say thank you for being here with me. hope to see you around again sometime 🤍"
            ),
            "first_message_reply": (
                "hey! saw your note ☕ i'm probably in the studio or running around seongsu right now, but i check my messages as soon as i'm back at my desk. talk soon!"
            ),
        }
        for trig, text in templates.items():
            client.set_automated_message(trigger=trig, text=text, price=0, dry_run=args.dry_run)

    if args.post:
        media_uuids = []
        if args.image:
            img_path = pathlib.Path(args.image)
            if not img_path.is_absolute():
                img_path = (PROJECT_ROOT / img_path if (PROJECT_ROOT / img_path).exists() else img_path).resolve()
            muuid = client.upload_media(img_path, dry_run=args.dry_run)
            if muuid:
                media_uuids.append(muuid)
        post_text = args.text or ""
        client.create_post(
            text=post_text,
            media_uuids=media_uuids if media_uuids else None,
            audience=args.audience,
            price_cents=args.price_cents,
            dry_run=args.dry_run,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
