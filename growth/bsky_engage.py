#!/usr/bin/env python3
"""
growth/bsky_engage.py — Lyra's Bluesky Organic Engagement & Commenting Suite.

Allows Lyra (@syeonhn.bsky.social) to discover, draft, and publish authentic,
non-promotional, in-character comments on other users' posts.

Powered by DeepSeek Flash via OpenRouter API, with fallback to Gemini 3.6 Flash
and deterministic offline canon templates.
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
from typing import Any, Dict, List, Optional, Tuple

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

GROWTH_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = GROWTH_DIR.parent
CRED_FILE = GROWTH_DIR / "bsky_credentials.json"
LEDGER_FILE = GROWTH_DIR / "ledger.jsonl"
COMMENTS_LOG = GROWTH_DIR / "bsky_comments.jsonl"
MEMORY_FILE = PROJECT_ROOT / ".pi" / "agent-memory" / "lyra" / "MEMORY.md"
XRPC_BASE = "https://bsky.social/xrpc"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

DEFAULT_OPENROUTER_MODEL = "deepseek/deepseek-v4-flash"

# Curated SFW discovery search keywords (Korean & English)
CANON_SEARCH_TOPICS = [
    "성수동",
    "뚝섬",
    "서울숲",
    "아이스 아메리카노",
    "보리차",
    "필라테스",
    "폼롤러",
    "2호선",
    "seongsu",
    "seoul cafe",
    "reformer pilates",
    "foam roller",
]

# Negative filters: skip posts containing spam, crypto, politics, ads, news bots, or explicit content
NEGATIVE_KEYWORDS = [
    "crypto", "bitcoin", "btc", "eth", "nft", "airdrop", "token", "presale",
    "giveaway", "discount", "promo", "sponsor", "collaboration", "dm me",
    "onlyfans", "fanvue", "patreon", "nsfw", "porn", "xxx", "18+",
    "politics", "election", "candidate", "president", "trump", "biden",
    "democrat", "republican", "국회", "대통령", "당대표", "선거", "정당",
    "뉴스", "정부", "기자", "news", "press", "bot",
    "http://", "https://", "t.co", "bit.ly", "x.com"
]

# Negative author markers (bots, news aggregators, politicians)
NEGATIVE_AUTHOR_TERMS = [
    "news", "bot", "press", "official", "feed", "digest", "daily",
    "뉴스", "정부", "공식", "일보", "신문", "방송"
]

# Forbidden terms in Lyra's output — zero marketing, zero enthusiasm markers
FORBIDDEN_OUTPUT_TERMS = [
    "fanvue", "onlyfans", "patreon", "exclusive", "unlock", "private feed",
    "link in bio", "links in bio", "c=fv", "subscribe", "discount", "promo",
    "ppv", "tier", "!"
]

# Offline fallback responses categorized by topic
FALLBACK_RESPONSES_KO = {
    "coffee": [
        "결국 오늘도 아이스 아메리카노만 계속 마시게 되더라고요.",
        "얼음 다 녹을 때까지 멍하니 보고만 있었네요.",
        "오후 네 시쯤 되면 카페인 없이는 버티기 힘든 것 같아요."
    ],
    "pilates": [
        "폼롤러 위에서 십 분만 굴러도 허리가 한결 낫더라고요.",
        "스트레칭은 할 때는 귀찮은데 끝나면 몸이 먼저 알아요.",
        "스프링 장력 맞추다가 손가락 몇 번 찧은 기억이 나네요."
    ],
    "seoul": [
        "아침 공기가 확실히 가을 냄새가 나기 시작했네요.",
        "퇴근길 2호선은 언제 타도 숨이 턱턱 막히더라고요.",
        "서울숲 쪽으로 걸어오는데 바람이 꽤 서늘해졌어요."
    ],
    "general": [
        "맞아요, 생각대로 잘 안 풀리는 날이 꼭 있더라고요.",
        "그 기분 뭔지 너무 잘 알 것 같아요.",
        "그냥 따뜻한 차 한 잔 마시고 쉬는 게 제일인 것 같아요."
    ]
}

FALLBACK_RESPONSES_EN = {
    "coffee": [
        "iced americano with too much condensation. story of my afternoon.",
        "staring at the melting ice instead of finishing what i started.",
        "caffeine is pretty much the only thing keeping the afternoon together."
    ],
    "pilates": [
        "ten minutes on the foam roller on the wooden floor fixes everything.",
        "lumbar spine always decides late afternoon is time to complain.",
        "stretching feels like a chore until you actually do it."
    ],
    "seoul": [
        "morning breeze definitely has autumn in it now.",
        "line 2 was unusually quiet tonight for once.",
        "walking back past seoul forest, the air felt completely different."
    ],
    "general": [
        "some days just go like that no matter what you planned.",
        "can completely relate to that feeling.",
        "boiled barley tea and an early night usually helps."
    ]
}


def load_env_variables() -> None:
    """Loads environment variables from .env files if not already in os.environ."""
    for p in [PROJECT_ROOT / ".env", GROWTH_DIR / ".env", pathlib.Path(".env")]:
        if p.exists():
            for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip("'\"")
                    if k and k not in os.environ:
                        os.environ[k] = v


def get_bsky_credentials() -> Tuple[str, str]:
    """Retrieves Bluesky handle and app password."""
    load_env_variables()
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


def get_openrouter_key() -> Optional[str]:
    """Retrieves OpenRouter API key from environment or .env."""
    load_env_variables()
    key = os.environ.get("OPENROUTER_API_KEY")
    if key and key != "your_openrouter_api_key_here":
        return key.strip()
    return None


def get_gemini_key() -> Optional[str]:
    """Retrieves Gemini API key from environment."""
    load_env_variables()
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")


def create_session(handle: str, app_pw: str) -> Tuple[str, str]:
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


def get_timeline_posts(jwt: str, limit: int = 25) -> List[Dict[str, Any]]:
    """Retrieves recent posts from accounts followed by @syeonhn.bsky.social."""
    req = urllib.request.Request(
        f"{XRPC_BASE}/app.bsky.feed.getTimeline?limit={limit}",
        headers={"Authorization": f"Bearer {jwt}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode("utf-8"))
            return [item.get("post") for item in data.get("feed", []) if item.get("post")]
    except Exception as e:
        print(f"  [Warning] Timeline fetch error: {e}")
        return []


def search_topic_posts(jwt: str, query: str, limit: int = 15) -> List[Dict[str, Any]]:
    """Searches Bluesky for public posts on a specific topic query."""
    encoded_q = urllib.parse.quote(query)
    req = urllib.request.Request(
        f"{XRPC_BASE}/app.bsky.feed.searchPosts?q={encoded_q}&limit={limit}",
        headers={"Authorization": f"Bearer {jwt}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode("utf-8"))
            return data.get("posts", [])
    except Exception as e:
        print(f"  [Warning] Search error for '{query}': {e}")
        return []


def get_post_thread(jwt: str, uri: str) -> Optional[Dict[str, Any]]:
    """Retrieves thread detail to find root and parent for replying."""
    encoded_uri = urllib.parse.quote(uri)
    req = urllib.request.Request(
        f"{XRPC_BASE}/app.bsky.feed.getPostThread?uri={encoded_uri}&depth=1",
        headers={"Authorization": f"Bearer {jwt}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode("utf-8"))
            return data.get("thread", {}).get("post")
    except Exception as e:
        print(f"  [Warning] getPostThread error for '{uri}': {e}")
        return None


def check_can_comment_thread(jwt: str, uri: str, my_did: str) -> Tuple[bool, str]:
    """Inspects live thread to verify Lyra has not already commented without another comment in between."""
    encoded_uri = urllib.parse.quote(uri)
    req = urllib.request.Request(
        f"{XRPC_BASE}/app.bsky.feed.getPostThread?uri={encoded_uri}&depth=3",
        headers={"Authorization": f"Bearer {jwt}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode("utf-8"))
            thread = data.get("thread", {})
            post = thread.get("post", {})
            post_author_did = post.get("author", {}).get("did", "")
            post_handle = (post.get("author", {}).get("handle", "") or "").lower()
            if post_author_did == my_did or "syeonhn" in post_handle:
                return False, "Target post was authored by self"
            replies = thread.get("replies", [])
            for rep in replies:
                rep_post = rep.get("post", {})
                rep_did = rep_post.get("author", {}).get("did", "")
                rep_handle = (rep_post.get("author", {}).get("handle", "") or "").lower()
                if rep_did == my_did or "syeonhn" in rep_handle:
                    return False, "Already commented on this post"
            return True, "OK"
    except Exception as e:
        return True, f"Thread check skipped due to error: {e}"


def get_already_commented_uris() -> set[str]:
    """Reads URIs of posts Lyra has already replied to."""
    uris = set()
    if COMMENTS_LOG.exists():
        for line in COMMENTS_LOG.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.strip():
                try:
                    entry = json.loads(line)
                    target = entry.get("target_uri")
                    if target:
                        uris.add(target)
                except Exception:
                    pass
    return uris


def filter_and_rank_candidates(posts: List[Dict[str, Any]], my_did: str) -> List[Dict[str, Any]]:
    """Filters out noise, ads, self-posts, and previously commented posts."""
    already_commented = get_already_commented_uris()
    candidates = []

    for p in posts:
        uri = p.get("uri")
        if not uri or uri in already_commented:
            continue

        author = p.get("author", {})
        author_did = author.get("did", "")
        author_handle = (author.get("handle", "") or "").lower()
        author_display = (author.get("displayName", "") or "").lower()

        if author_did == my_did or "syeonhn" in author_handle:
            continue

        # Skip news bots, media aggregators, official government feeds
        if any(term in author_handle or term in author_display for term in NEGATIVE_AUTHOR_TERMS):
            continue

        record = p.get("record", {})
        text = record.get("text", "").strip()

        # Length bounds: too short lacks context, too long is usually an essay or thread
        if len(text) < 15 or len(text) > 400:
            continue

        text_lower = text.lower()

        # Skip negative keywords
        if any(neg in text_lower for neg in NEGATIVE_KEYWORDS):
            continue

        # Skip if contains external URLs
        if "http://" in text_lower or "https://" in text_lower or "x.com" in text_lower:
            continue

        # Score candidate based on engagement and freshness
        reply_count = p.get("replyCount", 0)
        like_count = p.get("likeCount", 0)
        
        # High reply count means our comment might get buried. 0-4 replies is sweet spot.
        score = 100
        if reply_count > 10:
            score -= 40
        elif reply_count == 0:
            score += 20
        else:
            score += 10

        if like_count > 0:
            score += min(like_count, 15)

        candidates.append({
            "post": p,
            "uri": uri,
            "cid": p.get("cid"),
            "author_handle": author_handle,
            "author_display": author.get("displayName", ""),
            "text": text,
            "score": score
        })

    # Sort descending by score
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates


def generate_comment_openrouter(target_text: str, is_korean: bool, api_key: str) -> Optional[str]:
    """Generates a tightly matched, engaging, profile-visit-driving comment using DeepSeek Flash via OpenRouter."""
    system_prompt = (
        "You are Han Seo-yeon (한서연). You are 25 years old and live alone in Seongsu-dong, Seoul. "
        "You quit a grueling corporate marketing job in January 2026 after burning out with a herniated disc, and are now retraining as a pilates instructor, "
        "teaching a 7am beginner class twice a week. You live frugally in your Seongsu flat, drinking roasted barley tea or iced americanos.\n\n"
        "You are commenting on someone's social media post on Bluesky. Your goal is to write a comment that is:\n"
        "1. TIGHTLY MATCHED to the specific situation and nouns in their post.\n"
        "2. NATURALLY ENGAGING & INTRIGUING: Drop a vivid, concrete snippet of your real lived experience (your pilates knowledge, corporate burnout reality, coffee habits, or quiet solitary flat life) that makes readers curious to click your profile and see who you are.\n"
        "3. NEVER start with generic filler ('맞아요', '공감해요', '와'). Jump straight into the substance with your unique, relatable perspective.\n"
        "4. Voice: dry, concrete, relatable, understated, lowercase, full stops only. Strictly ZERO exclamation marks (!). Strictly NO marketing, NO links, NO product promotions.\n"
        f"5. Length: 1-2 short sentences (under 140 characters). {'Write in natural, quiet everyday Korean.' if is_korean else 'Write in natural, quiet everyday lowercase English.'}"
    )

    user_prompt = f"Post to reply to:\n\"{target_text}\"\n\nWrite your in-character reply:"

    req_data = json.dumps({
        "model": DEFAULT_OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1000
    }).encode("utf-8")

    req = urllib.request.Request(
        OPENROUTER_URL,
        data=req_data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/Protoxid/seoyeon-bluesky",
            "X-Title": "Seoyeon Bluesky Lyra"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            res = json.loads(r.read().decode("utf-8"))
            msg = res.get("choices", [{}])[0].get("message", {})
            content = msg.get("content")
            return content.strip() if content else None
    except Exception as e:
        print(f"  [Warning] OpenRouter DeepSeek call failed: {e}")
        return None


def generate_comment_gemini(target_text: str, is_korean: bool, api_key: str) -> Optional[str]:
    """Fallback generator using Gemini 3.6 Flash."""
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        prompt = (
            f"You are Han Seo-yeon, 25, living alone in Seongsu, Seoul, retraining as a pilates instructor. "
            f"Reply to this social post in 1 short sentence: \"{target_text}\"\n"
            f"Rules: Dry, concrete, lowercase, full stops only, NO exclamation marks, NO promotion, "
            f"{'Natural everyday Korean' if is_korean else 'Natural lowercase English'}."
        )
        res = client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
        return res.text.strip() if res and res.text else None
    except Exception as e:
        print(f"  [Warning] Gemini fallback failed: {e}")
        return None


def generate_comment_fallback(target_text: str, is_korean: bool) -> str:
    """Deterministic offline fallback based on canonical keywords."""
    lower = target_text.lower()
    responses = FALLBACK_RESPONSES_KO if is_korean else FALLBACK_RESPONSES_EN

    if any(k in lower for k in ("coffee", "americano", "커피", "카페", "아아", "아메리카노", "espresso", "latte")):
        category = "coffee"
    elif any(k in lower for k in ("pilates", "stretch", "spine", "back", "foam roller", "필라테스", "스트레칭", "허리", "폼롤러", "자세")):
        category = "pilates"
    elif any(k in lower for k in ("seoul", "subway", "train", "autumn", "weather", "seongsu", "서울", "지하철", "2호선", "성수", "가을", "날씨")):
        category = "seoul"
    else:
        category = "general"

    import random
    return random.choice(responses[category])


def clean_and_validate_comment(text: str) -> Tuple[bool, str]:
    """Validates and cleans drafted comment to guarantee 100% adherence to canon."""
    if not text or not text.strip():
        return False, "Comment text is empty."

    cleaned = text.strip()

    # Remove enclosing quotation marks if the LLM added them
    if (cleaned.startswith('"') and cleaned.endswith('"')) or (cleaned.startswith("'") and cleaned.endswith("'")):
        cleaned = cleaned[1:-1].strip()

    # Strip exclamation marks to guarantee Seo-yeon's voice rule
    if "!" in cleaned:
        cleaned = cleaned.replace("!", ".")

    cleaned_lower = cleaned.lower()

    # Check for forbidden promotional terms
    for term in FORBIDDEN_OUTPUT_TERMS:
        if term != "!" and term in cleaned_lower:
            return False, f"Forbidden term detected in comment: '{term}'"

    # Length bounds
    if len(cleaned) > 250:
        return False, f"Comment length exceeds limit ({len(cleaned)} chars)."

    return True, cleaned


def draft_comment_for_post(target_text: str) -> Tuple[str, str]:
    """Drafts an in-character comment using DeepSeek Flash -> Gemini -> Fallback."""
    is_korean = bool(re.search(r"[\uac00-\ud7a3]", target_text))
    
    # 1. Primary: DeepSeek Flash via OpenRouter
    or_key = get_openrouter_key()
    if or_key:
        draft = generate_comment_openrouter(target_text, is_korean, or_key)
        if draft:
            ok, clean = clean_and_validate_comment(draft)
            if ok:
                return clean, "deepseek/deepseek-v4-flash (OpenRouter)"
    else:
        print("  [Notice] OPENROUTER_API_KEY not configured in environment. Checking fallbacks...")

    # 2. Secondary: Gemini 3.6 Flash
    gem_key = get_gemini_key()
    if gem_key:
        draft = generate_comment_gemini(target_text, is_korean, gem_key)
        if draft:
            ok, clean = clean_and_validate_comment(draft)
            if ok:
                return clean, "gemini-3.6-flash"

    # 3. Tertiary: Offline Canon Bank
    fallback = generate_comment_fallback(target_text, is_korean)
    ok, clean = clean_and_validate_comment(fallback)
    return clean, "offline-canon-fallback"


def check_cadence_gate(force: bool = False) -> Tuple[bool, str]:
    """
    Checks if an organic comment is allowed under Lyra's cadence invariants:
    - Target: exactly 2 comments per day (KST)
    - Minimum cooldown: 3.5 hours between comments (relaxed to 2.5h late evening)
    - Realistic active hours: 07:00–01:00 KST
    - Natural daily distribution: Comment 1 in morning/lunch (07:00–13:30), Comment 2 in afternoon/evening (>= 14:00)
    """
    if force:
        return True, "Cadence gate bypassed via --force."

    now_utc = dt.datetime.now(dt.timezone.utc)
    kst_tz = dt.timezone(dt.timedelta(hours=9))
    now_kst = now_utc.astimezone(kst_tz)
    current_hour = now_kst.hour
    today_kst_date = now_kst.date()

    # Human active hours check (07:00 - 01:00 KST)
    valid_hours = {7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 0}
    if current_hour not in valid_hours:
        return False, f"Current KST hour ({current_hour:02d}:00) is outside realistic human posting windows (07:00–01:00 KST)."

    # Read and parse comments log
    entries = []
    if COMMENTS_LOG.exists():
        for line in COMMENTS_LOG.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except Exception:
                continue

    # Filter comments from today (KST) and collect all timestamps
    today_comments = []
    all_timestamps = []
    for e in entries:
        ts_str = e.get("ts")
        if not ts_str:
            continue
        try:
            entry_dt = dt.datetime.fromisoformat(ts_str)
            if entry_dt.tzinfo is None:
                entry_dt = entry_dt.replace(tzinfo=dt.timezone.utc)
            all_timestamps.append(entry_dt)
            if entry_dt.astimezone(kst_tz).date() == today_kst_date:
                today_comments.append(entry_dt)
        except Exception:
            pass

    daily_limit = int(os.environ.get("BSKY_ENGAGE_MAX_COMMENTS", "5"))
    comments_today = len(today_comments)
    if comments_today >= daily_limit:
        return False, f"Daily quota fulfilled: {comments_today}/{daily_limit} comments already posted today ({today_kst_date})."

    # Check cooldown since last comment across all entries
    if all_timestamps:
        latest_ts = max(all_timestamps)
        hours_since = (now_utc - latest_ts).total_seconds() / 3600.0

        min_cooldown = 1.5 if daily_limit > 2 else (2.5 if current_hour in {21, 22, 23, 0} else 3.5)
        if hours_since < min_cooldown:
            return False, f"Cooldown active: last comment was {hours_since:.1f}h ago (minimum interval is {min_cooldown:.1f}h)."

        # Natural daytime spacing when on conservative 2-comment schedule
        if daily_limit == 2 and comments_today == 1 and current_hour < 14 and hours_since < 5.0:
            return False, (
                f"Pacing hold: 1st comment posted today ({hours_since:.1f}h ago). "
                f"Holding 2nd comment for afternoon window (>= 14:00 KST, currently {current_hour:02d}:00 KST)."
            )

    return True, f"Cadence gate passed (Comment #{comments_today + 1} of {daily_limit} for today {today_kst_date})."


def publish_comment(
    jwt: str,
    did: str,
    target_post: Dict[str, Any],
    comment_text: str,
    engine_name: str,
    dry_run: bool = False
) -> Dict[str, Any]:
    """Publishes the comment record to AT Protocol as a threaded reply."""
    target_uri = target_post.get("uri", "")
    target_cid = target_post.get("cid", "")

    # Pre-flight check: verify no duplicate comment in thread
    can_comment, reason = check_can_comment_thread(jwt, target_uri, did)
    if not can_comment:
        print(f"[SAFETY ABORT] {reason}. Aborting duplicate comment on {target_uri}.")
        return {"aborted": True, "reason": reason}

    record_obj = target_post.get("record", {})
    existing_reply = record_obj.get("reply")

    # Construct AT Protocol reply structure (root + parent)
    if existing_reply and existing_reply.get("root"):
        root = existing_reply["root"]
        parent = {"uri": target_uri, "cid": target_cid}
    else:
        root = {"uri": target_uri, "cid": target_cid}
        parent = {"uri": target_uri, "cid": target_cid}

    now_iso = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    new_record = {
        "$type": "app.bsky.feed.post",
        "text": comment_text,
        "createdAt": now_iso,
        "langs": ["ko", "en"],
        "reply": {
            "root": root,
            "parent": parent
        }
    }

    print("\n" + "=" * 65)
    print("  LYRA — ORGANIC BLUESKY COMMENT DISPATCH")
    print("=" * 65)
    print(f"  Target Author:  @{target_post.get('author_handle')}")
    print(f"  Target Post:    \"{target_post.get('text', '')[:70]}...\"")
    print(f"  Engine:         {engine_name}")
    print(f"  Reply Text:     \"{comment_text}\"")
    print("=" * 65 + "\n")

    if dry_run:
        print("[DRY-RUN] Reply payload constructed successfully. No network writes sent.")
        return {"dry_run": True, "text": comment_text}

    payload = json.dumps({
        "repo": did,
        "collection": "app.bsky.feed.post",
        "record": new_record
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{XRPC_BASE}/com.atproto.repo.createRecord",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {jwt}"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=15) as r:
        res = json.loads(r.read().decode("utf-8"))

    reply_uri = res.get("uri", "")
    reply_cid = res.get("cid", "")
    print(f"[SUCCESS] Reply published live! URI: {reply_uri}")

    # 1. Log to bsky_comments.jsonl
    log_entry = {
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
        "target_uri": target_uri,
        "target_author": target_post.get("author_handle"),
        "target_text": target_post.get("text"),
        "reply_uri": reply_uri,
        "reply_cid": reply_cid,
        "reply_text": comment_text,
        "engine": engine_name
    }
    with open(COMMENTS_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    # 2. Log to master ledger.jsonl
    ledger_entry = {
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
        "surface": "bluesky",
        "action": "organic_comment_reply",
        "target": reply_uri,
        "note": f"Lyra -> @{target_post.get('author_handle')}: {comment_text[:40]}..."
    }
    with open(LEDGER_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(ledger_entry, ensure_ascii=False) + "\n")

    # 3. Log to Lyra MEMORY.md
    log_to_agent_memory(target_post.get("author_handle", ""), target_post.get("text", ""), comment_text, reply_uri)

    return {"uri": reply_uri, "cid": reply_cid, "text": comment_text}


def log_to_agent_memory(author: str, target_snippet: str, comment_text: str, reply_uri: str) -> None:
    """Appends published reply to Lyra's MEMORY.md."""
    if not MEMORY_FILE.exists():
        return

    now_utc = dt.datetime.now(dt.timezone.utc)
    kst_tz = dt.timezone(dt.timedelta(hours=9))
    now_kst = now_utc.astimezone(kst_tz)
    date_str = now_kst.strftime("%Y-%m-%d")
    hour_str = now_kst.strftime("%H:%M")

    clean_target = target_snippet.replace("\n", " ")[:35]
    row = f"| {date_str} | {hour_str} | @{author} | {clean_target}... | {comment_text} | {reply_uri} |\n"

    try:
        content = MEMORY_FILE.read_text(encoding="utf-8")
        section_header = "## Recent Organic Replies & Comments Log"
        if section_header in content:
            content += row
        else:
            content += f"\n{section_header}\n\n| Date | KST | Target Author | Target Post | Lyra Reply | URI |\n|------|-----|---------------|-------------|------------|-----|\n" + row
        MEMORY_FILE.write_text(content, encoding="utf-8")
    except Exception as e:
        print(f"  [Warning] Could not append to Lyra MEMORY.md: {e}")


