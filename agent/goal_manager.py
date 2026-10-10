"""
agent/goal_manager.py — Persistent Goal & Pursuit Engine for Han Seo-yeon.

Maintains multi-day and multi-week personal pursuits, creative ambitions, and
domestic projects for Seo-yeon:
  - Persistent storage in data/memory/active_goals.json.
  - Life categories: cultural, domestic, social, personal_craft.
  - Anti-cliché quota: pilates & coffee goals strictly capped at <= 10%.
  - Integrates with Cognitive Decision Loop and Content Generator so her
    posts, replies, and quiet moments naturally reflect continuous progress.
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


GOALS_FILE = DATA_DIR / "memory" / "active_goals.json"


class GoalCategory(str, Enum):
    CULTURAL = "cultural"          # Independent cinema, books, typography, Seoul architecture
    DOMESTIC = "domestic"          # Cooking, plant care, flat organization, balcony seasons
    SOCIAL = "social"              # Neighborhood observations, quiet local connections
    PERSONAL_CRAFT = "personal_craft"  # Reformer technique, film photography, essay notes


class GoalPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class GoalStatus(str, Enum):
    PROPOSED = "PROPOSED"
    ACTIVE = "ACTIVE"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    PAUSED = "PAUSED"
    ABANDONED = "ABANDONED"


@dataclass
class ProgressEvent:
    timestamp: str
    event_type: str  # "progress", "milestone", "pause", "completion", "reflection"
    note: str
    post_uri: Optional[str] = None
    metrics_delta: Optional[Dict[str, Any]] = None


@dataclass
class Goal:
    goal_id: str
    title: str
    description: str
    category: str  # GoalCategory value
    priority: str  # GoalPriority value
    status: str    # GoalStatus value
    created_at: str
    target_date: Optional[str] = None
    progress_events: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    completion_notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Goal:
        return cls(
            goal_id=data.get("goal_id", f"g_{uuid.uuid4().hex[:8]}"),
            title=data.get("title", "Untitled Goal"),
            description=data.get("description", ""),
            category=data.get("category", GoalCategory.CULTURAL.value),
            priority=data.get("priority", GoalPriority.MEDIUM.value),
            status=data.get("status", GoalStatus.PROPOSED.value),
            created_at=data.get("created_at", dt.datetime.now(dt.timezone.utc).isoformat()),
            target_date=data.get("target_date"),
            progress_events=data.get("progress_events", []),
            metrics=data.get("metrics", {}),
            completion_notes=data.get("completion_notes"),
        )


# Fresh installations begin without invented achievements.
CANONICAL_SEED_GOALS = []


class GoalManager:
    """Manages persistent personal goals and multi-day narrative continuity."""

    def __init__(self, storage_file: Optional[pathlib.Path] = None):
        self.storage_file = storage_file or GOALS_FILE
        self._ensure_storage()

    @property
    def goals_file(self) -> pathlib.Path:
        return self.storage_file

    @goals_file.setter
    def goals_file(self, value: pathlib.Path) -> None:
        self.storage_file = value

    def _ensure_storage(self) -> None:
        """Ensures the storage file exists with valid structure."""
        if not self.storage_file.exists():
            self.storage_file.parent.mkdir(parents=True, exist_ok=True)
            self._save_raw({"goals": CANONICAL_SEED_GOALS, "updated_at": dt.datetime.now(dt.timezone.utc).isoformat()})

    def _load_raw(self) -> Dict[str, Any]:
        try:
            return json.loads(self.storage_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise RuntimeError("Cannot read goals; refusing to reset history") from exc

    def _save_raw(self, data: Dict[str, Any]) -> None:
        data["updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
        from .storage import write_json
        write_json(self.storage_file, data)

    def get_all_goals(self) -> List[Goal]:
        data = self._load_raw()
        return [Goal.from_dict(g) for g in data.get("goals", [])]

    def get_active_goals(self, include_in_progress: bool = True) -> List[Goal]:
        """Returns currently active or in-progress goals."""
        allowed_statuses = [GoalStatus.ACTIVE.value]
        if include_in_progress:
            allowed_statuses.append(GoalStatus.IN_PROGRESS.value)
        return [g for g in self.get_all_goals() if g.status in allowed_statuses]

    def get_goal(self, goal_id: str) -> Optional[Goal]:
        for g in self.get_all_goals():
            if g.goal_id == goal_id:
                return g
        return None

    def propose_goal(
        self,
        title: str,
        description: str,
        category: str,
        priority: str = GoalPriority.MEDIUM.value,
        target_date: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> Optional[Goal]:
        """Proposes an operator-supplied goal without prescribing a topic mix."""
        goal_id = f"g_{category}_{uuid.uuid4().hex[:6]}"
        now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
        goal = Goal(
            goal_id=goal_id,
            title=title,
            description=description,
            category=category,
            priority=priority,
            status=GoalStatus.PROPOSED.value,
            created_at=now_iso,
            target_date=target_date,
            metrics=metrics or {},
        )

        data = self._load_raw()
        goals = data.get("goals", [])
        goals.append(goal.to_dict())
        data["goals"] = goals
        self._save_raw(data)
        return goal

    def activate_goal(self, goal_id: str) -> bool:
        """Activates a proposed or paused goal."""
        data = self._load_raw()
        goals = data.get("goals", [])
        updated = False
        for g in goals:
            if g.get("goal_id") == goal_id:
                g["status"] = GoalStatus.ACTIVE.value
                updated = True
                break
        if updated:
            self._save_raw(data)
        return updated

    def record_progress(
        self,
        goal_id: str,
        note: str,
        event_type: str = "progress",
        metrics_update: Optional[Dict[str, Any]] = None,
        post_uri: Optional[str] = None,
    ) -> bool:
        """Records progress on an active goal."""
        data = self._load_raw()
        goals = data.get("goals", [])
        updated = False
        now_iso = dt.datetime.now(dt.timezone.utc).isoformat()

        for g in goals:
            if g.get("goal_id") == goal_id:
                if g.get("status") == GoalStatus.ACTIVE.value:
                    g["status"] = GoalStatus.IN_PROGRESS.value
                events = g.get("progress_events", [])
                events.append({
                    "timestamp": now_iso,
                    "event_type": event_type,
                    "note": note,
                    "post_uri": post_uri,
                    "metrics_delta": metrics_update,
                })
                g["progress_events"] = events
                if metrics_update:
                    curr_metrics = g.get("metrics", {})
                    curr_metrics.update(metrics_update)
                    g["metrics"] = curr_metrics
                updated = True
                break

        if updated:
            self._save_raw(data)
        return updated

    def complete_goal(
        self,
        goal_id: str,
        note: Optional[str] = None,
        post_uri: Optional[str] = None,
    ) -> bool:
        """Marks a goal as completed."""
        data = self._load_raw()
        goals = data.get("goals", [])
        updated = False
        now_iso = dt.datetime.now(dt.timezone.utc).isoformat()

        for g in goals:
            if g.get("goal_id") == goal_id:
                g["status"] = GoalStatus.COMPLETED.value
                g["completion_notes"] = note or "Goal achieved."
                events = g.get("progress_events", [])
                events.append({
                    "timestamp": now_iso,
                    "event_type": "completion",
                    "note": note or "Goal achieved.",
                    "post_uri": post_uri,
                })
                g["progress_events"] = events
                updated = True
                break

        if updated:
            self._save_raw(data)
        return updated

    def pause_goal(self, goal_id: str, reason: Optional[str] = None) -> bool:
        data = self._load_raw()
        goals = data.get("goals", [])
        updated = False
        for g in goals:
            if g.get("goal_id") == goal_id:
                g["status"] = GoalStatus.PAUSED.value
                if reason:
                    events = g.get("progress_events", [])
                    events.append({
                        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                        "event_type": "pause",
                        "note": reason,
                    })
                    g["progress_events"] = events
                updated = True
                break
        if updated:
            self._save_raw(data)
        return updated

    def abandon_goal(self, goal_id: str, reason: Optional[str] = None) -> bool:
        data = self._load_raw()
        goals = data.get("goals", [])
        updated = False
        for g in goals:
            if g.get("goal_id") == goal_id:
                g["status"] = GoalStatus.ABANDONED.value
                g["completion_notes"] = reason or "Goal abandoned."
                updated = True
                break
        if updated:
            self._save_raw(data)
        return updated

    def get_goals_context_for_prompt(self) -> str:
        """Formats active goals as dry, organic internal background context for LLM generation."""
        active = self.get_active_goals()
        if not active:
            return ""

        lines = ["Current ongoing personal pursuits and quiet domestic projects:"]
        for g in active:
            progress_summary = ""
            if g.metrics:
                parts = [f"{k}: {v}" for k, v in g.metrics.items()]
                progress_summary = f" ({', '.join(parts)})"
            lines.append(f"- [{g.category}] {g.title}: {g.description}{progress_summary}")
        return "\n".join(lines)

    def detect_and_record_goal_activity(self, text: str, post_uri=None) -> List[str]:
        """Compatibility API: prose is not evidence of work completed."""
        return []

    def advance_active_goals_daily(self, context=None, days_elapsed=1, dry_run=False) -> List[str]:
        """Elapsed days alone do not create achievements."""
        return []

    def apply_evidence(self, goal_id, event_id, note, metrics, completed=False):
        """Apply one validated activity atomically; replay is idempotent."""
        from .storage import file_lock
        if not event_id or not note or not isinstance(metrics, dict):
            raise ValueError("Progress requires event evidence and metrics")
        with file_lock(self.storage_file):
            data = self._load_raw()
            for goal in data.get("goals", []):
                if goal["goal_id"] != goal_id:
                    continue
                events = goal.setdefault("progress_events", [])
                if any(e.get("event_id") == event_id for e in events):
                    return False
                if goal["status"] not in {"ACTIVE", "IN_PROGRESS"}:
                    return False
                goal.setdefault("metrics", {}).update(metrics)
                goal["status"] = "COMPLETED" if completed else "IN_PROGRESS"
                events.append({"event_id": event_id, "note": note,
                               "metrics_delta": metrics, "event_type": "completion" if completed else "progress",
                               "timestamp": dt.datetime.now(dt.timezone.utc).isoformat()})
                if completed:
                    goal["completion_notes"] = note
                self._save_raw(data)
                return True
        return False


goal_manager = GoalManager()
