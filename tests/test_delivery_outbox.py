from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from agent.delivery import Outbox, new_record_key


class TestDeliveryOutbox(unittest.TestCase):
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