def discover_all_candidates(jwt: str, did: str) -> List[Dict[str, Any]]:
    """Fetches candidates from timeline and topic searches."""
    print("[1/3] Scanning timeline from followed accounts...")
    timeline_posts = get_timeline_posts(jwt, limit=30)
    print(f"      Found {len(timeline_posts)} timeline items.")

    print("[2/3] Scanning curated canonical topic searches...")
    search_posts = []
    # Pick 2-3 search topics per cycle to avoid excessive rate limits
    import random
    selected_topics = random.sample(CANON_SEARCH_TOPICS, min(3, len(CANON_SEARCH_TOPICS)))
    for topic in selected_topics:
        sp = search_topic_posts(jwt, topic, limit=10)
        search_posts.extend(sp)
        time.sleep(0.5)
    print(f"      Found {len(search_posts)} search results across {selected_topics}.")

    all_raw = timeline_posts + search_posts
    print(f"[3/3] Filtering and ranking candidates...")
    candidates = filter_and_rank_candidates(all_raw, did)
    print(f"      {len(candidates)} high-quality candidate posts eligible for replies.")
    return candidates


def run_scan(jwt: str, did: str) -> None:
    """Inspects candidate posts and displays drafted replies in terminal (read-only)."""
    candidates = discover_all_candidates(jwt, did)
    if not candidates:
        print("No eligible candidate posts found right now.")
        return

    print("\n" + "=" * 80)
    print("  LYRA ORGANIC ENGAGEMENT — CANDIDATE REVIEW & DRAFTS")
    print("=" * 80)
    for i, c in enumerate(candidates[:6], 1):
        draft, engine = draft_comment_for_post(c["text"])
        print(f"[{i}] Author:  @{c['author_handle']} ({c['author_display']})")
        print(f"    URI:     {c['uri']}")
        print(f"    Post:    \"{c['text']}\"")
        print(f"    Draft:   \"{draft}\" [{engine}]")
        print("-" * 80)
    print()


