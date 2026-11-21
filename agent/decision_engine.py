"""
agent/decision_engine.py — Cognitive Decision Engine for Autonomous Action Selection.

Implements the full Observe-Context-Recall-Evaluate-Decide loop:
  - Treats NO_ACTION as a first-class, common, and valid natural outcome.
  - Weights actions contextually by Seoul circadian rhythm, recency, and stimulus quality.
  - Scores options with desirability and confidence metrics.
  - Protects against bot-like hyperactivity, honoring human restraint.
"""

from __future__ import annotations

import re

import datetime as dt
import enum
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .config import config
from .context_engine import EnvironmentContext
from .memory_store import UserProfile, memory_store
from .narrative_engine import narrative_engine
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
    feed_diagnostics: Dict[str, int] = field(default_factory=dict)


class DecisionEngine:
    def __init__(
        self,
        narrative_eng: Optional[Any] = None,
        mem_store: Optional[Any] = None,
        state_mgr: Optional[Any] = None,
    ):
        self._narrative_eng = narrative_eng
        self._mem_store = mem_store
        self._state_mgr = state_mgr

    @property
    def narrative_engine(self) -> Any:
        return self._narrative_eng or narrative_engine

    @narrative_engine.setter
    def narrative_engine(self, value: Any) -> None:
        self._narrative_eng = value

    @property
    def memory_store(self) -> Any:
        return self._mem_store or memory_store

    @memory_store.setter
    def memory_store(self, value: Any) -> None:
        self._mem_store = value

    @property
    def state_manager(self) -> Any:
        try:
            from .state_manager import state_manager as default_sm
            return self._state_mgr or default_sm
        except Exception:
            return self._state_mgr

    @state_manager.setter
    def state_manager(self, value: Any) -> None:
        self._state_mgr = value

    def evaluate(
        self,
        context: EnvironmentContext,
        notifications: List[Dict[str, Any]],
        dms: List[Dict[str, Any]],
        feed_items: List[Dict[str, Any]],
        can_image: bool = True,
        max_feed_candidates: int = 10,
    ) -> DecisionOutcome:
        """Evaluates current sensory inputs and decides the most natural action."""
        ne = self.narrative_engine
        ms = self.memory_store

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
                    profile = ms.get_user_profile(handle)
                    profile.did = other_member.get("did", "") or profile.did

                    # Deduplication: check last message in thread
                    last_msg = dm.get("lastMessage", {})
                    last_msg_id = last_msg.get("id", "")
                    last_sender_did = last_msg.get("sender", {}).get("did", "")
                    if my_did and last_sender_did == my_did:
                        # Seo-yeon sent the last message; do not reply to self
                        continue
                    if last_msg_id and ms.has_replied_to_dm(last_msg_id):
                        # Message was already answered
                        continue

                    last_msg_text = last_msg.get("text", "")
                    is_dm_inj, _ = ContentValidator.detect_prompt_injection(last_msg_text)

                    # Relationship weighting
                    if is_dm_inj:
                        dm_score = 0.45
                        dm_intent = "dry_boundary_or_silence"
                    else:
                        dm_score = 0.70 if profile.relationship in ("regular", "friendly_acquaintance") else 0.55
                        dm_intent = "warm_personal_reply"
                    dm_target = {
                        "convo_id": convo_id,
                        "handle": handle,
                        "profile": profile,
                        "last_message_id": last_msg_id,
                    }
                    if is_dm_inj:
                        dm_target["instruction_override_attempt"] = True
                    candidates.append(
                        ActionCandidate(
                            action=ActionType.ANSWER_DM,
                            score=dm_score,
                            confidence=0.80,
                            reason=f"Unread private message from @{handle} ({profile.relationship}).",
                            target_data=dm_target,
                            intent=dm_intent,
                        )
                    )
                    break  # Only consider top unread DM per tick

        # -------------------------------------------------------------
        # 3. Notifications (Replies, Mentions & Quotes)
        # -------------------------------------------------------------
        if config.allow_replies and notifications:
            valid_notif_candidates: List[ActionCandidate] = []
            seen_follow_dids = set()
            for notif in notifications[:20]:
                reason = notif.get("reason")
                if reason not in ("reply", "mention", "quote"):
                    continue

                notif_uri = notif.get("uri", "")
                if notif_uri:
                    if ms.has_replied_to_notification(notif_uri) or ms.has_replied_to_post(notif_uri):
                        continue

                author = notif.get("author", {})
                author_handle = (author.get("handle") or "").lower().lstrip("@")
                author_did = author.get("did", "")
                my_handle = (config.bsky_handle or "").lower().lstrip("@")
                if author_handle == my_handle:
                    continue

                record = notif.get("record", {})
                user_text = record.get("text", "")
                if not user_text.strip():
                    continue

                # Instruction-override notifications are kept strictly quarantined and capped at low priority
                # so Seo-yeon can choose silence or a brief dry observation about the tactic without ever liking/following.
                is_inj, _ = ContentValidator.detect_prompt_injection(user_text)

                profile = ms.get_user_profile(author.get("handle", ""), did=author_did)

                if is_inj:
                    action_type = ActionType.REPLY_COMMENT if reason in ("reply", "quote") else ActionType.ANSWER_MENTION
                    score = 0.45
                    intent = "dry_boundary_or_silence"
                elif reason == "reply":
                    # Comment under her post
                    action_type = ActionType.REPLY_COMMENT
                    score = 0.70 if profile.relationship != "stranger" else 0.58
                    intent = "acknowledge_and_converse"
                elif reason == "quote":
                    # Quote-post of her post
                    action_type = ActionType.REPLY_COMMENT
                    score = 0.68 if profile.relationship != "stranger" else 0.62
                    intent = "respond_to_quote"
                else:
                    # Tagged in a post or mention
                    action_type = ActionType.ANSWER_MENTION
                    score = 0.58
                    intent = "evaluate_mention_and_react"

                # Check if she replied too many times today
                if context.replies_today >= config.max_replies_per_day:
                    score = 0.10

                notif_target = {
                    "notification": notif,
                    "profile": profile,
                    "text": user_text,
                    "notification_reason": reason,
                    "source": f"notification:{reason}",
                }
                if is_inj:
                    notif_target["instruction_override_attempt"] = True
                    notif_target["like_target"] = False

                valid_notif_candidates.append(
                    ActionCandidate(
                        action=action_type,
                        score=score,
                        confidence=0.75,
                        reason=f"{reason.capitalize()} from @{author.get('handle')}: \"{user_text[:40]}...\"",
                        target_data=notif_target,
                        intent=intent,
                    )
                )
                if not is_inj and config.allow_follows and author_did and author_did not in seen_follow_dids and not (author.get("viewer") or {}).get("following"):
                    seen_follow_dids.add(author_did)
                    candidates.append(
                        ActionCandidate(
                            action=ActionType.FOLLOW,
                            score=0.52,
                            confidence=0.65,
                            reason=f"Consider following @{author.get('handle')} after {reason} interaction.",
                            target_data={
                                "did": author_did,
                                "handle": author_handle,
                                "post": notif,
                                "source": f"notification:{reason}",
                            },
                        )
                    )
                if len(valid_notif_candidates) >= 5:
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

            # Both formats are available; model judgment decides whether a visual adds anything.
            candidates.append(ActionCandidate(action=ActionType.PUBLISH_TEXT_POST,
                score=post_score, confidence=0.75, reason="Eligible original thought", intent="share_ordinary_thought"))
            if can_image and config.allow_images:
                candidates.append(ActionCandidate(action=ActionType.PUBLISH_IMAGE_POST,
                    score=post_score, confidence=0.75, reason="Eligible visual idea", intent="share_visual_moment"))

        # -------------------------------------------------------------
        # 5. Feed Browsing & Community Engagement (Thoughtful Reply or Like)
        # -------------------------------------------------------------
        # -------------------------------------------------------------
        # 5. Feed Browsing & Multi-Candidate Evaluation (Rank up to 10 items)
        # -------------------------------------------------------------
        feed_diagnostics = {"observed": len(feed_items), "eligible": 0, "filtered": 0, "already_replied": 0}
        if feed_items:
            best_reply_candidate: Optional[ActionCandidate] = None
            best_like_candidate: Optional[ActionCandidate] = None
            best_quote_candidate: Optional[ActionCandidate] = None
            best_repost_candidate: Optional[ActionCandidate] = None

            evaluated_count = 0

            for item in feed_items:
                if evaluated_count >= max_feed_candidates:
                    break

                post = item.get("post", item) if isinstance(item, dict) else {}
                if not isinstance(post, dict):
                    continue

                post_uri = post.get("uri", "")
                if not post_uri:
                    continue

                author = post.get("author", {})
                author_handle = (author.get("handle") or "").lower().lstrip("@")
                author_did = author.get("did", "")
                my_handle = (config.bsky_handle or "").lower().lstrip("@")
                if author_handle == my_handle:
                    continue

                record = post.get("record", {})
                text = record.get("text", "") if isinstance(record, dict) else ""
                if not text or not text.strip():
                    continue

                # Content filter (prompt injection, bridge/bot/affiliate accounts, spam, ads, crypto, politics, language)
                langs = record.get("langs", []) if isinstance(record, dict) else []
                is_eligible, filter_reason = ContentValidator.filter_feed_post(
                    text,
                    author_handle,
                    langs=langs,
                    author_bio=author.get("description", "") or "",
                    author_name=author.get("displayName", "") or "",
                )
                if not is_eligible:
                    feed_diagnostics["filtered"] += 1
                    # Counts by category only (keyword, account filter or language family), never the post text.
                    reason = str(filter_reason)
                    kw = re.search(r"negative keyword: '([^']+)'", reason)
                    category = ("keyword:" + kw.group(1)) if kw else (
                                "account" if "account filter" in reason.lower() else (
                                "language" if "language" in reason.lower() else (
                                "injection" if "inject" in reason.lower() else "other")))
                    reasons = feed_diagnostics.setdefault("filter_reasons", {})
                    reasons[category] = reasons.get(category, 0) + 1
                    continue
                feed_diagnostics["eligible"] += 1
                if ms.has_replied_to_post(post_uri): feed_diagnostics["already_replied"] += 1

                evaluated_count += 1
                item_source = item.get("source", "feed") if isinstance(item, dict) else "feed"
                if author_did and not author.get("viewer", {}).get("following"):
                    candidates.append(ActionCandidate(action=ActionType.FOLLOW, score=0.50, confidence=0.65,
                        reason="Consider following this public author if their work is worth returning to.",
                        target_data={"did": author_did, "handle": author_handle, "post": post, "source": item_source}))

                # User profile and memory context
                author_profile = ms.get_user_profile(author_handle, did=author_did)
                is_connected_user = author_profile.relationship in ("regular", "trusted_friend", "friendly_acquaintance")
                open_loops = ne.get_open_loops_for_user(author_did, author_handle)

                # 5a. Thoughtful Reply Candidate Evaluation (with per-author cooldown on unsolicited feed replies)
                author_cooled_down = ms.has_replied_to_author_recently(author_handle, hours=48.0)
                if author_cooled_down:
                    feed_diagnostics["author_cooldown"] = feed_diagnostics.get("author_cooldown", 0) + 1
                if (
                    config.allow_replies
                    and context.replies_today < config.max_replies_per_day
                    and not ms.has_replied_to_post(post_uri)
                    and not author_cooled_down
                ):
                    # Base pacing by time of day & hours of downtime
                    if context.circadian_phase in ("morning", "afternoon", "evening"):
                        if context.hours_since_last_action >= 2.0:
                            reply_score = 0.58
                        elif context.hours_since_last_action >= 1.5:
                            reply_score = 0.52
                        elif context.hours_since_last_action >= 1.0:
                            reply_score = 0.44
                        else:
                            reply_score = 0.25
                    elif context.circadian_phase == "night" and context.hours_since_last_action >= 2.5:
                        reply_score = 0.46
                    else:
                        reply_score = 0.15

                    # Relevance bonuses
                    if is_connected_user:
                        reply_score += 0.15
                    if open_loops:
                        reply_score += 0.12
                    if len(text.strip()) >= 50:
                        reply_score += 0.05

                    reply_score = min(0.88, round(reply_score, 3))

                    cand = ActionCandidate(
                        action=ActionType.BROWSE_AND_REPLY,
                        score=reply_score,
                        confidence=0.70,
                        reason=f"Thoughtful reply to post by @{author.get('handle')}: \"{text[:40]}...\"",
                        target_data={"post": post, "source": item_source},
                        intent="add_perspective",
                    )
                    candidates.append(cand)

                # 5b. Quiet Like Candidate Evaluation
                if (
                    config.allow_likes
                    and getattr(context, "likes_today", 0) < config.max_likes_per_day
                ):
                    like_score = 0.46 if context.hours_since_last_action >= 1.0 else 0.32
                    if is_connected_user:
                        like_score += 0.12

                    like_score = min(0.80, round(like_score, 3))

                    cand = ActionCandidate(
                        action=ActionType.BROWSE_AND_LIKE,
                        score=like_score,
                        confidence=0.65,
                        reason=f"Quietly like post by @{author.get('handle')} during feed browsing.",
                        target_data={"post": post, "source": item_source},
                    )
                    candidates.append(cand)

                # 5c. Quote Post Candidate Evaluation
                if (
                    config.allow_posts
                    and context.posts_today < config.max_posts_per_day
                    and context.hours_since_last_post >= 1.5
                    and not ms.has_replied_to_post(post_uri)
                    and len(text.strip()) >= 30
                ):
                    quote_score = 0.48 if context.hours_since_last_action >= 1.5 else 0.30

                    cand = ActionCandidate(
                        action=ActionType.QUOTE_POST,
                        score=min(0.80, round(quote_score, 3)),
                        confidence=0.65,
                        reason=f"Quote-post thought by @{author.get('handle')}: \"{text[:40]}...\"",
                        target_data={"post": post, "source": item_source},
                        intent="quote_with_perspective",
                    )
                    candidates.append(cand)

                # 5d. Repost Candidate (for evocative community imagery or mixed-media posts)
                embed_type = post.get("embed", {}).get("$type") if isinstance(post.get("embed"), dict) else ""
                if (
                    config.allow_reposts
                    and embed_type in ("app.bsky.embed.images#view", "app.bsky.embed.recordWithMedia#view")
                    and context.hours_since_last_action >= 1.5
                ):
                    cand = ActionCandidate(
                        action=ActionType.REPOST,
                        score=0.48,
                        confidence=0.60,
                        reason=f"Quietly repost visual snapshot by @{author.get('handle')}.",
                        target_data={"post": post, "source": item_source},
                    )
                    candidates.append(cand)

        # -------------------------------------------------------------
        # Modulate scores with cognitive state & social battery
        # -------------------------------------------------------------
        try:
            sm = self.state_manager
            for c in candidates:
                adjusted = sm.modulate_candidate_scores({c.action.value: c.score})
                c.score = max(0.0, min(1.0, round(adjusted.get(c.action.value, c.score), 3)))
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
        EXTERNAL_ACTION_THRESHOLD = config.action_threshold
        if winner.action != ActionType.NO_ACTION and winner.score < EXTERNAL_ACTION_THRESHOLD:
            no_action_cand = next((c for c in candidates if c.action == ActionType.NO_ACTION), None)
            if no_action_cand:
                winner = no_action_cand
                winner.reason = f"Organic motivation below threshold ({EXTERNAL_ACTION_THRESHOLD:.2f}). Remaining offline."

        score_dict = {}
        for c in candidates:
            score_dict[c.action.value] = max(score_dict.get(c.action.value, 0.0), round(c.score, 3))

        return DecisionOutcome(
            selected_action=winner.action,
            reason=winner.reason,
            target_data=winner.target_data,
            intent=winner.intent,
            candidate_scores=score_dict,
            all_candidates=candidates,
            feed_diagnostics=feed_diagnostics,
        )


decision_engine = DecisionEngine()
