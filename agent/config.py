"""
agent/config.py — Central Configuration & Control Plane for Seo-yeon's Autonomous Agent.

Handles environment variables, feature flags, safety limits, model choices,
and operational parameters for GitHub Actions and local execution.
"""

from __future__ import annotations

import os
import pathlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional


PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE_DIR = PROJECT_ROOT
DATA_DIR = pathlib.Path(os.environ.get("SEOYEON_DATA_DIR", str(PROJECT_ROOT / "data")))
MEMORY_DIR = DATA_DIR / "memory"
LOGS_DIR = DATA_DIR / "logs"


def _load_env_files() -> None:
    """Loads environment variables from .env files if present."""
    if os.environ.get("ENV") == "test" or os.environ.get("SEOYEON_MODE") == "offline":
        return
    for p in [PROJECT_ROOT / ".env", PROJECT_ROOT / "growth" / ".env", pathlib.Path(".env")]:
        if p.exists() and p.is_file():
            try:
                for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k, v = k.strip(), v.strip().strip("'\"")
                        if k and k not in os.environ:
                            os.environ[k] = v
            except Exception:
                pass


_load_env_files()


def _get_bool(key: str, default: bool) -> bool:
    val = os.environ.get(key)
    if val is None:
        return default
    return val.strip().lower() in ("true", "1", "yes", "on")


def _get_int(key: str, default: int) -> int:
    val = os.environ.get(key)
    if val is None:
        return default
    try:
        return int(val.strip())
    except ValueError:
        return default


def _get_float(key: str, default: float) -> float:
    val = os.environ.get(key)
    if val is None:
        return default
    try:
        return float(val.strip())
    except ValueError:
        return default