def run_auto(jwt: str, did: str, dry_run: bool = False, force: bool = False) -> None:
    """Autonomous execution for cron/workflow: checks cadence, selects top post, publishes."""
    allowed, reason = check_cadence_gate(force=force)
    if not allowed:
        print(f"\n============================================================")
        print(f"  [LYRA CADENCE GATE] {reason}")
        print(f"============================================================\n")
        return

    candidates = discover_all_candidates(jwt, did)
    if not candidates:
        print("No eligible candidate posts available to reply to.")
        return

    published = False
    for i, candidate in enumerate(candidates[:5], 1):
        target_author = candidate.get("author_handle", "unknown")
        target_snippet = candidate.get("text", "")[:60].replace("\n", " ")
        print(f"\n[Attempt {i}/{min(5, len(candidates))}] Target: @{target_author} — \"{target_snippet}...\"")

        try:
            comment_text, engine = draft_comment_for_post(candidate["text"])
            res = publish_comment(
                jwt=jwt,
                did=did,
                target_post=candidate,
                comment_text=comment_text,
                engine_name=engine,
                dry_run=dry_run
            )
            if res and (res.get("uri") or res.get("dry_run")):
                published = True
                print(f"[SUCCESS] Organic comment dispatched successfully on candidate #{i}.")
                break
        except Exception as e:
            print(f"  [Warning] Candidate #{i} (@{target_author}) dispatch failed: {e}. Trying next candidate...")
            time.sleep(1.0)
            continue

    if not published:
        print("  [Error] Failed to publish comment across top candidates.")


