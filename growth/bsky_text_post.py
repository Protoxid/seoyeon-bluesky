#!/usr/bin/env python3
"""
growth/bsky_text_post.py — Spontaneous Organic Bluesky Text Publisher for Lyra.

Publishes authentic, text-only micro-thoughts to Bluesky (@syeonhn.bsky.social)
with ZERO images, ZERO promotional copy, and ZERO Fanvue links.
Operates to build genuine parasocial connection and make the profile feel alive.
"""

from __future__ import annotations
import argparse
import datetime as dt
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

# Ensure UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

GROWTH_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = GROWTH_DIR.parent
CRED_FILE = GROWTH_DIR / "bsky_credentials.json"
LEDGER_FILE = GROWTH_DIR / "ledger.jsonl"
HISTORY_FILE = GROWTH_DIR / "bsky_organic_posts.jsonl"
XRPC_BASE = "https://bsky.social/xrpc"

# Forbidden promotional / adult terms — Lyra NEVER advertises
FORBIDDEN_TERMS = [
    "fanvue",
    "onlyfans",
    "patreon",
    "exclusive",
    "unlock",
    "private feed",
    "link in bio",
    "links in bio",
    "c=fv",
    "subscribe",
    "discount",
    "promo",
    "ppv",
    "tier",
    "!",  # Seo-yeon's voice NEVER uses exclamation marks
]

# Curated bank of canonical in-character organic micro-thoughts (time/routine categorized)
ORGANIC_THOUGHT_BANK = [
    # Morning / Early studio
    {
        "slot": "morning",
        "hours_kst": [6, 7, 8, 9],
        "text": "floor at the studio is always freezing at 6:45. unwinding the springs on three reformers before anyone else arrives."
    },
    {
        "slot": "morning",
        "hours_kst": [7, 8, 9, 10],
        "text": "first beginner class done. trying to explain neutral spine without using the word pelvis five times in one minute."
    },
    {
        "slot": "morning",
        "hours_kst": [8, 9, 10, 11],
        "text": "walked past seoul forest on the way back. mist coming off the trees. autumn is definitely here."
    },
    # Afternoon / Laptop freelance grind / Coffee
    {
        "slot": "afternoon",
        "hours_kst": [12, 13, 14, 15],
        "text": "iced americano in a glass with too much condensation. three client marketing decks open, zero completed."
    },
    {
        "slot": "afternoon",
        "hours_kst": [14, 15, 16, 17],
        "text": "the cafe near ttukseom station changed their espresso beans. darker roast than before. not sure how i feel about it."
    },
    {
        "slot": "afternoon",
        "hours_kst": [15, 16, 17, 18],
        "text": "lumbar spine decided 4pm was the exact time to complain. ten minutes on the foam roller on the wooden floor."
    },
    # Evening / Errands / Solitary flat
    {
        "slot": "evening",
        "hours_kst": [18, 19, 20, 21],
        "text": "went to the mart for tofu and came back with three persimmons and an enamel pot i don't need."
    },
    {
        "slot": "evening",
        "hours_kst": [19, 20, 21, 22],
        "text": "boiled roasted barley tea. the flat smells like toasted grain. steam on the kitchen tile."
    },
    {
        "slot": "evening",
        "hours_kst": [20, 21, 22],
        "text": "line 2 was unusually quiet tonight. watched three people reading actual paper books instead of looking at their phones."
    },
    # Late night / Insomnia / Quiet thoughts
    {
        "slot": "night",
        "hours_kst": [22, 23, 0, 1],
        "text": "it is 23:40 and the motorcycle couriers on seongsu-ro sound like they are driving through my living room."
    },
    {
        "slot": "night",
        "hours_kst": [23, 0, 1, 2],
        "text": "washing machine finished its cycle twenty minutes ago. debating whether getting up to hang it is worth the effort."
    },
    {
        "slot": "night",
        "hours_kst": [0, 1, 2, 3],
        "text": "stretching in the dark before sleeping. quietest hour in the neighbourhood."
    },
]


def get_credentials() -> tuple[str, str]:
    """Retrieves Bluesky handle and app password from environment or credential file."""
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
        return "", ""

    if "." not in handle:
        handle = f"{handle}.bsky.social"

    return handle.strip(), app_pw.strip()


def validate_text(text: str) -> tuple[bool, str]:
    """Validates that text conforms to Seo-yeon's organic non-commercial voice."""
    if not text or not text.strip():
        return False, "Post text is empty."

    t = text.strip()
    lower = t.lower()

    for term in FORBIDDEN_TERMS:
        if term == "!":
            if "!" in t:
                return False, "Exclamation mark detected. Seo-yeon's voice uses full stops only."
        elif re.search(r"\b" + re.escape(term) + r"\b", lower) or term in lower:
            return False, f"Forbidden marketing/promotional term detected: '{term}'."

    if len(t) > 300:
        return False, f"Text exceeds Bluesky 300-character limit ({len(t)} chars)."

    return True, "Valid."


