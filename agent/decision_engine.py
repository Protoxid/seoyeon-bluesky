"""
agent/decision_engine.py — Cognitive Decision Engine for Autonomous Action Selection.

Implements the full Observe-Context-Recall-Evaluate-Decide loop:
  - Treats NO_ACTION as a first-class, common, and valid natural outcome.
  - Weights actions contextually by Seoul circadian rhythm, recency, and stimulus quality.
  - Scores options with desirability and confidence metrics.
  - Protects against bot-like hyperactivity, honoring human restraint.
"""

from __future__ import annotations

import datetime as dt
import enum
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .config import config
from .context_engine import EnvironmentContext
from .memory_store import UserProfile, memory_store
from .validator import ContentValidator


class ActionType(enum.Enum):
    NO_ACTION = "NO_ACTION"
    REPLY_COMMENT = "REPLY_COMMENT"
    ANSWER_MENTION = "ANSWER_MENTION"
    ANSWER_DM = "ANSWER_DM"
    BROWSE_AND_LIKE = "BROWSE_AND_LIKE"
    BROWSE_AND_REPLY = "BROWSE_AND_REPLY"
    QUOTE_POST = "QUOTE_POST"
    REPOST = "REPOST"
    FOLLOW = "FOLLOW"
    PUBLISH_TEXT_POST = "PUBLISH_TEXT_POST"
    PUBLISH_IMAGE_POST = "PUBLISH_IMAGE_POST"


@dataclass
class ActionCandidate:
    action: ActionType
    score: float  # [0.0, 1.0] desirability * confidence
    confidence: float
    reason: str
    target_data: Dict[str, Any] = field(default_factory=dict)
    intent: str = ""


@dataclass
class DecisionOutcome:
    selected_action: ActionType
    reason: str
    target_data: Dict[str, Any]
    intent: str
    candidate_scores: Dict[str, float]
    all_candidates: List[ActionCandidate]