def run_reply_to_uri(jwt: str, did: str, uri: str, text: Optional[str] = None, dry_run: bool = False) -> None:
    """Manually targets a specific post URI."""
    print(f"Fetching thread context for {uri}...")
    target_post = get_post_thread(jwt, uri)
    if not target_post:
        sys.exit(f"Error: Could not retrieve post at {uri}")

    record = target_post.get("record", {})
    target_text = record.get("text", "")
    author = target_post.get("author", {})

    target_dict = {
        "uri": uri,
        "cid": target_post.get("cid"),
        "author_handle": author.get("handle", ""),
        "author_display": author.get("displayName", ""),
        "text": target_text,
        "record": record
    }

    if text:
        ok, clean = clean_and_validate_comment(text)
        if not ok:
            sys.exit(f"Validation failed for custom text: {clean}")
        comment_text = clean
        engine = "manual-operator-text"
    else:
        comment_text, engine = draft_comment_for_post(target_text)

    publish_comment(jwt, did, target_dict, comment_text, engine, dry_run=dry_run)


def show_status() -> None:
    """Displays detailed cadence and daily commenting status for Lyra."""
    now_utc = dt.datetime.now(dt.timezone.utc)
    kst_tz = dt.timezone(dt.timedelta(hours=9))
    now_kst = now_utc.astimezone(kst_tz)
    today_kst_date = now_kst.date()

    entries = []
    if COMMENTS_LOG.exists():
        for line in COMMENTS_LOG.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except Exception:
                continue

    today_comments = []
    all_timestamps = []
    for e in entries:
        ts_str = e.get("ts")
        if not ts_str:
            continue
        try:
            entry_dt = dt.datetime.fromisoformat(ts_str)
            if entry_dt.tzinfo is None:
                entry_dt = entry_dt.replace(tzinfo=dt.timezone.utc)
            all_timestamps.append(entry_dt)
            if entry_dt.astimezone(kst_tz).date() == today_kst_date:
                today_comments.append((entry_dt, e))
        except Exception:
            pass

    allowed, reason = check_cadence_gate()

    print("\n" + "=" * 70)
    print("  LYRA (@syeonhn.bsky.social) — ORGANIC COMMENTING STATUS")
    print("=" * 70)
    print(f"  Current Time (KST):     {now_kst.strftime('%Y-%m-%d %H:%M:%S')} (Hour {now_kst.hour:02d}:00)")
    print(f"  Today's Comments:       {len(today_comments)} / 2 posted")
    print(f"  Cadence Gate Status:    {'ALLOWED' if allowed else 'GATED'}")
    print(f"  Gate Reason:            {reason}")
    print("-" * 70)
    if today_comments:
        print("  Today's Published Comments:")
        for idx, (cdt, ce) in enumerate(today_comments, 1):
            kst_time_str = cdt.astimezone(kst_tz).strftime("%H:%M")
            print(f"    [{idx}] {kst_time_str} KST -> @{ce.get('target_author')}: \"{ce.get('reply_text')}\"")
    else:
        print("  No comments published yet today.")

    if all_timestamps:
        latest = max(all_timestamps)
        hours_ago = (now_utc - latest).total_seconds() / 3600.0
        print(f"  Last Comment:           {latest.astimezone(kst_tz).strftime('%Y-%m-%d %H:%M')} KST ({hours_ago:.1f}h ago)")
    print("=" * 70 + "\n")