@dataclass
class AgentConfig:
    # --- Master Switches ---
    autonomous_mode: bool = field(default_factory=lambda: _get_bool("AUTONOMOUS_MODE", True))
    emergency_stop: bool = field(default_factory=lambda: _get_bool("EMERGENCY_STOP", False))
    dry_run: bool = field(default_factory=lambda: _get_bool("DRY_RUN", False))

    # --- Permitted Action Flags ---
    allow_posts: bool = field(default_factory=lambda: _get_bool("ALLOW_POSTS", True))
    allow_replies: bool = field(default_factory=lambda: _get_bool("ALLOW_REPLIES", True))
    allow_likes: bool = field(default_factory=lambda: _get_bool("ALLOW_LIKES", True))
    allow_dms: bool = field(default_factory=lambda: _get_bool("ALLOW_DMS", True))
    allow_images: bool = field(default_factory=lambda: _get_bool("ALLOW_IMAGES", True))

    # --- Activity & Cadence Limits ---
    max_posts_per_day: int = field(default_factory=lambda: _get_int("MAX_POSTS_PER_DAY", 3))
    max_replies_per_day: int = field(default_factory=lambda: _get_int("MAX_REPLIES_PER_DAY", 12))
    max_likes_per_day: int = field(default_factory=lambda: _get_int("MAX_LIKES_PER_DAY", 25))
    max_dms_per_day: int = field(default_factory=lambda: _get_int("MAX_DMS_PER_DAY", 15))
    max_images_per_day: int = field(default_factory=lambda: _get_int("MAX_IMAGES_PER_DAY", 1))
    max_actions_per_tick: int = field(default_factory=lambda: _get_int("MAX_ACTIONS_PER_TICK", 2))

    # --- Budget & Safety Controls ---
    daily_ai_budget: float = field(default_factory=lambda: _get_float("DAILY_AI_BUDGET", 2.00))  # in USD
    monthly_ai_budget: float = field(default_factory=lambda: _get_float("MONTHLY_AI_BUDGET", 30.00))

    # --- Model Configuration ---
    # Text generation runs EXCLUSIVELY via OpenRouter API
    # Top frontier model for nuanced, intelligent persona writing and cognitive reasoning
    primary_text_model: str = field(
        default_factory=lambda: os.environ.get("PRIMARY_TEXT_MODEL", "anthropic/claude-sonnet-5.5")
    )
    # OpenRouter API Endpoint (supports https://openrouter.ai/api/v1 or https://eu.openrouter.ai/api/v1)
    openrouter_base_url: str = field(
        default_factory=lambda: os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    )
    # Secondary resilient fallback on OpenRouter
    fallback_text_model: str = field(
        default_factory=lambda: os.environ.get("FALLBACK_TEXT_MODEL", "deepseek-v4.1-flash")
    )
    # Image generator model via Kie.ai API (gpt-image-2.5-sunburst i2i)
    kie_image_model: str = field(
        default_factory=lambda: os.environ.get("KIE_IMAGE_MODEL", "gpt-image-2-5-sunburst-image-to-image")
    )
    kie_pov_model: str = field(default_factory=lambda: os.environ.get(
        "KIE_POV_MODEL", "gpt-image-2-5-sunburst-text-to-image"))
    kie_resolution: str = field(default_factory=lambda: os.environ.get("KIE_RESOLUTION", "1K"))
    action_threshold: float = field(default_factory=lambda: _get_float("ACTION_THRESHOLD", 0.50))
    enable_continuity: bool = field(default_factory=lambda: _get_bool("ENABLE_CONTINUITY", True))
    vision_model: str = field(default_factory=lambda: os.environ.get("VISION_MODEL", "anthropic/claude-sonnet-5.5"))

    # --- Bluesky Credentials ---
    bsky_handle: str = field(
        default_factory=lambda: os.environ.get("BSKY_HANDLE", "syeonhn.bsky.social")
    )
    bsky_app_password: str = field(
        default_factory=lambda: os.environ.get("BSKY_APP_PASSWORD", "")
    )
    bsky_xrpc_base: str = "https://bsky.social/xrpc"
    bsky_chat_base: str = "https://api.bsky.chat/xrpc"

    # --- Discovery & Engagement Topics ---
    canon_search_topics: List[str] = field(
        default_factory=lambda: [
            "성수동",
            "뚝섬",
            "서울숲",
            "독립영화",
            "헌책",
            "한글 타이포그래피",
            "서울 건축",
            "2호선",
            "seongsu",
            "translated literature",
            "independent cinema",
            "graphic design",
        ]
    )

    # --- Outbound Master Communication (Telegram) ---
    # If Seo-yeon needs guidance, approval, or unknown facts, she sends a Telegram message
    telegram_bot_token: Optional[str] = field(
        default_factory=lambda: os.environ.get("TELEGRAM_BOT_TOKEN")
    )
    telegram_chat_id: str = field(
        default_factory=lambda: os.environ.get("TELEGRAM_CHAT_ID", "")
    )
    master_telegram_handle: str = field(
        default_factory=lambda: os.environ.get("MASTER_TELEGRAM_HANDLE", "my master")
    )
    master_designations: List[str] = field(
        default_factory=lambda: ["my master", "my human"]
    )

    # --- API Keys ---
    kie_api_key: Optional[str] = field(
        default_factory=lambda: os.environ.get("KIE_API_KEY") or (
            (PROJECT_ROOT / "personas" / "seoyeon" / "kie_key.txt").read_text(encoding="utf-8").strip()
            if os.environ.get("ENV") != "test" and os.environ.get("SEOYEON_MODE") != "offline" and (PROJECT_ROOT / "personas" / "seoyeon" / "kie_key.txt").exists() else None
        )
    )
    openrouter_api_key: Optional[str] = field(
        default_factory=lambda: os.environ.get("OPENROUTER_API_KEY")
    )

    def is_operational(self) -> tuple[bool, str]:
        """Checks if the agent can run."""
        if self.emergency_stop:
            return False, "EMERGENCY_STOP is active. All outbound agent activities are disabled."
        if not self.autonomous_mode:
            return False, "AUTONOMOUS_MODE is disabled."
        if os.environ.get("ENV") == "test":
            return True, "Operational (test mode)"
        if not self.bsky_handle or not self.bsky_app_password:
            return False, "Bluesky credentials (BSKY_HANDLE / BSKY_APP_PASSWORD) are not set."
        return True, "Operational"


# Global singleton instance
config = AgentConfig()
