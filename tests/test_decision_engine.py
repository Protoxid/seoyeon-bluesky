"""
tests/test_decision_engine.py — Unit tests for the Cognitive Decision Engine.
"""

import pathlib
import tempfile
import unittest
from agent.decision_engine import ActionType, DecisionEngine
from agent.context_engine import EnvironmentContext, WeatherSnapshot
from agent.state_manager import StateManager, AgentState


class TestDecisionEngine(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.test_state_file = pathlib.Path(self.tmp_dir.name) / "agent_state.json"
        self.test_state_mgr = StateManager(state_file=self.test_state_file)
        self.test_state_mgr.save_state(AgentState(social_battery=0.85, physical_fatigue=0.20))
        self.engine = DecisionEngine(state_mgr=self.test_state_mgr)
        self.dummy_weather = WeatherSnapshot(
            temperature_c=20.0,
            description="clear",
            is_raining=False,
            is_snowing=False,
            windspeed_kmh=5.0,
            retrieved_at="2026-10-03T12:00:00Z"
        )

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_deep_night_prefers_no_action(self):
        # 03:00 KST, no urgent incoming stimuli
        night_context = EnvironmentContext(
            seoul_time_iso="2026-10-03T03:00:00+09:00",
            seoul_time_display="03:00 KST",
            date_display="2026-10-03",
            day_of_week="Saturday",
            is_weekend=True,
            circadian_phase="deep_night",
            season="autumn",
            holiday_note=None,
            weather=self.dummy_weather,
            hours_since_last_post=6.0,
            hours_since_last_action=4.0,
            posts_today=1,
            replies_today=2,
            dms_today=0,
        )

        outcome = self.engine.evaluate(
            context=night_context,
            notifications=[],
            dms=[],
            feed_items=[],
            can_image=True,
        )
        self.assertEqual(outcome.selected_action, ActionType.NO_ACTION)
        self.assertGreaterEqual(outcome.candidate_scores["NO_ACTION"], 0.8)

    def test_post_recency_cooldown(self):
        # If last post was just 0.5 hours ago, posting probability should be negligible
        recent_post_context = EnvironmentContext(
            seoul_time_iso="2026-10-03T14:30:00+09:00",
            seoul_time_display="14:30 KST",
            date_display="2026-10-03",
            day_of_week="Saturday",
            is_weekend=True,
            circadian_phase="afternoon",
            season="autumn",
            holiday_note=None,
            weather=self.dummy_weather,
            hours_since_last_post=0.5,
            hours_since_last_action=0.5,
            posts_today=1,
            replies_today=0,
            dms_today=0,
        )

        outcome = self.engine.evaluate(
            context=recent_post_context,
            notifications=[],
            dms=[],
            feed_items=[],
            can_image=True,
        )
        # Should NOT decide to publish another post
        self.assertNotEqual(outcome.selected_action, ActionType.PUBLISH_TEXT_POST)
        self.assertNotEqual(outcome.selected_action, ActionType.PUBLISH_IMAGE_POST)
        self.assertEqual(outcome.selected_action, ActionType.NO_ACTION)

    def test_unread_dm_prioritization(self):
        # A legitimate unread DM from an acquaintance should be prioritized
        day_context = EnvironmentContext(
            seoul_time_iso="2026-10-03T16:00:00+09:00",
            seoul_time_display="16:00 KST",
            date_display="2026-10-03",
            day_of_week="Saturday",
            is_weekend=True,
            circadian_phase="afternoon",
            season="autumn",
            holiday_note=None,
            weather=self.dummy_weather,
            hours_since_last_post=4.0,
            hours_since_last_action=2.0,
            posts_today=1,
            replies_today=1,
            dms_today=0,
        )

        fake_dm = {
            "id": "convo_test_123",
            "unreadCount": 1,
            "members": [
                {"did": "did:plc:other", "handle": "friend.bsky.social"},
                {"did": "did:plc:self", "handle": "syeonhn.bsky.social"},
            ]
        }

        outcome = self.engine.evaluate(
            context=day_context,
            notifications=[],
            dms=[fake_dm],
            feed_items=[],
            can_image=True,
        )
        self.assertEqual(outcome.selected_action, ActionType.ANSWER_DM)
        self.assertEqual(outcome.target_data.get("convo_id"), "convo_test_123")

    def test_skips_already_replied_notification(self):
        from agent.memory_store import memory_store

        notif_uri = "at://did:plc:other/app.bsky.feed.post/already_done"
        memory_store.mark_notification_handled(notif_uri)

        fake_notif = {
            "uri": notif_uri,
            "cid": "cid_done",
            "reason": "reply",
            "author": {"did": "did:plc:other", "handle": "friend.bsky.social"},
            "record": {"text": "hello again", "reply": {}}
        }

        day_context = EnvironmentContext(
            seoul_time_iso="2026-10-03T16:00:00+09:00",
            seoul_time_display="16:00 KST",
            date_display="2026-10-03",
            day_of_week="Saturday",
            is_weekend=True,
            circadian_phase="afternoon",
            season="autumn",
            holiday_note=None,
            weather=self.dummy_weather,
            hours_since_last_post=4.0,
            hours_since_last_action=2.0,
            posts_today=1,
            replies_today=1,
            dms_today=0,
        )

        outcome = self.engine.evaluate(
            context=day_context,
            notifications=[fake_notif],
            dms=[],
            feed_items=[],
            can_image=True,
        )
        # Must NOT choose REPLY_COMMENT for already handled notification
        self.assertNotEqual(outcome.selected_action, ActionType.REPLY_COMMENT)

    def test_bsky_client_can_reply_to_thread(self):
        from agent.bsky_client import bsky_client
        bsky_client.handle = "syeonhn.bsky.social"
        bsky_client.did = "did:plc:self"

        # Case 1: Target post is authored by self -> cannot reply
        thread_self = {
            "thread": {
                "$type": "app.bsky.feed.defs#threadViewPost",
                "post": {
                    "uri": "at://did:plc:self/app.bsky.feed.post/p1",
                    "author": {"handle": "syeonhn.bsky.social", "did": "did:plc:self"}
                },
                "replies": []
            }
        }
        can_r, reason = bsky_client.can_reply_to_thread("at://did:plc:self/app.bsky.feed.post/p1", thread_self)
        self.assertFalse(can_r)
        self.assertIn("authored by Seo-yeon herself", reason)

        # Case 2: Target post already has a direct reply from self and no subsequent user reply -> cannot reply
        thread_already_replied = {
            "thread": {
                "$type": "app.bsky.feed.defs#threadViewPost",
                "post": {
                    "uri": "at://did:plc:user1/app.bsky.feed.post/p2",
                    "author": {"handle": "user1.bsky.social", "did": "did:plc:user1"}
                },
                "replies": [
                    {
                        "$type": "app.bsky.feed.defs#threadViewPost",
                        "post": {
                            "uri": "at://did:plc:self/app.bsky.feed.post/rep1",
                            "author": {"handle": "syeonhn.bsky.social", "did": "did:plc:self"}
                        },
                        "replies": []
                    }
                ]
            }
        }
        can_r, reason = bsky_client.can_reply_to_thread("at://did:plc:user1/app.bsky.feed.post/p2", thread_already_replied)
        self.assertFalse(can_r)
        self.assertIn("already commented on this post without another comment in between", reason)

        # Case 3: Target post has no reply from self -> SAFE to reply
        thread_clean = {
            "thread": {
                "$type": "app.bsky.feed.defs#threadViewPost",
                "post": {
                    "uri": "at://did:plc:user1/app.bsky.feed.post/p3",
                    "author": {"handle": "user1.bsky.social", "did": "did:plc:user1"}
                },
                "replies": []
            }
        }
        can_r, reason = bsky_client.can_reply_to_thread("at://did:plc:user1/app.bsky.feed.post/p3", thread_clean)
        self.assertTrue(can_r)
        self.assertEqual(reason, "Safe to reply")

    def test_browse_and_reply_discovery(self):
        # Daytime, 2.5h since last action, post recently published so no new post due, feed item available
        day_context = EnvironmentContext(
            seoul_time_iso="2026-10-05T14:30:00+09:00",
            seoul_time_display="14:30 KST",
            date_display="2026-10-05",
            day_of_week="Monday",
            is_weekend=False,
            circadian_phase="afternoon",
            season="autumn",
            holiday_note=None,
            weather=self.dummy_weather,
            hours_since_last_post=2.0,
            hours_since_last_action=2.5,
            posts_today=1,
            replies_today=1,
            dms_today=0,
        )

        feed_item = {
            "post": {
                "uri": "at://did:plc:someone/app.bsky.feed.post/community_1",
                "cid": "cid_c1",
                "author": {"handle": "coffee_lover.bsky.social", "did": "did:plc:someone"},
                "record": {"text": "seoul forest weather is lovely today, drinking cold brew by the lake"},
            }
        }

        outcome = self.engine.evaluate(
            context=day_context,
            notifications=[],
            dms=[],
            feed_items=[feed_item],
            can_image=False,
        )
        self.assertEqual(outcome.selected_action, ActionType.BROWSE_AND_REPLY)
        self.assertEqual(outcome.target_data.get("post", {}).get("uri"), "at://did:plc:someone/app.bsky.feed.post/community_1")

    def test_browse_and_reply_skips_already_replied(self):
        from agent.memory_store import memory_store

        already_replied_uri = "at://did:plc:someone/app.bsky.feed.post/already_seen_post"
        memory_store.mark_notification_handled(already_replied_uri, target_post_uri=already_replied_uri)

        day_context = EnvironmentContext(
            seoul_time_iso="2026-10-05T15:00:00+09:00",
            seoul_time_display="15:00 KST",
            date_display="2026-10-05",
            day_of_week="Monday",
            is_weekend=False,
            circadian_phase="afternoon",
            season="autumn",
            holiday_note=None,
            weather=self.dummy_weather,
            hours_since_last_post=2.0,
            hours_since_last_action=2.5,
            posts_today=1,
            replies_today=1,
            dms_today=0,
        )

        feed_items = [
            {
                "post": {
                    "uri": already_replied_uri,
                    "author": {"handle": "user1.bsky.social"},
                    "record": {"text": "already commented post from yesterday morning"},
                }
            },
            {
                "post": {
                    "uri": "at://did:plc:newuser/app.bsky.feed.post/fresh_post",
                    "author": {"handle": "newuser.bsky.social"},
                    "record": {"text": "anyone walking in seongsu today? the breeze is chilly"},
                }
            }
        ]

        outcome = self.engine.evaluate(
            context=day_context,
            notifications=[],
            dms=[],
            feed_items=feed_items,
            can_image=False,
        )
        self.assertEqual(outcome.selected_action, ActionType.BROWSE_AND_REPLY)
        self.assertEqual(outcome.target_data.get("post", {}).get("uri"), "at://did:plc:newuser/app.bsky.feed.post/fresh_post")

    def test_multiple_notifications_evaluation(self):
        from agent.memory_store import memory_store

        old_notif_uri = "at://did:plc:old/app.bsky.feed.post/old_comment"
        memory_store.mark_notification_handled(old_notif_uri)

        notifications = [
            {
                "uri": old_notif_uri,
                "reason": "reply",
                "author": {"handle": "harbourlightgame.bsky.social"},
                "record": {"text": "old comment that was already replied to"},
            },
            {
                "uri": "at://did:plc:fresh/app.bsky.feed.post/fresh_comment",
                "reason": "reply",
                "author": {"handle": "friendly_neighbor.bsky.social"},
                "record": {"text": "have you tried that new bakery near seoul forest?"},
            }
        ]

        day_context = EnvironmentContext(
            seoul_time_iso="2026-10-05T15:30:00+09:00",
            seoul_time_display="15:30 KST",
            date_display="2026-10-05",
            day_of_week="Monday",
            is_weekend=False,
            circadian_phase="afternoon",
            season="autumn",
            holiday_note=None,
            weather=self.dummy_weather,
            hours_since_last_post=2.0,
            hours_since_last_action=2.0,
            posts_today=1,
            replies_today=1,
            dms_today=0,
        )

        outcome = self.engine.evaluate(
            context=day_context,
            notifications=notifications,
            dms=[],
            feed_items=[],
            can_image=False,
        )
        self.assertEqual(outcome.selected_action, ActionType.REPLY_COMMENT)
        self.assertEqual(outcome.target_data.get("notification", {}).get("uri"), "at://did:plc:fresh/app.bsky.feed.post/fresh_comment")

    def test_image_post_organic_selection(self):
        # Morning stroll in Seongsu, 14h since last post, no recent image post
        morning_context = EnvironmentContext(
            seoul_time_iso="2026-10-06T08:30:00+09:00",
            seoul_time_display="08:30 KST",
            date_display="2026-10-06",
            day_of_week="Tuesday",
            is_weekend=False,
            circadian_phase="morning",
            season="autumn",
            holiday_note=None,
            weather=self.dummy_weather,
            hours_since_last_post=14.0,
            hours_since_last_action=8.0,
            posts_today=0,
            replies_today=0,
            dms_today=0,
            likes_today=0,
            scheduled_area="Seongsu red-brick streets",
        )

        outcome = self.engine.evaluate(
            context=morning_context,
            notifications=[],
            dms=[],
            feed_items=[],
            can_image=True,
        )
        self.assertEqual(outcome.selected_action, ActionType.PUBLISH_IMAGE_POST)
        self.assertIn("PUBLISH_IMAGE_POST", outcome.candidate_scores)
        self.assertGreaterEqual(outcome.candidate_scores["PUBLISH_IMAGE_POST"], 0.70)

    def test_image_post_falls_back_to_text_when_image_disabled(self):
        # Same context but can_image=False -> chooses text post
        morning_context = EnvironmentContext(
            seoul_time_iso="2026-10-06T08:30:00+09:00",
            seoul_time_display="08:30 KST",
            date_display="2026-10-06",
            day_of_week="Tuesday",
            is_weekend=False,
            circadian_phase="morning",
            season="autumn",
            holiday_note=None,
            weather=self.dummy_weather,
            hours_since_last_post=14.0,
            hours_since_last_action=8.0,
            posts_today=0,
            replies_today=0,
            dms_today=0,
            likes_today=0,
        )

        outcome = self.engine.evaluate(
            context=morning_context,
            notifications=[],
            dms=[],
            feed_items=[],
            can_image=False,
        )
        self.assertEqual(outcome.selected_action, ActionType.PUBLISH_TEXT_POST)

    def test_dm_deduplication_skips_handled_message(self):
        from agent.memory_store import memory_store
        handled_msg_id = "msg_handled_999"
        memory_store.mark_dm_handled(handled_msg_id)

        day_context = EnvironmentContext(
            seoul_time_iso="2026-10-06T16:00:00+09:00",
            seoul_time_display="16:00 KST",
            date_display="2026-10-06",
            day_of_week="Tuesday",
            is_weekend=False,
            circadian_phase="afternoon",
            season="autumn",
            holiday_note=None,
            weather=self.dummy_weather,
            hours_since_last_post=4.0,
            hours_since_last_action=2.0,
            posts_today=1,
            replies_today=1,
            dms_today=0,
            likes_today=0,
        )

        handled_dm = {
            "id": "convo_test_handled",
            "unreadCount": 1,
            "members": [
                {"did": "did:plc:other", "handle": "friend.bsky.social"},
                {"did": "did:plc:self", "handle": "syeonhn.bsky.social"},
            ],
            "lastMessage": {
                "id": handled_msg_id,
                "sender": {"did": "did:plc:other"},
                "text": "are you free later?"
            }
        }

        outcome = self.engine.evaluate(
            context=day_context,
            notifications=[],
            dms=[handled_dm],
            feed_items=[],
            can_image=False,
        )
        self.assertNotEqual(outcome.selected_action, ActionType.ANSWER_DM)

    def test_dm_skips_self_sent_last_message(self):
        from agent.bsky_client import bsky_client
        bsky_client.did = "did:plc:self"

        day_context = EnvironmentContext(
            seoul_time_iso="2026-10-06T16:00:00+09:00",
            seoul_time_display="16:00 KST",
            date_display="2026-10-06",
            day_of_week="Tuesday",
            is_weekend=False,
            circadian_phase="afternoon",
            season="autumn",
            holiday_note=None,
            weather=self.dummy_weather,
            hours_since_last_post=4.0,
            hours_since_last_action=2.0,
            posts_today=1,
            replies_today=1,
            dms_today=0,
            likes_today=0,
        )

        self_dm = {
            "id": "convo_self_last",
            "unreadCount": 1,
            "members": [
                {"did": "did:plc:other", "handle": "friend.bsky.social"},
                {"did": "did:plc:self", "handle": "syeonhn.bsky.social"},
            ],
            "lastMessage": {
                "id": "msg_self_111",
                "sender": {"did": "did:plc:self"},
                "text": "talk to you soon"
            }
        }

        outcome = self.engine.evaluate(
            context=day_context,
            notifications=[],
            dms=[self_dm],
            feed_items=[],
            can_image=False,
        )
        self.assertNotEqual(outcome.selected_action, ActionType.ANSWER_DM)


if __name__ == "__main__":
    unittest.main()
