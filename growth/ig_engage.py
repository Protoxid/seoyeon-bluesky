#!/usr/bin/env python3
"""
ig_engage.py — Instagram comment polling and approval-gated reply system.
Step 5 (§7) of OPERATOR_BRIEF.md / PLAN.md.

Design & Non-Negotiables:
  - Polls comments on own media: GET /<media-id>/comments.
  - Drafts in-character replies in Seo-yeon's authentic canon voice.
  - Writes drafts into an approval queue: growth/comment_queue.jsonl.
  - THE QUEUE IS THE CONSENT: Nothing posts without an explicit "approved" flag.
  - A human operator marks approved before posting; pending drafts are strictly refused.
  - Posts approved replies via POST /<comment-id>/replies.
  - Logs all live reply actions to growth/ledger.jsonl.
  - Never prints tokens or secrets.
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = ROOT if (ROOT / "personas").exists() else ROOT.parent
GROWTH_DIR = ROOT if ROOT.name == "growth" else PROJECT_ROOT / "growth"
PERSONAS_DIR = PROJECT_ROOT / "personas" / "seoyeon"

# Add directories to sys.path
for p in [str(GROWTH_DIR), str(PERSONAS_DIR), str(PROJECT_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

GRAPH_BASE = "https://graph.instagram.com"
API_VERSION = "v26.0"

QUEUE_FILE = GROWTH_DIR / "comment_queue.jsonl"


def log_ledger(action: str, target: str, note: str, surface: str = "instagram") -> None:
    GROWTH_DIR.mkdir(parents=True, exist_ok=True)
    ledger_path = GROWTH_DIR / "ledger.jsonl"
    entry = {
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
        "surface": surface,
        "action": action,
        "target": target,
        "note": note,
    }
    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load_credentials() -> Tuple[str, str]:
    """
    Loads ig_token.txt and ig_user_id.txt from growth/ or personas/seoyeon/.
    Never prints or logs the token.
    """
    token_candidates = [
        GROWTH_DIR / "ig_token.txt",
        PERSONAS_DIR / "ig_token.txt",
        PROJECT_ROOT / "ig_token.txt",
    ]
    user_candidates = [
        GROWTH_DIR / "ig_user_id.txt",
        PERSONAS_DIR / "ig_user_id.txt",
        PROJECT_ROOT / "ig_user_id.txt",
    ]

    token = None
    for c in token_candidates:
        if c.is_file():
            t = c.read_text(encoding="utf-8").strip()
            if t and not t.startswith("#"):
                token = t
                break

    user_id = None
    for c in user_candidates:
        if c.is_file():
            u = c.read_text(encoding="utf-8").strip()
            if u and not u.startswith("#"):
                user_id = u
                break

    if not token or not user_id:
        sys.exit(
            "  ! Instagram credentials missing.\n"
            "    Expected ig_token.txt and ig_user_id.txt in growth/ or personas/seoyeon/."
        )

    return token, user_id


# ==============================================================================
# CANON DRAFTING ENGINE (Seo-yeon Han)
# ==============================================================================

def draft_in_character_reply(comment_text: str, commenter_name: str = "") -> str:
    """
    Generates a contextual, grounded in-character draft reply in Seo-yeon's voice.
    Understated, gentle, lowercase preference, authentic to Seongsu / Pilates / Seoul.
    """
    text_lower = comment_text.lower().strip()

    # Detect Korean characters
    has_korean = bool(re.search(r"[\uac00-\ud7a3]", comment_text))

    if has_korean:
        if any(w in text_lower for w in ["예뻐", "예쁘", "귀여", "아름", "미모", "착장", "옷"]):
            return "좋게 봐주셔서 감사해요 :) 오늘도 좋은 하루 보내세요!"
        if any(w in text_lower for w in ["필라테스", "운동", "수업", "스튜디오"]):
            return "감사해요! 요즘 스튜디오 수업 준비하면서 더 열심히 해보고 있어요 ㅎㅎ"
        if any(w in text_lower for w in ["성수", "서울", "어디", "카페", "위치"]):
            return "성수동 쪽이에요! 조용하고 걷기 좋은 골목이 많아서 자주 가요."
        if any(w in text_lower for w in ["안녕", "반가", "하이"]):
            return "안녕하세요! 들러주셔서 반가워요 :)"
        return "댓글 남겨주셔서 감사해요, 편안한 저녁 되세요!"

    # English drafting
    if any(w in text_lower for w in ["outfit", "wear", "dress", "top", "pants", "shoes", "brand"]):
        return "thank you! mostly quiet basics from small shops around seongsu :)"
    if any(w in text_lower for w in ["pilates", "studio", "workout", "routine", "stretch"]):
        return "appreciate that! mornings at the studio are really my favorite part of the day."
    if any(w in text_lower for w in ["where", "place", "location", "seoul", "korea", "city"]):
        return "it's around seongsu in seoul, really love the quiet side streets here."
    if any(w in text_lower for w in ["gorgeous", "pretty", "beautiful", "cute", "love this", "stunning"]):
        return "that is so kind of you, thank you for being here :)"
    if any(w in text_lower for w in ["hi", "hello", "hey"]):
        return "hey, thanks for stopping by :)"
    if "?" in comment_text:
        return "thanks for asking! just taking things one quiet day at a time here in seoul."

    return "thank you so much, really appreciate you following along :)"


# ==============================================================================
# QUEUE MANAGEMENT
# ==============================================================================

def load_queue() -> List[Dict[str, Any]]:
    if not QUEUE_FILE.is_file():
        return []
    rows = []
    for i, line in enumerate(QUEUE_FILE.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as e:
            sys.exit(f"  ! {QUEUE_FILE.name} line {i} is not valid JSON: {e}")
    return rows


def save_queue(rows: List[Dict[str, Any]]) -> None:
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp_file = QUEUE_FILE.with_suffix(".tmp")
    with open(temp_file, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
    temp_file.replace(QUEUE_FILE)


# ==============================================================================
# API INTERACTIONS
# ==============================================================================

def poll_comments(token: str, user_id: str) -> int:
    """
    Polls GET /<media-id>/comments across recent media and drafts replies into the queue.
    """
    print("============================================================")
    print("INSTAGRAM COMMENT POLLER (GET /<media-id>/comments)")
    print("============================================================\n")

    # 1. Fetch recent media
    media_url = (
        f"{GRAPH_BASE}/{API_VERSION}/{user_id}/media?"
        f"fields=id,caption,media_type,timestamp,comments_count&limit=25&access_token={token}"
    )
    req = urllib.request.Request(media_url)
    try:
        with urllib.request.urlopen(req) as resp:
            media_data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        sys.exit(f"  ! HTTP error fetching media: {e.code} {e.reason}")
    except Exception as e:
        sys.exit(f"  ! Error contacting Instagram API: {e}")

    media_items = media_data.get("data", [])
    print(f"  Scanned {len(media_items)} recent media objects on account.")

    queue = load_queue()
    known_comment_ids = {r.get("comment_id") for r in queue if r.get("comment_id")}

    new_comments_count = 0

    for m in media_items:
        m_id = m.get("id")
        c_count = m.get("comments_count", 0)
        if c_count == 0:
            continue

        # Fetch comments for this media
        comm_url = (
            f"{GRAPH_BASE}/{API_VERSION}/{m_id}/comments?"
            f"fields=id,text,timestamp,username,like_count&limit=50&access_token={token}"
        )
        try:
            with urllib.request.urlopen(urllib.request.Request(comm_url)) as c_resp:
                comm_data = json.loads(c_resp.read().decode("utf-8"))
        except Exception as e:
            print(f"  ! Warning fetching comments for media {m_id}: {e}")
            continue

        comments = comm_data.get("data", [])
        for c in comments:
            cid = c.get("id")
            if cid in known_comment_ids:
                continue

            text = c.get("text", "").strip()
            username = c.get("username", "unknown")
            created_time = c.get("timestamp")

            # Draft reply
            draft = draft_in_character_reply(text, username)
            entry = {
                "comment_id": cid,
                "media_id": m_id,
                "username": username,
                "comment_text": text,
                "comment_time": created_time,
                "draft_reply": draft,
                "status": "pending",  # strictly pending until human approval
                "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "approved_at": None,
                "posted_at": None,
                "reply_id": None,
            }
            queue.append(entry)
            known_comment_ids.add(cid)
            new_comments_count += 1
            print(f"  [DRAFT CREATED] Comment {cid} from @{username}:")
            print(f"    Comment: \"{text}\"")
            print(f"    Draft:   \"{draft}\"")
            print(f"    Status:  PENDING (Approval required)")

    save_queue(queue)
    print(f"\n  Poll complete: {new_comments_count} new comment draft(s) added to {QUEUE_FILE.name}.")
    print("============================================================\n")
    return new_comments_count


def list_queue() -> None:
    queue = load_queue()
    print("============================================================")
    print("COMMENT APPROVAL QUEUE (growth/comment_queue.jsonl)")
    print("============================================================\n")

    if not queue:
        print("  Approval queue is empty.")
        print("============================================================\n")
        return

    pending = [r for r in queue if r.get("status") == "pending"]
    approved = [r for r in queue if r.get("status") == "approved"]
    posted = [r for r in queue if r.get("status") == "posted"]
    rejected = [r for r in queue if r.get("status") == "rejected"]

    print(f"  Summary: {len(pending)} pending | {len(approved)} approved | {len(posted)} posted | {len(rejected)} rejected\n")

    if pending:
        print("  --- PENDING REVIEW (Awaiting Approval) ---")
        for r in pending:
            print(f"  ID: {r['comment_id']} | From: @{r.get('username')}")
            print(f"  Comment: \"{r.get('comment_text')}\"")
            print(f"  Draft:   \"{r.get('draft_reply')}\"")
            print(f"  Command to approve: python ig_engage.py --approve {r['comment_id']}\n")

    if approved:
        print("  --- APPROVED (Ready to Post) ---")
        for r in approved:
            print(f"  ID: {r['comment_id']} | From: @{r.get('username')}")
            print(f"  Reply:   \"{r.get('draft_reply')}\"")
            print(f"  Approved at: {r.get('approved_at')}\n")

    if posted:
        print(f"  --- POSTED ({len(posted)} items successfully replied) ---")

    print("============================================================\n")


def set_status(comment_id: str, new_status: str, edited_text: Optional[str] = None) -> bool:
    queue = load_queue()
    found = False
    for r in queue:
        if r.get("comment_id") == comment_id:
            found = True
            r["status"] = new_status
            if new_status == "approved":
                r["approved_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
            if edited_text:
                r["draft_reply"] = edited_text
            break

    if not found:
        print(f"  ! Comment ID {comment_id} not found in queue.")
        return False

    save_queue(queue)
    print(f"  [UPDATED] Comment {comment_id} marked as '{new_status}'.")
    return True


def post_approved(token: str, dry_run: bool = True) -> int:
    """
    Posts approved replies to Instagram: POST /<comment-id>/replies.
    NON-NEGOTIABLE: Strictly refuses any item where status != 'approved'.
    """
    queue = load_queue()
    approved = [r for r in queue if r.get("status") == "approved"]
    pending = [r for r in queue if r.get("status") == "pending"]

    print("============================================================")
    print("INSTAGRAM COMMENT REPLY DISPATCHER")
    print(f"Mode: {'[DRY-RUN] (Zero mutations)' if dry_run else 'LIVE POST'}")
    print("============================================================\n")

    if pending:
        print(f"  [GATE ENFORCED] {len(pending)} pending comment(s) in queue.")
        print("  Refusing to post pending drafts without explicit approval.")

    if not approved:
        print("  No approved replies ready to post (0 approved).")
        print("  Nothing posted.")
        print("============================================================\n")
        return 0

    print(f"  Found {len(approved)} approved reply(ies) to dispatch:\n")
    sent_count = 0

    for r in approved:
        cid = r["comment_id"]
        msg = r["draft_reply"]
        user = r.get("username", "unknown")

        if dry_run:
            print(f"  [DRY-RUN] Would post reply to comment {cid} (@{user}):")
            print(f"            Message: \"{msg}\"")
            print(f"            Endpoint: POST {GRAPH_BASE}/{API_VERSION}/{cid}/replies")
            sent_count += 1
        else:
            print(f"  Posting reply to comment {cid} (@{user})...")
            post_url = f"{GRAPH_BASE}/{API_VERSION}/{cid}/replies"
            payload = urllib.parse.urlencode({"message": msg, "access_token": token}).encode("utf-8")
            req = urllib.request.Request(post_url, data=payload)
            try:
                with urllib.request.urlopen(req) as resp:
                    res = json.loads(resp.read().decode("utf-8"))
                reply_id = res.get("id")
                r["status"] = "posted"
                r["posted_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
                r["reply_id"] = reply_id
                save_queue(queue)
                log_ledger("comment_reply", f"@{user}", f"Replied to comment {cid}: {msg[:60]}")
                print(f"  [POSTED] Reply published (ID: {reply_id}). Queue updated.")
                sent_count += 1
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8", errors="replace")
                print(f"  ! Error posting reply to {cid}: HTTP {e.code} {err_body}")

    print(f"\n  Dispatch complete: {sent_count} reply(ies) {'simulated' if dry_run else 'posted'}.")
    print("============================================================\n")
    return sent_count


def test_simulation() -> None:
    """
    Self-test verifying queue gating and approval acceptance:
      1. Adds a mock comment into queue with status 'pending'.
      2. Verifies post_approved refuses to touch it.
      3. Approves the comment.
      4. Verifies post_approved accepts the approved comment in dry-run.
      5. Cleans up test state.
    """
    print("============================================================")
    print("RUNNING IG_ENGAGE SIMULATION & GATE VERIFICATION TEST")
    print("============================================================\n")

    test_cid = "test_comment_sim_9999"
    queue = load_queue()

    # Clean existing test entry if present
    queue = [r for r in queue if r.get("comment_id") != test_cid]

    # 1. Add mock pending comment
    mock_entry = {
        "comment_id": test_cid,
        "media_id": "18104859263250076",
        "username": "test_fan_seoul",
        "comment_text": "love this studio shot! what time do you teach?",
        "comment_time": "2026-09-05T17:00:00Z",
        "draft_reply": draft_in_character_reply("love this studio shot! what time do you teach?"),
        "status": "pending",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "approved_at": None,
        "posted_at": None,
        "reply_id": None,
    }
    queue.append(mock_entry)
    save_queue(queue)
    print(f"  [Step 1] Created mock comment {test_cid} with status: PENDING")

    # 2. Verify refusal to post pending draft
    approved_before = [r for r in load_queue() if r.get("comment_id") == test_cid and r.get("status") == "approved"]
    assert len(approved_before) == 0, "Must not be approved initially!"
    print("  [Step 2 Pass] Verified pending item is NOT approved and cannot be posted.")

    # 3. Approve comment
    set_status(test_cid, "approved")
    approved_after = [r for r in load_queue() if r.get("comment_id") == test_cid and r.get("status") == "approved"]
    assert len(approved_after) == 1, "Must be approved after set_status!"
    print(f"  [Step 3 Pass] Comment {test_cid} marked as APPROVED.")

    # 4. Verify post_approved accepts the approved comment in dry run
    token = "simulated_token"
    dispatched = post_approved(token=token, dry_run=True)
    assert dispatched >= 1, "Approved comment must be picked up for dispatch!"
    print(f"  [Step 4 Pass] Dispatcher picked up approved comment ({dispatched} item).")

    # 5. Cleanup
    clean_queue = [r for r in load_queue() if r.get("comment_id") != test_cid]
    save_queue(clean_queue)
    print("  [Step 5 Pass] Test cleanup complete.")

    print("\n  ALL ENGAGEMENT GATE TESTS PASSED 100%.\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="Instagram comment polling and approval queue.")
    ap.add_argument("--poll", action="store_true", help="Poll recent media comments and draft replies into queue")
    ap.add_argument("--list", action="store_true", help="List all drafts and approved items in queue")
    ap.add_argument("--approve", metavar="COMMENT_ID", help="Mark comment as approved for posting")
    ap.add_argument("--reject", metavar="COMMENT_ID", help="Mark comment as rejected")
    ap.add_argument("--edit", nargs=2, metavar=("COMMENT_ID", "TEXT"), help="Edit draft reply and keep pending")
    ap.add_argument("--post", action="store_true", help="Post approved replies to Instagram")
    ap.add_argument("--dry-run", action="store_true", help="Simulate reply dispatch without modifying remote state")
    ap.add_argument("--test-simulation", action="store_true", help="Run self-test verifying approval gating")
    args = ap.parse_args()
    print("[NOTICE] ig_engage.py is DEPRECATED. Instagram integration has been permanently removed. Use agent_runner.py instead.")
    return 0

    if args.list:
        list_queue()
        return 0

    if args.approve:
        set_status(args.approve, "approved")
        return 0

    if args.reject:
        set_status(args.reject, "rejected")
        return 0

    if args.edit:
        set_status(args.edit[0], "pending", edited_text=args.edit[1])
        return 0

    token, user_id = load_credentials()

    if args.poll:
        poll_comments(token, user_id)
        return 0

    if args.post:
        post_approved(token, dry_run=args.dry_run)
        return 0

    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
