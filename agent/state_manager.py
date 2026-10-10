"""
agent/state_manager.py — Dynamic Cognitive State, Energy, & Social Battery Engine.

Manages Seo-yeon's internal human state:
  - Social Battery (0.0 to 1.0): Depleted by answering comments and DMs; recharged by sleep and quiet offline hours.
  - Physical Fatigue (0.0 to 1.0): Heightened right after teaching the 7:00 AM reformer class; lowest after morning rest.
  - Financial Awareness (0.0 to 1.0): Tightness around rent/studio expenses; peaks around the 25th of the month.
  - Creative Drive (0.0 to 1.0): Tendency to observe, notice details, or take candid photographs.
  - Internal Mood: Short textual description grounded in her understated, dry persona.

This ensures her restraint (NO_ACTION) feels truly biological and human rather than purely stochastic.
"""

from __future__ import annotations

import datetime as dt
import json
import pathlib
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional, Tuple

from .config import MEMORY_DIR


STATE_FILE = MEMORY_DIR / "agent_state.json"


@dataclass
class AgentState:
    social_battery: float = 0.85      # 0.0 (drained) to 1.0 (energetic/open)
    physical_fatigue: float = 0.20    # 0.0 (rested) to 1.0 (exhausted)
    financial_awareness: float = 0.40 # 0.0 (relaxed) to 1.0 (frugal/budget-conscious)
    creative_drive: float = 0.65      # 0.0 (passive) to 1.0 (observant/expressive)
    mood_descriptor: str = ""
    last_updated: str = ""
    last_consolidation_date: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class StateManager:
    def __init__(self, state_file: Optional[pathlib.Path] = None):
        self.state_file = state_file or STATE_FILE
        self._state: Optional[AgentState] = None

    def get_state(self) -> AgentState:
        if self._state is None:
            self._state = self.load_state()
        return self._state

    def load_state(self) -> AgentState:
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text(encoding="utf-8"))
                return AgentState(
                    social_battery=float(data.get("social_battery", 0.85)),
                    physical_fatigue=float(data.get("physical_fatigue", 0.20)),
                    financial_awareness=float(data.get("financial_awareness", 0.40)),
                    creative_drive=float(data.get("creative_drive", 0.65)),
                    mood_descriptor=str(data.get("mood_descriptor", "quiet, observant")),
                    last_updated=str(data.get("last_updated", "")),
                    last_consolidation_date=str(data.get("last_consolidation_date", "")),
                )
            except Exception as e:
                print(f"[StateManager] Failed to parse state file, using defaults: {e}")
        now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
        state = AgentState(last_updated=now_iso)
        self.save_state(state)
        return state

    def save_state(self, state: Optional[AgentState] = None, now=None) -> None:
        if state is not None:
            self._state = state
        cur = self._state or AgentState()
        cur.last_updated = (now or dt.datetime.now(dt.timezone.utc)).isoformat()
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        from .storage import write_json
        write_json(self.state_file, cur.to_dict())

    def update_circadian_dynamics(self, hour, day_of_month, is_raining=False, now=None):
        """Elapsed-time recovery, without inventing work, meals, or whereabouts."""
        import math
        st = self.get_state()
        now = now or dt.datetime.now(dt.timezone.utc)
        previous = dt.datetime.fromisoformat(st.last_updated) if st.last_updated else now
        if previous.tzinfo is None:
            previous = previous.replace(tzinfo=dt.timezone.utc)
        elapsed = max(0.0, (now - previous).total_seconds() / 3600)
        if elapsed == 0:
            return st
        recovery = 1 - math.exp(-elapsed / 8.0)
        st.social_battery += (0.85 - st.social_battery) * recovery
        st.physical_fatigue += (0.20 - st.physical_fatigue) * recovery
        self.save_state(st, now=now)
        return st

    def consume_interaction(self, action_type: str) -> None:
        """Depletes social battery slightly when interacting on Bluesky."""
        st = self.get_state()
        if action_type in ("REPLY_COMMENT", "BROWSE_AND_REPLY"):
            st.social_battery = max(0.05, round(st.social_battery - 0.08, 2))
        elif action_type == "ANSWER_DM":
            st.social_battery = max(0.05, round(st.social_battery - 0.12, 2))
        elif action_type in ("PUBLISH_TEXT_POST", "PUBLISH_IMAGE_POST"):
            st.social_battery = max(0.10, round(st.social_battery - 0.04, 2))
            st.creative_drive = max(0.20, round(st.creative_drive - 0.15, 2))
        elif action_type == "BROWSE_AND_LIKE":
            st.social_battery = max(0.05, round(st.social_battery - 0.01, 2))
        self.save_state(st)

    def on_master_contact(self, note=""):
        """Contact is an observation, not a predetermined emotional response."""
        return None

    def modulate_candidate_scores(self, scores: Dict[str, float]) -> Dict[str, float]:
        """
        Biases candidate scores according to current social battery & fatigue.
        When drained, NO_ACTION and quiet LIKES organically outscore heavy replies.
        """
        st = self.get_state()
        modulated = dict(scores)

        # Low social battery -> boost NO_ACTION, suppress heavy conversation
        if st.social_battery < 0.35:
            modulated["NO_ACTION"] = modulated.get("NO_ACTION", 0.3) + 0.25
            if "REPLY_COMMENT" in modulated:
                modulated["REPLY_COMMENT"] = max(0.0, modulated["REPLY_COMMENT"] - 0.15)
            if "BROWSE_AND_REPLY" in modulated:
                modulated["BROWSE_AND_REPLY"] = max(0.0, modulated["BROWSE_AND_REPLY"] - 0.25)
            if "BROWSE_AND_LIKE" in modulated:
                modulated["BROWSE_AND_LIKE"] = modulated.get("BROWSE_AND_LIKE", 0.0) + 0.10

        # High physical fatigue -> quiet restraint preferred
        if st.physical_fatigue > 0.70:
            modulated["NO_ACTION"] = modulated.get("NO_ACTION", 0.3) + 0.20
            if "PUBLISH_IMAGE_POST" in modulated:
                modulated["PUBLISH_IMAGE_POST"] = max(0.0, modulated["PUBLISH_IMAGE_POST"] - 0.20)

        # Ensure all scores remain strictly within normalized [0.0, 1.0] interval
        for k in modulated:
            modulated[k] = max(0.0, min(1.0, round(modulated[k], 3)))

        return modulated

    def format_prompt_state(self) -> str:
        st = self.get_state()
        return (
            f"- Internal Energy State: Social battery {int(st.social_battery * 100)}%, "
            f"Physical fatigue {int(st.physical_fatigue * 100)}%, "
            f"Current mindset: '{st.mood_descriptor}'."
        )


state_manager = StateManager()
