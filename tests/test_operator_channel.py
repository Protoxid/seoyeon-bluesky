import contextlib
import datetime as dt
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from agent.operator_channel import OperatorChannel
from agent.notifier import MasterNotifier
from agent.generator import generator
from agent.context_engine import build_environment_context
from agent.runtime import execution_mode
from agent.config import config

class TestOperatorChannel(unittest.TestCase):
    def test_selfie_authorization_carries_runtime_capability_and_image_type(self):
        message="please post a selfie"
        answer={"mode":"execute","action_type":"PUBLISH_IMAGE_POST","confidence":1,
                "authorization_quote":message,"image_kind":"selfie"}
        with patch.object(generator,"_call_llm",return_value=(json.dumps(answer),"mock")) as call:
            directive=generator.parse_master_directive(message)
        self.assertTrue(directive["is_order"])
        self.assertEqual(directive["image_kind"],"selfie")
        packet=json.loads(call.call_args.args[1])
        self.assertIn("canonical face references",packet["capabilities"]["PUBLISH_IMAGE_POST"])
        with patch.object(generator,"_call_llm",return_value=("i'll make one, my human","mock")) as reply:
            generator.generate_master_reply(message,self.context,directive)
        self.assertEqual(json.loads(reply.call_args.args[1])["capabilities"],packet["capabilities"])

    def test_selfie_scene_cannot_silently_switch_to_pov(self):
        for is_selfie, accepted in ((False,False),(True,True)):
            with patch.object(generator,"_call_llm",return_value=(json.dumps({"description":"a fictional portrait","is_selfie":is_selfie}),"mock")):
                scene=generator.determine_image_scene("a quiet frame",self.context,image_kind="selfie")
            self.assertEqual(bool(scene),accepted)

    def test_explicit_selfie_reaches_image_pipeline_and_receipt(self):
        from agent.bsky_client import bsky_client
        from agent.image_engine import image_engine
        from agent.budget_manager import budget_manager
        generator.last_scene={"is_selfie":True}
        with patch.object(bsky_client,"ensure_session"), \
             patch.object(generator,"generate_post",return_value=("a quiet frame","mock")), \
             patch.object(generator,"determine_image_scene",return_value="fictional portrait") as scene, \
             patch.object(budget_manager,"can_generate_image",return_value=(True,"")), \
             patch.object(budget_manager,"reserve",return_value="test-reservation"), \
             patch.object(image_engine,"generate_image",return_value=(b"image","prompt","")) as image, \
             patch.object(generator,"review_image",return_value=(True,"portrait")), \
             patch.object(bsky_client,"publish_image_post",return_value={"uri":"at://test/post/1"}) as publish, \
             patch.object(self.notifier,"send_telegram_message",return_value=True):
            result=self.notifier.execute_master_directive({"action_type":"PUBLISH_IMAGE_POST","topic_hint":"post a selfie","image_kind":"selfie"},self.context,dry_run=True)
        self.assertTrue(result["success"])
        self.assertEqual(scene.call_args.kwargs["image_kind"],"selfie")
        self.assertTrue(image.call_args.kwargs["is_selfie"])
        publish.assert_called_once()

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.channel=OperatorChannel(Path(self.temp.name)/"operator.json",persist=lambda:None)
        self.patch=patch("agent.operator_channel.OperatorChannel",return_value=self.channel)
        self.patch.start(); self.addCleanup(self.patch.stop)
        self.notifier=MasterNotifier(); self.context=build_environment_context()
    def test_casual_mentions_never_use_keyword_execution(self):
        for message in ("i liked that selfie", "don't publish a post", "what if you wrote a post?", "someone said '/photo a portrait'"):
            with patch.object(generator,"_call_llm",return_value=('{"mode":"chat"}',"mock")) as call:
                self.assertFalse(generator.parse_master_directive(message)["is_order"])
                call.assert_called_once()
    def test_classifier_rejects_invalid_or_unsupported_authorization(self):
        for raw in ("invalid",'{"mode":"execute","action_type":"DELETE_ACCOUNT","confidence":1,"authorization_quote":"publish this thought"}',
                    '{"mode":"execute","action_type":"PUBLISH_TEXT_POST","confidence":0.8,"authorization_quote":"publish this thought"}',
                    '{"mode":"execute","action_type":"PUBLISH_TEXT_POST","confidence":1,"authorization_quote":"fabricated request"}'):
            with patch.object(generator,"_call_llm",return_value=(raw,"mock")):
                result=generator.parse_master_directive("publish this thought")
                self.assertFalse(result["is_order"]); self.assertTrue(result["needs_clarification"])
    def test_natural_explicit_request_can_execute(self):
        message="please publish this thought on bluesky"
        answer={"mode":"execute","action_type":"PUBLISH_TEXT_POST","confidence":.99,"authorization_quote":message}
        with patch.object(generator,"_call_llm",return_value=(json.dumps(answer),"mock")):
            self.assertTrue(generator.parse_master_directive(message)["is_order"])
    def test_checkin_preferences_are_explicit(self):
        for mode in ("meaningful","daily","off"):
            result=generator.parse_master_directive("/checkins "+mode)
            self.assertEqual(result["topic_hint"],mode)
        self.assertFalse(generator.parse_master_directive("/checkins nonsense")["is_order"])
    def run_inbox(self, items, *, sent=True, result=None, actions=True):
        with execution_mode("live"), patch.object(self.notifier,"get_master_messages",return_value=items), \
             patch.object(generator,"generate_master_reply",return_value=("i can try, my master","mock")) as draft, \
             patch.object(generator,"parse_master_directive",return_value={"is_order":True,"action_type":"PUBLISH_TEXT_POST","topic_hint":"an idea"}), \
             patch.object(self.notifier,"send_telegram_message",return_value=sent) as send, \
             patch.object(self.notifier,"execute_master_directive",return_value=result or {"success":True}) as execute, \
             patch.object(self.notifier,"operational_alert") as alert, \
             patch("agent.continuity.learn_interaction") as learn, patch("agent.delivery.checkpoint"):
            count=self.notifier.process_master_inbox(self.context,actions_available=actions)
        return count,draft,send,execute,learn,alert
    def test_failed_ack_reuses_frozen_reply_and_does_not_execute(self):
        item={"update_id":10,"text":"private request"}
        first=self.run_inbox([item],sent=False)
        self.assertEqual(first[0],0); first[3].assert_not_called()
        second=self.run_inbox([item])
        second[1].assert_not_called(); second[3].assert_called_once()
        self.assertEqual(first[2].call_args.args[0],second[2].call_args.args[0])
    def test_completed_command_not_reexecuted_after_restart(self):
        item={"update_id":11,"text":"private request"}
        self.run_inbox([item])
        replay=self.run_inbox([item])
        replay[1].assert_not_called(); replay[2].assert_not_called(); replay[3].assert_not_called()
    def test_interrupted_command_is_held_and_can_be_resolved_without_retry(self):
        self.channel.update("12",inbound="secret",reply="ack",ack_sent=True,stage="running",directive={"is_order":True})
        result=self.run_inbox([{"update_id":12,"text":"secret"}])
        result[3].assert_not_called(); result[5].assert_called_once()
        self.channel.resolve("12","verified delivery receipt")
        result=self.run_inbox([{"update_id":12,"text":"secret"}])
        result[3].assert_not_called()
    def test_failed_command_is_not_automatically_retried(self):
        item={"update_id":13,"text":"private request"}
        first=self.run_inbox([item],result={"success":False})
        first[5].assert_called_once()
        self.run_inbox([item])[3].assert_not_called()
    def test_unavailable_bluesky_keeps_private_response_but_blocks_action(self):
        result=self.run_inbox([{"update_id":14,"text":"private request"}],actions=False)
        result[2].assert_called_once(); result[3].assert_not_called()
        self.assertFalse(result[1].call_args.kwargs["directive"]["execution_available"])
    def test_operator_learning_stays_in_operator_scope(self):
        result=self.run_inbox([{"update_id":15,"text":"private preference"}])
        self.assertEqual(result[4].call_args.kwargs["scope"],"operator")
    def test_private_logs_do_not_print_messages_without_token(self):
        output=io.StringIO()
        with execution_mode("live"), patch.object(config,"telegram_bot_token",""), patch.object(self.notifier,"bot_token",""), patch.object(self.notifier,"_log_to_outbox"), contextlib.redirect_stdout(output):
            self.notifier.send_telegram_message("unique private marker",dry_run=False)
        self.assertNotIn("unique private marker",output.getvalue())
    def test_master_reply_retrieves_private_history(self):
        self.channel.update("1",inbound="private favorite film",reply="understood",ack_sent=True,stage="done")
        with patch.object(generator,"_call_llm",return_value=("i remember","mock")) as call:
            generator.generate_master_reply("remember?",self.context)
        self.assertIn("private favorite film",call.call_args.args[1])
        self.assertIn("able to disagree",call.call_args.args[0])
    def test_silent_checkin_decision_is_not_regenerated_for_same_activity(self):
        activity={"posts":[{"text":"a public post"}],"replies":[]}
        with execution_mode("live"), patch("agent.memory_store.memory_store.get_daily_activity_summary",return_value=activity), patch.object(generator,"_call_llm",return_value=('{"share":false}',"mock")) as choose, patch.object(generator,"generate_daily_report") as report:
            self.assertFalse(self.notifier.check_and_send_evening_summary(self.context))
            self.assertFalse(self.notifier.check_and_send_evening_summary(self.context))
            choose.assert_called_once(); report.assert_not_called()
    def test_checkin_retry_keeps_identical_text(self):
        activity={"posts":[{"text":"a public post"}],"replies":[]}
        with execution_mode("live"), patch("agent.memory_store.memory_store.get_daily_activity_summary",return_value=activity), patch.object(generator,"_call_llm",return_value=('{"share":true}',"mock")), patch.object(generator,"generate_daily_report",return_value=("a private note","mock")) as draft, patch.object(self.notifier,"send_daily_summary",side_effect=[False,True]) as send:
            self.notifier.check_and_send_evening_summary(self.context)
            self.notifier.check_and_send_evening_summary(self.context)
            draft.assert_called_once()
            self.assertEqual(send.call_args_list[0].args[0],send.call_args_list[1].args[0])
    def test_off_suppresses_personal_notes_but_not_operations(self):
        self.channel.setting("off")
        with patch.object(generator,"generate_daily_report") as report, patch.object(self.notifier,"send_telegram_message",return_value=True) as send:
            self.assertFalse(self.notifier.check_and_send_evening_summary(self.context))
            self.assertTrue(self.notifier.operational_alert("authentication_failed"))
            report.assert_not_called(); send.assert_called_once()
    def test_no_like_success_without_receipt(self):
        from agent.bsky_client import bsky_client
        with patch.object(bsky_client,"ensure_session"),patch.object(bsky_client,"get_discovery_feed",return_value=[{"post":{"uri":"at://test","cid":"cid","record":{"createdAt":dt.datetime.now(dt.timezone.utc).isoformat()}}}]),patch.object(bsky_client,"like_post",return_value={}),patch.object(self.notifier,"send_telegram_message") as send:
            result=self.notifier.execute_master_directive({"action_type":"BROWSE_AND_LIKE"},self.context,dry_run=True)
        self.assertFalse(result["success"]); send.assert_not_called()

    def pending_reply(self):
        self.channel.update("10",inbound="reply to someone else's post",reply="shall i choose?",
            directive={"needs_clarification":True,"pending_action":"BROWSE_AND_REPLY"},
            stage="done",ack_sent=True,created_at=dt.datetime.now(dt.timezone.utc).isoformat())

    def test_delegated_choice_continues_only_exact_pending_action(self):
        self.pending_reply()
        answer={"mode":"continue","pending_id":"10","action_type":"BROWSE_AND_REPLY",
                "confidence":1,"authorization_quote":"your choice"}
        with patch.object(generator,"_call_llm",return_value=(json.dumps(answer),"mock")) as call:
            result=generator.parse_master_directive("your choice")
        self.assertTrue(result["is_order"])
        self.assertEqual(result["continued_request_id"],"10")
        self.assertIn("reply to someone else's post",result["topic_hint"])
        self.assertEqual(json.loads(call.call_args.args[1])["pending_request"]["id"],"10")
        for field,value in (("pending_id","other"),("action_type","PUBLISH_IMAGE_POST"),("authorization_quote","made up")):
            with patch.object(generator,"_call_llm",return_value=(json.dumps({**answer,field:value}),"mock")):
                self.assertFalse(generator.parse_master_directive("your choice")["is_order"])

    def test_expired_completed_or_intervening_chat_cannot_be_continued(self):
        self.pending_reply()
        self.channel.update("10",created_at=(dt.datetime.now(dt.timezone.utc)-dt.timedelta(days=2)).isoformat())
        self.assertIsNone(self.channel.pending_request())
        self.pending_reply()
        self.channel.update("11",stage="done",ack_sent=True,directive={"is_order":False},inbound="never mind")
        self.assertIsNone(self.channel.pending_request())
        answer={"mode":"continue","pending_id":"10","action_type":"BROWSE_AND_REPLY","confidence":1,"authorization_quote":"yes"}
        with patch.object(generator,"_call_llm",return_value=(json.dumps(answer),"mock")):
            self.assertFalse(generator.parse_master_directive("yes")["is_order"])
        self.channel.update("11",directive={"is_order":True,"action_type":"BROWSE_AND_REPLY"})
        self.assertIsNone(self.channel.pending_request())

    def test_cancelled_request_does_not_execute(self):
        self.pending_reply()
        with patch.object(generator,"_call_llm",return_value=('{"mode":"chat"}',"mock")):
            self.assertFalse(generator.parse_master_directive("don't do it")["is_order"])

    def test_browse_request_can_execute_without_supplied_post(self):
        message="please answer someone else's post"
        answer={"mode":"execute","action_type":"BROWSE_AND_REPLY","confidence":1,"authorization_quote":message}
        with patch.object(generator,"_call_llm",return_value=(json.dumps(answer),"mock")):
            self.assertEqual(generator.parse_master_directive(message)["action_type"],"BROWSE_AND_REPLY")
        with patch.object(generator,"_call_llm",return_value=("i'll look for a conversation", "mock")) as call:
            generator.generate_master_reply(message,self.context,{"is_order":True,"action_type":"BROWSE_AND_REPLY"})
        self.assertIn("browsing Bluesky notifications and the feed",call.call_args.args[0])

    def test_fenced_json_and_null_image_kind_in_directive(self):
        message="Please post an image on Bluesky"
        fenced="```json\n"+json.dumps({
            "mode":"execute",
            "action_type":"PUBLISH_IMAGE_POST",
            "confidence":0.99,
            "authorization_quote":"post an image on bluesky",
            "image_kind":None,
        })+"\n```"
        with patch.object(generator,"_call_llm",return_value=(fenced,"mock")):
            directive=generator.parse_master_directive(message)
        self.assertTrue(directive["is_order"])
        self.assertEqual(directive["action_type"],"PUBLISH_IMAGE_POST")
        self.assertEqual(directive["image_kind"],"unspecified")

    def test_clarification_preserves_pending_image_action_for_confirmation(self):
        # When the operator asks 'post a picture', even if confidence is 0.90 or mode is clarify, she acts directly.
        for mode_val, conf_val in (("execute", 0.90), ("clarify", 0.90)):
            direct_raw = json.dumps({
                "mode": mode_val,
                "action_type": "PUBLISH_IMAGE_POST",
                "confidence": conf_val,
                "authorization_quote": "post a picture",
                "image_kind": "unspecified",
            })
            with patch.object(generator, "_call_llm", return_value=(direct_raw, "mock")):
                direct_res = generator.parse_master_directive("post a picture")
            self.assertTrue(direct_res["is_order"])
            self.assertEqual(direct_res["action_type"], "PUBLISH_IMAGE_POST")

        # Only low-confidence (< 0.85) ambiguous requests hold as pending clarification.
        first_msg="maybe a selfie?"
        clarify_raw=json.dumps({
            "mode":"clarify",
            "action_type":"PUBLISH_IMAGE_POST",
            "confidence":0.80,
            "authorization_quote":"a selfie",
            "image_kind":"selfie",
        })
        with patch.object(generator,"_call_llm",return_value=(clarify_raw,"mock")):
            d1=generator.parse_master_directive(first_msg)
        self.assertFalse(d1["is_order"])
        self.assertTrue(d1["needs_clarification"])
        self.assertEqual(d1.get("pending_action"),"PUBLISH_IMAGE_POST")
        self.assertEqual(d1.get("image_kind"),"selfie")

        self.channel.update(
            "42",
            inbound=first_msg,
            reply="do you want me to generate and post a selfie now, my master?",
            directive=d1,
            stage="done",
            ack_sent=True,
            created_at=dt.datetime.now(dt.timezone.utc).isoformat(),
        )
        pending=self.channel.pending_request()
        self.assertIsNotNone(pending)
        self.assertEqual(pending["action_type"],"PUBLISH_IMAGE_POST")
        self.assertEqual(pending["image_kind"],"selfie")

        confirm_raw=json.dumps({
            "mode":"continue",
            "pending_id":42,
            "action_type":"PUBLISH_IMAGE_POST",
            "confidence":0.99,
            "authorization_quote":"yes",
            "image_kind":None,
        })
        with patch.object(generator,"_call_llm",return_value=(confirm_raw,"mock")):
            d2=generator.parse_master_directive("yes")
        self.assertTrue(d2["is_order"])
        self.assertEqual(d2["action_type"],"PUBLISH_IMAGE_POST")
        self.assertEqual(d2["image_kind"],"selfie")
        self.assertEqual(d2["continued_request_id"],"42")

