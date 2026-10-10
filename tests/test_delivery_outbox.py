from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock
from agent.delivery import Outbox


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
