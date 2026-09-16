#!/usr/bin/env python3
"""
growth/bsky_reply_worker.py — Lyra's Autonomous Inbound Reply & Mention Worker.

Monitors incoming comments, mentions, and replies to @syeonhn.bsky.social.
Drafts and publishes authentic, dry, lowercase conversational replies in Seo-yeon's canon voice:
  - Doubles thread engagement velocity for algorithmic discovery (What's Hot Classic / Discover feeds).
  - Deepens parasocial loyalty, driving traffic to the threaded Fanvue link (c=fv-4).
  - Enforces strict invariants: zero promotion, dry understatement, lowercase, full stops, no exclamation marks.
  - Multi-tier LLM engine: DeepSeek Flash -> Gemini 3.6 Flash -> Offline canon fallback.

Usage:
  python growth/bsky_reply_worker.py --auto
  python growth/bsky_reply_worker.py --status
  python growth/bsky_reply_worker.py --dry-run
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Set, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

GROWTH_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = GROWTH_DIR.parent
CRED_FILE = GROWTH_DIR / "bsky_credentials.json"
LEDGER_FILE = GROWTH_DIR / "ledger.jsonl"
REPLIED_LOG = GROWTH_DIR / "bsky_replied_notifications.jsonl"
XRPC_BASE = "https://bsky.social/xrpc"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

DEFAULT_OPENROUTER_MODEL = "deepseek/deepseek-v4-flash"

# Negative filters: skip spam, crypto, bots, vulgar harassment
NEGATIVE_KEYWORDS = [
    "crypto", "bitcoin", "btc", "eth", "nft", "airdrop", "token",
    "whatsapp", "telegram", "sugar daddy", "cashapp", "paypal",
    "f4f", "followback", "dm me", "check out my", "giveaway"
]

FORBIDDEN_OUTPUT_TERMS = [
    "fanvue", "onlyfans", "patreon", "exclusive", "unlock", "private feed",
    "link in bio", "links in bio", "c=fv", "subscribe", "discount", "promo",
    "ppv", "tier", "!"
]

# Offline fallback banks for inbound replies
FALLBACK_REPLIES_KO = [
    "맞아요. 저도 그 생각 하면서 하루 보냈네요.",
    "역시 다들 비슷하게 느끼시는 것 같아요.",
    "듣고 보니 진짜 그러네요. 커피 한 잔 더 내려야겠어요.",
    "생각지도 못했는데 덕분에 조금 웃었네요.",
    "오늘따라 날씨도 그렇고 여러 가지로 타이밍이 묘하네요.",
]

FALLBACK_REPLIES_EN = [
    "honestly pretty much how my afternoon went too.",
    "glad it is not just me who noticed that.",
    "staring at my screen right now thinking the exact same thing.",
    "timing on that was strangely accurate.",
    "making roasted barley tea right now and hoping tomorrow is quieter.",
]

MAX_REPLIES_PER_TICK = 3
MAX_REPLIES_PER_DAY = 10


def load_env_variables() -> None:
    for p in [PROJECT_ROOT / ".env", GROWTH_DIR / ".env", pathlib.Path(".env")]:
        if p.exists():
            for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip("'\"")
                    if k and k not in os.environ:
                        os.environ[k] = v


load_env_variables()


def get_credentials() -> Tuple[str, str]:
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
        sys.exit("  ! Error: BSKY_HANDLE or BSKY_APP_PASSWORD not set.")

    if "." not in handle:
        handle = f"{handle}.bsky.social"

    return handle.strip(), app_pw.strip()


def get_openrouter_key() -> Optional[str]:
    return os.environ.get("OPENROUTER_API_KEY")


def get_gemini_key() -> Optional[str]:
    return os.environ.get("GEMINI_API_KEY")


def create_session(handle: str, app_pw: str) -> Tuple[str, str]:
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


def xrpc_get(endpoint: str, params: Dict[str, Any], jwt: str) -> Dict[str, Any]:
    qs = urllib.parse.urlencode(params)
    url = f"{XRPC_BASE}/{endpoint}?{qs}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {jwt}"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print(f"  [XRPC GET Error] {endpoint}: {e}")
        return {}


def load_replied_ids() -> Set[str]:
    replied: Set[str] = set()
    if not REPLIED_LOG.exists():
        return replied
    for line in REPLIED_LOG.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
            uri = entry.get("reply_to_uri") or entry.get("notification_uri")
            if uri:
                replied.add(uri)
        except Exception:
            continue
    return replied


def append_replied_log(entry: Dict[str, Any]) -> None:
    GROWTH_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPLIED_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def log_ledger(action: str, target: str, note: str) -> None:
    GROWTH_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
        "surface": "bluesky",
        "action": action,
        "target": target,
        "note": note
    }
    with open(LEDGER_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def clean_and_validate_reply(text: str) -> Tuple[bool, str]:
    if not text or not text.strip():
        return False, "Empty reply text."

    cleaned = text.strip()
    if (cleaned.startswith('"') and cleaned.endswith('"')) or (cleaned.startswith("'") and cleaned.endswith("'")):
        cleaned = cleaned[1:-1].strip()

    # Seo-yeon never uses exclamation marks
    if "!" in cleaned:
        cleaned = cleaned.replace("!", ".")

    cleaned_lower = cleaned.lower()
    for term in FORBIDDEN_OUTPUT_TERMS:
        if term != "!" and term in cleaned_lower:
            return False, f"Forbidden term '{term}' in output."

    if len(cleaned) > 280:
        return False, f"Reply too long ({len(cleaned)} chars)."

    return True, cleaned


def draft_reply_llm(user_handle: str, user_text: str, is_korean: bool) -> Tuple[str, str]:
    """Drafts an in-character reply using DeepSeek -> Gemini -> Offline Fallback."""
    prompt = (
        "You are Han Seo-yeon (한서연), a 26-year-old Korean pilates instructor and freelance visual designer living alone in Seongsu-dong, Seoul.\n"
        "Your voice: dry, observant, understated, lowercase, quiet humor, full stops only. ZERO exclamation marks (!).\n"
        "ZERO marketing, ZERO promotion, NEVER mention Fanvue, links, subscriptions, or sales.\n"
        f"A user (@{user_handle}) left this comment on your Bluesky post:\n"
        f'"{user_text}"\n\n'
        f"Write a short, natural, in-character conversational reply (1-2 sentences max). "
        f"{'Write in natural casual Korean (반말 or 부드러운 해요체, full stops, no exclamation marks).' if is_korean else 'Write in natural English (all lowercase, no exclamation marks).'}"
    )

    # 1. Primary: DeepSeek Flash via OpenRouter
    or_key = get_openrouter_key()
    if or_key:
        payload = {
            "model": DEFAULT_OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": "You are Han Seo-yeon. Respond strictly in character. Never use exclamation marks. Output only the reply text."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 120
        }
        req = urllib.request.Request(
            OPENROUTER_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {or_key}"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                res = json.loads(r.read().decode("utf-8"))
                ans = res["choices"][0]["message"]["content"].strip()
                ok, clean = clean_and_validate_reply(ans)
                if ok:
                    return clean, "deepseek/deepseek-v4-flash"
        except Exception as e:
            print(f"  [LLM Notice] OpenRouter draft failed: {e}. Falling back to Gemini...")

    # 2. Secondary: Gemini 3.6 Flash
    gem_key = get_gemini_key()
    if gem_key:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gem_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 100}
        }
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                res = json.loads(r.read().decode("utf-8"))
                candidates = res.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        ok, clean = clean_and_validate_reply(parts[0].get("text", ""))
                        if ok:
                            return clean, "gemini-2.5-flash"
        except Exception as e:
            print(f"  [LLM Notice] Gemini draft failed: {e}. Falling back to canon bank...")

    # 3. Tertiary: Offline canon fallback
    import random
    bank = FALLBACK_REPLIES_KO if is_korean else FALLBACK_REPLIES_EN
    return random.choice(bank), "offline-canon-fallback"


def post_reply(
    reply_text: str,
    parent_uri: str,
    parent_cid: str,
    root_uri: str,
    root_cid: str,
    my_did: str,
    jwt: str,
    dry_run: bool = False
) -> Tuple[bool, str]:
    if dry_run:
        print(f"  [DRY-RUN] Would post reply: \"{reply_text}\" to {parent_uri}")
        return True, "simulated-uri"

    now_iso = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    record = {
        "$type": "app.bsky.feed.post",
        "text": reply_text,
        "createdAt": now_iso,
        "langs": ["ko", "en"],
        "reply": {
            "root": {"uri": root_uri, "cid": root_cid},
            "parent": {"uri": parent_uri, "cid": parent_cid}
        }
    }

    payload = json.dumps({
        "repo": my_did,
        "collection": "app.bsky.feed.post",
        "record": record
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{XRPC_BASE}/com.atproto.repo.createRecord",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {jwt}"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            res = json.loads(r.read().decode("utf-8"))
            return True, res.get("uri", "")
    except Exception as e:
        print(f"  ! Error posting reply: {e}")
        return False, str(e)


def update_seen(jwt: str) -> None:
    now_iso = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    payload = json.dumps({"seenAt": now_iso}).encode("utf-8")
    req = urllib.request.Request(
        f"{XRPC_BASE}/app.bsky.notification.updateSeen",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {jwt}"},
        method="POST"
    )
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception:
        pass


def run_reply_worker(dry_run: bool = False) -> int:
    print("============================================================")
    print("  BLUESKY INBOUND REPLY & CONVERSATION WORKER")
    print(f"  Mode: {'[DRY-RUN] Simulation' if dry_run else '[LIVE EXECUTION]'}")
    print("============================================================")

    handle, app_pw = get_credentials()
    jwt, my_did = create_session(handle, app_pw)

    # 1. Check daily pacing
    replied_ids = load_replied_ids()
    today_utc = dt.datetime.now(dt.timezone.utc).date()
    replies_today = 0
    if REPLIED_LOG.exists():
        for line in REPLIED_LOG.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
                if dt.datetime.fromisoformat(e["replied_at"]).date() == today_utc:
                    replies_today += 1
            except Exception:
                continue

    print(f"  Replies executed today: {replies_today}/{MAX_REPLIES_PER_DAY}")
    if replies_today >= MAX_REPLIES_PER_DAY:
        print("  [Notice] Daily reply limit reached. Protecting pacing.")
        return 0

    quota = min(MAX_REPLIES_PER_TICK, MAX_REPLIES_PER_DAY - replies_today)

    # 2. Fetch notifications
    print("  Polling notifications (reasons: reply, mention)...")
    res = xrpc_get("app.bsky.notification.listNotifications", {"limit": 30}, jwt)
    notifications = res.get("notifications", [])
    print(f"  Total notifications received: {len(notifications)}")

    reply_candidates: List[Dict[str, Any]] = []
    for notif in notifications:
        reason = notif.get("reason")
        if reason not in ("reply", "mention", "quote"):
            continue

        author = notif.get("author", {})
        if author.get("did") == my_did:
            continue  # Don't reply to self

        uri = notif.get("uri", "")
        if uri in replied_ids:
            continue

        record = notif.get("record", {})
        text = record.get("text", "").strip()
        if not text:
            continue

        # Check negative spam keywords
        if any(neg in text.lower() for neg in NEGATIVE_KEYWORDS):
            continue

        reply_candidates.append(notif)
        if len(reply_candidates) >= quota:
            break

    print(f"  Pending quality reply opportunities: {len(reply_candidates)}")
    if not reply_candidates:
        print("  No new inbound interactions requiring replies.")
        if not dry_run:
            update_seen(jwt)
        return 0

    replied_count = 0
    for notif in reply_candidates:
        author = notif.get("author", {})
        author_handle = author.get("handle", "user")
        record = notif.get("record", {})
        user_text = record.get("text", "")
        target_uri = notif.get("uri", "")
        target_cid = notif.get("cid", "")

        # Resolve root post
        reply_meta = record.get("reply", {})
        if reply_meta and "root" in reply_meta:
            root_uri = reply_meta["root"].get("uri", target_uri)
            root_cid = reply_meta["root"].get("cid", target_cid)
        else:
            root_uri = target_uri
            root_cid = target_cid

        is_korean = bool(re.search(r"[\uac00-\ud7a3]", user_text))
        print(f"\n  -> Comment from @{author_handle}: \"{user_text}\"")

        # Draft reply
        draft, model_used = draft_reply_llm(author_handle, user_text, is_korean)
        print(f"     Draft ({model_used}): \"{draft}\"")

        ok, published_uri = post_reply(
            reply_text=draft,
            parent_uri=target_uri,
            parent_cid=target_cid,
            root_uri=root_uri,
            root_cid=root_cid,
            my_did=my_did,
            jwt=jwt,
            dry_run=dry_run
        )

        if ok:
            replied_count += 1
            now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
            log_entry = {
                "reply_to_uri": target_uri,
                "reply_to_handle": author_handle,
                "user_text": user_text,
                "reply_text": draft,
                "published_uri": published_uri,
                "model_used": model_used,
                "replied_at": now_iso
            }
            if not dry_run:
                append_replied_log(log_entry)
                log_ledger("inbound_reply", f"@{author_handle}", f"Replied to comment on {target_uri}")
                print(f"     [SUCCESS] Reply published: {published_uri}")
            time.sleep(2.0)

    if not dry_run:
        update_seen(jwt)

    print("\n============================================================")
    print(f"  Inbound Reply Pass Complete. Replies Published: {replied_count}")
    print("============================================================\n")
    return replied_count


def show_status() -> int:
    replied_ids = load_replied_ids()
    today_utc = dt.datetime.now(dt.timezone.utc).date()
    replies_today = 0
    if REPLIED_LOG.exists():
        for line in REPLIED_LOG.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
                if dt.datetime.fromisoformat(e["replied_at"]).date() == today_utc:
                    replies_today += 1
            except Exception:
                continue

    print("\n============================================================")
    print("  BLUESKY INBOUND REPLY WORKER STATUS")
    print("============================================================")
    print(f"  Total Inbound Replies Logged: {len(replied_ids)}")
    print(f"  Replies Executed Today:       {replies_today}/{MAX_REPLIES_PER_DAY}")
    print("============================================================\n")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Bluesky Inbound Reply Worker")
    ap.add_argument("--auto", action="store_true", help="Run scheduled inbound reply pass")
    ap.add_argument("--status", action="store_true", help="Show live reply metrics")
    ap.add_argument("--dry-run", action="store_true", help="Simulate reply check and drafting without posting")
    args = ap.parse_args()

    if args.status:
        return show_status()

    if args.auto or args.dry_run:
        run_reply_worker(dry_run=args.dry_run)
        return 0

    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
