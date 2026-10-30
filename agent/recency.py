"""Recency eligibility for public social targets, independent of personality."""
import datetime as dt

MAX_POST_AGE = dt.timedelta(hours=72)
FUTURE_TOLERANCE = dt.timedelta(minutes=5)


def post_recency(post, now=None):
    """Use the target's authored date, never indexing/repost time or thread root."""
    record = post.get("record") if isinstance(post, dict) else None
    raw = record.get("createdAt") if isinstance(record, dict) else None
    if not isinstance(raw, str):
        return "unknown_date"
    try:
        created = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if created.tzinfo is None:
            return "unknown_date"
        age = (now or dt.datetime.now(dt.timezone.utc)) - created
    except (ValueError, TypeError, OverflowError):
        return "unknown_date"
    if age < -FUTURE_TOLERANCE:
        return "future_date"
    return "recent" if age <= MAX_POST_AGE else "stale"


def candidate_recency(candidate):
    from .decision_engine import ActionType
    public = {ActionType.BROWSE_AND_REPLY, ActionType.BROWSE_AND_LIKE,
              ActionType.QUOTE_POST, ActionType.REPOST, ActionType.FOLLOW,
              ActionType.REPLY_COMMENT, ActionType.ANSWER_MENTION}
    if candidate.action not in public:
        return "recent"
    data = candidate.target_data or {}
    return post_recency(data.get("post") or data.get("notification") or {})
