"""
Unified LLM Provider implementations for LM Studio, Google Gemini, and Anthropic Claude.
"""

from abc import ABC, abstractmethod
import json
import os
from typing import Any, Dict, List, Optional
import httpx

from .config import AgentConfig


class LLMResponse:
    def __init__(
        self,
        content: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        raw: Optional[Any] = None,
    ):
        self.content = content or ""
        self.tool_calls = tool_calls or []
        self.raw = raw

    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0


class BaseProvider(ABC):
    @abstractmethod
    def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        pass


class LMStudioProvider(BaseProvider):
    """Interacts with local LM Studio OpenAI-compatible endpoint."""

    def __init__(self, config: AgentConfig):
        self.base_url = config.lm_studio_url.rstrip("/")
        self.model = config.local_model
        self.timeout = 120.0

    def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()

        choice = data["choices"][0]
        msg = choice.get("message", {})
        content = msg.get("content") or ""

        tool_calls = []
        if "tool_calls" in msg and msg["tool_calls"]:
            for tc in msg["tool_calls"]:
                fn = tc.get("function", {})
                args = fn.get("arguments", "{}")
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {"raw": args}
                tool_calls.append({
                    "id": tc.get("id", "call_1"),
                    "name": fn.get("name"),
                    "arguments": args,
                })

        return LLMResponse(content=content, tool_calls=tool_calls, raw=data)


class GeminiProvider(BaseProvider):
    """Interacts with Google Gemini (3.8 Flash / 3.1 Pro)."""

    def __init__(self, config: AgentConfig, model_name: Optional[str] = None):
        self.api_key = config.gemini_api_key
        self.model_name = model_name or config.gemini_flash_model
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set.")

    def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        # Try google-genai SDK first
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)

            # Format history into prompt/contents
            prompt_parts = []
            for m in messages:
                role = m.get("role", "user")
                content = m.get("content", "")
                prompt_parts.append(f"[{role.upper()}]:\n{content}")
            full_prompt = "\n\n".join(prompt_parts)

            config = types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )

            res = client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
                config=config,
            )
            return LLMResponse(content=res.text or "")
        except Exception as e:
            # Direct HTTP REST fallback
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
            contents = []
            for m in messages:
                role = "user" if m.get("role") in ["user", "system"] else "model"
                contents.append({"role": role, "parts": [{"text": m.get("content", "")}]})

            body = {
                "contents": contents,
                "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
            }
            with httpx.Client(timeout=60.0) as client:
                r = client.post(url, json=body)
                r.raise_for_status()
                data = r.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return LLMResponse(content=text, raw=data)


class ClaudeProvider(BaseProvider):
    """Interacts with Anthropic Claude (Claude Opus 5 / Sonnet 5)."""

    def __init__(self, config: AgentConfig, model_name: Optional[str] = None):
        self.api_key = config.anthropic_api_key
        self.model_name = model_name or config.claude_sonnet_model
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set.")

    def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        system_prompt = ""
        user_msgs = []
        for m in messages:
            if m.get("role") == "system":
                system_prompt += m.get("content", "") + "\n"
            else:
                user_msgs.append({"role": m.get("role"), "content": m.get("content")})

        payload = {
            "model": self.model_name,
            "max_tokens": max_tokens,
            "messages": user_msgs,
            "temperature": temperature,
        }
        if system_prompt:
            payload["system"] = system_prompt.strip()

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        with httpx.Client(timeout=90.0) as client:
            resp = client.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        text = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                text += block.get("text", "")

        return LLMResponse(content=text, raw=data)


def create_provider(provider_type: str, config: AgentConfig, model_name: Optional[str] = None) -> BaseProvider:
    """Instantiate the appropriate LLM provider."""
    ptype = provider_type.lower()
    if ptype == "gemini":
        return GeminiProvider(config, model_name)
    elif ptype == "claude":
        return ClaudeProvider(config, model_name)
    elif ptype in ["local", "lmstudio"]:
        return LMStudioProvider(config)
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")
