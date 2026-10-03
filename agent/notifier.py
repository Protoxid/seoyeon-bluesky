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


# Global singleton instance
notifier = MasterNotifier()
