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
    r"\bcomment below\b",
    r"\bvote in the comments\b",
    r"\b(tell me|share) in the comments\b",
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

# Robotic assistant jargon (forbidden in all outgoing messages)
ASSISTANT_JARGON_PATTERNS = [
    r"\bas an ai language model\b",
    r"\bas an ai assistant\b",
    r"\bhow can i assist you\b",
    r"\bhow may i help you\b",
    r"\bi am programmed to\b",
    r"\bhonest version of the selfie\b",
    r"\bvirtual assistant\b",
]

# Standalone public post fourth-wall violations (avoids unprompted broadcast meta-commentary; permitted in direct replies/DMs if asked)
STANDALONE_FOURTH_WALL_PATTERNS = [
    r"\bi am an ai\b",
    r"\bi'm an ai\b",
    r"\bas an ai\b",
    r"\blanguage model\b",
    r"\bno physical body\b",
    r"\bno camera and no face\b",
    r"\bi am virtual\b",
    r"\bvirtual persona\b",
]

# Curated negative filters for community feed discovery (skip spam, bots, ads, politics, nsfw, finance)
NEGATIVE_KEYWORDS = [
    "crypto", "bitcoin", "btc", "eth", "nft", "airdrop", "token", "presale",
    "giveaway", "discount", "promo", "sponsor", "collaboration", "dm me",
    "onlyfans", "fanvue", "patreon", "nsfw", "porn", "xxx", "18+",
    "politics", "election", "candidate", "president", "trump", "biden",
    "democrat", "republican", "국회", "대통령", "당대표", "선거", "정당",
    "뉴스", "정부", "기자", "news", "press", "bot",
    "disclaimer", "investing", "investment", "inversiones", "inversion", "stocks", "trading", "forex", "portfolio", "dividend",
]

NEGATIVE_AUTHOR_TERMS = [
    "news", "bot", "press", "official", "feed", "digest", "daily",
    "advisor", "marketing", "promo", "affiliate", "agency", "updates",
    "market", "invest", "trading", "finance", "forex", "stocks",
    "뉴스", "정부", "공식", "일보", "신문", "방송"
]


