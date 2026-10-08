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

# OpenRouter model pricing per 1,000,000 tokens (USD)
# Ref: https://openrouter.ai/models
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    # Anthropic Claude 3.5 / 5.5 Sonnet
    "anthropic/claude-sonnet-5.5": {"input_per_m": 3.00, "output_per_m": 15.00},
    "anthropic/claude-3.5-sonnet": {"input_per_m": 3.00, "output_per_m": 15.00},
    # DeepSeek V3 / V4.1 / Flash
    "deepseek/deepseek-chat": {"input_per_m": 0.14, "output_per_m": 0.28},
    "deepseek-v4.1-flash": {"input_per_m": 0.14, "output_per_m": 0.28},
    "deepseek/deepseek-r1": {"input_per_m": 0.55, "output_per_m": 2.19},
    # Default fallback rate for other LLMs
    "_default": {"input_per_m": 1.00, "output_per_m": 3.00},
}
IMAGE_GEN_COST = 0.045  # Kie.ai GPT Image 2.5 per generation (~$0.045)


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
                "daily_tokens": 0,
                "monthly_tokens": 0,
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
            data["daily_tokens"] = 0

        # Reset monthly spend on new month
        if data.get("current_month") != current_month:
            data["current_month"] = current_month
            data["monthly_spend_usd"] = 0.0
            data["monthly_tokens"] = 0

        return data

    def _save_ledger(self, data: Dict[str, Any]) -> None:
        self.ledger_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def calculate_token_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculates exact dollar cost for token usage according to provider pricing."""
        pricing = MODEL_PRICING.get(model)
        if not pricing:
            for k, p in MODEL_PRICING.items():
                if k != "_default" and (k in model or model in k):
                    pricing = p
                    break
        if not pricing:
            pricing = MODEL_PRICING["_default"]

        cost = (prompt_tokens / 1_000_000.0) * pricing["input_per_m"] + \
               (completion_tokens / 1_000_000.0) * pricing["output_per_m"]
        return round(cost, 6)

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

        # Estimated cost for Kie.ai GPT-Image 2.5 is ~$0.045
        return self.can_spend(IMAGE_GEN_COST)

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

    def record_token_usage(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        action_type: str,
        details: str = "",
    ) -> float:
        """Records exact actual token spend based on provider pricing."""
        cost_usd = self.calculate_token_cost(model, prompt_tokens, completion_tokens)
        data = self._load_ledger()
        data["daily_spend_usd"] = round(data.get("daily_spend_usd", 0.0) + cost_usd, 4)
        data["monthly_spend_usd"] = round(data.get("monthly_spend_usd", 0.0) + cost_usd, 4)

        total_tokens = prompt_tokens + completion_tokens
        data["daily_tokens"] = data.get("daily_tokens", 0) + total_tokens
        data["monthly_tokens"] = data.get("monthly_tokens", 0) + total_tokens

        entry = {
            "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
            "cost_usd": cost_usd,
            "action_type": action_type,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "details": details,
        }
        hist = data.get("history", [])
        hist.append(entry)
        data["history"] = hist[-100:]

        self._save_ledger(data)
        return cost_usd

    def record_image_spend(self, model: str = "", details: str = "") -> float:
        """Records Kie.ai image generation spend."""
        cost_usd = IMAGE_GEN_COST
        self.record_spend(cost_usd, "image_generation", details or f"Kie.ai {model or config.kie_image_model}")
        return cost_usd

    def get_summary(self) -> Dict[str, Any]:
        data = self._load_ledger()
        return {
            "daily_spend_usd": data.get("daily_spend_usd", 0.0),
            "daily_budget_usd": config.daily_ai_budget,
            "monthly_spend_usd": data.get("monthly_spend_usd", 0.0),
            "monthly_budget_usd": config.monthly_ai_budget,
            "daily_images_count": data.get("daily_images_count", 0),
            "max_daily_images": config.max_images_per_day,
            "daily_tokens": data.get("daily_tokens", 0),
            "monthly_tokens": data.get("monthly_tokens", 0),
        }


budget_manager = BudgetManager()

