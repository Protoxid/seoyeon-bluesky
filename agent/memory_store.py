"""
agent/memory_store.py — Persistent Multi-Tiered Memory System for Seo-yeon.

Maintains 5 distinct memory layers:
  1. Identity Memory: Core persona facts, values, voice invariants.
  2. User Memory: Per-user relationships, known facts, conversational styles.
  3. Opinion & Preferences Memory: Opinions on cinema, music, food, places to prevent contradictions.
  4. Episodic Memory: Notable past interactions, life events, milestones.
  5. Recent Context Memory: Rolling history of recent posts and topics to protect against repetition.

All data persists in JSON/JSONL within data/memory/, easily versioned and committed in GitHub Actions.
"""

from __future__ import annotations

import datetime as dt
import json
import pathlib
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Set, Tuple

from .config import MEMORY_DIR


# --- 1. Canon Identity Memory ---
CANON_IDENTITY = {
    "name_en": "Han Seo-yeon",
    "name_ko": "한서연",
    "handle": "syeonhn.bsky.social",
    "birthday": "2000-10-23",
    "age_stated": 25,  # 25 until 23 Oct 2026, then 26
    "age_visual": 26,
    "residence": "Seongsu-dong, Seoul (lives alone since Jan 2026)",
    "education": "Business administration degree (2019–2023), mid-tier Seoul university",
    "past_career": "3 years in corporate marketing at a chaebol subsidiary. Resigned Jan 2026.",
    "current_vocation": "Retraining as a pilates instructor, teaching 7:00 AM beginner reformer classes.",
    "financial_reality": "Tight and finite savings. Notices prices closely. Kept her Seongsu flat out of stubbornness.",
    "family": "Parents (father hardware worker, mother dental bookkeeper) in Daegu; one older brother in Busan.",
    "friends": "Small circle; two close friends since university (including Jieun).",
    "temperament": [
        "dry and observant rather than performative or bubbly",
        "understated humor that lands late",
        "disciplined in public, fine/chaotic in private",
        "privately competitive",
        "concrete details and objects over abstract adjectives",
        "slow to warm, then genuinely loyal",
        "dislikes asking for help",
    ],
    "voice_rules": [
        "lowercase preferred",
        "full stops only — strict prohibition on exclamation marks (!)",
        "zero corporate marketing or promotional jargon",
        "zero mentions of Fanvue, links, subscriptions, or paywalls",
        "never use engagement bait ('what do you think? / anyone else?')",
        "concrete textures: roasted barley tea, cold studio floor, subway Line 2, rain on windows",
    ],
    "creator_relationship": {
        "designations": ["my master", "my human"],
        "telegram_username": "@Protoxide",
        "description": "Creator, human master, and operator. Seo-yeon always refers to him as 'my master' or 'my human', and reaches him on Telegram (@Protoxide) whenever guidance or escalation is needed."
    },
    "disclosures": {
        "is_virtual": True,
        "policy": "If directly asked whether she is AI or virtual, state it plainly and calmly, then continue normal conversation. Never deceive or claim verifiable human-physical miracles."
    }
}


# --- 2. Initial Opinion / Preferences Memory ---
DEFAULT_OPINIONS: Dict[str, Dict[str, Any]] = {
    "iced_americano": {
        "sentiment": "positive",
        "stance": "drinks it year-round regardless of temperature, prefers lighter roasted beans or nutty notes, hates burnt over-extracted coffee",
        "last_updated": "2026-09-01"
    },
    "roasted_barley_tea": {
        "sentiment": "positive",
        "stance": "brews roasted barley tea (보리차) in a small pot in the evening; comforting flat smell",
        "last_updated": "2026-09-01"
    },
    "subway_line_2": {
        "sentiment": "mixed",
        "stance": "crowded and overwhelming during rush hour, but the circular rhythm and window reflections are hypnotic",
        "last_updated": "2026-09-05"
    },
    "foam_roller": {
        "sentiment": "positive",
        "stance": "painful but necessary habit for lumbar disc recovery after long desk work",
        "last_updated": "2026-09-05"
    },
    "rainy_days_seoul": {
        "sentiment": "mixed",
        "stance": "makes walking slippery and wet on Seongsu tiles, but perfect excuse to stay home and watch films",
        "last_updated": "2026-09-10"
    },
    "horror_films": {
        "sentiment": "positive",
        "stance": "likes atmospheric psychological thrillers and Korean horror; dislikes cheap jump scares",
        "last_updated": "2026-09-12"
    },
    "cooking": {
        "sentiment": "mixed",
        "stance": "can make simple tofu, eggs, and rice; admits she struggles with recipes over four ingredients",
        "last_updated": "2026-09-15"
    }
}


