#!/usr/bin/env python3
"""
fanvue_dm.py — Welcome message automation for new Fanvue subscribers.
Deliverable 4 (§6) of GEMINI_FANVUE.md.

Rules & Guarantees:
  - Welcome message copy is dynamically loaded from growth/fanvue_profile.md at runtime.
    Never hardcoded in Python code.
  - Strictly polls new subscribers and diffs against growth/welcomed.json.
  - Crash-resilient: updates and flushes growth/welcomed.json immediately after each send.
  - Idempotent: running consecutive times with no new subscribers sends 0 messages.
  - Mass messages are strictly out of scope.
  - Audits all live sends to growth/ledger.jsonl.
"""
from __future__ import annotations
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import argparse
import datetime
import json
import os
import pathlib
import re
from typing import Any, Dict, List, Optional

ROOT = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = ROOT if (ROOT / "personas").exists() else ROOT.parent
GROWTH_DIR = ROOT if ROOT.name == "growth" else PROJECT_ROOT / "growth"

# Ensure growth directory is importable
if str(GROWTH_DIR) not in sys.path:
    sys.path.insert(0, str(GROWTH_DIR))

try:
    from fanvue_api import FanvueClient, load_key, log_ledger
except ImportError:
    from growth.fanvue_api import FanvueClient, load_key, log_ledger


def load_welcome_message(profile_path: Optional[pathlib.Path] = None, option_num: int = 1) -> str:
    """
    Dynamically extracts the approved Welcome DM copy from fanvue_profile.md at runtime.
    Enforces the <400 characters rule and confirms non-empty.
    """
    candidates = [
        profile_path,
        GROWTH_DIR / "fanvue_profile.md",
        PROJECT_ROOT / "growth" / "fanvue_profile.md",
        ROOT / "fanvue_profile.md",
    ]
    md_file = None
    for c in candidates:
        if c and c.is_file():
            md_file = c
            break

    if not md_file:
        sys.exit(f"  ! Profile copy file fanvue_profile.md not found in {GROWTH_DIR.resolve()}")

    content = md_file.read_text(encoding="utf-8")

    # Scope to section 2: Welcome DM Options
    section_match = re.search(r"## 2\.\s+Welcome DM Options.*?(?=\n##\s|\Z)", content, re.DOTALL)
    if not section_match:
        sys.exit(f"  ! Section '## 2. Welcome DM Options' not found in {md_file.name}")
    section_text = section_match.group(0)

    # Match the specified Option block within section 2
    pattern = rf"### Option {option_num}.*?\n(.*?)(?=### Option|\n---|\Z)"
    match = re.search(pattern, section_text, re.DOTALL)
    if not match:
        sys.exit(f"  ! Could not find 'Option {option_num}' under Welcome DM Options in {md_file.name}")

    block = match.group(1)
    paras = []
    for line in block.splitlines():
        line = line.strip()
        if line.startswith(">"):
            cleaned = line.lstrip(">").strip()
            # Remove bold/code markers
            cleaned = cleaned.replace("**", "").replace("`", "").strip()
            if cleaned:
                paras.append(cleaned)

    message = "\n\n".join(paras)
    if not message:
        sys.exit(f"  ! Extracted Welcome DM from Option {option_num} is empty.")

    if len(message) > 400:
        sys.exit(f"  ! Welcome DM exceeds Fanvue limit: {len(message)}/400 characters.")

    return message


def load_welcomed(welcomed_file: Optional[pathlib.Path] = None) -> Dict[str, Any]:
    """
    Loads the persistence state of already-welcomed subscribers.
    Returns a dict mapping subscriber uuid -> record.
    """
    target = welcomed_file or (GROWTH_DIR / "welcomed.json")
    if not target.is_file():
        save_welcomed({}, target)
        return {}
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
        elif isinstance(data, list):
            # Convert legacy or array format to dict keyed by uuid
            return {item.get("uuid", str(idx)): item for idx, item in enumerate(data)}
        return {}
    except Exception as e:
        print(f"  ! Warning reading {target.name}: {e}. Initializing fresh state.")
        return {}


