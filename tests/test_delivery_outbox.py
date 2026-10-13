from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from agent.delivery import Outbox, new_record_key


class TestDeliveryOutbox(unittest.TestCase):
    def test_abandoned_targets_are_ineligible_without_becoming_delivered(self):
        from agent.delivery import completed_social_actions, exclude_completed_candidates
        from agent.decision_engine import ActionCandidate, ActionType
        from agent.storage import write_json
        for action, collection, subject in [
            (ActionType.BROWSE_AND_LIKE, "app.bsky.feed.like", {"uri": "post:old"}),
            (ActionType.REPOST, "app.bsky.feed.repost", {"uri": "post:old"}),
            (ActionType.FOLLOW, "app.bsky.graph.follow", "did:old")]:
            with self.subTest(action=action):
                row = {"status": "abandoned", "payload": {"collection": collection, "record": {"subject": subject}}}
                write_json(self.path, {"closed": row})
                old = {"post": {"uri": "post:old", "author": {"did": "did:old"}}}
                fresh = {"post": {"uri": "post:new", "author": {"did": "did:new"}}}
                blocked = ActionCandidate(action, 1, 1, "", old)
                allowed = [ActionCandidate(action, 1, 1, "", fresh),
                           ActionCandidate(ActionType.BROWSE_AND_REPLY, 1, 1, "", old),
                           ActionCandidate(ActionType.NO_ACTION, 0, 1, "")]
                before = self.path.read_bytes()
                with patch("agent.delivery.Outbox", return_value=self.outbox):
                    self.assertEqual(exclude_completed_candidates([blocked] + allowed), allowed)
                    self.assertFalse(completed_social_actions()[collection])
                self.assertEqual(self.path.read_bytes(), before)
                transport = Mock()
                self.assertEqual(self.outbox.send("closed", "endpoint", {}, transport, idempotent=True), {})
                transport.assert_not_called()

    def test_chooser_never_offers_abandoned_repost_to_model(self):
        import json
        from agent.choice import choose
        from agent.context_engine import build_environment_context
        from agent.decision_engine import ActionCandidate, ActionType, DecisionOutcome
        from agent.runtime import execution_mode
        from agent.storage import write_json
        write_json(self.path, {"closed": {"status": "abandoned", "payload": {
            "collection": "app.bsky.feed.repost", "record": {"subject": {"uri": "post:old"}}}}})
        blocked = ActionCandidate(ActionType.REPOST, 1, 1, "", {"post": {"uri": "post:old"}})
        quiet = ActionCandidate(ActionType.NO_ACTION, 0, 1, "")
        outcome = DecisionOutcome(blocked.action, "", {}, "", {}, [blocked, quiet])
        with execution_mode("live"), patch("agent.delivery.Outbox", return_value=self.outbox), patch(
            "agent.generator.generator._call_llm", return_value=('{"candidate_id":0,"confidence":0.99}', "mock")
        ) as model:
            result = choose(outcome, build_environment_context())
        self.assertEqual(result.selected_action, ActionType.NO_ACTION)
        options = json.loads(model.call_args.args[1])["options"]
        self.assertEqual([option["action"] for option in options], ["NO_ACTION"])

    def test_completed_social_targets_are_excluded_but_other_actions_remain(self):
        from agent.delivery import exclude_completed_candidates
        from agent.decision_engine import ActionCandidate, ActionType
        from agent.storage import write_json
        rows = {}
        for action, collection, subject in [
            (ActionType.BROWSE_AND_LIKE, "app.bsky.feed.like", {"uri": "post:old"}),
            (ActionType.REPOST, "app.bsky.feed.repost", {"uri": "post:old"}),
            (ActionType.FOLLOW, "app.bsky.graph.follow", "did:old")]:
            rows[action.value] = {"status": "delivered", "payload": {"collection": collection, "record": {"subject": subject}}}
        write_json(self.path, rows)
        old = {"post": {"uri": "post:old", "author": {"did": "did:old"}}}
        new = {"post": {"uri": "post:new", "author": {"did": "did:new"}}}
        candidates = [ActionCandidate(action, 0, 1, "", data) for data in (old, new) for action in ActionType]
        with patch("agent.delivery.Outbox", return_value=self.outbox):
            retained = exclude_completed_candidates(candidates)
        self.assertEqual(len(retained), len(candidates) - 3)
        self.assertTrue(any(c.action == ActionType.BROWSE_AND_REPLY and c.target_data == old for c in retained))
        self.assertTrue(any(c.action == ActionType.NO_ACTION for c in retained))

    def test_viewer_state_and_recent_likes_exclude_completed_candidates(self):
        from agent.delivery import exclude_completed_candidates
        from agent.decision_engine import ActionCandidate, ActionType
        data = {"post": {"uri": "post:1", "viewer": {"like": "receipt", "repost": "receipt"},
                         "author": {"viewer": {"following": "receipt"}}}}
        candidates = [ActionCandidate(action, 0, 1, "", data) for action in (ActionType.BROWSE_AND_LIKE, ActionType.REPOST, ActionType.FOLLOW)]
        with patch("agent.delivery.Outbox", return_value=self.outbox):
            self.assertEqual(exclude_completed_candidates(candidates), [])
            candidate = ActionCandidate(ActionType.BROWSE_AND_LIKE, 0, 1, "", {"post": {"uri": "post:recent", "viewer": None}})
            self.assertEqual(exclude_completed_candidates([candidate], [None, "post:recent"]), [])

    def test_uncertain_delivery_is_not_misclassified_as_completed(self):
        from agent.delivery import completed_social_actions
        from agent.storage import write_json
        write_json(self.path, {"one": {"status": "uncertain", "payload": {"collection": "app.bsky.feed.like", "record": {"subject": {"uri": "post:1"}}}}})
        with patch("agent.delivery.Outbox", return_value=self.outbox):
            self.assertFalse(completed_social_actions()["app.bsky.feed.like"])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "outbox.json"
        self.outbox = Outbox(self.path, persist=lambda: None)

    def test_payload_is_frozen_across_restart(self):
        self.outbox.prepare("one", "post", {"text": "original"})
        restarted = Outbox(self.path, persist=lambda: None)
        transport = Mock(return_value={"uri": "at://one"})
        restarted.send("one", "post", {"text": "different"}, transport)
        self.assertEqual(transport.call_args.args[1]["text"], "original")

    def test_failed_checkpoint_never_sends(self):
        outbox = Outbox(self.path, persist=Mock(side_effect=RuntimeError("disk failure")))
        transport = Mock()
        with self.assertRaises(RuntimeError):
            outbox.send("one", "post", {}, transport)
        transport.assert_not_called()

    def test_ambiguous_dm_is_not_retried(self):
        transport = Mock(return_value={})
        self.assertEqual(self.outbox.send("one", "dm", {}, transport), {})
        self.assertEqual(Outbox(self.path, persist=lambda: None).send("one", "dm", {}, transport), {})
        transport.assert_called_once()

    def test_delivered_message_is_not_resent(self):
        transport = Mock(return_value={"id": "one"})
        for _ in range(3):
            self.assertEqual(self.outbox.send("one", "dm", {}, transport), {"id": "one"})
        transport.assert_called_once()

    def test_idempotent_record_recovers_after_timeout(self):
        transport = Mock(return_value={})
        self.outbox.send("one", "post", {"rkey": "stable"}, transport, idempotent=True)
        lookup = Mock(return_value={"uri": "at://stable"})
        result = self.outbox.send("one", "post", {}, transport, lookup, idempotent=True)
        self.assertEqual(result["uri"], "at://stable")
        transport.assert_called_once()

    def test_transport_exception_leaves_uncertain_record(self):
        with self.assertRaises(TimeoutError):
            self.outbox.send("one", "dm", {}, Mock(side_effect=TimeoutError))
        self.assertEqual(self.outbox.pending()["one"]["status"], "uncertain")

    def test_record_key_matches_protocol_and_decodes_timestamp(self):
        with patch("agent.delivery.time.time_ns", return_value=1720000000123456000), patch("agent.delivery._tid_last", 0):
            key = new_record_key()
        self.assertRegex(key, r"^[234567abcdefghij][234567abcdefghijklmnopqrstuvwxyz]{12}$")
        value = 0
        for char in key:
            value = value * 32 + "234567abcdefghijklmnopqrstuvwxyz".index(char)
        self.assertEqual(value >> 10, 1720000000123456)

    def test_record_keys_increase_when_clock_stalls_or_moves_back(self):
        with patch("agent.delivery.time.time_ns", side_effect=[2000000, 2000000, 1000000]), patch("agent.delivery._tid_last", 0):
            keys = [new_record_key() for _ in range(3)]
        self.assertEqual(keys, sorted(set(keys)))

    def test_bluesky_collections_use_tid_and_keep_frozen_key_on_restart(self):
        from agent.bsky_client import BlueskyClient
        from agent.runtime import execution_mode
        for collection in ("app.bsky.feed.post", "app.bsky.feed.like", "app.bsky.feed.repost", "app.bsky.graph.follow"):
            with self.subTest(collection=collection):
                payload = {"repo": "did:plc:test", "collection": collection,
                           "record": {"subject": {"uri": "at://test/post", "cid": "test"}, "createdAt": "2026-10-10T20:00:00Z"}}
                sent = []
                def transport(endpoint, frozen):
                    self.assertRegex(frozen["rkey"], r"^[234567abcdefghij][234567abcdefghijklmnopqrstuvwxyz]{12}$")
                    sent.append(dict(frozen))
                    return {} if len(sent) == 1 else {"uri": "at://test/" + frozen["rkey"]}
                with execution_mode("live"), patch("agent.delivery.Outbox", side_effect=lambda: self.outbox):
                    for _ in range(2):
                        client = BlueskyClient(dry_run=False)
                        with patch.object(client, "_xrpc_post_raw", side_effect=transport), patch.object(client, "xrpc_get", return_value={}):
                            client.xrpc_post("com.atproto.repo.createRecord", payload)
                self.assertEqual(len(sent), 2)
                self.assertEqual(sent[0], sent[1])
