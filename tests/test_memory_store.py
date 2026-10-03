"""
tests/test_memory_store.py — Unit tests for the Persistent Memory Store.
"""

import shutil
import tempfile
import unittest
import pathlib

from agent.memory_store import MemoryStore, UserProfile


class TestMemoryStore(unittest.TestCase):
    def setUp(self):
        self.test_dir = pathlib.Path(tempfile.mkdtemp())
        self.store = MemoryStore(memory_dir=self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_identity_initialization(self):
        ident = self.store.get_identity()
        self.assertEqual(ident["name_en"], "Han Seo-yeon")
        self.assertEqual(ident["name_ko"], "한서연")
        self.assertIn("voice_rules", ident)

        prompt = self.store.format_identity_prompt()
        self.assertIn("Han Seo-yeon", prompt)
        self.assertIn("Seongsu-dong", prompt)

    def test_user_memory_progression(self):
        # Initial stranger profile
        handle = "bookworm.bsky.social"
        prof = self.store.get_user_profile(handle)
        self.assertEqual(prof.relationship, "stranger")
        self.assertEqual(prof.interaction_count, 0)

        # 3 interactions should elevate to friendly_acquaintance
        for i in range(3):
            self.store.record_user_interaction(
                handle=handle,
                incoming_text=f"hello message {i}",
                outgoing_text=f"reply message {i}",
                interaction_type="reply",
                discovered_fact="reads Korean literature" if i == 0 else None,
            )

        updated_prof = self.store.get_user_profile(handle)
        self.assertEqual(updated_prof.interaction_count, 3)
        self.assertEqual(updated_prof.relationship, "friendly_acquaintance")
        self.assertIn("reads Korean literature", updated_prof.known_facts)

    def test_opinion_consistency(self):
        # Default opinion exists
        op = self.store.check_opinion("iced_americano")
        self.assertIsNotNone(op)
        self.assertEqual(op["sentiment"], "positive")

        # Record new opinion
        self.store.record_opinion(
            topic="cyberpunk_anime",
            sentiment="positive",
            stance="loves retro 90s aesthetic and sound design"
        )
        op2 = self.store.check_opinion("cyberpunk_anime")
        self.assertIsNotNone(op2)
        self.assertIn("retro 90s", op2["stance"])

    def test_recent_context_tracking(self):
        self.store.record_recent_post("post one", topic="test", post_id="p1")
        self.store.record_recent_post("post two", topic="test", post_id="p2")

        ctx = self.store.get_recent_context()
        posts = ctx.get("posts", [])
        self.assertEqual(len(posts), 2)
        self.assertEqual(posts[0]["text"], "post two")
        self.assertAlmostEqual(self.store.get_hours_since_last_post(), 0.0, delta=0.1)

    def test_replied_notification_and_post_tracking(self):
        target_post = "at://did:plc:other/app.bsky.feed.post/12345"
        notif_uri = "at://did:plc:other/app.bsky.feed.post/notif_999"

        # Initially False
        self.assertFalse(self.store.has_replied_to_notification(notif_uri))
        self.assertFalse(self.store.has_replied_to_post(target_post))

        # Record reply
        self.store.record_recent_reply(
            target_handle="user.bsky.social",
            user_text="loved the class!",
            reply_text="glad you enjoyed it.",
            uri="at://did:plc:self/app.bsky.feed.post/my_reply_1",
            target_uri=target_post,
            root_uri=target_post,
            notification_uri=notif_uri,
        )

        # Now should be True
        self.assertTrue(self.store.has_replied_to_notification(notif_uri))
        self.assertTrue(self.store.has_replied_to_post(target_post))

        # Test mark_notification_handled
        another_notif = "at://did:plc:other/app.bsky.feed.post/notif_888"
        self.assertFalse(self.store.has_replied_to_notification(another_notif))
        self.store.mark_notification_handled(another_notif)
        self.assertTrue(self.store.has_replied_to_notification(another_notif))


if __name__ == "__main__":
    unittest.main()
