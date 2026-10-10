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
import math
import pathlib
import uuid
from typing import Any, Dict, Optional, Tuple

from .config import DATA_DIR, config
from .storage import write_json, serialized

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

    @serialized("ledger_file")
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
                "active_reservations": {},
                "history": [],
            }
            write_json(self.ledger_file, initial_data)

    @serialized("ledger_file")
    def _load_ledger(self) -> Dict[str, Any]:
        self._ensure_ledger()
        try:
            data = json.loads(self.ledger_file.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            raise RuntimeError("Budget ledger unreadable; spending blocked") from exc

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

        if "active_reservations" not in data or not isinstance(data["active_reservations"], dict):
            data["active_reservations"] = {}

        # Expire stale reservations (> 15 mins old) from interrupted or crashed runner executions
        now_utc = dt.datetime.now(dt.timezone.utc)
        stale_cutoff = now_utc - dt.timedelta(minutes=15)
        active_res = data["active_reservations"]
        expired_keys = []
        for res_id, res_info in list(active_res.items()):
            ts_str = res_info.get("timestamp")
            if ts_str:
                try:
                    ts = dt.datetime.fromisoformat(ts_str)
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=dt.timezone.utc)
                    if ts < stale_cutoff and res_info.get("status") == "held":
                        expired_keys.append(res_id)
                except Exception:
                    expired_keys.append(res_id)

        if expired_keys:
            for k in expired_keys:
                print(f"[BudgetManager] Expiring stale reservation {k} from prior interrupted execution.")
                del active_res[k]
            self._save_ledger(data)

        return data

    def _save_ledger(self, data: Dict[str, Any]) -> None:
        write_json(self.ledger_file, data)

    def get_reserved_amount(self) -> float:
        """Returns the total dollar amount currently held under active reservations."""
        data = self._load_ledger()
        return sum(r.get("amount_usd", 0.0) for r in data.get("active_reservations", {}).values())

    def get_active_reservations(self) -> Dict[str, Any]:
        """Returns the dictionary of currently active reservations."""
        data = self._load_ledger()
        return data.get("active_reservations", {})

    def _get_model_pricing(self, model: str) -> Dict[str, float]:
        pricing = MODEL_PRICING.get(model)
        if not pricing:
            for k, p in MODEL_PRICING.items():
                if k != "_default" and (k in model or model in k):
                    return p
            return MODEL_PRICING["_default"]
        return pricing

    def calculate_token_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculates exact dollar cost for token usage according to provider pricing."""
        pricing = self._get_model_pricing(model)
        cost = (prompt_tokens / 1_000_000.0) * pricing["input_per_m"] + \
               (completion_tokens / 1_000_000.0) * pricing["output_per_m"]
        return round(cost, 6)

    def estimate_max_cost(
        self,
        model: str,
        prompt_text: str = "",
        max_tokens: int = 150,
        is_reasoning: bool = True,
    ) -> float:
        """
        Estimates upper-bound dollar cost of an LLM request before execution,
        accounting for prompt tokens, maximum completion tokens, reasoning tokens,
        and a 25% uncertainty margin.
        """
        pricing = self._get_model_pricing(model)
        # Approximate 3.5 chars per token for mixed Korean/English prompts
        approx_prompt_tokens = max(50, len(prompt_text.encode("utf-8"))) if prompt_text else 350

        # Enforce reasoning token headroom for models like Claude Sonnet 5.5
        effective_output_tokens = max(max_tokens, 700) if is_reasoning else max_tokens

        raw_estimate = (approx_prompt_tokens / 1_000_000.0) * pricing["input_per_m"] + \
                       (effective_output_tokens / 1_000_000.0) * pricing["output_per_m"]

        conservative_estimate = raw_estimate * 1.25
        return round(max(0.002, conservative_estimate), 6)

    @serialized("ledger_file")
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

    @serialized("ledger_file")
    def can_generate_image(self) -> Tuple[bool, str]:
        """Checks if an image generation is permitted today."""
        if not config.allow_images:
            return False, "Image generation disabled via ALLOW_IMAGES=false."

        data = self._load_ledger()
        img_count = data.get("daily_images_count", 0)
        if img_count >= config.max_images_per_day:
            return False, f"Daily image limit reached ({img_count}/{config.max_images_per_day})."

        return self.can_spend(IMAGE_GEN_COST)

    @serialized("ledger_file")
    def reserve(
        self,
        amount_usd: float = 0.005,
        action_type: str = "llm",
        details: str = "",
        provider: str = "openrouter",
        model: str = "",
    ) -> Optional[str]:
        """
        Atomically checks availability and durably records reservation in the ledger
        prior to starting an API call. Survives runner restarts.
        Returns reservation_id if approved, None if budget exhausted.
        """
        if not math.isfinite(amount_usd) or amount_usd < 0:
            raise ValueError("Negative reservation")
        data = self._load_ledger()
        reserved = self.get_reserved_amount()
        daily = data.get("daily_spend_usd", 0.0) + reserved
        monthly = data.get("monthly_spend_usd", 0.0) + reserved
        if action_type == "image_generation":
            pending = sum(r.get("action_type") == "image_generation" for r in data["active_reservations"].values())
            if data.get("daily_images_count", 0) + pending >= config.max_images_per_day:
                return None

        if daily + amount_usd > config.daily_ai_budget:
            return None
        if monthly + amount_usd > config.monthly_ai_budget:
            return None

        res_id = f"res_{uuid.uuid4().hex[:12]}"
        reservation_record = {
            "reservation_id": res_id,
            "amount_usd": round(amount_usd, 6),
            "action_type": action_type,
            "provider": provider,
            "model": model,
            "details": details,
            "status": "held",
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        }

        if "active_reservations" not in data:
            data["active_reservations"] = {}
        data["active_reservations"][res_id] = reservation_record
        self._save_ledger(data)
        return res_id

    @serialized("ledger_file")
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
        if not math.isfinite(actual_cost_usd) or actual_cost_usd < 0:
            raise ValueError("Negative charge")
        data = self._load_ledger()
        if reservation_id in data.get("reconciled_ids", []):
            return 0.0
        if reservation_id:
            data.setdefault("reconciled_ids", []).append(reservation_id)
        if reservation_id and "active_reservations" in data and reservation_id in data["active_reservations"]:
            del data["active_reservations"][reservation_id]

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

    @serialized("ledger_file")
    def release(self, reservation_id: Optional[str]) -> None:
        """Releases an active reservation without committing any charges (e.g. on call failure)."""
        if not reservation_id:
            return
        data = self._load_ledger()
        if "active_reservations" in data and reservation_id in data["active_reservations"]:
            del data["active_reservations"][reservation_id]
            self._save_ledger(data)

    @serialized("ledger_file")
    def mark_submitted(self, reservation_id, request_id=""):
        data = self._load_ledger()
        if reservation_id in data["active_reservations"]:
            data["active_reservations"][reservation_id].update(status="submitted", request_id=request_id)
            self._save_ledger(data)
            import os
            if os.environ.get("SEOYEON_GIT_CHECKPOINT") == "1":
                from .delivery import checkpoint
                checkpoint()

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
