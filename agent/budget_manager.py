"""
agent/budget_manager.py — Cost Control & Budget Protection Manager.

Enforces spending caps and monitors API consumption:
  - Tracks LLM tokens and estimated costs.
  - Limits daily and monthly dollar budgets.
  - Limits daily image generation counts.
  - Automatically trips an emergency circuit breaker if spending exceeds limits.
"""

from __future__ import annotations

import datetime as dt
import json
import pathlib
from typing import Any, Dict, Optional, Tuple

from .config import DATA_DIR, config

BUDGET_LEDGER_FILE = DATA_DIR / "budget_ledger.json"


class BudgetManager:
    def __init__(self, ledger_file: pathlib.Path = BUDGET_LEDGER_FILE):
        self.ledger_file = ledger_file
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._ensure_ledger()

    def _get_seoul_date_str(self) -> str:
        """Returns the current date in Seoul (KST = UTC+9)."""
        utc_now = dt.datetime.now(dt.timezone.utc)
        kst_tz = dt.timezone(dt.timedelta(hours=9))
        return utc_now.astimezone(kst_tz).date().isoformat()

    def _ensure_ledger(self) -> None:
        if not self.ledger_file.exists():
            today_str = self._get_seoul_date_str()
            initial_data = {
                "current_day": today_str,
                "current_month": today_str[:7],
                "daily_spend_usd": 0.0,
                "monthly_spend_usd": 0.0,
                "daily_images_count": 0,
                "history": [],
            }
            self.ledger_file.write_text(json.dumps(initial_data, indent=2), encoding="utf-8")

    def _load_ledger(self) -> Dict[str, Any]:
        self._ensure_ledger()
        try:
            data = json.loads(self.ledger_file.read_text(encoding="utf-8"))
        except Exception:
            data = {}

        today_str = self._get_seoul_date_str()
        current_month = today_str[:7]

        # Reset daily spend on new Seoul day
        if data.get("current_day") != today_str:
            data["current_day"] = today_str
            data["daily_spend_usd"] = 0.0
            data["daily_images_count"] = 0

        # Reset monthly spend on new month
        if data.get("current_month") != current_month:
            data["current_month"] = current_month
            data["monthly_spend_usd"] = 0.0

        return data

    def _save_ledger(self, data: Dict[str, Any]) -> None:
        self.ledger_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def can_spend(self, estimated_cost: float = 0.005) -> Tuple[bool, str]:
        """Checks if estimated spend is within daily and monthly caps."""
        data = self._load_ledger()
        daily = data.get("daily_spend_usd", 0.0)
        monthly = data.get("monthly_spend_usd", 0.0)

        if daily + estimated_cost > config.daily_ai_budget:
            return False, f"Daily budget reached (${daily:.3f} / ${config.daily_ai_budget:.2f})"

        if monthly + estimated_cost > config.monthly_ai_budget:
            return False, f"Monthly budget reached (${monthly:.3f} / ${config.monthly_ai_budget:.2f})"

        return True, "Within budget limits"

    def can_generate_image(self) -> Tuple[bool, str]:
        """Checks if an image generation is permitted today."""
        if not config.allow_images:
            return False, "Image generation disabled via ALLOW_IMAGES=false."

        data = self._load_ledger()
        img_count = data.get("daily_images_count", 0)
        if img_count >= config.max_images_per_day:
            return False, f"Daily image limit reached ({img_count}/{config.max_images_per_day})."

        # Estimated cost for GPT-Image 2.5 / DALL-E image is ~$0.04
        return self.can_spend(0.045)

    def record_spend(self, cost_usd: float, action_type: str, details: str = "") -> None:
        data = self._load_ledger()
        data["daily_spend_usd"] = round(data.get("daily_spend_usd", 0.0) + cost_usd, 4)
        data["monthly_spend_usd"] = round(data.get("monthly_spend_usd", 0.0) + cost_usd, 4)

        if action_type == "image_generation":
            data["daily_images_count"] = data.get("daily_images_count", 0) + 1

        entry = {
            "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
            "cost_usd": cost_usd,
            "action_type": action_type,
            "details": details,
        }
        hist = data.get("history", [])
        hist.append(entry)
        data["history"] = hist[-100:]  # Keep last 100 entries

        self._save_ledger(data)

    def get_summary(self) -> Dict[str, Any]:
        data = self._load_ledger()
        return {
            "daily_spend_usd": data.get("daily_spend_usd", 0.0),
            "daily_budget_usd": config.daily_ai_budget,
            "monthly_spend_usd": data.get("monthly_spend_usd", 0.0),
            "monthly_budget_usd": config.monthly_ai_budget,
            "daily_images_count": data.get("daily_images_count", 0),
            "max_daily_images": config.max_images_per_day,
        }


budget_manager = BudgetManager()
