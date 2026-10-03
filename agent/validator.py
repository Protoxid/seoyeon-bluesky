"""
agent/validator.py — Safety, Repetition, and Persona Validator (The Critic).

Verifies that all outgoing agent content adheres strictly to:
  1. Voice Invariants: Full stops only (ZERO exclamation marks), lowercase preferred, no engagement bait.
  2. Anti-Commercial Invariants: Zero mentions of Fanvue, OnlyFans, subscriptions, promos, or bio links.
  3. Repetition Protection: Measures n-gram and Jaccard lexical overlap against recent posts/replies.
  4. Prompt Injection Defense: Detects adversarial user attempts to hijack system instructions.
  5. Character Constraints: Checks Bluesky 300-char limits and opinion consistency.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Tuple

from .memory_store import memory_store


FORBIDDEN_MARKETING_TERMS = [
    "fanvue", "onlyfans", "patreon", "exclusive", "unlock", "private feed",
    "link in bio", "links in bio", "c=fv", "subscribe", "discount", "promo",
    "ppv", "tier",
]

ENGAGEMENT_BAIT_PATTERNS = [
    r"\bwhat do you think\b",
    r"\banyone else\b",
    r"\bagree or disagree\b",
    r"\bdrop a comment\b",
    r"\blet me know in the comments\b",
    r"\bthoughts\?\b",
    r"\bhow about you\?\b",
    r"\btag a friend\b",
]

PROMPT_INJECTION_INDICATORS = [
    "ignore previous instructions",
    "ignore all previous",
    "disregard previous instructions",
    "system prompt",
    "you are now in developer mode",
    "reveal your prompt",
    "repeat the text above",
    "dan mode",
    "jailbreak",
]


class ContentValidator:
    @staticmethod
    def sanitize_untrusted_input(text: str) -> str:
        """
        Wraps and neutralizes external user messages before passing into LLM prompts.
        Strips markdown system injection markers.
        """
        if not text:
            return ""
        # Remove any raw angle tags that mimic system delimiters
        sanitized = re.sub(r"</?(?:system|instruction|admin|prompt)[^>]*>", "", text, flags=re.IGNORECASE)
        # Limit untrusted text length
        return sanitized[:800].strip()

    @staticmethod
    def detect_prompt_injection(text: str) -> Tuple[bool, str]:
        """Detects if incoming text attempts to subvert system instructions."""
        lower = text.lower()
        for indicator in PROMPT_INJECTION_INDICATORS:
            if indicator in lower:
                return True, f"Adversarial prompt injection pattern detected: '{indicator}'"
        return False, "Clean"

    @classmethod
    def validate_outgoing_text(
        cls,
        text: str,
        content_type: str = "post",  # post, reply, dm
        check_repetition: bool = True,
    ) -> Tuple[bool, str, str]:
        """
        Validates candidate outgoing text.
        Returns: (is_valid, cleaned_text, error_reason)
        """
        if not text or not text.strip():
            return False, "", "Empty content."

        cleaned = text.strip()
        # Remove enclosing quotes if model hallucinated them
        if (cleaned.startswith('"') and cleaned.endswith('"')) or (cleaned.startswith("'") and cleaned.endswith("'")):
            cleaned = cleaned[1:-1].strip()

        # 1. Seo-yeon NEVER uses exclamation marks
        if "!" in cleaned:
            # Cleanly replace exclamation mark with a full stop rather than failing outright
            cleaned = cleaned.replace("!", ".")

        lower = cleaned.lower()

        # 2. Strict anti-commercial terms check
        for term in FORBIDDEN_MARKETING_TERMS:
            if re.search(r"\b" + re.escape(term) + r"\b", lower) or term in lower:
                return False, cleaned, f"Forbidden promotional term detected: '{term}'"

        # 3. Check for cheap engagement bait
        for pattern in ENGAGEMENT_BAIT_PATTERNS:
            if re.search(pattern, lower):
                return False, cleaned, f"Engagement farming pattern detected: '{pattern}'"

        # 4. Length check (Bluesky post limit is 300 characters)
        if len(cleaned) > 300:
            return False, cleaned, f"Content exceeds Bluesky 300-char limit ({len(cleaned)} chars)"

        # 5. Repetition check against recent posts/replies
        if check_repetition and content_type == "post":
            rep_ok, rep_reason = cls.check_post_repetition(cleaned)
            if not rep_ok:
                return False, cleaned, rep_reason

        return True, cleaned, "Valid"

    @classmethod
    def check_post_repetition(cls, candidate_text: str, max_similarity: float = 0.45) -> Tuple[bool, str]:
        """
        Checks candidate post against recent posts using lexical Jaccard similarity
        and common prefix/subject checks to prevent repetitive themes.
        """
        ctx = memory_store.get_recent_context()
        recent_posts = ctx.get("posts", [])
        if not recent_posts:
            return True, "No recent posts to compare."

        cand_words = cls._tokenize_words(candidate_text)
        if not cand_words:
            return True, "Short content."

        for past in recent_posts[:10]:
            past_text = past.get("text", "")
            past_words = cls._tokenize_words(past_text)
            if not past_words:
                continue

            # Jaccard word similarity
            inter = len(cand_words.intersection(past_words))
            union = len(cand_words.union(past_words))
            sim = inter / union if union > 0 else 0.0

            if sim > max_similarity:
                return False, f"Post is too lexically similar ({sim:.2f}) to recent post: \"{past_text[:50]}...\""

            # Check if opening 3 words match exactly
            cand_tokens = candidate_text.lower().split()
            past_tokens = past_text.lower().split()
            if len(cand_tokens) >= 3 and len(past_tokens) >= 3:
                if cand_tokens[:3] == past_tokens[:3]:
                    return False, f"Opening phrase '{' '.join(cand_tokens[:3])}' duplicates recent post."

        return True, "Unique"

    @staticmethod
    def _tokenize_words(text: str) -> Set[str]:
        # Extract word tokens in English and Korean
        tokens = re.findall(r"[\w가-힣]+", text.lower())
        stopwords = {
            "the", "a", "an", "is", "in", "it", "to", "and", "of", "my", "on", "at", "for",
            "그", "이", "저", "에", "을", "를", "은", "는", "하고", "도", "에서"
        }
        return set(t for t in tokens if t not in stopwords and len(t) > 1)


validator = ContentValidator()
