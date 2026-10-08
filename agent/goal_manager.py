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


# Default canonical goals grounded in her identity and seasonal reality
CANONICAL_SEED_GOALS: List[Dict[str, Any]] = [
    {
        "goal_id": "g_novel_han_kang_202610",
        "title": "Finishing Han Kang's 'We Do Not Part'",
        "description": "Reading the Korean paperback edition in quiet evening hours; reflecting on memory and quiet prose.",
        "category": GoalCategory.CULTURAL.value,
        "priority": GoalPriority.HIGH.value,
        "status": GoalStatus.ACTIVE.value,
        "created_at": "2026-10-01T00:00:00+00:00",
        "target_date": "2026-10-25",
        "progress_events": [
            {
                "timestamp": "2026-10-02T14:30:00+00:00",
                "event_type": "progress",
                "note": "Read chapters 1 through 3 on the subway Line 2 loop.",
                "post_uri": None,
                "metrics_delta": {"current_page": 65, "total_pages": 310},
            }
        ],
        "metrics": {"current_page": 65, "total_pages": 310, "percent": 21.0},
    },
    {
        "goal_id": "g_domestic_kitchen_crockery_202610",
        "title": "Water propagating kitchen ivy cuttings",
        "description": "Rooting two small English ivy stems in small clear glass jars on the sunlit kitchen windowsill.",
        "category": GoalCategory.DOMESTIC.value,
        "priority": GoalPriority.MEDIUM.value,
        "status": GoalStatus.ACTIVE.value,
        "created_at": "2026-10-04T08:00:00+00:00",
        "target_date": "2026-10-31",
        "progress_events": [
            {
                "timestamp": "2026-10-04T08:00:00+00:00",
                "event_type": "milestone",
                "note": "Trimmed stems and placed in filtered water.",
                "post_uri": None,
                "metrics_delta": {"stage": "placed in water", "roots_visible": False},
            }
        ],
        "metrics": {"stage": "waiting for root nodes", "days_in_water": 4},
    },
    {
        "goal_id": "g_craft_seoul_typography_202610",
        "title": "Documenting vintage Hangul storefront signboards",
        "description": "Walking Seongsu and Euljiro backstreets noticing geometric metal and painted letterforms from the 1980s.",
        "category": GoalCategory.PERSONAL_CRAFT.value,
        "priority": GoalPriority.MEDIUM.value,
        "status": GoalStatus.ACTIVE.value,
        "created_at": "2026-10-05T11:00:00+00:00",
        "target_date": "2026-11-15",
        "progress_events": [],
        "metrics": {"signs_documented": 3, "target_signs": 10},
    },
]


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
        except Exception:
            return {"goals": CANONICAL_SEED_GOALS, "updated_at": dt.datetime.now(dt.timezone.utc).isoformat()}

    def _save_raw(self, data: Dict[str, Any]) -> None:
        data["updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
        temp_file = self.storage_file.with_suffix(".tmp")
        temp_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        temp_file.replace(self.storage_file)

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
        """Proposes a new goal while strictly enforcing anti-cliché quotas."""
        # Anti-cliché quota check: pilates & coffee <= 10%
        text_for_cliche = f"{title} {description}".lower()
        is_cliche = any(w in text_for_cliche for w in ("pilates", "필라테스", "coffee", "커피", "latte", "cafe"))
        if is_cliche:
            all_goals = self.get_all_goals()
            cliche_count = sum(
                1 for g in all_goals
                if any(w in f"{g.title} {g.description}".lower() for w in ("pilates", "필라테스", "coffee", "커피", "latte", "cafe"))
            )
            total_count = len(all_goals) + 1
            if (cliche_count + 1) / total_count > 0.10:
                print(f"[GoalManager] Blocked proposing cliché goal '{title}': exceeds 10% quota limit.")
                return None

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

    def detect_and_record_goal_activity(self, text: str, post_uri: Optional[str] = None) -> List[str]:
        """
        Scans published text or interaction content to check if it organically touches
        upon an active goal, registering a progress milestone and updating concrete metrics.
        """
        text_lower = text.lower()
        advanced_goal_ids = []

        keywords_map = {
            "g_novel_han_kang_202610": ["han kang", "한강", "we do not part", "작별하지 않는다", "novel", "소설", "chapter", "reading page"],
            "g_domestic_kitchen_crockery_202610": ["ivy", "water prop", "cuttings", "windowsill", "glass jar", "kitchen sill", "roots", "아이비"],
            "g_craft_seoul_typography_202610": ["typography", "signboard", "hangul sign", "간판", "letterform", "euljiro print", "vintage type"],
        }

        for goal in self.get_active_goals():
            gid = goal.goal_id
            kw_list = keywords_map.get(gid, [])
            title_tokens = [w.lower() for w in re.findall(r"\w+", goal.title) if len(w) > 3]
            match = any(kw in text_lower for kw in kw_list) or (sum(1 for t in title_tokens if t in text_lower) >= 2)

            if match:
                snippet = text[:150] + "..." if len(text) > 150 else text
                metrics = dict(goal.metrics)
                note = f"Organically referenced in social reflection: \"{snippet}\""
                metrics_update = None

                if gid == "g_novel_han_kang_202610":
                    curr_page = metrics.get("current_page", 65)
                    total_pages = metrics.get("total_pages", 310)
                    new_page = min(total_pages, curr_page + 15)
                    percent = round((new_page / total_pages) * 100, 1)
                    metrics_update = {"current_page": new_page, "percent": percent}
                    note = f"Social reflection on han kang novel (page {new_page}/{total_pages}): \"{snippet}\""
                    if new_page >= total_pages:
                        self.complete_goal(gid, note="Finished reading Han Kang novel following reflection.", post_uri=post_uri)
                        advanced_goal_ids.append(gid)
                        continue

                elif gid == "g_craft_seoul_typography_202610":
                    signs = metrics.get("signs_documented", 3)
                    target = metrics.get("target_signs", 10)
                    new_signs = min(target, signs + 1)
                    metrics_update = {"signs_documented": new_signs}
                    note = f"Social reflection on vintage signboards. Documented {new_signs}/{target}."
                    if new_signs >= target:
                        self.complete_goal(gid, note="Completed documentation of 10 storefront signboards.", post_uri=post_uri)
                        advanced_goal_ids.append(gid)
                        continue

                self.record_progress(
                    goal_id=gid,
                    note=note,
                    event_type="reflection",
                    metrics_update=metrics_update,
                    post_uri=post_uri,
                )
                advanced_goal_ids.append(gid)

        return advanced_goal_ids

    def advance_active_goals_daily(
        self,
        context: Optional[Any] = None,
        days_elapsed: int = 1,
        dry_run: bool = False,
    ) -> List[str]:
        """
        Advances active personal pursuits autonomously as calendar days elapse
        (during quiet evening reflection or nightly consolidation pass).
        Ensures reading progresses, plant cuttings root, and craft projects advance
        without requiring constant social media posting.
        """
        advanced_notes: List[str] = []
        for goal in self.get_active_goals():
            gid = goal.goal_id
            metrics = dict(goal.metrics)

            if gid == "g_novel_han_kang_202610":
                curr_page = metrics.get("current_page", 65)
                total_pages = metrics.get("total_pages", 310)
                new_page = min(total_pages, curr_page + 20 * days_elapsed)
                percent = round((new_page / total_pages) * 100, 1)
                metrics["current_page"] = new_page
                metrics["percent"] = percent
                note = f"Read quiet pages before sleep ({new_page}/{total_pages} pages, {percent}%)."

                if new_page >= total_pages:
                    if not dry_run:
                        self.complete_goal(gid, note="Finished reading the complete Korean edition of Han Kang's 'We Do Not Part'.")
                    advanced_notes.append(f"{goal.title}: Completed ({total_pages}/{total_pages} pages)")
                else:
                    if not dry_run:
                        self.record_progress(gid, note=note, event_type="progress", metrics_update=metrics)
                    advanced_notes.append(f"{goal.title}: {note}")

            elif gid == "g_domestic_kitchen_crockery_202610":
                days_in_water = metrics.get("days_in_water", 4) + days_elapsed
                metrics["days_in_water"] = days_in_water
                if days_in_water >= 21:
                    metrics["stage"] = "fully rooted, ready to pot"
                    if not dry_run:
                        self.complete_goal(gid, note="Both ivy cuttings have developed robust 3-inch white roots and were potted into soil.")
                    advanced_notes.append(f"{goal.title}: Completed (roots mature after {days_in_water} days)")
                elif days_in_water >= 10:
                    metrics["stage"] = "first pale root tips emerged"
                    metrics["roots_visible"] = True
                    note = f"First white root tips emerged from the lower node in the glass jar (day {days_in_water})."
                    if not dry_run:
                        self.record_progress(gid, note=note, event_type="milestone", metrics_update=metrics)
                    advanced_notes.append(f"{goal.title}: {note}")
                else:
                    note = f"Changed filtered water on the sunny windowsill (day {days_in_water})."
                    if not dry_run:
                        self.record_progress(gid, note=note, event_type="progress", metrics_update=metrics)
                    advanced_notes.append(f"{goal.title}: {note}")

            elif gid == "g_craft_seoul_typography_202610":
                signs = metrics.get("signs_documented", 3)
                target = metrics.get("target_signs", 10)
                new_signs = min(target, signs + 1)
                metrics["signs_documented"] = new_signs
                if new_signs >= target:
                    if not dry_run:
                        self.complete_goal(gid, note=f"Completed documenting {target} vintage Hangul storefront signboards across Seongsu and Euljiro.")
                    advanced_notes.append(f"{goal.title}: Completed ({target}/{target} signs)")
                else:
                    note = f"Cataloged painted enamel signboard in alley ({new_signs}/{target})."
                    if not dry_run:
                        self.record_progress(gid, note=note, event_type="progress", metrics_update=metrics)
                    advanced_notes.append(f"{goal.title}: {note}")

        return advanced_notes


goal_manager = GoalManager()
