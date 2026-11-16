"""Shared test fixtures: a fresh feed candidate so the contextual chooser has something new to consider.

Since 2026-11-16 the chooser is skipped (no model call) when nothing new is eligible; tests that exercise
the chooser itself add one fresh feed post with this helper.
"""
import datetime as dt
import uuid


def fresh_feed_candidate():
    from agent.decision_engine import ActionCandidate, ActionType
    post = {"uri": f"at://did:plc:test/app.bsky.feed.post/{uuid.uuid4().hex[:12]}",
            "record": {"createdAt": dt.datetime.now(dt.timezone.utc).isoformat(), "text": "a fresh post"},
            "author": {"handle": "someone.test", "did": "did:plc:someone"}}
    return ActionCandidate(ActionType.BROWSE_AND_LIKE, .1, .9, "", {"post": post})