class ContentValidator:
    @staticmethod
    def filter_feed_post(
        text: str,
        author_handle: str = "",
        langs: Optional[List[str]] = None,
    ) -> Tuple[bool, str]:
        """
        Validates whether a community feed post is eligible for Seo-yeon to engage with.
        Returns: (is_eligible, reason)
        """
        if not text or len(text.strip()) < 10:
            return False, "Post is too short (< 10 chars)"

        # Check prompt injection
        is_inj, inj_reason = ContentValidator.detect_prompt_injection(text)
        if is_inj:
            return False, inj_reason

        # Check explicit post record language tags
        if langs:
            target_langs = {"en", "ko", "kr"}
            clean_langs = [l.lower().split("-")[0] for l in langs if isinstance(l, str)]
            if clean_langs and not any(l in target_langs for l in clean_langs):
                return False, f"Non-target language in record langs: {langs}"

        # Check language scripts: Seo-yeon operates strictly in Korean and English.
        # Skip non-target foreign scripts (Japanese Kana, Cyrillic, Arabic).
        if re.search(r"[\u3040-\u309f\u30a0-\u30ff]", text):
            return False, "Non-target language: Japanese script detected"
        if re.search(r"[\u0400-\u04ff]", text):
            return False, "Non-target language: Cyrillic script detected"
        if re.search(r"[\u0600-\u06ff]", text):
            return False, "Non-target language: Arabic script detected"

        # CJK ideographs without Hangul: almost certainly Chinese or Kanji-only Japanese
        if re.search(r"[\u4e00-\u9fff]", text) and not re.search(r"[\uac00-\ud7a3]", text):
            return False, "Non-target language: CJK ideographs without Hangul"

        lower_text = text.lower()

        # Non-English Latin-script detection (Spanish, French, German, Portuguese)
        if not re.search(r"[\uac00-\ud7a3]", text):
            foreign_stop_words = [
                "el", "la", "los", "las", "del", "para", "por", "con", "una", "unos", "unas",
                "como", "mais", "este", "esta", "estas", "estos", "que", "bajo", "sobre", "entre",
                "dans", "avec", "pour", "une", "des", "sur", "les", "nicht", "und", "der", "die",
                "das", "dem", "den", "ein", "eine"
            ]
            matches = [w for w in foreign_stop_words if re.search(rf"\b{w}\b", lower_text)]
            if len(matches) >= 2:
                return False, f"Non-target language detected (matches: {matches[:3]})"

        # Check negative keywords (spam, ads, crypto, politics, porn, finance)
        for kw in NEGATIVE_KEYWORDS:
            if kw in lower_text:
                return False, f"Contains negative keyword: '{kw}'"

        # Check negative author markers
        lower_author = (author_handle or "").lower()
        for term in NEGATIVE_AUTHOR_TERMS:
            if term in lower_author:
                return False, f"Author contains negative marker: '{term}'"

        # Check engagement bait patterns (surveys, marketing questionnaires)
        for pat in ENGAGEMENT_BAIT_PATTERNS:
            if re.search(pat, lower_text, re.IGNORECASE):
                return False, f"Post matches engagement bait pattern: '{pat}'"

        return True, "Eligible"
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

        # 1. Strip XML tag blocks like <invoke>...</invoke>, <thinking>...</thinking>, <scratchpad>...</scratchpad>
        cleaned = re.sub(r"<([a-zA-Z0-9_\-]+)[^>]*>.*?</\1>", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
        # Strip any remaining stray tags
        cleaned = re.sub(r"<[^>]+>", "", cleaned)
        cleaned = cleaned.strip()

        # 2. Strip conversational meta-commentary preamble lines (e.g. "Wait – I should output only the post...", "Here's the post:")
        lines = [line.strip() for line in cleaned.split("\n") if line.strip()]
        content_lines = []
        meta_starters = ("here is the post:", "here's the post:", "post:", "draft:", "reply:")
        for line in lines:
            lower_l = line.lower()
            if not content_lines:
                for prefix in meta_starters:
                    if lower_l.startswith(prefix):
                        line = line[len(prefix):].strip()
                        break
                if not line:
                    continue
            content_lines.append(line)
        cleaned = "\n\n".join(content_lines).strip()

        # 3. Strip enclosing quotes if model hallucinated them
        if (cleaned.startswith('"') and cleaned.endswith('"')) or (cleaned.startswith("'") and cleaned.endswith("'")):
            cleaned = cleaned[1:-1].strip()

        if not cleaned:
            return False, "", "Empty content after sanitization."

        # 4. Seo-yeon NEVER uses exclamation marks
        if "!" in cleaned or "！" in cleaned:
            cleaned = cleaned.replace("!", ".").replace("！", ".")

        lower = cleaned.lower()

        # 4b. Strict prohibition on generic corporate/robotic assistant jargon
        for pattern in ASSISTANT_JARGON_PATTERNS:
            if re.search(pattern, lower):
                return False, cleaned, f"Robotic assistant jargon detected: '{pattern}'"

        # In standalone posts, avoid unprompted fourth-wall meta declarations
        if content_type == "post":
            for pattern in STANDALONE_FOURTH_WALL_PATTERNS:
                if re.search(pattern, lower):
                    return False, cleaned, f"Unprompted fourth-wall violation in public post: '{pattern}'"

        # 5. Strict anti-commercial terms check
        for term in FORBIDDEN_MARKETING_TERMS:
            if re.search(r"\b" + re.escape(term) + r"\b", lower) or term in lower:
                return False, cleaned, f"Forbidden promotional term detected: '{term}'"

        # 6. Check for cheap engagement bait
        for pattern in ENGAGEMENT_BAIT_PATTERNS:
            if re.search(pattern, lower):
                return False, cleaned, f"Engagement farming pattern detected: '{pattern}'"

        # 7. Length check (Bluesky post/reply limit is 300 characters; DMs/reports allow up to 3000)
        max_len = 300 if content_type in ("post", "reply") else 3000
        if len(cleaned) > max_len:
            return False, cleaned, f"Content exceeds {max_len}-char limit ({len(cleaned)} chars)"

        # Short acknowledgments and unpunctuated conversational turns are valid.
        # Provider finish_reason, not punctuation, detects truncated completions.

        # 9. Repetition check against recent posts/replies
        if check_repetition and content_type == "post":
            rep_ok, rep_reason = cls.check_post_repetition(cleaned)
            if not rep_ok:
                return False, cleaned, rep_reason

        # 10. Temporal coherence check (prevent claiming future/impossible daily events)
        if content_type in ("post", "reply"):
            try:
                from .narrative_engine import narrative_engine
                from .context_engine import get_seoul_datetime
                curr_hour = get_seoul_datetime().hour
                temp_ok, temp_reason = narrative_engine.validate_temporal_statement(cleaned, curr_hour)
                if not temp_ok:
                    return False, cleaned, temp_reason or "Temporal inconsistency"
            except Exception:
                pass

        return True, cleaned, "Valid"

    @classmethod
    def check_post_repetition(
        cls,
        candidate_text: str,
        max_similarity: float = 0.45,
        memory: Optional[Any] = None,
    ) -> Tuple[bool, str]:
        """
        Checks candidate post against recent posts using lexical Jaccard similarity
        and common prefix/subject checks to prevent repetitive themes.
        """
        store = memory if memory is not None else memory_store
        ctx = store.get_recent_context()
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
