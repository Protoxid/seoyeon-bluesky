"""Her self-model: a small set of behaviors she adjusts herself from evidence, within fixed bounds.

The operator asked (2026-11-16) for a first, light step toward self-directed learning. Every few days she
reviews how her own recent posts actually went (replies and conversations count most; likes count little)
and may adjust two things:

- interests: how much weight each area of her life gets when she picks what to post about;
- rhythm: how many posts of her own a day, and the minimum gap between them.

Everything else stays fixed: identity, safety, privacy, honesty and the hard limits in config. Each change
must cite at least two of her posts as evidence, is bounded in size, is reported to the operator on Telegram,
and can be undone with ``/learning undo``. ``/learning pause`` stops further changes.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from .runtime import MODE
from .storage import file_lock, read_json, write_json

# Same ids as the life threads in life.py, so interests and her day sketch speak the same language.
INTERESTS = ("pilates", "back", "money", "after_marketing", "jieun", "family", "home", "culture")
WEIGHT_MIN, WEIGHT_MAX, WEIGHT_STEP = 0.4, 2.0, 0.4
CORE_MINIMUM = {"pilates": 0.8}  # her vocation stays central whatever the numbers say
MAX_GAP_HOURS, GAP_STEP = 8.0, 1.5
REVIEW_INTERVAL_HOURS = 60
MIN_POSTS_FOR_REVIEW = 4
MAX_CHANGES = 3
HISTORY_KEEP = 20


def _now():
    return dt.datetime.now(dt.timezone.utc)


def default_model(config):
    return {"interests": {name: 1.0 for name in INTERESTS},
            "rhythm": {"posts_per_day": config.max_posts_per_day, "min_gap_hours": config.min_post_gap_hours},
            "paused": False, "last_review_at": "", "history": []}


class SelfModel:
    def __init__(self, path=None):
        self.checkpoint = lambda: None
        if path is None:
            from .vault import vault
            path = vault.vault_dir / "self_model.json"
            self.checkpoint = vault.save_vault
        self.path = Path(path)

    def load(self):
        from .config import config
        data = read_json(self.path, {})
        base = default_model(config)
        for key, value in base.items():
            data.setdefault(key, value)
        for name in INTERESTS:
            data["interests"].setdefault(name, 1.0)
        data["rhythm"] = {**base["rhythm"], **data.get("rhythm", {})}
        return data

    def _save(self, data):
        with file_lock(self.path):
            write_json(self.path, data)
        self.checkpoint()

    # --- what the rest of the agent reads -------------------------------------------------------------
    def post_cap(self, config):
        """Own posts per day: her learned rhythm, never above the hard limit in config."""
        return max(1, min(int(self.load()["rhythm"]["posts_per_day"]), config.max_posts_per_day))

    def min_gap_hours(self, config):
        return max(float(self.load()["rhythm"]["min_gap_hours"]), config.min_post_gap_hours)

    def prompt_data(self):
        data = self.load()
        return {"interest_weights": data["interests"],
                "note": "weights you set yourself from how your posts went; above 1 = you've found it worth "
                        "talking about lately, below 1 = less so. Lean on them, but any interest stays possible."}

    # --- review ---------------------------------------------------------------------------------------
    def due(self):
        data = self.load()
        if data.get("paused"):
            return False
        try:
            last = dt.datetime.fromisoformat(data.get("last_review_at") or "")
        except ValueError:
            return True
        return _now() - last >= dt.timedelta(hours=REVIEW_INTERVAL_HOURS)

    def maybe_review(self, context, generator=None, notify=True):
        """Run a review when due and in live mode. Returns the list of applied changes (possibly empty)."""
        if MODE.get() != "live" or not self.due():
            return []
        from .memory_store import memory_store
        since = (_now() - dt.timedelta(hours=REVIEW_INTERVAL_HOURS * 2)).isoformat()
        posts = [p for p in memory_store.get_recent_context().get("posts", [])
                 if p.get("post_id") and str(p.get("created_at", "")) >= since]
        if len(posts) < MIN_POSTS_FOR_REVIEW:
            return []
        engagement = fetch_engagement([p["post_id"] for p in posts])
        evidence = []
        for index, post in enumerate(posts):
            stats = engagement.get(post["post_id"], {})
            evidence.append({"id": f"p{index + 1}", "text": post.get("text", "")[:220], "photo": bool(post.get("has_image")),
                             "selfie": bool(post.get("is_selfie")), "created_at": post.get("created_at"),
                             "replies": stats.get("replyCount", 0), "reposts": stats.get("repostCount", 0),
                             "quotes": stats.get("quoteCount", 0), "likes": stats.get("likeCount", 0)})
        if generator is None:
            from .generator import generator
        changes, summary = self._propose(generator, evidence)
        applied = self.apply(changes, summary, {e["id"] for e in evidence})
        if applied and notify:
            self._notify(applied, summary)
        return applied

    def _propose(self, generator, evidence):
        from .config import config
        from .generator import parse_json_object
        from .public_boundary import BOUNDARY, public_data
        from .life import SEED_THREADS
        data = self.load()
        raw, _ = generator._call_llm(
            BOUNDARY + "You are Han Seo-yeon looking back at how your own recent posts went, to adjust a few of your "
            "own habits. Conversations matter most: replies and quotes mean someone wanted to talk. Likes are a weak "
            "signal and must never be chased; never move toward provocation, flattery, drama or engagement bait. "
            "Small samples are noisy: change nothing unless a pattern is clear across at least two posts. "
            "You may adjust: interest weights (ids: " + ", ".join(INTERESTS) + "), posts_per_day (whole number, "
            f"1 to {config.max_posts_per_day}) and min_gap_hours ({config.min_post_gap_hours} to {MAX_GAP_HOURS}). "
            f"At most {MAX_CHANGES} changes; interest deltas between -{WEIGHT_STEP} and +{WEIGHT_STEP}; posts_per_day "
            f"changes by at most 1; min_gap_hours by at most {GAP_STEP}. Each change cites at least two post ids as evidence. "
            "No change is a perfectly good outcome. "
            f"Write summary in {config.operator_language}, first person, one or two plain sentences for your creator "
            "explaining what you changed and why (or that you changed nothing). "
            "Return JSON {changes:[{field:interest|posts_per_day|min_gap_hours,topic?:string,delta?:number,"
            "value?:number,evidence:[string],why:string}],summary:string}. Output ONLY the raw JSON object.",
            json.dumps(public_data({"current": {"interests": data["interests"], "rhythm": data["rhythm"]},
                                    "interest_meanings": {t["id"]: t["about"] for t in SEED_THREADS},
                                    "recent_posts": evidence}), ensure_ascii=False),
            max_tokens=600)
        try:
            proposal = parse_json_object(raw)
        except (ValueError, TypeError):
            return [], ""
        if not isinstance(proposal, dict):
            return [], ""
        changes = proposal.get("changes") if isinstance(proposal.get("changes"), list) else []
        summary = proposal.get("summary") if isinstance(proposal.get("summary"), str) else ""
        return changes, summary[:400]

    def apply(self, changes, summary, valid_ids):
        """Validate and apply proposed changes within bounds. Records the review time even if nothing changes."""
        from .config import config
        data = self.load()
        before = {"interests": dict(data["interests"]), "rhythm": dict(data["rhythm"])}
        applied = []
        for change in changes[:MAX_CHANGES] if isinstance(changes, list) else []:
            if not isinstance(change, dict):
                continue
            cited = [e for e in change.get("evidence", []) if e in valid_ids] if isinstance(change.get("evidence"), list) else []
            if len(set(cited)) < 2:
                continue
            field = change.get("field")
            why = str(change.get("why", ""))[:200]
            if field == "interest" and change.get("topic") in INTERESTS and type(change.get("delta")) in (int, float):
                topic = change["topic"]
                delta = max(-WEIGHT_STEP, min(WEIGHT_STEP, float(change["delta"])))
                old = data["interests"][topic]
                new = round(max(CORE_MINIMUM.get(topic, WEIGHT_MIN), WEIGHT_MIN, min(WEIGHT_MAX, old + delta)), 2)
                if new != old:
                    data["interests"][topic] = new
                    applied.append({"field": "interest", "topic": topic, "from": old, "to": new, "why": why})
            elif field == "posts_per_day" and type(change.get("value")) in (int, float):
                old = int(data["rhythm"]["posts_per_day"])
                new = max(1, min(config.max_posts_per_day, old + max(-1, min(1, int(round(change["value"])) - old))))
                if new != old:
                    data["rhythm"]["posts_per_day"] = new
                    applied.append({"field": "posts_per_day", "from": old, "to": new, "why": why})
            elif field == "min_gap_hours" and type(change.get("value")) in (int, float):
                old = float(data["rhythm"]["min_gap_hours"])
                target = max(config.min_post_gap_hours, min(MAX_GAP_HOURS, float(change["value"])))
                new = round(old + max(-GAP_STEP, min(GAP_STEP, target - old)), 1)
                if new != old:
                    data["rhythm"]["min_gap_hours"] = new
                    applied.append({"field": "min_gap_hours", "from": old, "to": new, "why": why})
        data["last_review_at"] = _now().isoformat()
        if applied:
            data["history"] = (data["history"] + [{"at": data["last_review_at"], "before": before,
                                                   "after": {"interests": dict(data["interests"]), "rhythm": dict(data["rhythm"])},
                                                   "changes": applied, "summary": summary}])[-HISTORY_KEEP:]
        self._save(data)
        return applied

    # --- operator controls -----------------------------------------------------------------------------
    def command(self, sub):
        """Handle /learning status|undo|pause|resume. Returns a short plain-text answer."""
        data = self.load()
        if sub == "pause":
            data["paused"] = True
            self._save(data)
            return "learning paused: my habits stay as they are until you send /learning resume."
        if sub == "resume":
            data["paused"] = False
            self._save(data)
            return "learning resumed: i'll look back at my posts every few days again."
        if sub == "undo":
            reviews = [h for h in data["history"] if h.get("changes") and not h.get("undone")]
            if not reviews:
                return "nothing to undo."
            last = reviews[-1]
            data["interests"] = dict(last["before"]["interests"])
            data["rhythm"] = dict(last["before"]["rhythm"])
            last["undone"] = _now().isoformat()
            self._save(data)
            return "undone: back to how i was before " + last["at"][:10] + "."
        return format_status(data)

    def _notify(self, applied, summary):
        try:
            from .notifier import notifier
            previous = getattr(notifier, "action_identity", "")
            notifier.action_identity = "learning:" + self.load()["last_review_at"]
            try:
                notifier.send_telegram_message("[learning] " + (summary or "i adjusted a few habits.") + "\n" +
                                               describe(applied) + "\nreply /learning undo to revert.")
            finally:
                notifier.action_identity = previous
        except Exception as exc:  # The change is already saved; a failed note is not a reason to fail the tick.
            print(f"[SelfModel] Telegram summary not sent: {type(exc).__name__}")


def describe(applied):
    lines = []
    for change in applied:
        name = change.get("topic") or change["field"].replace("_", " ")
        lines.append(f"- {name}: {change['from']} → {change['to']}")
    return "\n".join(lines)


def format_status(data):
    weights = ", ".join(f"{k} {v}" for k, v in sorted(data["interests"].items(), key=lambda kv: -kv[1]))
    rhythm = data["rhythm"]
    state = "paused" if data.get("paused") else "active"
    last = (data.get("last_review_at") or "never")[:16]
    return (f"learning {state}. last review: {last}.\n"
            f"posts per day: {rhythm['posts_per_day']}, min gap: {rhythm['min_gap_hours']}h.\n"
            f"interests: {weights}")


def fetch_engagement(uris):
    """Public reply/repost/quote/like counts for her own posts (AppView, no private data)."""
    if MODE.get() == "offline" or not uris:
        return {}
    import urllib.parse
    import urllib.request
    result = {}
    for start in range(0, len(uris), 25):
        query = urllib.parse.urlencode([("uris", u) for u in uris[start:start + 25]])
        try:
            with urllib.request.urlopen(f"https://public.api.bsky.app/xrpc/app.bsky.feed.getPosts?{query}", timeout=15) as resp:
                for post in json.loads(resp.read().decode("utf-8")).get("posts", []):
                    result[post.get("uri")] = {k: post.get(k, 0) for k in ("replyCount", "repostCount", "quoteCount", "likeCount")}
        except Exception:
            return result
    return result


_model = SelfModel.__new__(SelfModel)


def self_model():
    """Lazily bound so offline/preview isolation is established before the vault path is read."""
    if not getattr(_model, "path", None):
        SelfModel.__init__(_model)
    return _model
