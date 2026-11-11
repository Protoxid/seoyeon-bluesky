import unittest
from unittest.mock import Mock, patch


class TestThreadPublishing(unittest.TestCase):
    def test_each_thread_part_has_its_own_delivery_identity(self):
        import agent.runner as runner
        from agent.bsky_client import bsky_client
        seen = []
        def post(text):
            seen.append(("post", bsky_client.action_identity, text))
            return {"uri": "at://me/post/1", "cid": "c1"}
        def reply(text, parent_uri, parent_cid, root_uri, root_cid):
            seen.append(("reply", bsky_client.action_identity, text, parent_uri, root_uri))
            return {"uri": f"at://me/post/{len(seen)}", "cid": f"c{len(seen)}"}
        bsky_client.action_identity = "PUBLISH_TEXT_POST:2026-11-12:x"
        with patch.object(bsky_client, "publish_text_post", side_effect=post), \
             patch.object(bsky_client, "publish_reply", side_effect=reply):
            first, uris = runner._publish_thread("one\n---\ntwo\n---\nthree")
        self.assertEqual(len(uris), 3)
        identities = [row[1] for row in seen]
        self.assertEqual(len(set(identities)), 3)
        self.assertEqual(seen[2][3], "at://me/post/2")  # third part replies to the second
        self.assertEqual(seen[2][4], "at://me/post/1")  # root stays the first post
        self.assertEqual(bsky_client.action_identity, "PUBLISH_TEXT_POST:2026-11-12:x")

    def test_failed_continuation_leaves_first_post_and_restores_identity(self):
        import agent.runner as runner
        from agent.bsky_client import bsky_client
        bsky_client.action_identity = "base"
        with patch.object(bsky_client, "publish_text_post", return_value={"uri": "at://me/1", "cid": "c"}), \
             patch.object(bsky_client, "publish_reply", return_value={}):
            first, uris = runner._publish_thread("one\n---\ntwo")
        self.assertEqual(uris, ["at://me/1"])
        self.assertEqual(bsky_client.action_identity, "base")

    def test_single_post_is_not_split(self):
        import agent.runner as runner
        from agent.bsky_client import bsky_client
        with patch.object(bsky_client, "publish_text_post", return_value={"uri": "at://me/1", "cid": "c"}), \
             patch.object(bsky_client, "publish_reply") as reply:
            runner._publish_thread("just one post - with a dash")
        reply.assert_not_called()


class TestCasualThreadDraft(unittest.TestCase):
    def _gen(self, *responses):
        gen = Mock()
        gen._call_llm.side_effect = [(r, "mock") for r in responses]
        return gen

    def test_parts_validated_separately_and_joined(self):
        from agent.discussion import casual_draft, THREAD_SEPARATOR
        gen = self._gen("first part\n---\nsecond part", '{"approved":true,"issue":"none"}')
        with patch("agent.validator.validator.validate_outgoing_text", side_effect=lambda t, **k: (True, t, None)) as validate:
            text, _ = casual_draft(gen, "system", "prompt", max_parts=3)
        self.assertEqual(text, "first part" + THREAD_SEPARATOR + "second part")
        self.assertEqual([c.kwargs["check_repetition"] for c in validate.call_args_list], [True, False])

    def test_split_draft_rejected_when_threads_not_allowed(self):
        from agent.discussion import casual_draft
        gen = self._gen("first part\n---\nsecond part")
        with patch("agent.validator.validator.validate_outgoing_text", side_effect=lambda t, **k: (True, t, None)):
            self.assertEqual(casual_draft(gen, "system", "prompt")[0], "")


class TestProposalOptions(unittest.TestCase):
    def propose(self, payload, formats):
        from agent.original_ideas import propose
        gen = Mock()
        gen._call_llm.return_value = (payload, "mock")
        return propose(gen, "identity", "context", {}, [], formats)[0]

    def test_thread_only_for_text_reflections_and_photos_bounded(self):
        idea = self.propose('{"format":"text","kind":"reflection","idea":"why i quit marketing","thread":true}', ["text"])
        self.assertTrue(idea["thread"])
        idea = self.propose('{"format":"text","kind":"moment","idea":"cold kimbap again","thread":true}', ["text"])
        self.assertFalse(idea["thread"])
        idea = self.propose('{"format":"image","kind":"moment","idea":"market haul on the counter","photos":9}', ["image"])
        self.assertEqual(idea["photos"], 3)
        idea = self.propose('{"format":"image","kind":"moment","idea":"market haul on the counter","photos":"2"}', ["image"])
        self.assertEqual(idea["photos"], 1)


if __name__ == "__main__":
    unittest.main()
