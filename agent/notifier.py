"""
agent/notifier.py — Direct Outbound Telegram Messenger for Seo-yeon to Her Master / Human.

Implements real-time messaging from Seo-yeon to her human creator / operator (@Protoxide):
  - Always addresses the user as "my master" or "my human".
  - Sends direct Telegram alerts via the Telegram Bot API (https://api.telegram.org/bot<TOKEN>/sendMessage).
  - Handles dry-run simulations, recording messages to data/logs/telegram_outbox.jsonl.
  - Automatically logs episodic memory whenever Seo-yeon reaches out to her master.
"""

from __future__ import annotations

import datetime as dt
import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional

from .config import LOGS_DIR, config
from .context_engine import get_seoul_datetime


TELEGRAM_OUTBOX_FILE = LOGS_DIR / "telegram_outbox.jsonl"


class MasterNotifier:
    """Handles communication between Seo-yeon Han and her human creator/master."""

    def __init__(self):
        self.bot_token = config.telegram_bot_token
        self.chat_id = config.telegram_chat_id
        self.master_handle = config.master_telegram_handle

    def _log_to_outbox(self, entry: Dict[str, Any]) -> None:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        with open(TELEGRAM_OUTBOX_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def send_telegram_message(
        self,
        text: str,
        dry_run: Optional[bool] = None,
    ) -> bool:
        """
        Sends an outbound text message to the human creator (@Protoxide) on Telegram.
        Falls back cleanly to local outbox logging in dry-run or if the bot token is unset.
        """
        is_dry = dry_run if dry_run is not None else config.dry_run
        seoul_now = get_seoul_datetime().strftime("%Y-%m-%d %H:%M:%S KST")

        outbox_entry = {
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
            "seoul_time": seoul_now,
            "recipient": self.master_handle,
            "text": text,
            "dry_run": is_dry,
            "status": "pending",
        }

        if is_dry:
            print(f"\n[DRY-RUN Telegram -> my master {self.master_handle}]")
            for line in text.splitlines():
                print(f"  {line}")
            outbox_entry["status"] = "simulated_dry_run"
            self._log_to_outbox(outbox_entry)
            return True

        token = config.telegram_bot_token or self.bot_token
        chat_id = config.telegram_chat_id or self.chat_id

        if not token:
            print(f"\n[Telegram Notice] TELEGRAM_BOT_TOKEN not configured yet in environment.")
            print(f"Message logged to outbox for my master {self.master_handle}: \"{text[:80]}...\"")
            outbox_entry["status"] = "token_missing_saved_to_outbox"
            self._log_to_outbox(outbox_entry)
            return True

        # Send live message via Telegram Bot API
        telegram_url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
        }

        try:
            req = urllib.request.Request(
                telegram_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                if res.get("ok"):
                    print(f"  [SUCCESS] Telegram message delivered to my master {self.master_handle}")
                    outbox_entry["status"] = "delivered"
                    outbox_entry["message_id"] = res.get("result", {}).get("message_id")
                    self._log_to_outbox(outbox_entry)
                    return True
                else:
                    print(f"  [WARNING] Telegram API returned non-ok: {res}")
                    outbox_entry["status"] = f"api_error_{res.get('description', '')}"
                    self._log_to_outbox(outbox_entry)
                    return False
        except Exception as e:
            print(f"  [ERROR] Failed to send Telegram message to my master {self.master_handle}: {e}")
            outbox_entry["status"] = f"network_error: {str(e)}"
            self._log_to_outbox(outbox_entry)
            return False

    def ask_master(
        self,
        question: str,
        context: Optional[str] = None,
        dry_run: Optional[bool] = None,
    ) -> bool:
        """
        In-character inquiry or escalation to the human creator / operator.
        Always addresses the human as 'my master' or 'my human'.
        """
        seoul_now = get_seoul_datetime().strftime("%Y-%m-%d %H:%M:%S KST")

        lines = [
            f"From: Han Seo-yeon (한서연) | @{config.bsky_handle}",
            f"To: my master ({self.master_handle})",
            f"Time: {seoul_now}",
            "",
            "Message for my master:",
            question.strip(),
        ]
        if context:
            lines.extend([
                "",
                "Context:",
                context.strip(),
            ])

        formatted_msg = "\n".join(lines)
        success = self.send_telegram_message(formatted_msg, dry_run=dry_run)


        return success

    def send_daily_summary(
        self,
        summary_text: str,
        summary_data: Optional[Dict[str, Any]] = None,
        dry_run: Optional[bool] = None,
    ) -> bool:
        """
        Sends the end-of-day in-character check-in message to my master (@Protoxide).
        """
        seoul_now = get_seoul_datetime().strftime("%Y-%m-%d %H:%M:%S KST")
        date_str = (summary_data or {}).get("date", get_seoul_datetime().strftime("%Y-%m-%d"))

        formatted_msg = (
            f"From: Han Seo-yeon (한서연) | @{config.bsky_handle}\n"
            f"To: my master ({self.master_handle})\n"
            f"Date: {date_str} (Late Evening Check-in — {seoul_now})\n\n"
            f"{summary_text.strip()}"
        )

        success = self.send_telegram_message(formatted_msg, dry_run=dry_run)


        return success

    def get_master_messages(self, dry_run: Optional[bool] = None) -> list[Dict[str, Any]]:
        """
        Polls the Telegram Bot API for incoming messages sent by my master (@Protoxide).
        Only processes messages matching the master's handle or chat ID.
        """
        is_dry = dry_run if dry_run is not None else config.dry_run
        if is_dry:
            return []

        token = config.telegram_bot_token or self.bot_token
        if not token:
            return []

        from .memory_store import memory_store
        last_update_id = memory_store.get_telegram_last_update_id()

        params = {"timeout": 3}
        if last_update_id > 0:
            params["offset"] = last_update_id + 1

        query = urllib.parse.urlencode(params)
        url = f"https://api.telegram.org/bot{token}/getUpdates?{query}"

        master_clean_handle = self.master_handle.lower().lstrip("@")
        master_chat_id = str(config.telegram_chat_id or self.chat_id or "").strip()

        messages: list[Dict[str, Any]] = []
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SeoYeonAgent/1.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for update in data.get("result", []):
                    up_id = update.get("update_id")
                    msg = update.get("message", {})
                    sender = msg.get("from", {})
                    sender_username = (sender.get("username") or "").lower().lstrip("@")
                    sender_id = str(sender.get("id", "")).strip()
                    chat_id = str(msg.get("chat", {}).get("id", "")).strip()
                    text = msg.get("text", "").strip()

                    # Always advance update offset to acknowledge receipt
                    if up_id:
                        memory_store.set_telegram_last_update_id(up_id)

                    if not text:
                        continue

                    # Authenticate: sender must be my master (@Protoxide or chat_id)
                    is_master = (
                        sender_username == master_clean_handle
                        or (master_chat_id and sender_id == master_chat_id)
                        or (master_chat_id and chat_id == master_chat_id)
                    )

                    if is_master:
                        messages.append({
                            "update_id": up_id,
                            "message_id": msg.get("message_id"),
                            "from": sender_username or sender_id,
                            "chat_id": chat_id,
                            "text": text,
                            "date": msg.get("date"),
                        })
                    else:
                        print(f"[Telegram Notice] Ignored message from unauthorized sender: @{sender_username} (id: {sender_id})")
        except Exception as e:
            print(f"[MasterNotifier] Error polling getUpdates: {e}")

        return messages

    def execute_master_directive(
        self,
        directive: Dict[str, Any],
        context: Any,
        dry_run: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Executes an explicit order from my master (@Protoxide) on Bluesky.
        Maintains strict space-time and environmental coherence with her current Seoul moment.
        Sends a follow-up confirmation message to my master upon completion.
        """
        is_dry = dry_run if dry_run is not None else config.dry_run
        action_type = directive.get("action_type")
        topic_hint = directive.get("topic_hint") or ""

        from .generator import generator
        from .bsky_client import bsky_client
        from .budget_manager import budget_manager
        from .memory_store import memory_store

        # Ensure Bluesky client has session configured
        bsky_client.dry_run = is_dry
        bsky_client.ensure_session()

        result: Dict[str, Any] = {"action_type": action_type, "success": False}

        # -------------------------------------------------------------
        # 1. PUBLISH IMAGE POST
        # -------------------------------------------------------------
        if action_type == "PUBLISH_IMAGE_POST":
            from .image_engine import image_engine

            print(f"[Master Directive: Image Post] Generating image post coherent with {context.seoul_time_display}...")
            post_text, model_used = generator.generate_post(
                intent="master_order_image",
                context=context,
                topic_hint=topic_hint,
                include_image=True,
            )
            scene_desc = generator.determine_image_scene(post_text, context, hint=topic_hint)
            print(f"  Post draft: \"{post_text}\"")
            print(f"  Scene prompt: \"{scene_desc}\"")

            img_bytes, prompt_used, err = image_engine.generate_image(scene_desc, dry_run=is_dry)
            if img_bytes:
                res = bsky_client.publish_image_post(post_text, img_bytes, alt_text="Han Seo-yeon candid moment")
                uri = res.get("uri", "")
                if uri:
                    result["success"] = True
                    result["uri"] = uri
                    result["post_text"] = post_text

                    if not is_dry:
                        memory_store.record_recent_post(post_text, topic="master_ordered_image", post_id=uri, has_image=True)
                        budget_manager.record_spend(0.045, "image_generation", prompt_used[:40])

                    rkey = uri.split("/")[-1]
                    handle = config.bsky_handle or "syeonhn.bsky.social"
                    web_url = f"https://bsky.app/profile/{handle}/post/{rkey}"

                    confirm_msg = f"done, my master. posted to bluesky: {web_url}"
                    self.send_telegram_message(confirm_msg, dry_run=dry_run)
            else:
                # If image generation service failed, fall back to text post
                print(f"[Master Directive: Image Post] Image generation failed ({err}). Falling back to text post.")
                res = bsky_client.publish_text_post(post_text)
                uri = res.get("uri", "")
                rkey = uri.split("/")[-1]
                handle = config.bsky_handle or "syeonhn.bsky.social"
                web_url = f"https://bsky.app/profile/{handle}/post/{rkey}"
                confirm_msg = f"camera service hit an issue, my master, so i shared the thought as text: {web_url}"
                self.send_telegram_message(confirm_msg, dry_run=dry_run)

        # -------------------------------------------------------------
        # 2. PUBLISH TEXT POST
        # -------------------------------------------------------------
        elif action_type == "PUBLISH_TEXT_POST":
            print(f"[Master Directive: Text Post] Generating post coherent with {context.seoul_time_display}...")
            post_text, model_used = generator.generate_post(
                intent="master_order_post",
                context=context,
                topic_hint=topic_hint,
                include_image=False,
            )
            print(f"  Post draft: \"{post_text}\"")

            res = bsky_client.publish_text_post(post_text)
            uri = res.get("uri", "")
            if uri:
                result["success"] = True
                result["uri"] = uri
                result["post_text"] = post_text

                if not is_dry:
                    memory_store.record_recent_post(post_text, topic="master_ordered_post", post_id=uri)
                    budget_manager.record_spend(0.002, "text_post", post_text[:30])

                rkey = uri.split("/")[-1]
                handle = config.bsky_handle or "syeonhn.bsky.social"
                web_url = f"https://bsky.app/profile/{handle}/post/{rkey}"

                confirm_msg = f"done, my master. posted to bluesky: {web_url}"
                self.send_telegram_message(confirm_msg, dry_run=dry_run)

        # -------------------------------------------------------------
        # 3. ANSWER DIRECT MESSAGES
        # -------------------------------------------------------------
        elif action_type == "ANSWER_DM":
            print("[Master Directive: Answer DM] Checking Bluesky conversations...")
            convos = bsky_client.list_convos(limit=10)
            answered = False
            for convo in convos:
                convo_id = convo.get("id")
                members = convo.get("members", [])
                other = next((m for m in members if m.get("did") != bsky_client.did), members[0] if members else {})
                handle = other.get("handle", "user")

                raw_msgs = bsky_client.get_convo_messages(convo_id, limit=10)
                if not raw_msgs:
                    continue

                dm_history = [
                    {
                        "sender_handle": handle if m.get("sender", {}).get("did") != bsky_client.did else config.bsky_handle,
                        "text": m.get("text", ""),
                    }
                    for m in raw_msgs
                ]
                profile = memory_store.get_user_profile(handle)
                reply_text, model = generator.generate_dm_reply(dm_history, profile, context)
                dm_res = bsky_client.send_dm(convo_id, reply_text)
                if dm_res:
                    if not is_dry:
                        memory_store.record_user_interaction(handle, dm_history[-1]["text"] if dm_history else "", reply_text, "dm")
                        budget_manager.record_spend(0.002, "dm", f"to @{handle}")
                    result["success"] = True
                    result["dm_to"] = handle
                    answered = True
                    confirm_msg = f"done, my master. answered the message from @{handle}."
                    self.send_telegram_message(confirm_msg, dry_run=dry_run)
                    break

            if not answered:
                confirm_msg = "checked my direct messages, my master. inbox is clear right now, no unread dms."
                self.send_telegram_message(confirm_msg, dry_run=dry_run)

        # -------------------------------------------------------------
        # 4. BROWSE FEED & REPLY / COMMENT
        # -------------------------------------------------------------
        elif action_type in ("BROWSE_AND_REPLY", "REPLY_COMMENT", "ANSWER_MENTION"):
            print("[Master Directive: Reply / Comments] Checking notifications and feed...")
            notifs = bsky_client.list_notifications(limit=25)
            replied = False
            for n in notifs:
                reason = n.get("reason")
                if reason in ("mention", "reply"):
                    t_uri = n.get("uri", "")
                    t_cid = n.get("cid", "")
                    t_author = n.get("author", {}).get("handle", "user")
                    u_text = n.get("record", {}).get("text", "")

                    if memory_store.has_replied_to_notification(t_uri) or memory_store.has_replied_to_post(t_uri):
                        continue

                    thread_ctx = bsky_client.get_thread_context(t_uri)
                    can_rep, _ = bsky_client.can_reply_to_thread(t_uri, thread_ctx)
                    if not can_rep:
                        continue

                    profile = memory_store.get_user_profile(t_author)
                    reply_text, model = generator.generate_reply(t_author, u_text, thread_ctx, profile, context)

                    rec = n.get("record", {})
                    rmeta = rec.get("reply", {})
                    r_uri = rmeta.get("root", {}).get("uri", t_uri) if rmeta else t_uri
                    r_cid = rmeta.get("root", {}).get("cid", t_cid) if rmeta else t_cid

                    res = bsky_client.publish_reply(reply_text, t_uri, t_cid, r_uri, r_cid)
                    if res.get("uri"):
                        if not is_dry:
                            memory_store.record_user_interaction(t_author, u_text, reply_text, "reply", did=n.get("author", {}).get("did", ""))
                            memory_store.record_recent_reply(
                                target_handle=t_author,
                                user_text=u_text,
                                reply_text=reply_text,
                                uri=res.get("uri", ""),
                                target_uri=t_uri,
                                root_uri=r_uri,
                                notification_uri=t_uri,
                            )
                        bsky_client.update_seen()
                        result["success"] = True
                        replied = True
                        confirm_msg = f"done, my master. replied to @{t_author}'s comment on bluesky."
                        self.send_telegram_message(confirm_msg, dry_run=dry_run)
                        break

            if not replied:
                # Browse feed to leave a thoughtful comment
                feed_items = bsky_client.get_discovery_feed(limit=15)
                for item in feed_items:
                    p = item.get("post", {})
                    p_uri = p.get("uri", "")
                    p_cid = p.get("cid", "")
                    p_author = p.get("author", {}).get("handle", "user")
                    p_text = p.get("record", {}).get("text", "")

                    if memory_store.has_replied_to_post(p_uri):
                        continue
                    thread_ctx = bsky_client.get_thread_context(p_uri)
                    can_rep, _ = bsky_client.can_reply_to_thread(p_uri, thread_ctx)
                    if not can_rep:
                        continue

                    profile = memory_store.get_user_profile(p_author)
                    reply_text, model = generator.generate_reply(p_author, p_text, thread_ctx, profile, context)
                    r_meta = p.get("record", {}).get("reply", {})
                    r_uri = r_meta.get("root", {}).get("uri", p_uri) if r_meta else p_uri
                    r_cid = r_meta.get("root", {}).get("cid", p_cid) if r_meta else p_cid

                    res = bsky_client.publish_reply(reply_text, p_uri, p_cid, r_uri, r_cid)
                    if res.get("uri"):
                        if not is_dry:
                            memory_store.record_user_interaction(p_author, p_text, reply_text, "reply", did=p.get("author", {}).get("did", ""))
                            memory_store.record_recent_reply(
                                target_handle=p_author,
                                user_text=p_text,
                                reply_text=reply_text,
                                uri=res.get("uri", ""),
                                target_uri=p_uri,
                                root_uri=r_uri,
                                notification_uri=p_uri,
                            )
                        result["success"] = True
                        replied = True
                        confirm_msg = f"done, my master. left a comment on @{p_author}'s post on the feed."
                        self.send_telegram_message(confirm_msg, dry_run=dry_run)
                        break

            if not replied:
                confirm_msg = "checked bluesky comments and timeline, my master. all caught up."
                self.send_telegram_message(confirm_msg, dry_run=dry_run)

        # -------------------------------------------------------------
        # 5. BROWSE & LIKE
        # -------------------------------------------------------------
        elif action_type == "BROWSE_AND_LIKE":
            feed_items = bsky_client.get_discovery_feed(limit=10)
            if feed_items:
                p = feed_items[0].get("post", {})
                bsky_client.like_post(p.get("uri", ""), p.get("cid", ""))
                author = p.get("author", {}).get("handle", "")
                result["success"] = True
                confirm_msg = f"done, my master. liked a post by @{author} on the feed."
                self.send_telegram_message(confirm_msg, dry_run=dry_run)
            else:
                confirm_msg = "checked feed, my master. no matching posts to like right now."
                self.send_telegram_message(confirm_msg, dry_run=dry_run)

        # -------------------------------------------------------------
        # 6. CONSOLIDATE MEMORIES & PRIVATE JOURNAL
        # -------------------------------------------------------------
        elif action_type == "CONSOLIDATE":
            from .consolidator import consolidator
            res = consolidator.consolidate(context, dry_run=is_dry, force=True)
            result["success"] = True
            confirm_msg = "done, my master. consolidated today's thoughts and updated my private journal."
            self.send_telegram_message(confirm_msg, dry_run=dry_run)

        return result

    def process_master_inbox(self, context: Any, dry_run: Optional[bool] = None) -> int:
        """
        Processes any unread inbound messages from my master (@Protoxide).
        Generates in-character thoughtful replies and updates Seo-yeon's cognitive state.
        If the message contains an order or directive, she obeys and executes it on Bluesky.
        """
        incoming = self.get_master_messages(dry_run=dry_run)
        if not incoming:
            return 0

        from .generator import generator
        from .state_manager import state_manager
        from .memory_store import memory_store

        processed = 0
        for item in incoming:
            text = item.get("text", "")
            print(f"\n[Telegram Inbound from my master {self.master_handle}]: \"{text}\"")

            # 1. Reassure and recharge cognitive social battery
            state_manager.on_master_contact(note=text[:30])

            # 2. Parse directive / order from my master
            directive = generator.parse_master_directive(text)

            # 3. Generate in-character reply (grounded in current space/time, obedient to orders)
            reply_text, model_used = generator.generate_master_reply(text, context, directive=directive)
            print(f"[Telegram Outbound to my master]: \"{reply_text}\" (model: {model_used})")

            # 4. Deliver acknowledgment to master
            self.send_telegram_message(reply_text, dry_run=dry_run)

            # 5. If it is an order, execute it on Bluesky with strict space-time coherence!
            exec_details: Dict[str, Any] = {}
            if directive.get("is_order"):
                print(f"[Master Directive] Obeying directive '{directive.get('action_type')}' from my master...")
                exec_details = self.execute_master_directive(directive, context, dry_run=dry_run)

            processed += 1

        return processed

    def check_and_send_evening_summary(self, context: Any, dry_run: Optional[bool] = None) -> bool:
        """
        Robust evening check-in and catch-up reporting for my master.
        Guarantees that no day is missed even if GitHub Actions runs outside the exact evening hour.
        """
        now_kst = get_seoul_datetime()
        today_date = now_kst.date()
        yesterday_date = today_date - dt.timedelta(days=1)
        today_str = today_date.strftime("%Y-%m-%d")
        yesterday_str = yesterday_date.strftime("%Y-%m-%d")

        from .memory_store import memory_store
        from .generator import generator

        last_report_date = memory_store.get_last_daily_report_date()
        sent_any = False

        # 1. CATCH-UP: If yesterday was never reported, generate and send yesterday's summary
        if not last_report_date or last_report_date < yesterday_str:
            print(f"\n[Notice] Catching up missed daily summary for yesterday ({yesterday_str})...")
            yesterday_data = memory_store.get_daily_activity_summary(yesterday_date)
            report_text, model = generator.generate_daily_report(yesterday_data, context, is_catchup=True)
            sent = self.send_daily_summary(report_text, yesterday_data, dry_run=dry_run)
            if sent:
                sent_any = True
                if not dry_run:
                    memory_store.set_last_daily_report_date(yesterday_str)
                    last_report_date = yesterday_str
                print(f"  [SUCCESS] Yesterday's catch-up summary ({yesterday_str}) delivered to my master.")

        # 2. REGULAR EVENING: If current time is >= 21:00 KST and today hasn't been reported yet
        if now_kst.hour >= 21 and last_report_date != today_str:
            print(f"\n[Evening in Seoul ({now_kst.strftime('%H:%M KST')})] Generating evening check-in for my master ({self.master_handle})...")
            today_data = memory_store.get_daily_activity_summary(today_date)
            report_text, model = generator.generate_daily_report(today_data, context, is_catchup=False)
            sent = self.send_daily_summary(report_text, today_data, dry_run=dry_run)
            if sent:
                sent_any = True
                if not dry_run:
                    memory_store.set_last_daily_report_date(today_str)
                print(f"  [SUCCESS] Evening daily check-in ({today_str}) delivered to my master.")

        return sent_any


# Global singleton instance
notifier = MasterNotifier()
