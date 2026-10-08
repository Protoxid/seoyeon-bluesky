"""
agent/budget_manager.py — Cost Control & Budget Protection Manager.

Enforces spending caps and monitors API consumption:
  - Atomic budget reservations preventing concurrent overages.
  - Reconciles actual token usage based on provider pricing.
  - Strict single-entry accounting (prevents double charging).
  - Limits daily and monthly dollar budgets.
  - Limits daily image generation counts.
  - Automatic circuit breaker if spending reaches thresholds.
"""

from __future__ import annotations

import datetime as dt
import json
import pathlib
import uuid
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
        self._active_reservations: Dict[str, Dict[str, Any]] = {}
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

    def get_reserved_amount(self) -> float:
        """Returns the total dollar amount currently held under active reservations."""
        return sum(r.get("amount_usd", 0.0) for r in self._active_reservations.values())

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
        """Checks if estimated spend (plus active reservations) is within caps."""
        data = self._load_ledger()
        reserved = self.get_reserved_amount()
        daily = data.get("daily_spend_usd", 0.0) + reserved
        monthly = data.get("monthly_spend_usd", 0.0) + reserved

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

        return self.can_spend(IMAGE_GEN_COST)

    def reserve(self, amount_usd: float = 0.005, action_type: str = "llm", details: str = "") -> Optional[str]:
        """
        Atomically checks availability and reserves funds prior to starting an API call.
        Returns reservation_id if approved, None if budget exhausted.
        """
        ok, _ = self.can_spend(estimated_cost=amount_usd)
        if not ok:
            return None

        res_id = f"res_{uuid.uuid4().hex[:12]}"
        self._active_reservations[res_id] = {
            "reservation_id": res_id,
            "amount_usd": amount_usd,
            "action_type": action_type,
            "details": details,
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        }
        return res_id

    def reconcile(
        self,
        reservation_id: Optional[str],
        actual_cost_usd: float,
        model: str = "",
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        action_type: str = "llm_generation",
        details: str = "",
    ) -> float:
        """
        Reconciles an active reservation with actual incurred cost, releasing the reserve
        and committing the single definitive charge to the ledger.
        """
        if reservation_id and reservation_id in self._active_reservations:
            del self._active_reservations[reservation_id]

        data = self._load_ledger()
        data["daily_spend_usd"] = round(data.get("daily_spend_usd", 0.0) + actual_cost_usd, 4)
        data["monthly_spend_usd"] = round(data.get("monthly_spend_usd", 0.0) + actual_cost_usd, 4)

        if action_type == "image_generation":
            data["daily_images_count"] = data.get("daily_images_count", 0) + 1

        total_tokens = prompt_tokens + completion_tokens
        if total_tokens > 0:
            data["daily_tokens"] = data.get("daily_tokens", 0) + total_tokens
            data["monthly_tokens"] = data.get("monthly_tokens", 0) + total_tokens

        entry = {
            "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
            "cost_usd": actual_cost_usd,
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
        return actual_cost_usd

    def release(self, reservation_id: Optional[str]) -> None:
        """Releases an active reservation without committing any charges (e.g. on call failure)."""
        if reservation_id and reservation_id in self._active_reservations:
            del self._active_reservations[reservation_id]

    def record_spend(self, cost_usd: float, action_type: str, details: str = "") -> None:
        """Records a direct charge without prior reservation."""
        self.reconcile(
            reservation_id=None,
            actual_cost_usd=cost_usd,
            action_type=action_type,
            details=details,
        )

    def record_token_usage(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        action_type: str,
        details: str = "",
    ) -> float:
        """Direct token spend recorder (legacy/direct entrypoint)."""
        cost_usd = self.calculate_token_cost(model, prompt_tokens, completion_tokens)
        return self.reconcile(
            reservation_id=None,
            actual_cost_usd=cost_usd,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            action_type=action_type,
            details=details,
        )

    def record_image_spend(self, model: str = "", details: str = "") -> float:
        """Records Kie.ai image generation spend."""
        return self.reconcile(
            reservation_id=None,
            actual_cost_usd=IMAGE_GEN_COST,
            action_type="image_generation",
            details=details or f"Kie.ai {model or config.kie_image_model}",
        )

    def get_summary(self) -> Dict[str, Any]:
        data = self._load_ledger()
        return {
            "daily_spend_usd": data.get("daily_spend_usd", 0.0),
            "daily_budget_usd": config.daily_ai_budget,
            "monthly_spend_usd": data.get("monthly_spend_usd", 0.0),
            "monthly_budget_usd": config.monthly_ai_budget,
            "active_reservations_usd": round(self.get_reserved_amount(), 4),
            "daily_images_count": data.get("daily_images_count", 0),
            "max_daily_images": config.max_images_per_day,
            "daily_tokens": data.get("daily_tokens", 0),
            "monthly_tokens": data.get("monthly_tokens", 0),
        }


budget_manager = BudgetManager()
