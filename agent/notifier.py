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

        # Record episodic memory
        try:
            from .memory_store import memory_store
            memory_store.log_episode(
                "telegram_contact_with_master",
                f"Sent message to my master ({self.master_handle})",
                {"question": question, "context": context, "delivered": success},
            )
        except Exception:
            pass

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

        # Record episodic memory
        try:
            from .memory_store import memory_store
            memory_store.log_episode(
                "daily_report_to_master",
                f"Delivered evening daily summary to my master ({self.master_handle})",
                {"date": date_str, "summary": summary_text[:120], "delivered": success},
            )
        except Exception:
            pass

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

    def process_master_inbox(self, context: Any, dry_run: Optional[bool] = None) -> int:
        """
        Processes any unread inbound messages from my master (@Protoxide).
        Generates in-character thoughtful replies and updates Seo-yeon's cognitive state.
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

            # 2. Generate in-character reply
            reply_text, model_used = generator.generate_master_reply(text, context)
            print(f"[Telegram Outbound to my master]: \"{reply_text}\" (model: {model_used})")

            # 3. Deliver reply
            self.send_telegram_message(reply_text, dry_run=dry_run)

            # 4. Log episodic memory
            memory_store.log_episode(
                "master_telegram_dialogue",
                f"Conversation with my master on Telegram",
                {
                    "master_text": text,
                    "reply_text": reply_text,
                    "model": model_used,
                },
            )
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