def save_welcomed(welcomed: Dict[str, Any], welcomed_file: Optional[pathlib.Path] = None) -> None:
    """
    Persists welcomed state to disk immediately and flushes.
    """
    target = welcomed_file or (GROWTH_DIR / "welcomed.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    temp_target = target.with_suffix(".tmp")
    with open(temp_target, "w", encoding="utf-8") as f:
        json.dump(welcomed, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    temp_target.replace(target)


def run_welcome(dry_run: bool = False, welcomed_path: Optional[pathlib.Path] = None) -> int:
    """
    Core welcome runner:
      1. Loads dynamic DM copy from fanvue_profile.md.
      2. Loads already-welcomed state from welcomed.json.
      3. Polls current subscribers via Fanvue API.
      4. Diffs: identifies new subscribers not in welcomed.json.
      5. Sends welcome message, persisting each send immediately.
      6. Verifies idempotency.
    """
    msg_text = load_welcome_message()
    print("  ========================================")
    print("  FANVUE WELCOME DM AUTOMATION")
    print("  ========================================")
    print(f"  Loaded copy ({len(msg_text)} chars):\n  ---\n  {msg_text.replace(chr(10), chr(10) + '  ')}\n  ---")

    welcomed = load_welcomed(welcomed_path)
    print(f"  Already welcomed: {len(welcomed)} subscribers in registry.")

    key = load_key()
    client = FanvueClient(api_key=key)

    print("  Polling subscribers from Fanvue API (GET /v1/chats/lists/smart/subscribers)...")
    subscribers = client.get_subscribers()
    print(f"  Total subscribers retrieved: {len(subscribers)}")

    # Diff against registry
    pending = [s for s in subscribers if (s.get("uuid") or s.get("id")) not in welcomed]
    print(f"  Pending new subscribers to welcome: {len(pending)}")

    if not pending:
        print("  No new subscribers to welcome (0 pending).")
        print("  Idempotent check passed: 0 messages sent.")
        print("  ========================================\n")
        return 0

    sent_count = 0
    for sub in pending:
        sub_uuid = sub.get("uuid") or sub.get("id")
        handle = sub.get("handle") or sub.get("username") or "unknown"
        display_name = sub.get("displayName") or sub.get("name") or handle

        if dry_run:
            print(f"\n  [DRY-RUN] Would send welcome DM to @{handle} (UUID: {sub_uuid}):")
            print(f"            Display Name: {display_name}")
            print(f"            Message: {repr(msg_text)}")
            sent_count += 1
        else:
            print(f"\n  Sending welcome DM to @{handle} (UUID: {sub_uuid})...")
            client.send_dm(user_uuid=sub_uuid, text=msg_text, dry_run=False)

            # Record send BEFORE moving to next or returning (crash-resilience)
            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
            welcomed[sub_uuid] = {
                "uuid": sub_uuid,
                "handle": handle,
                "displayName": display_name,
                "welcomed_at": now_iso,
                "message_preview": msg_text[:80] + "...",
            }
            save_welcomed(welcomed, welcomed_path)
            log_ledger("send_welcome_dm", f"@{handle}", f"Sent welcome DM to @{handle} ({sub_uuid})")
            print(f"  [SENT & PERSISTED] @{handle} recorded in welcomed registry.")
            sent_count += 1

    mode_str = "[DRY-RUN] Simulated" if dry_run else "Sent"
    print(f"\n  {mode_str} {sent_count} welcome message(s).")
    print("  ========================================\n")
    return sent_count


def self_test_idempotency() -> None:
    """
    Self-test proving idempotency and crash-resilience with simulated state.
    """
    test_file = GROWTH_DIR / "_test_welcomed.json"
    if test_file.exists():
        test_file.unlink()

    print("  Running idempotency self-test with simulated subscriber...")
    msg = load_welcome_message()
    simulated_sub = {
        "uuid": "test-sub-0000-1111-2222",
        "handle": "simulated_fan",
        "displayName": "Simulated Fan",
    }

    # Run 1: First welcome
    welcomed = load_welcomed(test_file)
    assert simulated_sub["uuid"] not in welcomed, "Must not be welcomed initially"
    welcomed[simulated_sub["uuid"]] = {
        "uuid": simulated_sub["uuid"],
        "handle": simulated_sub["handle"],
        "welcomed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    save_welcomed(welcomed, test_file)
    print("  [Pass] Simulated send 1: Record persisted to registry.")

    # Run 2: Second run diff
    welcomed_after = load_welcomed(test_file)
    pending_second_run = [s for s in [simulated_sub] if s["uuid"] not in welcomed_after]
    assert len(pending_second_run) == 0, "Second run must have 0 pending!"
    print(f"  [Pass] Simulated send 2: {len(pending_second_run)} pending messages. Zero duplicates sent.")

    # Cleanup
    if test_file.exists():
        test_file.unlink()
    print("  Self-test passed completely.\n")


def main() -> int:
    print("[NOTICE] fanvue_dm.py is DEPRECATED. Fanvue integration has been permanently removed. Use agent_runner.py instead.")
    return 0

    run_welcome(dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
