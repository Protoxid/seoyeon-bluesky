#!/usr/bin/env python3
"""
growth/fanvue_chat_agent.py — Autonomous Subscriber Retention & Chat Agent for Fanvue.

Operates the private subscriber sanctuary for Seo-yeon Han (@syeon.hn):
  1. Welcome DM Automation: Checks for newly subscribed fans and delivers the canon welcome DM.
  2. Inbound Chat Monitoring: Polls GET /chats for unread incoming subscriber messages.
  3. Conversational Nurturing: Drafts intimate, unhurried, lowercase responses in Seo-yeon's Fanvue voice:
     - Warm, quiet, late-night, personal, lowercase, full stops.
     - Creates parasocial loyalty that keeps subscribers paying month-over-month ($9.99/mo)
       and drives impulse PPV unlocks.
  4. Idempotency & Crash-Resilience: Records every interaction to growth/fanvue_chat_history.jsonl
     and growth/ledger.jsonl.

Usage:
  python growth/fanvue_chat_agent.py --auto
  python growth/fanvue_chat_agent.py --status
  python growth/fanvue_chat_agent.py --dry-run
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
from typing import Any, Dict, List, Optional, Set, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

GROWTH_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = GROWTH_DIR.parent
CHAT_LOG = GROWTH_DIR / "fanvue_chat_history.jsonl"
LEDGER_FILE = GROWTH_DIR / "ledger.jsonl"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

if str(GROWTH_DIR) not in sys.path:
    sys.path.insert(0, str(GROWTH_DIR))

try:
    from fanvue_api import FanvueClient, load_key, log_ledger
    from fanvue_dm import run_welcome, load_welcomed
except ImportError:
    from growth.fanvue_api import FanvueClient, load_key, log_ledger
    from growth.fanvue_dm import run_welcome, load_welcomed

# Fallback responses for subscriber DMs
FALLBACK_SUBSCRIBER_REPLIES = [
    "hey, thank you for writing 🖤 just got back to the flat after studio sessions. having cold water at the counter before stretching. how has your day been?",
    "loved reading this... today was long but teaching reformer always clears my head. are you relaxing at home tonight or still busy?",
    "so glad you are here with me xx resting on the floor with roasted barley tea right now. what time is it over there?",
    "means a lot that you took the time to message. slipping into something comfortable and looking through tomorrow's sets. tell me what you're up to tonight.",
]


def load_chat_history() -> Dict[str, Dict[str, Any]]:
    """Loads past chat interaction records by message UUID or user_uuid:ts."""
    history: Dict[str, Dict[str, Any]] = {}
    if not CHAT_LOG.exists():
        return history
    for line in CHAT_LOG.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
            key = entry.get("message_uuid") or f"{entry.get('user_uuid')}_{entry.get('incoming_text', '')[:20]}"
            history[key] = entry
        except Exception:
            continue
    return history


def append_chat_log(entry: Dict[str, Any]) -> None:
    GROWTH_DIR.mkdir(parents=True, exist_ok=True)
    with open(CHAT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def get_openrouter_key() -> Optional[str]:
    return os.environ.get("OPENROUTER_API_KEY")


def draft_fanvue_reply(user_name: str, incoming_text: str) -> Tuple[str, str]:
    """
    Drafts an intimate, warm, lowercase reply in Seo-yeon's Fanvue voice.
    Distinct from public Bluesky voice: here she is warm, private, unhurried, and genuinely welcoming.
    """
    or_key = get_openrouter_key()
    if or_key:
        prompt = (
            "You are Han Seo-yeon (한서연), a 26-year-old Korean pilates instructor and visual designer from Seoul.\n"
            "You are messaging a paid subscriber on Fanvue (@syeon.hn) who pays $9.99/mo to be in your private sanctuary.\n"
            "Your Fanvue voice: warm, quiet, late-night, intimate, lowercase, soft unhurried candour, full stops.\n"
            "Tone: You genuinely appreciate them being in your private circle. You talk about relaxing at home after the studio, stretching on the floor, tea, your flat in Seongsu.\n"
            "ZERO corporate language, ZERO robotic hype, NO exclamation marks (!).\n"
            f"Subscriber {user_name} wrote to you:\n"
            f'"{incoming_text}"\n\n'
            "Write a warm, authentic, personal response (2-3 sentences max) that answers them gently and asks an easy question back."
        )
        payload = {
            "model": "deepseek/deepseek-v4-flash",
            "messages": [
                {"role": "system", "content": "You are Han Seo-yeon on Fanvue. Write strictly in character. All lowercase, full stops only."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.75,
            "max_tokens": 150
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
                if ans.startswith('"') and ans.endswith('"'):
                    ans = ans[1:-1].strip()
                ans = ans.replace("!", ".")
                return ans, "deepseek/deepseek-v4-flash"
        except Exception as e:
            print(f"  [Notice] OpenRouter chat draft failed: {e}. Using canon fallback.")

    import random
    return random.choice(FALLBACK_SUBSCRIBER_REPLIES), "offline-fanvue-fallback"


def process_fanvue_chats(client: FanvueClient, dry_run: bool = False) -> int:
    """
    Polls active chats and responds to incoming subscriber messages.
    """
    print("  Polling active Fanvue chats (GET /chats)...")
    chats_res = client.request("GET", "/chats", raise_for_status=False)
    chats = chats_res.get("data", []) if isinstance(chats_res, dict) else []
    print(f"  Total active chat threads: {len(chats)}")

    if not chats:
        print("  No active chats requiring response.")
        return 0

    history = load_chat_history()
    replies_sent = 0

    for chat in chats:
        chat_uuid = chat.get("uuid") or chat.get("id")
        recipient = chat.get("recipient") or chat.get("user") or {}
        user_uuid = recipient.get("uuid") or recipient.get("id")
        handle = recipient.get("handle") or recipient.get("username") or "subscriber"
        display_name = recipient.get("displayName") or recipient.get("name") or handle

        last_message = chat.get("lastMessage") or {}
        msg_text = last_message.get("text", "")
        sender_id = last_message.get("senderId") or last_message.get("senderUuid")

        # Skip if last message was sent by creator herself
        if sender_id and str(sender_id) == str(client.creator_id if hasattr(client, "creator_id") else ""):
            continue

        msg_uuid = last_message.get("uuid") or f"{user_uuid}_{msg_text[:20]}"
        if msg_uuid in history:
            continue

        if not msg_text:
            continue

        print(f"\n  -> Inbound chat from @{handle} ({display_name}): \"{msg_text[:60]}...\"")
        reply_draft, model_used = draft_fanvue_reply(display_name, msg_text)
        print(f"     Draft ({model_used}):\n     \"{reply_draft}\"")

        if dry_run:
            print(f"     [DRY-RUN] Would send DM to @{handle} ({user_uuid})")
            replies_sent += 1
        else:
            client.send_dm(user_uuid=user_uuid, text=reply_draft, dry_run=False)
            now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
            log_entry = {
                "message_uuid": msg_uuid,
                "user_uuid": user_uuid,
                "handle": handle,
                "incoming_text": msg_text,
                "reply_text": reply_draft,
                "model_used": model_used,
                "sent_at": now_iso
            }
            append_chat_log(log_entry)
            log_ledger("fanvue_chat_reply", f"@{handle}", f"Replied to chat from @{handle} ({user_uuid})")
            print(f"     [SENT & PERSISTED] Replied to @{handle}")
            replies_sent += 1
            time.sleep(2.0)

    return replies_sent


def show_status() -> int:
    key = load_key()
    client = FanvueClient(api_key=key)
    creator = client.whoami()
    welcomed = load_welcomed()
    history = load_chat_history()

    print("============================================================")
    print("  FANVUE AUTONOMOUS AGENT STATUS")
    print("============================================================")
    print(f"  Creator Handle:     @{creator.get('handle', 'syeon.hn')}")
    print(f"  Total Welcomed:     {len(welcomed)} subscribers")
    print(f"  Total Chat Replies: {len(history)} messages logged")
    print("============================================================\n")
    return 0


def run_autonomous_cycle(dry_run: bool = False) -> None:
    print("============================================================")
    print("  FANVUE AUTONOMOUS RETENTION & CHAT RUNNER")
    print(f"  Mode: {'[DRY-RUN] Simulation' if dry_run else '[LIVE EXECUTION]'}")
    print("============================================================")

    # 1. Welcome new subscribers
    print("\n[1/2] Processing Fanvue Subscriber Welcome Loop...")
    welcomes = run_welcome(dry_run=dry_run)
    print(f"  Welcome loop finished: {welcomes} new subscriber(s) welcomed.")

    # 2. Inbound chat processing
    print("\n[2/2] Processing Inbound Fanvue Subscriber Chats...")
    key = load_key()
    client = FanvueClient(api_key=key)
    replies = process_fanvue_chats(client, dry_run=dry_run)
    print(f"  Chat loop finished: {replies} conversational reply(ies) processed.")

    print("\n============================================================")
    print("  Fanvue Autonomous Cycle Complete.")
    print("============================================================\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="Fanvue Autonomous Retention & Chat Agent")
    ap.add_argument("--auto", action="store_true", help="Run full welcome + chat retention loop")
    ap.add_argument("--status", action="store_true", help="Display Fanvue agent status")
    ap.add_argument("--dry-run", action="store_true", help="Simulate welcome and chat actions without writes")
    args = ap.parse_args()

    if args.status:
        return show_status()

    if args.auto or args.dry_run:
        run_autonomous_cycle(dry_run=args.dry_run)
        return 0

    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