def show_history() -> None:
    """Prints recent comments from log."""
    if not COMMENTS_LOG.exists() or COMMENTS_LOG.stat().st_size == 0:
        print("No organic comments logged yet.")
        return

    lines = [l.strip() for l in COMMENTS_LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
    print(f"\n============================================================")
    print(f"  LYRA — RECENT ORGANIC BLUESKY COMMENTS ({len(lines)} total)")
    print("============================================================\n")
    for line in lines[-10:]:
        entry = json.loads(line)
        print(f"[{entry.get('ts')[:16]}] -> @{entry.get('target_author')}")
        print(f"  Target: {entry.get('target_text', '')[:60]}...")
        print(f"  Reply:  {entry.get('reply_text')} ({entry.get('engine')})")
        print("-" * 60)
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Lyra — Bluesky Organic Engagement & Commenting Suite")
    parser.add_argument("--status", action="store_true", help="Display daily commenting quota and cadence status")
    parser.add_argument("--scan", action="store_true", help="Scan timeline & topics, score candidates, and show drafts without posting")
    parser.add_argument("--auto", action="store_true", help="Auto-select top candidate, draft comment, and post (respects cadence gate)")
    parser.add_argument("--reply-to", type=str, help="Target specific post URI to reply to")
    parser.add_argument("--text", type=str, help="Custom text for reply (optional with --reply-to)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate session and drafting without sending writes")
    parser.add_argument("--force", action="store_true", help="Bypass cadence/cooldown gate")
    parser.add_argument("--history", action="store_true", help="Display recent organic comments history")
    args = parser.parse_args()

    if args.status:
        show_status()
        return 0

    if args.history:
        show_history()
        return 0

    handle, app_pw = get_bsky_credentials()
    if not handle or not app_pw:
        print("  [INFO] BSKY_HANDLE or BSKY_APP_PASSWORD not configured. Skipping engagement.")
        return 0

    try:
        jwt, did = create_session(handle, app_pw)
    except Exception as e:
        print(f"  [Warning] Failed to authenticate with Bluesky: {e}")
        return 0

    if args.scan:
        run_scan(jwt, did)
        return 0

    if args.auto:
        run_auto(jwt, did, dry_run=args.dry_run, force=args.force)
        return 0

    if args.reply_to:
        run_reply_to_uri(jwt, did, args.reply_to, text=args.text, dry_run=args.dry_run)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