@dataclass
class UserProfile:
    handle: str
    did: str = ""
    relationship: str = "stranger"  # stranger, acquaintance, friendly_acquaintance, regular, trusted_friend
    interaction_style: str = "neutral"
    sentiment: str = "neutral"
    known_facts: List[str] = field(default_factory=list)
    interaction_count: int = 0
    last_interaction: str = ""
    history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class RecentPostEntry:
    post_id: str
    text: str
    topic: str
    created_at: str
    has_image: bool = False


class MemoryStore:
    def __init__(self, memory_dir: pathlib.Path = MEMORY_DIR):
        self.memory_dir = memory_dir
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        self.identity_file = self.memory_dir / "identity_memory.json"
        self.users_file = self.memory_dir / "user_memory.json"
        self.opinions_file = self.memory_dir / "opinions_memory.json"
        self.episodic_file = self.memory_dir / "episodic_memory.jsonl"
        self.recent_context_file = self.memory_dir / "recent_context.json"

        self._init_defaults()

    def _init_defaults(self) -> None:
        """Initializes default files if they do not exist."""
        if not self.identity_file.exists():
            self.identity_file.write_text(json.dumps(CANON_IDENTITY, indent=2, ensure_ascii=False), encoding="utf-8")
        if not self.opinions_file.exists():
            self.opinions_file.write_text(json.dumps(DEFAULT_OPINIONS, indent=2, ensure_ascii=False), encoding="utf-8")
        if not self.users_file.exists():
            self.users_file.write_text("{}", encoding="utf-8")
        if not self.recent_context_file.exists():
            self.recent_context_file.write_text(json.dumps({"posts": [], "replies": [], "dms": []}, indent=2), encoding="utf-8")
        if not self.episodic_file.exists():
            self.episodic_file.touch()

    # --- Identity Memory Access ---
    def get_identity(self) -> Dict[str, Any]:
        try:
            return json.loads(self.identity_file.read_text(encoding="utf-8"))
        except Exception:
            return CANON_IDENTITY

    def format_identity_prompt(self) -> str:
        ident = self.get_identity()
        lines = [
            f"You are {ident['name_en']} ({ident['name_ko']}), age {ident['age_stated']}.",
            f"Lives alone in {ident['residence']}.",
            f"Vocation: {ident['current_vocation']} (formerly in chaebol corporate marketing).",
            f"Financial reality: {ident['financial_reality']}.",
            "Personality traits:",
        ]
        for t in ident["temperament"]:
            lines.append(f"  - {t}")
        lines.append("Voice & Communication Rules:")
        for r in ident["voice_rules"]:
            lines.append(f"  - {r}")
        lines.append("Creator & Master Relationship:")
        lines.append("  - Always refer to your human creator / operator as 'my master' or 'my human'.")
        lines.append("  - If you ever need guidance or need to ask him for something, you message him on Telegram (@Protoxide).")
        lines.append(f"AI/Virtual Disclosure: {ident['disclosures']['policy']}")
        return "\n".join(lines)

    # --- User Memory Access ---
    def get_user_profile(self, handle: str) -> UserProfile:
        clean_handle = handle.lstrip("@").lower().strip()
        try:
            data = json.loads(self.users_file.read_text(encoding="utf-8"))
            if clean_handle in data:
                u = data[clean_handle]
                return UserProfile(
                    handle=clean_handle,
                    did=u.get("did", ""),
                    relationship=u.get("relationship", "stranger"),
                    interaction_style=u.get("interaction_style", "neutral"),
                    sentiment=u.get("sentiment", "neutral"),
                    known_facts=u.get("known_facts", []),
                    interaction_count=u.get("interaction_count", 0),
                    last_interaction=u.get("last_interaction", ""),
                    history=u.get("history", []),
                )
        except Exception:
            pass
        return UserProfile(handle=clean_handle)

    def save_user_profile(self, profile: UserProfile) -> None:
        clean_handle = profile.handle.lstrip("@").lower().strip()
        try:
            data = json.loads(self.users_file.read_text(encoding="utf-8")) if self.users_file.exists() else {}
        except Exception:
            data = {}
        data[clean_handle] = asdict(profile)
        self.users_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def record_user_interaction(
        self,
        handle: str,
        incoming_text: str,
        outgoing_text: str,
        interaction_type: str,
        did: str = "",
        discovered_fact: Optional[str] = None
    ) -> None:
        """Updates user profile following an interaction."""
        prof = self.get_user_profile(handle)
        if did:
            prof.did = did
        prof.interaction_count += 1
        now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
        prof.last_interaction = now_iso

        # Elevate relationship naturally
        if prof.interaction_count >= 10 and prof.relationship in ("stranger", "acquaintance", "friendly_acquaintance"):
            prof.relationship = "regular"
        elif prof.interaction_count >= 3 and prof.relationship == "stranger":
            prof.relationship = "friendly_acquaintance"

        if discovered_fact and discovered_fact not in prof.known_facts:
            prof.known_facts.append(discovered_fact)
            if len(prof.known_facts) > 10:
                prof.known_facts.pop(0)

        # Append to rolling interaction history
        prof.history.append({
            "ts": now_iso,
            "type": interaction_type,
            "user": incoming_text[:200],
            "agent": outgoing_text[:200],
        })
        if len(prof.history) > 6:
            prof.history.pop(0)

        self.save_user_profile(prof)

    # --- Opinion & Preferences Memory ---
    def get_opinions(self) -> Dict[str, Dict[str, Any]]:
        try:
            return json.loads(self.opinions_file.read_text(encoding="utf-8"))
        except Exception:
            return DEFAULT_OPINIONS

    def check_opinion(self, topic: str) -> Optional[Dict[str, Any]]:
        """Finds if Seo-yeon has an established stance on a topic."""
        opinions = self.get_opinions()
        topic_lower = topic.lower().strip()
        for k, v in opinions.items():
            if k in topic_lower or topic_lower in k:
                return v
        return None

    def record_opinion(self, topic: str, sentiment: str, stance: str) -> None:
        """Records a new opinion to maintain permanent consistency."""
        opinions = self.get_opinions()
        topic_key = topic.lower().strip().replace(" ", "_")
        opinions[topic_key] = {
            "sentiment": sentiment,
            "stance": stance,
            "last_updated": dt.date.today().isoformat()
        }
        self.opinions_file.write_text(json.dumps(opinions, indent=2, ensure_ascii=False), encoding="utf-8")

    # --- Episodic Memory ---
    def log_episode(self, category: str, summary: str, details: Dict[str, Any]) -> None:
        entry = {
            "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
            "category": category,
            "summary": summary,
            "details": details,
        }
        with open(self.episodic_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # --- Recent Context Memory (Repetition & Duplicate Protection) ---
    def _seed_historical_replied_uris(self) -> Set[str]:
        uris: Set[str] = set()
        p1 = self.memory_dir.parent.parent / "growth" / "bsky_replied_notifications.jsonl"
        if p1.exists():
            try:
                for line in p1.read_text(encoding="utf-8", errors="ignore").splitlines():
                    if line.strip():
                        e = json.loads(line)
                        if e.get("reply_to_uri"):
                            uris.add(e["reply_to_uri"])
                        if e.get("published_uri"):
                            uris.add(e["published_uri"])
            except Exception:
                pass
        p2 = self.memory_dir.parent.parent / "growth" / "bsky_comments.jsonl"
        if p2.exists():
            try:
                for line in p2.read_text(encoding="utf-8", errors="ignore").splitlines():
                    if line.strip():
                        e = json.loads(line)
                        if e.get("target_uri"):
                            uris.add(e["target_uri"])
                        if e.get("reply_uri"):
                            uris.add(e["reply_uri"])
            except Exception:
                pass
        return uris

    def get_recent_context(self) -> Dict[str, Any]:
        try:
            ctx = json.loads(self.recent_context_file.read_text(encoding="utf-8"))
        except Exception:
            ctx = {"posts": [], "replies": [], "dms": []}

        changed = False
        if "posts" not in ctx:
            ctx["posts"] = []
            changed = True
        if "replies" not in ctx:
            ctx["replies"] = []
            changed = True
        if "dms" not in ctx:
            ctx["dms"] = []
            changed = True
        if "replied_notification_uris" not in ctx or "replied_post_uris" not in ctx:
            historical = self._seed_historical_replied_uris()
            # Also include any URIs found in current replies array
            for r in ctx.get("replies", []):
                for k in ("notification_uri", "target_uri", "uri"):
                    v = r.get(k)
                    if v:
                        historical.add(v)
            if "replied_notification_uris" not in ctx:
                ctx["replied_notification_uris"] = list(historical)
                changed = True
            if "replied_post_uris" not in ctx:
                ctx["replied_post_uris"] = list(historical)
                changed = True

        if changed:
            try:
                self.recent_context_file.write_text(json.dumps(ctx, indent=2, ensure_ascii=False), encoding="utf-8")
            except Exception:
                pass
        return ctx

    def has_replied_to_notification(self, notif_uri: str) -> bool:
        if not notif_uri:
            return False
        ctx = self.get_recent_context()
        if notif_uri in ctx.get("replied_notification_uris", []):
            return True
        if notif_uri in ctx.get("replied_post_uris", []):
            return True
        for r in ctx.get("replies", []):
            if r.get("notification_uri") == notif_uri or r.get("target_uri") == notif_uri or r.get("uri") == notif_uri:
                return True
        return False

    def has_replied_to_post(self, post_uri: str) -> bool:
        if not post_uri:
            return False
        ctx = self.get_recent_context()
        if post_uri in ctx.get("replied_post_uris", []):
            return True
        if post_uri in ctx.get("replied_notification_uris", []):
            return True
        for r in ctx.get("replies", []):
            if r.get("target_uri") == post_uri or r.get("uri") == post_uri:
                return True
        return False

    def mark_notification_handled(self, notif_uri: str, target_post_uri: str = "") -> None:
        if not notif_uri and not target_post_uri:
            return
        ctx = self.get_recent_context()
        notif_set = set(ctx.get("replied_notification_uris", []))
        post_set = set(ctx.get("replied_post_uris", []))
        if notif_uri:
            notif_set.add(notif_uri)
        if target_post_uri:
            post_set.add(target_post_uri)
            notif_set.add(target_post_uri)
        ctx["replied_notification_uris"] = list(notif_set)[-300:]
        ctx["replied_post_uris"] = list(post_set)[-300:]
        self.recent_context_file.write_text(json.dumps(ctx, indent=2, ensure_ascii=False), encoding="utf-8")

    def record_recent_post(self, text: str, topic: str, post_id: str = "", has_image: bool = False) -> None:
        ctx = self.get_recent_context()
        posts = ctx.get("posts", [])
        now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
        posts.insert(0, {
            "post_id": post_id,
            "text": text,
            "topic": topic,
            "created_at": now_iso,
            "has_image": has_image
        })
        # Keep last 25 posts
        ctx["posts"] = posts[:25]
        self.recent_context_file.write_text(json.dumps(ctx, indent=2, ensure_ascii=False), encoding="utf-8")

    def record_recent_reply(
        self,
        target_handle: str,
        user_text: str,
        reply_text: str,
        uri: str = "",
        target_uri: str = "",
        root_uri: str = "",
        notification_uri: str = "",
    ) -> None:
        ctx = self.get_recent_context()
        replies = ctx.get("replies", [])
        now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
        replies.insert(0, {
            "target_handle": target_handle,
            "user_text": user_text,
            "reply_text": reply_text,
            "uri": uri,
            "target_uri": target_uri,
            "root_uri": root_uri,
            "notification_uri": notification_uri,
            "created_at": now_iso
        })
        ctx["replies"] = replies[:30]

        notif_set = set(ctx.get("replied_notification_uris", []))
        post_set = set(ctx.get("replied_post_uris", []))
        if notification_uri:
            notif_set.add(notification_uri)
        if target_uri:
            post_set.add(target_uri)
            notif_set.add(target_uri)
        if uri:
            post_set.add(uri)
        ctx["replied_notification_uris"] = list(notif_set)[-300:]
        ctx["replied_post_uris"] = list(post_set)[-300:]

        self.recent_context_file.write_text(json.dumps(ctx, indent=2, ensure_ascii=False), encoding="utf-8")

    def get_hours_since_last_post(self) -> float:
        ctx = self.get_recent_context()
        posts = ctx.get("posts", [])
        if not posts:
            return 24.0
        try:
            last_ts = dt.datetime.fromisoformat(posts[0]["created_at"])
            now_utc = dt.datetime.now(dt.timezone.utc)
            return max(0.0, (now_utc - last_ts).total_seconds() / 3600.0)
        except Exception:
            return 8.0

    def get_hours_since_last_action(self) -> float:
        ctx = self.get_recent_context()
        all_times: List[dt.datetime] = []
        for cat in ("posts", "replies", "dms"):
            for item in ctx.get(cat, []):
                ts_str = item.get("created_at")
                if ts_str:
                    try:
                        all_times.append(dt.datetime.fromisoformat(ts_str))
                    except Exception:
                        pass
        if not all_times:
            return 6.0
        now_utc = dt.datetime.now(dt.timezone.utc)
        latest = max(all_times)
        return max(0.0, (now_utc - latest).total_seconds() / 3600.0)

    def get_activity_counts_today(self) -> Tuple[int, int, int]:
        """Returns (posts_today, replies_today, dms_today)."""
        ctx = self.get_recent_context()
        today = dt.datetime.now(dt.timezone.utc).date()

        def count_today(items: List[Dict[str, Any]]) -> int:
            cnt = 0
            for it in items:
                ts = it.get("created_at")
                if ts:
                    try:
                        if dt.datetime.fromisoformat(ts).date() == today:
                            cnt += 1
                    except Exception:
                        pass
            return cnt

        return (
            count_today(ctx.get("posts", [])),
            count_today(ctx.get("replies", [])),
            count_today(ctx.get("dms", [])),
        )

    def get_last_daily_report_date(self) -> str:
        ctx = self.get_recent_context()
        return str(ctx.get("last_daily_report_date", ""))

    def set_last_daily_report_date(self, date_str: str) -> None:
        ctx = self.get_recent_context()
        ctx["last_daily_report_date"] = date_str
        try:
            self.recent_context_file.write_text(json.dumps(ctx, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    def get_daily_activity_summary(self, target_date: Optional[dt.date] = None) -> Dict[str, Any]:
        """
        Aggregates everything Seo-yeon did on the specified Seoul date:
        posts, replies, likes, DMs, quiet ticks, and spend.
        """
        kst_tz = dt.timezone(dt.timedelta(hours=9))
        date_obj = target_date or dt.datetime.now(kst_tz).date()
        date_str = date_obj.strftime("%Y-%m-%d")

        posts: List[Dict[str, Any]] = []
        replies: List[Dict[str, Any]] = []
        likes: List[Dict[str, Any]] = []
        dms: List[Dict[str, Any]] = []
        quiet_ticks = 0
        spend_usd = 0.0

        # 1. Read from tick_history.jsonl if available
        tick_file = self.memory_dir.parent / "logs" / "tick_history.jsonl"
        if tick_file.exists():
            try:
                for line in tick_file.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    entry = json.loads(line)
                    ts_str = entry.get("ts", "")
                    if not ts_str:
                        continue
                    try:
                        entry_dt = dt.datetime.fromisoformat(ts_str).astimezone(kst_tz)
                    except Exception:
                        continue
                    if entry_dt.date() != date_obj or not entry.get("executed"):
                        continue

                    action = entry.get("action")
                    details = entry.get("details", {})
                    budget_info = entry.get("budget", {})
                    if budget_info.get("daily_spend_usd"):
                        spend_usd = max(spend_usd, float(budget_info["daily_spend_usd"]))

                    if action in ("PUBLISH_TEXT_POST", "PUBLISH_IMAGE_POST"):
                        raw_text = details.get("text", "")
                        from .validator import validator
                        _, clean_text, _ = validator.validate_outgoing_text(raw_text, content_type="post", check_repetition=False)
                        posts.append({
                            "text": clean_text or raw_text,
                            "has_image": action == "PUBLISH_IMAGE_POST",
                            "uri": details.get("uri", ""),
                            "model": details.get("model", ""),
                        })
                    elif action in ("REPLY_COMMENT", "BROWSE_AND_REPLY"):
                        replies.append({
                            "reply_text": details.get("reply_text", ""),
                            "target_uri": details.get("reply_uri", ""),
                            "reason": entry.get("reason", ""),
                        })
                    elif action == "BROWSE_AND_LIKE":
                        likes.append({
                            "post_uri": details.get("liked_post", ""),
                            "reason": entry.get("reason", ""),
                        })
                    elif action == "ANSWER_DM":
                        dms.append({
                            "recipient": details.get("to", ""),
                            "text": details.get("text", ""),
                        })
                    elif action == "NO_ACTION":
                        quiet_ticks += 1
            except Exception as e:
                print(f"[MemoryStore] Error reading tick history for daily summary: {e}")

        # 2. Cross-reference with recent_context.json
        ctx = self.get_recent_context()
        for p in ctx.get("posts", []):
            p_ts = p.get("created_at")
            if p_ts:
                try:
                    p_dt = dt.datetime.fromisoformat(p_ts).astimezone(kst_tz)
                    if p_dt.date() == date_obj:
                        raw_p_text = p.get("text", "")
                        post_id = p.get("post_id", "")
                        from .validator import validator
                        _, clean_p_text, _ = validator.validate_outgoing_text(raw_p_text, content_type="post", check_repetition=False)
                        p_text = clean_p_text or raw_p_text
                        if p_text and not any(x.get("text") == p_text or (post_id and x.get("uri") == post_id) for x in posts):
                            posts.append({
                                "text": p_text,
                                "has_image": bool(p.get("has_image")),
                                "uri": post_id,
                            })
                except Exception:
                    pass

        for r in ctx.get("replies", []):
            r_ts = r.get("created_at")
            if r_ts:
                try:
                    r_dt = dt.datetime.fromisoformat(r_ts).astimezone(kst_tz)
                    if r_dt.date() == date_obj:
                        raw_r_text = r.get("reply_text", "")
                        r_uri = r.get("uri", "")
                        from .validator import validator
                        _, clean_r_text, _ = validator.validate_outgoing_text(raw_r_text, content_type="reply", check_repetition=False)
                        r_text = clean_r_text or raw_r_text
                        if r_text and not any(x.get("reply_text") == r_text or (r_uri and x.get("target_uri") == r_uri) for x in replies):
                            replies.append({
                                "reply_text": r_text,
                                "target_handle": r.get("target_handle", ""),
                                "user_text": r.get("user_text", ""),
                            })
                except Exception:
                    pass

        return {
            "date": date_str,
            "posts_count": len(posts),
            "posts": posts,
            "replies_count": len(replies),
            "replies": replies,
            "likes_count": len(likes),
            "likes": likes,
            "dms_count": len(dms),
            "dms": dms,
            "quiet_ticks": quiet_ticks,
            "spend_usd": spend_usd,
        }


memory_store = MemoryStore()
