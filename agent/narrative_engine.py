"""
agent/narrative_engine.py — Narrative Continuity, Event Lifecycles & Conversational Loops.

Ensures long-term coherence across posts, replies, and direct messages:
  1. Event Lifecycle:
     - Events transition: PLANNED -> IN_PROGRESS -> COMPLETED / CANCELLED.
     - Enforces temporal coherence: prevents claims of completing activities before their time.
  2. Open Conversational Loops:
     - Tracks commitments made to users (e.g. promised book/movie follow-up, advice tested).
     - Grounds future interactions with that specific user in past shared topics.
  3. Multi-Day Narrative Arcs:
     - Connects everyday occurrences across days (e.g. buying a plant, repotting, new leaves).
"""

from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import re
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from .config import DATA_DIR, config
from .context_engine import get_seoul_datetime


NARRATIVE_STATE_FILE = DATA_DIR / "memory" / "narrative_state.json"


class EventStatus(str, Enum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class LoopStatus(str, Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    EXPIRED = "EXPIRED"


@dataclass
class ConversationalLoop:
    loop_id: str
    partner_identifier: str  # DID or handle
    partner_handle: str
    topic: str
    loop_type: str  # "recommendation_received", "promise_to_check", "shared_question", "follow_up"
    context_note: str
    created_at: str
    status: str = LoopStatus.OPEN.value
    resolved_at: Optional[str] = None
    resolution_note: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ConversationalLoop:
        return cls(
            loop_id=data.get("loop_id", f"loop_{uuid.uuid4().hex[:8]}"),
            partner_identifier=data.get("partner_identifier", ""),
            partner_handle=data.get("partner_handle", ""),
            topic=data.get("topic", ""),
            loop_type=data.get("loop_type", "follow_up"),
            context_note=data.get("context_note", ""),
            created_at=data.get("created_at", dt.datetime.now(dt.timezone.utc).isoformat()),
            status=data.get("status", LoopStatus.OPEN.value),
            resolved_at=data.get("resolved_at"),
            resolution_note=data.get("resolution_note"),
        )


@dataclass
class NarrativeArc:
    arc_id: str
    title: str
    summary: str
    milestones: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "ACTIVE"  # "ACTIVE" or "CONCLUDED"
    created_at: str = field(default_factory=lambda: dt.datetime.now(dt.timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> NarrativeArc:
        return cls(
            arc_id=data.get("arc_id", f"arc_{uuid.uuid4().hex[:8]}"),
            title=data.get("title", ""),
            summary=data.get("summary", ""),
            milestones=data.get("milestones", []),
            status=data.get("status", "ACTIVE"),
            created_at=data.get("created_at", dt.datetime.now(dt.timezone.utc).isoformat()),
        )


DEFAULT_NARRATIVE_STATE: Dict[str, Any] = {
    "open_loops": [],
    "narrative_arcs": [
        {
            "arc_id": "arc_autumn_persimmon_curtain",
            "title": "Autumn dried persimmon strings in kitchen",
            "summary": "Peeled three firm astringent persimmons bought at market and hung them near the kitchen window with hemp string to dry in the cool autumn breeze.",
            "status": "ACTIVE",
            "created_at": "2026-10-06T10:00:00+00:00",
            "milestones": [
                {
                    "date": "2026-10-06",
                    "note": "Peeled and strung persimmons; kitchen smells like sweet peel.",
                }
            ],
        }
    ],
    "daily_events": {},
    "updated_at": "2026-10-08T00:00:00+00:00",
}


class NarrativeContinuityEngine:
    """Maintains narrative consistency, temporal logic, and open conversational loops."""

    def __init__(self, storage_file: Optional[pathlib.Path] = None):
        self.storage_file = storage_file or NARRATIVE_STATE_FILE
        self._ensure_storage()

    def _ensure_storage(self) -> None:
        if not self.storage_file.exists():
            self.storage_file.parent.mkdir(parents=True, exist_ok=True)
            self._save_raw(DEFAULT_NARRATIVE_STATE)

    def _load_raw(self) -> Dict[str, Any]:
        try:
            return json.loads(self.storage_file.read_text(encoding="utf-8"))
        except Exception:
            return DEFAULT_NARRATIVE_STATE.copy()

    def _save_raw(self, data: Dict[str, Any]) -> None:
        data["updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
        temp_file = self.storage_file.with_suffix(".tmp")
        temp_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        temp_file.replace(self.storage_file)

    # --- Conversational Loops ---

    def open_loop(
        self,
        partner_identifier: str,
        partner_handle: str,
        topic: str,
        loop_type: str = "follow_up",
        context_note: str = "",
    ) -> ConversationalLoop:
        """Opens a new tracking loop for commitments or shared recommendations."""
        data = self._load_raw()
        loops = data.get("open_loops", [])

        # Check if an open loop with similar topic already exists for this user
        for existing in loops:
            if (
                existing.get("status") == LoopStatus.OPEN.value
                and (existing.get("partner_identifier") == partner_identifier or existing.get("partner_handle") == partner_handle)
                and existing.get("topic", "").lower() == topic.lower()
            ):
                return ConversationalLoop.from_dict(existing)

        loop = ConversationalLoop(
            loop_id=f"loop_{uuid.uuid4().hex[:8]}",
            partner_identifier=partner_identifier,
            partner_handle=partner_handle.lstrip("@"),
            topic=topic,
            loop_type=loop_type,
            context_note=context_note,
            created_at=dt.datetime.now(dt.timezone.utc).isoformat(),
            status=LoopStatus.OPEN.value,
        )

        loops.append(loop.to_dict())
        data["open_loops"] = loops
        self._save_raw(data)
        return loop

    def get_open_loops_for_user(self, partner_identifier: str, partner_handle: str = "") -> List[ConversationalLoop]:
        """Returns all open loops involving a specific user."""
        data = self._load_raw()
        loops = [ConversationalLoop.from_dict(l) for l in data.get("open_loops", [])]
        clean_handle = partner_handle.lstrip("@").lower().strip()

        matched = []
        for l in loops:
            if l.status != LoopStatus.OPEN.value:
                continue
            if partner_identifier and (l.partner_identifier == partner_identifier):
                matched.append(l)
            elif clean_handle and (l.partner_handle.lower() == clean_handle):
                matched.append(l)
        return matched

    def resolve_loop(self, loop_id: str, resolution_note: str = "") -> bool:
        """Marks a conversational loop as resolved."""
        data = self._load_raw()
        loops = data.get("open_loops", [])
        updated = False

        for l in loops:
            if l.get("loop_id") == loop_id:
                l["status"] = LoopStatus.RESOLVED.value
                l["resolved_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
                l["resolution_note"] = resolution_note
                updated = True
                break

        if updated:
            self._save_raw(data)
        return updated

    def format_loops_for_user_prompt(self, partner_identifier: str, partner_handle: str = "") -> str:
        """Formats open loops as prompt context when conversing with a specific user."""
        loops = self.get_open_loops_for_user(partner_identifier, partner_handle)
        if not loops:
            return ""

        lines = ["Past conversation threads and open commitments with this person:"]
        for l in loops:
            lines.append(f"- [{l.loop_type}] Topic: {l.topic} (Context: {l.context_note})")
        return "\n".join(lines)

    # --- Multi-Day Narrative Arcs ---

    def get_active_narrative_arcs(self) -> List[NarrativeArc]:
        data = self._load_raw()
        arcs = [NarrativeArc.from_dict(a) for a in data.get("narrative_arcs", [])]
        return [a for a in arcs if a.status == "ACTIVE"]

    def add_narrative_milestone(self, arc_id: str, note: str) -> bool:
        """Appends a new milestone to an ongoing narrative arc."""
        data = self._load_raw()
        arcs = data.get("narrative_arcs", [])
        updated = False
        today_str = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")

        for a in arcs:
            if a.get("arc_id") == arc_id:
                milestones = a.get("milestones", [])
                milestones.append({"date": today_str, "note": note})
                a["milestones"] = milestones
                updated = True
                break

        if updated:
            self._save_raw(data)
        return updated

    def format_narrative_arcs_context(self) -> str:
        """Formats active narrative arcs for LLM generation context."""
        arcs = self.get_active_narrative_arcs()
        if not arcs:
            return ""

        lines = ["Ongoing everyday multi-day domestic / lifestyle narrative arcs:"]
        for a in arcs:
            latest = a.milestones[-1]["note"] if a.milestones else a.summary
            lines.append(f"- {a.title}: {latest}")
        return "\n".join(lines)

    # --- Temporal Coherence Validation ---

    def validate_temporal_statement(
        self,
        text: str,
        current_hour_kst: int,
        scheduled_activity: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates whether a text statement is temporally coherent with current time.
        Rejects statements asserting an event occurred that is scheduled for later today.
        """
        text_lower = text.lower()

        # Morning hours (07:00 - 11:59): Cannot claim to have already had dinner or completed evening classes
        if current_hour_kst < 12:
            if any(w in text_lower for w in ("had dinner", "finished dinner", "ate dinner", "저녁 먹었", "저녁 다 먹")):
                return False, "Temporal inconsistency: claiming to have finished dinner during morning hours."
            if "tonight's class was" in text_lower or "오늘 밤" in text_lower and "끝났" in text_lower:
                return False, "Temporal inconsistency: claiming evening events completed during morning."

        # Daytime hours before evening (< 18:00): Cannot claim evening activity happened
        if current_hour_kst < 18:
            if any(w in text_lower for w in ("late night walk was", "midnight", "just went to sleep", "midnight tea")):
                return False, "Temporal inconsistency: claiming late-night activities occurred before evening."

        return True, None


narrative_engine = NarrativeContinuityEngine()
