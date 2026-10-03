#!/usr/bin/env python3
"""
bsky_follow_graph.py — Curated, rate-limited follow management for @syeonhn.bsky.social.

Why it exists: the follow graph is PUBLIC and shapes the "is she real" impression.
Only follow SFW accounts that fit Seo-yeon's canon (pilates, Seoul life, design,
illustration, books, slow media). NEVER follow adult/competitor/creator-platform
accounts — that would break the private-life illusion and leak the funnel.

Safety:
  - Resolves every handle first (skips nonexistent ones with a warning).
  - Dedupes against her current follows (paginated getFollows) — idempotent.
  - Rate-limited writes (--delay seconds between follows, default 3s).
  - --dry-run does zero writes.
  - Logs every follow to growth/bsky_follows.jsonl for memory/audit.

Usage:
    python growth/bsky_follow_graph.py --list-accounts        # show curated list
    python growth/bsky_follow_graph.py --dry-run              # plan only
    python growth/bsky_follow_graph.py                        # follow (respects --limit/--delay)
    python growth/bsky_follow_graph.py --limit 7 --delay 3
"""
import argparse
import datetime as dt
import json
import os
import pathlib
import sys
import time
import urllib.parse
import urllib.request

GROWTH_DIR = pathlib.Path(__file__).resolve().parent
CRED_FILE = GROWTH_DIR / "bsky_credentials.json"
FOLLOW_LOG = GROWTH_DIR / "bsky_follows.jsonl"
XRPC_BASE = "https://bsky.social/xrpc"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Curated seed list — SFW accounts that fit her canon world. Add/remove freely.
# Fields: handle, display (short human label), why (one line for memory).
CURATED_FOLLOWS = [
    {"handle": "orojiart.bsky.social",
     "display": "Eunbee Kim / ØROJI",
     "why": "picture-book author & illustrator — her reading/art side"},
    {"handle": "danukimart.bsky.social",
     "display": "Danu",
     "why": "illustrator — visual taste she'd share"},
    {"handle": "zinerally.bsky.social",
     "display": "Zinerally",
     "why": "editorial designer — her freelance design world"},
    {"handle": "seoulsearchinglexi.bsky.social",
     "display": "Lexi Song",
     "why": "Seoul life & travel — everyday city texture"},
    {"handle": "chilin777.bsky.social",
     "display": "Chilin",
     "why": "fitness/pilates director — her professional circle"},
    {"handle": "mings99.bsky.social",
     "display": "Mings",
     "why": "illustrator — art feed on her timeline"},
    {"handle": "dusgkwjd1.bsky.social",
     "display": "Yeonha Jeong",
     "why": "webnovel cover illustrator — she reads webnovels"},
    # --------------------------------------------------------------------------
    # BATCH 2 — music, Seoul photography, webtoons/books, illustrators
    # --------------------------------------------------------------------------
    {"handle": "koreanindie.bsky.social",
     "display": "Korean Indie",
     "why": "independent Korean music blog — her late-night listening"},
    {"handle": "koreamusic.bsky.social",
     "display": "Korea Music",
     "why": "Korean indie/R&B curation — background music for the flat"},
    {"handle": "ebysslabs.bsky.social",
     "display": "E Bysslabs",
     "why": "Seoul photo project #4StopsAway — city texture she'd collect"},
    {"handle": "iltalgraphy.bsky.social",
     "display": "Iltalgraphy",
     "why": "fashion & studio photographer — her design/fashion side"},
    {"handle": "cafeoso.bsky.social",
     "display": "Cafe Oso",
     "why": "Hongdae event cafe — Seoul café world"},
    {"handle": "dmwk00.bsky.social",
     "display": "Dmwk00",
     "why": "webtoon author — she reads webtoons"},
    {"handle": "dkbyak.bsky.social",
     "display": "DKB",
     "why": "Wet Sand creator — webtoon/illustration"},
    {"handle": "ttung-gae.bsky.social",
     "display": "Ttung-gae",
     "why": "illustrator — art feed"},
    {"handle": "0lkyou.bsky.social",
     "display": "0lkyou",
     "why": "illustrator — art feed"},
    {"handle": "sika73.bsky.social",
     "display": "Sika73",
     "why": "illustrator — art feed"},
]


def get_credentials() -> tuple[str, str]:
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
        sys.exit("Error: BSKY_HANDLE/BSKY_APP_PASSWORD not set in env or credentials file.")
    if "." not in handle:
        handle = f"{handle}.bsky.social"
    return handle.strip(), app_pw.strip()