class DecisionEngine:
    def evaluate(
        self,
        context: EnvironmentContext,
        notifications: List[Dict[str, Any]],
        dms: List[Dict[str, Any]],
        feed_items: List[Dict[str, Any]],
        can_image: bool = True,
    ) -> DecisionOutcome:
        """Evaluates current sensory inputs and decides the most natural action."""
        candidates: List[ActionCandidate] = []

        # -------------------------------------------------------------
        # 1. Baseline: NO_ACTION (Restraint is human)
        # -------------------------------------------------------------
        base_no_action_score = 0.40
        # If it's deep night (01:00 - 05:00 KST), bias heavily toward resting
        if context.circadian_phase == "deep_night":
            base_no_action_score = 0.88
        elif context.hours_since_last_action < 1.0:
            # Acted very recently, high likelihood of quiet browsing or resting
            base_no_action_score = 0.65

        candidates.append(
            ActionCandidate(
                action=ActionType.NO_ACTION,
                score=base_no_action_score,
                confidence=0.85,
                reason=f"Resting or quiet offline moment (circadian: {context.circadian_phase}, last action {context.hours_since_last_action:.1f}h ago).",
            )
        )

        # -------------------------------------------------------------
        # 2. Inbound Direct Messages (DMs)
        # -------------------------------------------------------------
        if config.allow_dms and dms:
            for dm in dms:
                convo_id = dm.get("id")
                unread = dm.get("unreadCount", 0)
                if unread > 0 and convo_id:
                    members = dm.get("members", [])
                    my_handle = (config.bsky_handle or "").lower().lstrip("@")
                    try:
                        from .bsky_client import bsky_client
                        my_did = bsky_client.did
                    except Exception:
                        my_did = ""

                    other_member = next(
                        (
                            m for m in members
                            if (m.get("handle") or "").lower().lstrip("@") != my_handle
                            and (not my_did or m.get("did") != my_did)
                        ),
                        {}
                    )
                    handle = other_member.get("handle", "user")
                    profile = memory_store.get_user_profile(handle)

                    # Deduplication: check last message in thread
                    last_msg = dm.get("lastMessage", {})
                    last_msg_id = last_msg.get("id", "")
                    last_sender_did = last_msg.get("sender", {}).get("did", "")
                    if my_did and last_sender_did == my_did:
                        # Seo-yeon sent the last message; do not reply to self
                        continue
                    if last_msg_id and memory_store.has_replied_to_dm(last_msg_id):
                        # Message was already answered
                        continue

                    # Relationship weighting
                    dm_score = 0.70 if profile.relationship in ("regular", "friendly_acquaintance") else 0.55
                    candidates.append(
                        ActionCandidate(
                            action=ActionType.ANSWER_DM,
                            score=dm_score,
                            confidence=0.80,
                            reason=f"Unread private message from @{handle} ({profile.relationship}).",
                            target_data={
                                "convo_id": convo_id,
                                "handle": handle,
                                "profile": profile,
                                "last_message_id": last_msg_id,
                            },
                            intent="warm_personal_reply",
                        )
                    )
                    break  # Only consider top unread DM per tick

        # -------------------------------------------------------------
        # 3. Notifications (Replies & Mentions)
        # -------------------------------------------------------------
        if config.allow_replies and notifications and context.circadian_phase != "deep_night":
            valid_notif_candidates: List[ActionCandidate] = []
            for notif in notifications[:20]:
                reason = notif.get("reason")
                if reason not in ("reply", "mention"):
                    continue

                notif_uri = notif.get("uri", "")
                if notif_uri:
                    if memory_store.has_replied_to_notification(notif_uri) or memory_store.has_replied_to_post(notif_uri):
                        continue

                author = notif.get("author", {})
                author_handle = (author.get("handle") or "").lower().lstrip("@")
                my_handle = (config.bsky_handle or "").lower().lstrip("@")
                if author_handle == my_handle:
                    continue

                record = notif.get("record", {})
                user_text = record.get("text", "")
                if not user_text.strip():
                    continue

                # Safety: check for prompt injection
                is_inj, _ = ContentValidator.detect_prompt_injection(user_text)
                if is_inj:
                    continue

                profile = memory_store.get_user_profile(author.get("handle", ""))

                if reason == "reply":
                    # Comment under her post
                    action_type = ActionType.REPLY_COMMENT
                    score = 0.70 if profile.relationship != "stranger" else 0.58
                    intent = "acknowledge_and_converse"
                else:
                    # Tagged in a post or mention
                    action_type = ActionType.ANSWER_MENTION
                    score = 0.58
                    intent = "evaluate_mention_and_react"

                # Check if she replied too many times today
                if context.replies_today >= config.max_replies_per_day:
                    score = 0.10

                valid_notif_candidates.append(
                    ActionCandidate(
                        action=action_type,
                        score=score,
                        confidence=0.75,
                        reason=f"{reason.capitalize()} from @{author.get('handle')}: \"{user_text[:40]}...\"",
                        target_data={"notification": notif, "profile": profile, "text": user_text},
                        intent=intent,
                    )
                )
                if len(valid_notif_candidates) >= 3:
                    break

            candidates.extend(valid_notif_candidates)

        # -------------------------------------------------------------
        # 4. Spontaneous Organic Posting (Text or Image)
        # -------------------------------------------------------------
        if config.allow_posts and context.posts_today < config.max_posts_per_day:
            # Probability depends on hours since last post and circadian phase
            post_score = 0.20
            if context.circadian_phase in ("morning", "afternoon", "evening"):
                if context.hours_since_last_post >= 14.0:
                    post_score = 0.72
                elif context.hours_since_last_post >= 7.0:
                    post_score = 0.58
                elif context.hours_since_last_post >= 4.0:
                    post_score = 0.35
                else:
                    post_score = 0.05
            elif context.circadian_phase == "night" and context.hours_since_last_post >= 8.0:
                post_score = 0.45
            else:
                post_score = 0.02

            # Does weather or holiday add natural inspiration?
            weather_inspire = context.weather.is_raining or context.weather.is_snowing
            if weather_inspire:
                post_score = min(0.85, post_score + 0.15)

            # Determine whether this post warrants an accompanying photograph or text-only
            wants_image = False
            if can_image and config.allow_images:
                try:
                    from .budget_manager import budget_manager
                    can_gen, _ = budget_manager.can_generate_image()
                except Exception:
                    can_gen = True

                if can_gen and post_score >= 0.45:
                    recent_posts = memory_store.get_recent_context().get("posts", [])
                    hours_since_last_image = 999.0
                    for p in recent_posts:
                        if p.get("has_image"):
                            try:
                                p_dt = dt.datetime.fromisoformat(p.get("created_at", ""))
                                if p_dt.tzinfo is None:
                                    p_dt = p_dt.replace(tzinfo=dt.timezone.utc)
                                diff = (dt.datetime.now(dt.timezone.utc) - p_dt).total_seconds() / 3600.0
                                hours_since_last_image = max(0.0, diff)
                                break
                            except Exception:
                                pass

                    is_atmospheric = (
                        weather_inspire
                        or context.circadian_phase in ("morning", "evening", "deep_night")
                        or bool(context.scheduled_area)
                    )
                    if hours_since_last_image >= 8.0 and is_atmospheric and context.hours_since_last_post >= 6.0:
                        wants_image = True

            if wants_image:
                candidates.append(
                    ActionCandidate(
                        action=ActionType.PUBLISH_IMAGE_POST,
                        score=min(0.88, post_score + 0.05),
                        confidence=0.75,
                        reason="Candid visual moment and ambient setting warrant an accompanying photograph.",
                        intent="share_visual_moment",
                    )
                )
            else:
                candidates.append(
                    ActionCandidate(
                        action=ActionType.PUBLISH_TEXT_POST,
                        score=post_score,
                        confidence=0.75,
                        reason=f"Spontaneous thought ({context.hours_since_last_post:.1f}h since last post, {context.circadian_phase}).",
                        intent="share_ordinary_thought",
                    )
                )

        # -------------------------------------------------------------
        # 5. Feed Browsing & Community Engagement (Thoughtful Reply or Like)
        # -------------------------------------------------------------
        if feed_items and context.circadian_phase != "deep_night":
            best_reply_candidate: Optional[ActionCandidate] = None
            best_like_candidate: Optional[ActionCandidate] = None

            for item in feed_items:
                post = item.get("post", item) if isinstance(item, dict) else {}
                if not isinstance(post, dict):
                    continue

                post_uri = post.get("uri", "")
                if not post_uri:
                    continue

                author = post.get("author", {})
                author_handle = (author.get("handle") or "").lower().lstrip("@")
                my_handle = (config.bsky_handle or "").lower().lstrip("@")
                if author_handle == my_handle:
                    continue

                record = post.get("record", {})
                text = record.get("text", "") if isinstance(record, dict) else ""
                if not text or len(text.strip()) < 10:
                    continue

                # Content filter (prompt injection, spam, ads, crypto, politics, bots/news, language)
                langs = record.get("langs", []) if isinstance(record, dict) else []
                is_eligible, _ = ContentValidator.filter_feed_post(text, author_handle, langs=langs)
                if not is_eligible:
                    continue

                # 5a. Thoughtful Reply Candidate
                if (
                    best_reply_candidate is None
                    and config.allow_replies
                    and context.replies_today < config.max_replies_per_day
                    and not memory_store.has_replied_to_post(post_uri)
                ):
                    # Natural human pacing and circadian distribution:
                    # When she has had 1.5h - 2h+ downtime during the day, organic commenting is highly natural
                    if context.circadian_phase in ("morning", "afternoon", "evening"):
                        if context.hours_since_last_action >= 2.0:
                            reply_score = 0.60
                        elif context.hours_since_last_action >= 1.5:
                            reply_score = 0.54
                        elif context.hours_since_last_action >= 1.0:
                            reply_score = 0.46
                        else:
                            reply_score = 0.25
                    elif context.circadian_phase == "night" and context.hours_since_last_action >= 2.5:
                        reply_score = 0.48
                    else:
                        reply_score = 0.15

                    # Relationship weighting: higher priority for established mutuals/regulars
                    author_profile = memory_store.get_user_profile(author_handle)
                    if author_profile.relationship in ("regular", "trusted_friend", "friendly_acquaintance"):
                        reply_score = min(0.85, reply_score + 0.15)

                    best_reply_candidate = ActionCandidate(
                        action=ActionType.BROWSE_AND_REPLY,
                        score=reply_score,
                        confidence=0.65,
                        reason=f"Thoughtful reply to feed post by @{author.get('handle')}: \"{text[:40]}...\"",
                        target_data={"post": post},
                        intent="add_perspective",
                    )

                # 5b. Quiet Like Candidate
                if (
                    best_like_candidate is None
                    and config.allow_likes
                    and getattr(context, "likes_today", 0) < config.max_likes_per_day
                ):
                    like_score = 0.46 if context.hours_since_last_action >= 1.0 else 0.32
                    author_profile = memory_store.get_user_profile(author_handle)
                    if author_profile.relationship in ("regular", "trusted_friend", "friendly_acquaintance"):
                        like_score = min(0.80, like_score + 0.12)

                    best_like_candidate = ActionCandidate(
                        action=ActionType.BROWSE_AND_LIKE,
                        score=like_score,
                        confidence=0.65,
                        reason=f"Quietly like post by @{author.get('handle')} during feed browsing.",
                        target_data={"post": post},
                    )

                # 5c. Quote Post Candidate
                if (
                    config.allow_posts
                    and context.posts_today < config.max_posts_per_day
                    and context.hours_since_last_post >= 4.0
                    and not memory_store.has_replied_to_post(post_uri)
                    and len(text.strip()) >= 30
                ):
                    quote_score = 0.48 if context.hours_since_last_action >= 1.5 else 0.30
                    candidates.append(
                        ActionCandidate(
                            action=ActionType.QUOTE_POST,
                            score=quote_score,
                            confidence=0.65,
                            reason=f"Quote-post thought by @{author.get('handle')}: \"{text[:40]}...\"",
                            target_data={"post": post},
                            intent="quote_with_perspective",
                        )
                    )

                # 5d. Repost Candidate (for evocative community posts)
                if (
                    "embed" in post
                    and post.get("embed", {}).get("$type") == "app.bsky.embed.images#view"
                    and context.hours_since_last_action >= 2.0
                ):
                    candidates.append(
                        ActionCandidate(
                            action=ActionType.REPOST,
                            score=0.40,
                            confidence=0.60,
                            reason=f"Quietly repost visual snapshot by @{author.get('handle')}.",
                            target_data={"post": post},
                        )
                    )

                if best_reply_candidate and best_like_candidate:
                    break

            if best_reply_candidate:
                candidates.append(best_reply_candidate)
            if best_like_candidate:
                candidates.append(best_like_candidate)

        # -------------------------------------------------------------
        # Modulate scores with cognitive state & social battery
        # -------------------------------------------------------------
        try:
            from .state_manager import state_manager
            raw_scores = {c.action.value: c.score for c in candidates}
            modulated_scores = state_manager.modulate_candidate_scores(raw_scores)
            for c in candidates:
                c.score = max(0.0, min(1.0, round(modulated_scores.get(c.action.value, c.score), 3)))
        except Exception:
            for c in candidates:
                c.score = max(0.0, min(1.0, round(c.score, 3)))

        # -------------------------------------------------------------
        # Select winning action & Calibrate Action Threshold
        # -------------------------------------------------------------
        # Sort candidates descending by score
        candidates.sort(key=lambda c: c.score, reverse=True)
        winner = candidates[0] if candidates else ActionCandidate(
            action=ActionType.NO_ACTION,
            score=1.0,
            confidence=1.0,
            reason="No action candidate available."
        )

        # Calibrated organic threshold: external outward actions require meaningful conviction (>= 0.50)
        EXTERNAL_ACTION_THRESHOLD = 0.50
        if winner.action != ActionType.NO_ACTION and winner.score < EXTERNAL_ACTION_THRESHOLD:
            no_action_cand = next((c for c in candidates if c.action == ActionType.NO_ACTION), None)
            if no_action_cand:
                winner = no_action_cand
                winner.reason = f"Organic motivation below threshold ({EXTERNAL_ACTION_THRESHOLD:.2f}). Remaining offline."

        score_dict = {c.action.value: round(c.score, 3) for c in candidates}

        return DecisionOutcome(
            selected_action=winner.action,
            reason=winner.reason,
            target_data=winner.target_data,
            intent=winner.intent,
            candidate_scores=score_dict,
            all_candidates=candidates,
        )


decision_engine = DecisionEngine()
