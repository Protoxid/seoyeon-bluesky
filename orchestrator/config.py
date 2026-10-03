"""
Configuration and model routing for Orchestrator and Operator agents.
"""

from dataclasses import dataclass, field
import os
from typing import Optional
import httpx


@dataclass
class AgentConfig:
    # LM Studio (Local Operator / Fallback Orchestrator)
    lm_studio_url: str = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1")
    local_model: str = os.getenv("LOCAL_MODEL", "qwen2.5-coder-14b-instruct-abliterated")
    local_model_fallback: str = "qwen3.8-27b"
    context_window: int = 32768
    local_temperature: float = 0.2

    # Google Gemini (Cloud Orchestrator)
    gemini_api_key: Optional[str] = field(
        default_factory=lambda: os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    )
    gemini_flash_model: str = os.getenv("GEMINI_FLASH_MODEL", "gemini-3.8-flash")
    gemini_pro_model: str = os.getenv("GEMINI_PRO_MODEL", "gemini-3.1-pro")

    # Anthropic Claude (Cloud Orchestrator / Operator)
    anthropic_api_key: Optional[str] = field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY")
    )
    claude_sonnet_model: str = os.getenv("CLAUDE_SONNET_MODEL", "claude-sonnet-5")
    claude_opus_model: str = os.getenv("CLAUDE_OPUS_MODEL", "claude-opus-5")

    # Routing preferences
    default_orchestrator: str = "auto"  # 'auto', 'gemini', 'claude', 'local'
    default_operator: str = "local"     # 'local', 'claude', 'gemini'

    workspace_root: str = field(
        default_factory=lambda: os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    )

    def check_lm_studio(self, timeout_sec: float = 2.0) -> bool:
        """Check if LM Studio server is running and accessible."""
        try:
            r = httpx.get(f"{self.lm_studio_url}/models", timeout=timeout_sec)
            return r.status_code == 200
        except Exception:
            return False

    def has_gemini(self) -> bool:
        """Check if a potential Gemini API key is configured."""
        k = self.gemini_api_key
        return bool(k and (k.startswith("AIzaSy") or len(k) > 20))

    def has_claude(self) -> bool:
        """Check if an Anthropic API key is configured."""
        k = self.anthropic_api_key
        return bool(k and (k.startswith("sk-ant") or len(k) > 20))

    def resolve_orchestrator_provider(self, override: Optional[str] = None) -> str:
        """Determine which provider will act as the orchestrator."""
        choice = (override or self.default_orchestrator).lower()
        if choice == "gemini":
            if self.has_gemini():
                return "gemini"
            print("[Config] Gemini requested but no valid key found. Falling back.")
        elif choice == "claude":
            if self.has_claude():
                return "claude"
            print("[Config] Claude requested but ANTHROPIC_API_KEY not found. Falling back.")
        elif choice == "local":
            return "local"

        # Auto resolution hierarchy:
        if self.has_claude():
            return "claude"
        if self.has_gemini():
            return "gemini"
        return "local"

    def resolve_operator_provider(self, override: Optional[str] = None) -> str:
        """Determine which provider will act as the operator."""
        choice = (override or self.default_operator).lower()
        if choice == "claude" and self.has_claude():
            return "claude"
        if choice == "gemini" and self.has_gemini():
            return "gemini"
        return "local"
