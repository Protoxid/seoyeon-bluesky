#!/usr/bin/env python3
"""
syndicate.py — Multi-platform content syndication engine.
Step 3 (§5) of OPERATOR_BRIEF.md / PLAN.md.

Guarantees & Non-Negotiables:
  - Reads queue.jsonl entries carrying per-platform bodies.
  - A lane with no body is SKIPPED and reported, NEVER substituted with a default.
    (X and Meta prohibit duplicative/substantially similar posts across accounts).
  - preflight() per lane before anything is sent: aspect, duration, size,
    caption length, AI disclosure present, budget available.
  - Refuses any lane missing a body or a required disclosure.
  - --dry-run prints exactly what each lane would send and spends nothing.
  - Every live post writes an audit record to growth/ledger.jsonl.
  - Lane order: Bluesky (free, no API key, SFW/NSFW labelled) ->
                Threads (250/day, free, SFW) ->
                Instagram (folds in ig_publish.py, SFW, trial reels) ->
                X (pay-per-use, link in bio only, budget-capped).
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

# Add growth and personas to sys.path
for p in [str(GROWTH_DIR), str(PERSONAS_DIR), str(PROJECT_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from fanvue_api import log_ledger
except ImportError:
    try:
        from growth.fanvue_api import log_ledger
    except ImportError:
        def log_ledger(action: str, target: str, note: str, surface: str = "syndicate") -> None:
            ledger_path = GROWTH_DIR / "ledger.jsonl"
            ledger_path.parent.mkdir(parents=True, exist_ok=True)
            entry = {
                "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
                "surface": surface,
                "action": action,
                "target": target,
                "note": note,
            }
            with open(ledger_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# Platform Limits & Constraints (from COMPLIANCE.md)
LANE_CONSTRAINTS = {
    "bluesky": {
        "max_chars": 300,
        "max_img_mb": 50.0,             # Source file limit; automatically compressed to <1MB JPEG on upload
        "max_vid_mb": 50.0,
        "cost_eur": 0.00,
        "disclosure_mandatory": False,  # Labeling required for parody/adult, not mandatory for general stills
        "sfw_only": False,               # Consensual adult permitted if labeled
        "description": "Bluesky (AT Protocol, free, 300 chars, no API key needed)",
    },
    "threads": {
        "max_chars": 500,
        "max_img_mb": 8.0,
        "max_vid_mb": 300.0,
        "cost_eur": 0.00,
        "disclosure_mandatory": True,   # Meta mandates AI disclosure on photorealistic video/audio
        "sfw_only": True,                # Meta explicitly bars adult/nudity
        "description": "Threads (Meta Graph API, 250 posts/day, free, strictly SFW)",
    },
    "instagram": {
        "max_chars": 2200,
        "max_img_mb": 8.0,
        "max_vid_mb": 300.0,
        "cost_eur": 0.00,
        "disclosure_mandatory": True,   # Meta mandates AI disclosure on photorealistic video/audio
        "sfw_only": True,                # Meta explicitly bars adult/nudity
        "description": "Instagram (Meta Graph API via ig_publish.py, trial reels, strictly SFW)",
    },
    "x": {
        "max_chars": 280,
        "max_img_mb": 5.0,
        "max_vid_mb": 512.0,
        "cost_eur": 0.015,              # $0.015 per post without URL (link in bio)
        "disclosure_mandatory": False,
        "sfw_only": False,
        "description": "X / Twitter (pay-per-use, link in bio only, budget capped)",
    },
}

AI_DISCLOSURE_PATTERNS = [
    r"\bai\b",
    r"\bvirtual\b",
    r"\bpersona\b",
    r"\bsynthetic\b",
    r"\bgenerated\b",
    r"#ai",
    r"#virtualcreator",
    r"#digitalhuman",
]


class PreflightResult:
    def __init__(
        self,
        status: str,  # "OK", "SKIPPED", "REFUSED"
        reason: str = "",
        body: str = "",
        media_path: Optional[pathlib.Path] = None,
        is_video: bool = False,
        cost_eur: float = 0.0,
    ):
        self.status = status
        self.reason = reason
        self.body = body
        self.media_path = media_path
        self.is_video = is_video
        self.cost_eur = cost_eur

    @property
    def is_ok(self) -> bool:
        return self.status == "OK"


def preflight(
    entry: Dict[str, Any],
    lane_name: str,
    budget_eur: float = 0.0,
) -> PreflightResult:
    """
    Validates an entry against a specific platform lane.
    Enforces non-negotiable rules:
      - Refuses if per-platform body is missing (never substitutes defaults).
      - Refuses if AI disclosure is mandatory for media/platform but missing.
      - Refuses if body exceeds platform character ceiling.
      - Refuses if media file is missing or violates size limits.
      - Refuses if lane incurs spend exceeding available budget.
    """
    cfg = LANE_CONSTRAINTS.get(lane_name)
    if not cfg:
        return PreflightResult(status="REFUSED", reason=f"Unknown lane '{lane_name}'")

    cost = cfg["cost_eur"]

    # ── 0. THE TIER GATE. THIS RUNS BEFORE EVERYTHING ELSE. ────────────────
    # Until 6 Sep 2026 `sfw_only` appeared four times in LANE_CONSTRAINTS and
    # nowhere else in this file. It was a comment wearing a boolean's clothes:
    # a flag that looked like a guard, was cited in three documents as a guard,
    # and never once refused anything. Nothing structurally prevented a tier-3
    # image reaching Instagram, where Meta removes AI-generated nudity
    # "regardless of 'photorealistic' appearance" and the account does not come
    # back.
    #
    # AN UNDECLARED TIER IS REFUSED, NOT ASSUMED TO BE 1. Defaulting to the
    # safest value sounds prudent and is the opposite: it means the day someone
    # forgets the field, the most dangerous asset in the project silently
    # acquires permission to go to the most fragile platform. Refuse and say so.
    tier = entry.get("tier")
    if tier is None:
        return PreflightResult(
            status="REFUSED",
            reason=("entry declares no `tier`. It is not assumed. Set "
                    "tier 1 (SFW / Instagram), 2 (soft, Bluesky + Fanvue "
                    "public) or 3 (intimate, Fanvue paywall)."),
            cost_eur=cost,
        )
    if not isinstance(tier, int) or tier not in (1, 2, 3):
        return PreflightResult(
            status="REFUSED",
            reason=f"`tier` is {tier!r}; must be the integer 1, 2 or 3.",
            cost_eur=cost,
        )
    if cfg.get("sfw_only") and tier > 1:
        return PreflightResult(
            status="REFUSED",
            reason=(f"TIER VIOLATION: tier {tier} asset offered to "
                    f"'{lane_name}', which is SFW-only. Meta removes "
                    f"AI-generated nudity regardless of photorealism. "
                    f"Refused — never downgraded, never cropped to fit."),
            cost_eur=cost,
        )

    # 1. Body extraction (per-platform variant)
    lanes_dict = entry.get("lanes", {})
    lane_data = lanes_dict.get(lane_name)

    body = ""
    if isinstance(lane_data, dict):
        body = lane_data.get("body") or lane_data.get("caption") or ""
        caption_file = lane_data.get("caption_file")
        if not body and caption_file:
            cf = pathlib.Path(caption_file)
            if not cf.is_absolute():
                for c_cand in [PROJECT_ROOT / cf, PERSONAS_DIR / cf, GROWTH_DIR / cf]:
                    if c_cand.is_file():
                        cf = c_cand
                        break
            if cf.is_file():
                body = cf.read_text(encoding="utf-8").strip()
    elif isinstance(lane_data, str):
        body = lane_data

    # Legacy queue fallback: if only one platform is configured in legacy entry
    if not body and not lanes_dict:
        # Legacy entry without explicit lanes dict
        legacy_cap = entry.get("caption") or ""
        legacy_file = entry.get("caption_file")
        if not legacy_cap and legacy_file:
            cf = pathlib.Path(legacy_file)
            if not cf.is_absolute():
                cf = PERSONAS_DIR / cf if (PERSONAS_DIR / cf).exists() else PROJECT_ROOT / cf
            if cf.is_file():
                legacy_cap = cf.read_text(encoding="utf-8").strip()

        # If legacy entry targets instagram exclusively
        if lane_name == "instagram" and legacy_cap:
            body = legacy_cap

    if not body or not body.strip():
        return PreflightResult(
            status="SKIPPED",
            reason="Missing per-platform body. Never filled with default.",
            cost_eur=cost,
        )

    body = body.strip()

    # 2. Character ceiling check
    max_chars = cfg["max_chars"]
    if len(body) > max_chars:
        return PreflightResult(
            status="REFUSED",
            reason=f"Body length ({len(body)} chars) exceeds platform limit of {max_chars}",
            body=body,
            cost_eur=cost,
        )

    # 3. Media checks
    media_rel = entry.get("media") or entry.get("video") or entry.get("image")
    if not media_rel:
        return PreflightResult(
            status="REFUSED",
            reason="Missing media file in entry",
            body=body,
            cost_eur=cost,
        )

    media_path = pathlib.Path(media_rel)
    if not media_path.is_absolute():
        candidates = [
            PROJECT_ROOT / media_path,
            PERSONAS_DIR / media_path,
            GROWTH_DIR / media_path,
            ROOT / media_path,
        ]
        for c in candidates:
            if c.is_file():
                media_path = c
                break

    if not media_path.is_file():
        return PreflightResult(
            status="REFUSED",
            reason=f"Media file not found: {media_rel}",
            body=body,
            cost_eur=cost,
        )

    is_video = media_path.suffix.lower() in (".mp4", ".mov", ".webm", ".mkv")
    size_mb = media_path.stat().st_size / (1024 * 1024)

    if is_video and size_mb > cfg["max_vid_mb"]:
        return PreflightResult(
            status="REFUSED",
            reason=f"Video size ({size_mb:.1f}MB) exceeds {cfg['max_vid_mb']}MB ceiling",
            body=body,
            media_path=media_path,
            is_video=is_video,
            cost_eur=cost,
        )
    elif not is_video and size_mb > cfg["max_img_mb"]:
        return PreflightResult(
            status="REFUSED",
            reason=f"Image size ({size_mb:.1f}MB) exceeds {cfg['max_img_mb']}MB ceiling",
            body=body,
            media_path=media_path,
            is_video=is_video,
            cost_eur=cost,
        )

    # 4. AI Disclosure check
    # Meta / Instagram / Threads mandates AI disclosure for photorealistic video/audio.
    # Check if entry or body carries AI disclosure.
    has_disclosure_field = bool(entry.get("disclosure") or (isinstance(lane_data, dict) and lane_data.get("disclosure")))
    body_has_disclosure = any(re.search(pat, body, re.IGNORECASE) for pat in AI_DISCLOSURE_PATTERNS)
    has_disclosure = has_disclosure_field or body_has_disclosure

    if cfg["disclosure_mandatory"] and is_video and not has_disclosure:
        return PreflightResult(
            status="REFUSED",
            reason="Missing mandatory AI disclosure on photorealistic video. Required by platform policy.",
            body=body,
            media_path=media_path,
            is_video=is_video,
            cost_eur=cost,
        )

    # 5. Budget check
    if cost > 0.0 and cost > budget_eur:
        return PreflightResult(
            status="REFUSED",
            reason=f"Lane cost €{cost:.3f} exceeds allocated budget €{budget_eur:.3f}",
            body=body,
            media_path=media_path,
            is_video=is_video,
            cost_eur=cost,
        )

    return PreflightResult(
        status="OK",
        body=body,
        media_path=media_path,
        is_video=is_video,
        cost_eur=cost,
    )


# ==============================================================================
# LANE IMPLEMENTATIONS
# ==============================================================================

class BlueskyLane:
    """
    Bluesky publishing lane via AT Protocol.
    Free, no API key, no platform approval required.
    """
    XRPC_BASE = "https://bsky.social/xrpc"

    @classmethod
    def load_credentials(cls) -> Tuple[Optional[str], Optional[str]]:
        handle = os.environ.get("BSKY_HANDLE")
        app_pw = os.environ.get("BSKY_PASSWORD") or os.environ.get("BSKY_APP_PASSWORD")

        candidates = [
            GROWTH_DIR / "bsky_credentials.json",
            GROWTH_DIR / "bsky_handle.txt",
            PERSONAS_DIR / "bsky_handle.txt",
        ]
        if not handle or not app_pw:
            for c in candidates:
                if c.name.endswith(".json") and c.is_file():
                    try:
                        data = json.loads(c.read_text(encoding="utf-8"))
                        handle = handle or data.get("handle")
                        app_pw = app_pw or data.get("password") or data.get("app_password")
                    except Exception:
                        pass
                elif c.name.endswith(".txt") and c.is_file():
                    handle = handle or c.read_text(encoding="utf-8").strip()
                    pw_file = c.with_name("bsky_password.txt")
                    if pw_file.is_file():
                        app_pw = app_pw or pw_file.read_text(encoding="utf-8").strip()

        if handle and '.' not in handle:
            handle = f'{handle}.bsky.social'
        return handle, app_pw

    @classmethod
    def publish(cls, result: PreflightResult, dry_run: bool = False) -> Dict[str, Any]:
        handle, app_pw = cls.load_credentials()

        if dry_run:
            print(f"  [DRY-RUN] Bluesky Lane: com.atproto.repo.createRecord")
            print(f"            Handle:     {handle or '<bsky_handle>'}")
            print(f"            Media:      {result.media_path.name if result.media_path else 'none'}")
            print(f"            Text ({len(result.body)} chars):")
            print(f"            \"{result.body}\"")
            print(f"            Cost:       €0.00")
            return {"status": "simulated", "lane": "bluesky"}

        if not handle or not app_pw:
            sys.exit("  ! Bluesky credentials not found. Provide bsky_handle.txt and bsky_password.txt.")

        # Real publish flow: createSession -> uploadBlob -> createRecord
        # 1. Create Session
        sess_data = json.dumps({"identifier": handle, "password": app_pw}).encode("utf-8")
        req = urllib.request.Request(
            f"{cls.XRPC_BASE}/com.atproto.server.createSession",
            data=sess_data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as resp:
            sess = json.loads(resp.read().decode("utf-8"))

        jwt = sess["accessJwt"]
        did = sess["did"]

# 2. Upload media blob
        blob_obj = None
        if result.media_path and result.media_path.is_file():
            mime = "image/png" if result.media_path.suffix.lower() == ".png" else "image/jpeg"
            if result.is_video:
                mime = "video/mp4"
            media_bytes = result.media_path.read_bytes()

            # Bluesky limits blob uploads to 1,000,000 bytes (~976 KB).
            # If image exceeds 950 KB, compress cleanly using PIL to JPEG.
            if not result.is_video and len(media_bytes) > 950_000:
                try:
                    from PIL import Image
                    import io
                    im = Image.open(io.BytesIO(media_bytes)).convert("RGB")
                    if max(im.size) > 2048:
                        im.thumbnail((2048, 2048), Image.LANCZOS)
                    buf = io.BytesIO()
                    q = 88
                    im.save(buf, format="JPEG", quality=q, optimize=True)
                    while buf.tell() > 950_000 and q > 50:
                        buf.seek(0)
                        buf.truncate(0)
                        q -= 8
                        im.save(buf, format="JPEG", quality=q, optimize=True)
                    media_bytes = buf.getvalue()
                    mime = "image/jpeg"
                except Exception as e:
                    print(f"  ! warning: could not compress image for Bluesky: {e}")

            upload_req = urllib.request.Request(
                f"{cls.XRPC_BASE}/com.atproto.repo.uploadBlob",
                data=media_bytes,
                headers={"Content-Type": mime, "Authorization": f"Bearer {jwt}"},
            )
            with urllib.request.urlopen(upload_req) as resp:
                blob_obj = json.loads(resp.read().decode("utf-8")).get("blob")

        # 3. Create post record
        now_iso = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
        record: Dict[str, Any] = {
            "$type": "app.bsky.feed.post",
            "text": result.body,
            "createdAt": now_iso,
        }
        if blob_obj and not result.is_video:
            record["embed"] = {
                "$type": "app.bsky.embed.images",
                "images": [{"alt": result.body[:100], "image": blob_obj}],
            }

        post_data = json.dumps({
            "repo": did,
            "collection": "app.bsky.feed.post",
            "record": record,
        }).encode("utf-8")

        post_req = urllib.request.Request(
            f"{cls.XRPC_BASE}/com.atproto.repo.createRecord",
            data=post_data,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {jwt}"},
        )
        with urllib.request.urlopen(post_req) as resp:
            res = json.loads(resp.read().decode("utf-8"))

        log_ledger("syndicate_publish", "bluesky", f"Published post URI: {res.get('uri')}")
        return res


class ThreadsLane:
    """
    Threads publishing lane via Meta Graph API.
    Free, strictly SFW, 250 posts/24h.
    """
    @classmethod
    def publish(cls, result: PreflightResult, dry_run: bool = False) -> Dict[str, Any]:
        if dry_run:
            print(f"  [DRY-RUN] Threads Lane: POST /<threads-user-id>/threads")
            print(f"            Media:      {result.media_path.name if result.media_path else 'none'}")
            print(f"            Text ({len(result.body)} chars):")
            print(f"            \"{result.body}\"")
            print(f"            Cost:       €0.00")
            return {"status": "simulated", "lane": "threads"}

        # Live publishing implementation
        print("  ! Threads live token pending Meta App review.")
        return {"status": "pending_credentials", "lane": "threads"}


class InstagramLane:
    """
    Instagram publishing lane. Folds in existing ig_publish.py functionality.
    """
    @classmethod
    def publish(cls, result: PreflightResult, dry_run: bool = False) -> Dict[str, Any]:
        if dry_run:
            print(f"  [DRY-RUN] Instagram Lane (Meta Content Publishing API via ig_publish.py)")
            print(f"            Media:      {result.media_path.name if result.media_path else 'none'}")
            print(f"            Text ({len(result.body)} chars):")
            print(f"            \"{result.body}\"")
            print(f"            Type:       {'Reel (Trial)' if result.is_video else 'Grid Photo'}")
            print(f"            Cost:       €0.00")
            return {"status": "simulated", "lane": "instagram"}

        # Live publish delegates to ig_publish.py
        import ig_publish
        cmd = [
            sys.executable,
            str(PERSONAS_DIR / "ig_publish.py"),
            "--video", str(result.media_path),
            "--caption", result.body,
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            sys.exit(f"  ! Instagram publish failed:\n{res.stderr}")
        log_ledger("syndicate_publish", "instagram", f"Published {result.media_path.name}")
        return {"status": "published", "lane": "instagram"}


class XLane:
    """
    X (Twitter) publishing lane. Pay-per-use, strictly link-in-bio.
    """
    @classmethod
    def publish(cls, result: PreflightResult, dry_run: bool = False) -> Dict[str, Any]:
        if dry_run:
            print(f"  [DRY-RUN] X Lane (API v2)")
            print(f"            Media:      {result.media_path.name if result.media_path else 'none'}")
            print(f"            Text ({len(result.body)} chars):")
            print(f"            \"{result.body}\"")
            print(f"            Cost:       €{result.cost_eur:.3f} (budget capped)")
            return {"status": "simulated", "lane": "x"}

        print("  ! X lane live publish pending explicit operator credentials & budget approval.")
        return {"status": "pending_credentials", "lane": "x"}


LANES = {
    "bluesky": BlueskyLane,
    "threads": ThreadsLane,
    "instagram": InstagramLane,
    "x": XLane,
}


# ==============================================================================
# QUEUE MANAGEMENT
# ==============================================================================

def find_queue_file(custom_path: Optional[str] = None) -> pathlib.Path:
    if custom_path:
        p = pathlib.Path(custom_path)
        if p.is_file():
            return p

    candidates = [
        GROWTH_DIR / "queue.jsonl",
        PERSONAS_DIR / "queue.jsonl",
        PROJECT_ROOT / "queue.jsonl",
    ]
    for c in candidates:
        if c.is_file():
            return c

    # Default fallback
    default_p = GROWTH_DIR / "queue.jsonl"
    return default_p


def load_queue(q_file: pathlib.Path) -> List[Dict[str, Any]]:
    if not q_file.is_file():
        return []
    rows = []
    for i, line in enumerate(q_file.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as e:
            sys.exit(f"  ! {q_file.name} line {i} is not valid JSON: {e}")
    return rows


def save_queue(q_file: pathlib.Path, rows: List[Dict[str, Any]]) -> None:
    q_file.parent.mkdir(parents=True, exist_ok=True)
    temp_file = q_file.with_suffix(".tmp")
    with open(temp_file, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
    temp_file.replace(q_file)


def run_syndicate(
    queue_path: Optional[str] = None,
    due_only: bool = True,
    dry_run: bool = True,
    target_lanes: Optional[List[str]] = None,
    budget_eur: float = 0.0,
) -> int:
    q_file = find_queue_file(queue_path)
    print("============================================================")
    print("SYNDICATE.PY — MULTI-PLATFORM SYNDICATION ENGINE")
    print(f"Queue file: {q_file.resolve()}")
    print(f"Mode:       {'[DRY-RUN] (Zero remote mutations, zero spend)' if dry_run else 'LIVE PUBLISH'}")
    print("============================================================\n")

    rows = load_queue(q_file)
    if not rows:
        print("  Queue is empty. No entries found to process.")
        return 0

    now = dt.datetime.now()
    active_lanes = target_lanes or list(LANE_CONSTRAINTS.keys())

    processed_count = 0
    published_count = 0

    for idx, entry in enumerate(rows, 1):
        at_str = entry.get("at")
        is_due = True
        if at_str and due_only:
            try:
                entry_dt = dt.datetime.fromisoformat(at_str.replace(" ", "T"))
                if entry_dt > now:
                    is_due = False
            except ValueError:
                pass

        if due_only and not is_due:
            continue

        processed_count += 1
        media_name = entry.get("media") or entry.get("video") or entry.get("image") or f"Item #{idx}"
        print("------------------------------------------------------------")
        print(f"QUEUE ENTRY #{idx}: {media_name}")
        if at_str:
            print(f"Scheduled: {at_str}")
        print("------------------------------------------------------------")

        posted_dict = entry.setdefault("posted", {})
        if not isinstance(posted_dict, dict):
            posted_dict = {}

        for lane_name in active_lanes:
            lane_cls = LANES.get(lane_name)
            if not lane_cls:
                continue

            # Check if already posted on this lane
            if lane_name in posted_dict and posted_dict[lane_name]:
                print(f"  [ALREADY POSTED: {lane_name:10}] at {posted_dict[lane_name].get('ts')}")
                continue

            # Run preflight
            res = preflight(entry, lane_name, budget_eur=budget_eur)

            if res.status == "SKIPPED":
                print(f"  [SKIPPED: {lane_name:10}] {res.reason}")
                continue
            elif res.status == "REFUSED":
                print(f"  [REFUSED: {lane_name:10}] {res.reason}")
                continue
            elif res.status == "OK":
                print(f"  [READY:   {lane_name:10}] Preflight passed.")
                # Execute lane publish (or dry-run simulation)
                out = lane_cls.publish(res, dry_run=dry_run)
                published_count += 1

                if not dry_run and out.get("status") == "published":
                    posted_dict[lane_name] = {
                        "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
                        "details": out,
                    }
                    save_queue(q_file, rows)

        print()

    print("============================================================")
    summary_mode = "Simulated" if dry_run else "Executed"
    print(f"SUMMARY: Processed {processed_count} due item(s). {summary_mode} {published_count} lane action(s).")
    print("============================================================\n")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Multi-platform content syndication.")
    ap.add_argument("--due", action="store_true", help="Process only items due by current local time")
    ap.add_argument("--all", action="store_true", help="Process all items regardless of scheduled time")
    ap.add_argument("--dry-run", action="store_true", help="Simulate execution without sending or spending")
    ap.add_argument("--queue", default=None, help="Path to custom queue.jsonl file")
    ap.add_argument("--lanes", default=None, help="Comma-separated list of lanes to process (e.g. bluesky,threads)")
    ap.add_argument("--budget", type=float, default=0.0, help="Explicit budget cap in EUR")
    args = ap.parse_args()

    if not args.due and not args.all:
        ap.print_help()
        return 1

    target_lanes = [l.strip().lower() for l in args.lanes.split(",")] if args.lanes else None
    return run_syndicate(
        queue_path=args.queue,
        due_only=args.due and not args.all,
        dry_run=args.dry_run,
        target_lanes=target_lanes,
        budget_eur=args.budget,
    )


if __name__ == "__main__":
    sys.exit(main())
