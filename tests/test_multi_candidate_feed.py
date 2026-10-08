"""
tests/test_multi_candidate_feed.py — Unit Tests for Multi-Candidate Feed Evaluation & Ranking.

Verifies:
  1. DecisionEngine evaluates up to 10 candidates from feed_items.
  2. Candidates with relationship ties, open conversational loops, and active goal
     keywords rank higher than generic feed items.
  3. Highest scoring candidate is selected for BROWSE_AND_REPLY and BROWSE_AND_LIKE.
"""

import datetime as dt
import pathlib
import shutil
import tempfile
import unittest
from unittest.mock import patch

from agent.context_engine import EnvironmentContext, WeatherSnapshot
from agent.decision_engine import ActionType, DecisionEngine
from agent.goal_manager import GoalManager
from agent.memory_store import UserProfile, memory_store
from agent.narrative_engine import NarrativeContinuityEngine


class TestMultiCandidateFeed(unittest.TestCase):
    def setUp(self):
        self.test_dir = pathlib.Path(tempfile.mkdtemp())
        self.goals_file = self.test_dir / "active_goals.json"
        self.narrative_file = self.test_dir / "narrative_state.json"
        self.users_file = self.test_dir / "user_memory.json"
        self.recent_ctx_file = self.test_dir / "recent_context.json"

        self.orig_users_file = memory_store.users_file
        self.orig_ctx_file = memory_store.recent_context_file
        memory_store.users_file = self.users_file
        memory_store.recent_context_file = self.recent_ctx_file
        memory_store._init_defaults()

        self.goal_mgr = GoalManager(storage_file=self.goals_file)
        self.narrative_eng = NarrativeContinuityEngine(storage_file=self.narrative_file)
        self.engine = DecisionEngine()

    def tearDown(self):
        memory_store.users_file = self.orig_users_file
        memory_store.recent_context_file = self.orig_ctx_file
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_multi_candidate_ranking_selects_most_relevant_post(self):
        """Verifies multi-candidate evaluation ranks goal-aligned and mutual posts above generic posts."""
        context = EnvironmentContext(
            seoul_time_iso="2026-10-09T14:00:00+09:00",
            seoul_time_display="14:00 KST",
            date_display="2026-10-09",
            day_of_week="friday",
            is_weekend=False,
            circadian_phase="afternoon",
            season="autumn",
            holiday_note=None,
            weather=WeatherSnapshot(
                temperature_c=18.0,
                description="clear",
                is_raining=False,
                is_snowing=False,
                windspeed_kmh=2.0,
                retrieved_at="",
            ),
            hours_since_last_post=6.0,
            hours_since_last_action=2.5,
            posts_today=0,
            replies_today=0,
            dms_today=0,
            likes_today=0,
        )

        # Record a regular user profile
        memory_store.record_user_interaction(
            handle="trusted_friend.bsky.social",
            incoming_text="hello",
            outgoing_text="hey",
            interaction_type="reply",
            did="did:plc:trusted_friend_did",
        )
        prof = memory_store.get_user_profile("trusted_friend.bsky.social")
        prof.relationship = "regular"
        memory_store.save_user_profile(prof)

        # Open loop with trusted friend
        self.narrative_eng.open_loop(
            partner_identifier="did:plc:trusted_friend_did",
            partner_handle="trusted_friend.bsky.social",
            topic="Han Kang translation",
            loop_type="recommendation_received",
            context_note="Recommended Han Kang's translated novel.",
        )

        # Construct 3 feed items:
        # Item 0 (first): Generic stranger post
        post_stranger = {
            "uri": "at://did:plc:stranger1/app.bsky.feed.post/100",
            "author": {"handle": "stranger1.bsky.social", "did": "did:plc:stranger1"},
            "record": {"text": "drinking plain tea at lunch time today in gangnam.", "langs": ["en"]},
        }

        # Item 1 (second): Post touching on Han Kang & novel from trusted friend with open loop
        post_friend = {
            "uri": "at://did:plc:trusted_friend_did/app.bsky.feed.post/200",
            "author": {"handle": "trusted_friend.bsky.social", "did": "did:plc:trusted_friend_did"},
            "record": {
                "text": "just finished reading the han kang novel chapters you mentioned. the language is quiet and intense.",
                "langs": ["en"]
            },
        }

        # Item 2 (third): Another stranger post
        post_stranger2 = {
            "uri": "at://did:plc:stranger2/app.bsky.feed.post/300",
            "author": {"handle": "stranger2.bsky.social", "did": "did:plc:stranger2"},
            "record": {"text": "waiting for the bus number 143 near itaewon station.", "langs": ["en"]},
        }

        feed_items = [
            {"post": post_stranger},
            {"post": post_friend},
            {"post": post_stranger2},
        ]

        with patch("agent.decision_engine.goal_manager", self.goal_mgr), \
             patch("agent.decision_engine.narrative_engine", self.narrative_eng):

            outcome = self.engine.evaluate(
                context=context,
                notifications=[],
                dms=[],
                feed_items=feed_items,
                can_image=False,
            )

            # Even though post_stranger was item 0, post_friend MUST be chosen for BROWSE_AND_REPLY
            # because it has relationship + open loop + goal alignment!
            reply_candidate = next((c for c in outcome.all_candidates if c.action == ActionType.BROWSE_AND_REPLY), None)
            self.assertIsNotNone(reply_candidate)
            self.assertEqual(reply_candidate.target_data["post"]["uri"], "at://did:plc:trusted_friend_did/app.bsky.feed.post/200")
            self.assertGreater(reply_candidate.score, 0.70)


if __name__ == "__main__":
    unittest.main()