def create_session(handle: str, app_pw: str) -> tuple[str, str]:
    """Creates an AT Protocol session via XRPC."""
    data = json.dumps({"identifier": handle, "password": app_pw}).encode("utf-8")
    req = urllib.request.Request(
        f"{XRPC_BASE}/com.atproto.server.createSession",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        res = json.loads(r.read().decode("utf-8"))
    return res["accessJwt"], res["did"]


def parse_facets(text: str) -> list[dict]:
    """Detects Hashtags in text and builds AT Protocol richtext tag facets."""
    facets = []
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


def publish_text_post(text: str, dry_run: bool = False) -> Dict[str, Any]:
    """Publishes a text-only record to Bluesky feed."""
    ok, reason = validate_text(text)
    if not ok:
        sys.exit(f"[VALIDATION ERROR]: {reason}")

    text = text.strip()
    print(f"\n============================================================")
    print(f"  LYRA — ORGANIC BLUESKY TEXT DISPATCH")
    print(f"============================================================")
    print(f"  Text: \"{text}\" ({len(text)} chars)")
    print(f"  Type: Text-Only (No images, No promotional links)")
    print(f"============================================================\n")

    handle, app_pw = get_credentials()
    if not handle or not app_pw:
        print("  [INFO] BSKY_HANDLE or BSKY_APP_PASSWORD not set. Skipping text post.")
        return {}

    if dry_run:
        print("[DRY-RUN] Authenticating and validating AT Protocol record...")
        try:
            jwt, did = create_session(handle, app_pw)
            print(f"[DRY-RUN] Session OK for DID: {did}. Simulation successful.")
        except Exception as e:
            print(f"[DRY-RUN] Session failed: {e}")
        return {"dry_run": True, "text": text}

    try:
        jwt, did = create_session(handle, app_pw)
    except Exception as e:
        print(f"  [Warning] Failed to authenticate with Bluesky: {e}")
        return {}

    now_iso = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    record = {
        "$type": "app.bsky.feed.post",
        "text": text,
        "createdAt": now_iso,
        "langs": ["ko", "en"]
    }
    facets = parse_facets(text)
    if facets:
        record["facets"] = facets

    payload = json.dumps({
        "repo": did,
        "collection": "app.bsky.feed.post",
        "record": record
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{XRPC_BASE}/com.atproto.repo.createRecord",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {jwt}"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=15) as r:
        res = json.loads(r.read().decode("utf-8"))

    uri = res.get("uri", "")
    cid = res.get("cid", "")
    print(f"[SUCCESS] Organic text post published! URI: {uri}")

    # Log to local history
    log_entry = {
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
        "uri": uri,
        "cid": cid,
        "text": text
    }
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    # Log to master financial/activity ledger
    with open(LEDGER_FILE, "a", encoding="utf-8") as f:
        ledger_entry = {
            "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
            "surface": "bluesky",
            "action": "organic_text_post",
            "target": uri,
            "note": f"Lyra: {text[:40]}..."
        }
        f.write(json.dumps(ledger_entry, ensure_ascii=False) + "\n")

    return {"uri": uri, "cid": cid, "text": text}


def check_cadence_gate(force: bool = False) -> tuple[bool, str]:
    """
    Checks if an organic post is allowed under Lyra's cadence invariants:
    - Minimum 4 hours between organic posts
    - Max 2 organic posts per calendar day
    - Realistic human active windows (06:00-10:00, 12:00-18:00, 20:00-01:00 KST)
    """
    if force:
        return True, "Forced bypass of cadence gate."

    now_utc = dt.datetime.now(dt.timezone.utc)
    kst_tz = dt.timezone(dt.timedelta(hours=9))
    now_kst = now_utc.astimezone(kst_tz)
    current_hour = now_kst.hour

    # 1. Human window check
    valid_hours = {6, 7, 8, 9, 10, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22, 23, 0}
    if current_hour not in valid_hours:
        return False, f"Current KST hour ({current_hour:02d}:00) is outside realistic human posting windows."

    # 2. History check for cooldown & daily count
    if HISTORY_FILE.exists():
        history_lines = [l.strip() for l in HISTORY_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]
        if history_lines:
            try:
                last_entry = json.loads(history_lines[-1])
                last_ts = dt.datetime.fromisoformat(last_entry["ts"])
                hours_since = (now_utc - last_ts).total_seconds() / 3600.0
                if hours_since < 4.0:
                    return False, f"Cooldown active: last organic post was {hours_since:.1f}h ago (minimum interval is 4h)."

                # Check posts today
                today_kst_date = now_kst.date()
                posts_today = 0
                for line in history_lines:
                    e = json.loads(line)
                    entry_dt = dt.datetime.fromisoformat(e["ts"]).astimezone(kst_tz)
                    if entry_dt.date() == today_kst_date:
                        posts_today += 1
                if posts_today >= 2:
                    return False, f"Daily limit reached: {posts_today} organic posts already published today ({today_kst_date})."
            except Exception as e:
                print(f"  [Warning] Error parsing history for cadence check: {e}")

    return True, "Cadence gate passed."


def log_to_agent_memory(text: str, uri: str) -> None:
    """Appends published organic thought to Lyra's agent memory file."""
    memory_file = PROJECT_ROOT / ".pi" / "agent-memory" / "lyra" / "MEMORY.md"
    if not memory_file.exists():
        return

    now_utc = dt.datetime.now(dt.timezone.utc)
    kst_tz = dt.timezone(dt.timedelta(hours=9))
    now_kst = now_utc.astimezone(kst_tz)
    date_str = now_kst.strftime("%Y-%m-%d")
    hour_str = now_kst.strftime("%H:%M")

    # Classify theme roughly
    theme = "organic thought"
    lower = text.lower()
    if any(k in lower for k in ("studio", "reformer", "pilates", "pelvis", "spine", "foam roller")):
        theme = "studio / body reality"
    elif any(k in lower for k in ("cafe", "americano", "coffee", "roast", "decks", "marketing")):
        theme = "freelance / coffee observation"
    elif any(k in lower for k in ("tea", "couriers", "seongsu", "washing machine", "persimmons", "mart")):
        theme = "solitary seongsu life"
    elif any(k in lower for k in ("line 2", "subway", "train", "forest", "autumn")):
        theme = "city / commute texture"

    row = f"| {date_str} | {hour_str} | {text} | {uri} | {theme} |\n"
    try:
        content = memory_file.read_text(encoding="utf-8")
        if "| Date | KST | Text | URI | Theme |" in content:
            content += row
            memory_file.write_text(content, encoding="utf-8")
    except Exception as e:
        print(f"  [Warning] Could not append to Lyra MEMORY.md: {e}")


def get_current_kst_hour() -> int:
    """Returns current hour in Korea Standard Time (UTC+9)."""
    kst_tz = dt.timezone(dt.timedelta(hours=9))
    return dt.datetime.now(dt.timezone.utc).astimezone(kst_tz).hour


def select_contextual_thought() -> str:
    """Selects an unposted contextual thought matching the current KST time of day."""
    posted_texts = set()
    if HISTORY_FILE.exists():
        for line in HISTORY_FILE.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    posted_texts.add(json.loads(line).get("text", "").strip())
                except Exception:
                    pass

    hour_kst = get_current_kst_hour()
    matching_candidates = [
        item["text"] for item in ORGANIC_THOUGHT_BANK
        if hour_kst in item["hours_kst"] and item["text"] not in posted_texts
    ]

    if matching_candidates:
        return matching_candidates[0]

    # Fallback to any unposted candidate
    unposted = [item["text"] for item in ORGANIC_THOUGHT_BANK if item["text"] not in posted_texts]
    if unposted:
        return unposted[0]

    # If all in bank were used, take the oldest
    return ORGANIC_THOUGHT_BANK[0]["text"]


def show_history() -> None:
    """Prints recent organic posts from history."""
    if not HISTORY_FILE.exists() or HISTORY_FILE.stat().st_size == 0:
        print("No organic posts logged yet.")
        return

    lines = [l for l in HISTORY_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]
    print(f"\n============================================================")
    print(f"  LYRA — RECENT ORGANIC BLUESKY POSTS ({len(lines)} total)")
    print(f"============================================================\n")
    for line in lines[-10:]:
        entry = json.loads(line)
        print(f"[{entry.get('ts')[:16]}] {entry.get('text')}")
    print("============================================================\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Lyra — Spontaneous Bluesky Organic Voice")
    parser.add_argument("--text", type=str, help="Specific text to publish")
    parser.add_argument("--auto", action="store_true", help="Pick contextual post matching current KST hour")
    parser.add_argument("--dry-run", action="store_true", help="Simulate session and record creation without publishing")
    parser.add_argument("--history", action="store_true", help="Display recent organic post history")
    parser.add_argument("--force", action="store_true", help="Bypass cadence/cooldown gate")
    args = parser.parse_args()

    if args.history:
        show_history()
        return 0

    if args.auto:
        allowed, reason = check_cadence_gate(force=args.force)
        if not allowed:
            print(f"\n============================================================")
            print(f"  [LYRA CADENCE GATE] {reason}")
            print(f"============================================================\n")
            return 0

        chosen_text = select_contextual_thought()
        res = publish_text_post(chosen_text, dry_run=args.dry_run)
        if not args.dry_run and res.get("uri"):
            log_to_agent_memory(chosen_text, res["uri"])
        return 0

    if args.text:
        res = publish_text_post(args.text, dry_run=args.dry_run)
        if not args.dry_run and res.get("uri"):
            log_to_agent_memory(args.text, res["uri"])
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())

