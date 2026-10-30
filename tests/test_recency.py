import datetime as dt
import json
import unittest
from unittest.mock import patch

from agent.recency import post_recency, candidate_recency, MAX_POST_AGE
from agent.decision_engine import ActionCandidate, ActionType, DecisionOutcome
from agent.runtime import execution_mode


def post(when, uri="at://test/post/fresh"):
    return {"uri": uri, "record": {"createdAt": when.isoformat(), "text": "a current question"}}


class TestRecency(unittest.TestCase):
    def test_operator_reply_skips_old_notifications_and_feed(self):
        from agent.bsky_client import bsky_client
        from agent.notifier import MasterNotifier
        from agent.context_engine import build_environment_context
        notifier = MasterNotifier()
        old = post(dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc))
        old["reason"] = "reply"
        with patch.object(bsky_client, "ensure_session"), patch.object(bsky_client, "list_notifications", return_value=[old]), patch.object(bsky_client, "get_discovery_feed", return_value=[{"post": old}]), patch.object(bsky_client, "publish_reply") as send, patch("agent.generator.generator.generate_reply") as draft, patch.object(notifier, "send_telegram_message"):
            result = notifier.execute_master_directive({"action_type": "BROWSE_AND_REPLY"}, build_environment_context(), dry_run=True)
        self.assertFalse(result["success"])
        draft.assert_not_called()
        send.assert_not_called()

    def test_age_boundary_uses_authored_date(self):
        now = dt.datetime.now(dt.timezone.utc)
        self.assertEqual(post_recency(post(now - MAX_POST_AGE), now), "recent")
        old = post(now - MAX_POST_AGE - dt.timedelta(microseconds=1))
        old["indexedAt"] = now.isoformat()
        old["reason"] = {"indexedAt": now.isoformat()}
        self.assertEqual(post_recency(old, now), "stale")

    def test_invalid_dates_fail_closed(self):
        now = dt.datetime.now(dt.timezone.utc)
        for value in (None, "", "bad", "2026-10-30T12:00:00", 42):
            self.assertEqual(post_recency({"record": {"createdAt": value}}, now), "unknown_date")
        for value in (None, [], "broken"):
            self.assertEqual(post_recency({"record": value}, now), "unknown_date")
        self.assertEqual(post_recency(post(now + dt.timedelta(minutes=6)), now), "future_date")
        offset = now.astimezone(dt.timezone(dt.timedelta(hours=9)))
        self.assertEqual(post_recency(post(offset), now), "recent")

    def test_new_turn_in_old_thread_is_eligible(self):
        target = post(dt.datetime.now(dt.timezone.utc))
        target["record"]["reply"] = {"root": post(dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc))}
        for action in (ActionType.REPLY_COMMENT, ActionType.ANSWER_MENTION):
            self.assertEqual(candidate_recency(ActionCandidate(action, 0, 0, "", {"notification": target})), "recent")
        for action in (ActionType.ANSWER_DM, ActionType.PUBLISH_TEXT_POST, ActionType.NO_ACTION):
            self.assertEqual(candidate_recency(ActionCandidate(action, 0, 0, "", {})), "recent")

    def test_discovery_filters_before_limit_and_requests_latest(self):
        from agent.bsky_client import BlueskyClient
        client = BlueskyClient()
        with patch.object(client, "xrpc_get", return_value={"posts": []}) as get:
            client.search_posts("movement")
        params = get.call_args.args[1]
        self.assertEqual(params["sort"], "latest")
        self.assertLess(abs((dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(params["since"].replace("Z", "+00:00")) - MAX_POST_AGE).total_seconds()), 5)
        old = post(dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc), "old")
        fresh = post(dt.datetime.now(dt.timezone.utc))
        with patch.object(client, "get_timeline", return_value=[{"post": old}, {"post": fresh}]), patch.object(client, "search_posts", return_value=[old]):
            self.assertEqual([x["post"]["uri"] for x in client.get_discovery_feed(limit=1, topics=["movement"])], [fresh["uri"]])
        with patch.object(client, "get_timeline", return_value=[{"post": old}]), patch.object(client, "search_posts", return_value=[old]):
            self.assertEqual(client.get_discovery_feed(topics=["movement"]), [])

    def test_old_target_never_reaches_model_choice(self):
        from agent.choice import choose
        from agent.context_engine import build_environment_context
        stale = ActionCandidate(ActionType.BROWSE_AND_REPLY, 1, 1, "", {"post": post(dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc))})
        quiet = ActionCandidate(ActionType.NO_ACTION, 0, 0, "")
        outcome = DecisionOutcome(quiet.action, "", {}, "", {}, [stale, quiet])
        with execution_mode("live"), patch("agent.generator.generator._call_llm", return_value=(json.dumps({"candidate_id": 0, "confidence": .9}), "mock")) as call:
            result = choose(outcome, build_environment_context())
        self.assertEqual(result.selected_action, ActionType.NO_ACTION)
        self.assertNotIn("a current question", call.call_args.args[1])
        self.assertEqual(result.discussion_diagnostics["recency_exclusions"], {"stale": 1})