def create_session(handle: str, app_pw: str) -> tuple[str, str]:
    payload = json.dumps({"identifier": handle, "password": app_pw}).encode("utf-8")
    req = urllib.request.Request(
        f"{XRPC_BASE}/com.atproto.server.createSession",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        res = json.loads(r.read().decode("utf-8"))
    return res["accessJwt"], res["did"]


def xrpc_get(jwt: str, method: str, params: dict) -> dict:
    qs = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
    req = urllib.request.Request(
        f"{XRPC_BASE}/{method}?{qs}",
        headers={"Authorization": f"Bearer {jwt}"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def xrpc_post(jwt: str, method: str, body: dict) -> dict:
    req = urllib.request.Request(
        f"{XRPC_BASE}/{method}",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {jwt}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def resolve_handle(jwt: str, handle: str) -> str | None:
    try:
        res = xrpc_get(jwt, "com.atproto.identity.resolveHandle", {"handle": handle})
        return res.get("did")
    except Exception as e:
        print(f"  ! resolve failed for {handle}: {e}")

def get_following(jwt: str, actor: str) -> set[str]:
    """Paginated list of DIDs this account already follows."""
    followed: set[str] = set()
    cursor: str | None = None
    while True:
        params: dict = {"actor": actor, "limit": 100}
        if cursor:
            params["cursor"] = cursor
        res = xrpc_get(jwt, "app.bsky.graph.getFollows", params)
        for f in res.get("follows", []):
            followed.add(f.get("did"))
            followed.add((f.get("handle") or "").lower())
        cursor = res.get("cursor")
        if not cursor:
            break
    return followed


def log_follow(entry: dict) -> None:
    with open(FOLLOW_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="Curated Bluesky follow manager for syeonhn")
    ap.add_argument("--list-accounts", action="store_true", help="Show curated follow list")
    ap.add_argument("--dry-run", action="store_true", help="Plan only, zero writes")
    ap.add_argument("--limit", type=int, default=None, help="Max follows to execute this run")
    ap.add_argument("--delay", type=float, default=3.0, help="Seconds between follow writes (default 3)")
    args = ap.parse_args()

    if args.list_accounts:
        for i, a in enumerate(CURATED_FOLLOWS, 1):
            print(f"{i}. @{a['handle']} — {a['display']} — {a['why']}")
        return 0

    handle, app_pw = get_credentials()
    print(f"  Authenticating as @{handle} ...")
    jwt, my_did = create_session(handle, app_pw)
    print(f"  Session OK (DID {my_did[:20]}...)")

    print("  Resolving curated handles ...")
    targets = []
    for a in CURATED_FOLLOWS:
        did = resolve_handle(jwt, a["handle"])
        if did:
            targets.append({**a, "did": did})
            print(f"    ✓ @{a['handle']} -> {did}")
        else:
            print(f"    ✗ @{a['handle']} NOT FOUND — skipped")
    if not targets:
        print("No resolvable targets. Nothing to do.")
        return 1

    print("  Fetching current follow graph ...")
    already = get_following(jwt, handle)
    pending = [t for t in targets if t["did"] not in already]
    skipped_dup = [t for t in targets if t["did"] in already]
    if skipped_dup:
        print(f"  Already following {len(skipped_dup)}: {', '.join(a['display'] for a in skipped_dup)}")
    if args.limit:
        pending = pending[: args.limit]

    if args.dry_run or not pending:
        print(f"\n[DRY-RUN] Would follow {len(pending)} accounts:")
        for t in pending:
            print(f"  + @{t['handle']} — {t['display']} ({t['why']})")
        print("No writes performed.")
        return 0

    print(f"\nFollowing {len(pending)} accounts (delay {args.delay}s)...")
    now_iso = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    ok, fail = 0, 0
    for i, t in enumerate(pending, 1):
        record = {
            "$type": "app.bsky.graph.follow",
            "subject": t["did"],
            "createdAt": now_iso,
        }
        try:
            res = xrpc_post(jwt, "com.atproto.repo.createRecord", {
                "repo": my_did,
                "collection": "app.bsky.graph.follow",
                "record": record,
            })
            uri = res.get("uri")
            log_follow({
                "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
                "surface": "bluesky",
                "action": "follow",
                "target_handle": t["handle"],
                "target_did": t["did"],
                "target_display": t["display"],
                "why": t["why"],
                "uri": uri,
            })
            print(f"  [{i}/{len(pending)}] ✓ followed @{t['handle']} ({t['display']}) {uri}")
            ok += 1
        except Exception as e:
            print(f"  [{i}/{len(pending)}] ✗ failed @{t['handle']}: {e}")
            fail += 1
        if i < len(pending):
            time.sleep(args.delay)

    print(f"\nDone: {ok} followed, {fail} failed.")
    print(f"Log: {FOLLOW_LOG}")
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    sys.exit(main())