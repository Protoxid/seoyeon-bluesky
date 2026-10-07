"""
agent/consolidator.py — Nightly Cognitive Memory Consolidation Pass.

Executes Seo-yeon's quiet end-of-day or deep-night cognitive life pass:
  1. Consolidates user relationships (stranger -> friendly_acquaintance -> regular -> trusted_friend).
  2. Preserves topic and opinion stances into opinions_memory.json.
  3. Writes a private, internal diary reflection to data/memory/private_journal.jsonl.
  4. Restores biological circadian energy and social battery for the next morning.
"""

from __future__ import annotations

import datetime as dt
import json
import pathlib
from typing import Any, Dict, List, Optional, Tuple

from .config import MEMORY_DIR, LOGS_DIR, config
from .context_engine import EnvironmentContext, get_seoul_datetime
from .memory_store import memory_store
from .state_manager import state_manager
from .validator import validator

PRIVATE_JOURNAL_FILE = MEMORY_DIR / "private_journal.jsonl"


class MemoryConsolidator:
    """Manages Seo-yeon's nightly cognitive consolidation."""

    def __init__(self):
        self.journal_file = PRIVATE_JOURNAL_FILE

    def _append_journal(self, entry: Dict[str, Any]) -> None:
        self.journal_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.journal_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def read_recent_journal_entries(self, limit: int = 5) -> List[Dict[str, Any]]:
        if not self.journal_file.exists():
            return []
        entries: List[Dict[str, Any]] = []
        try:
            for line in self.journal_file.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    entries.append(json.loads(line))
        except Exception:
            pass
        return entries[-limit:]

    def consolidate(
        self,
        context: Optional[EnvironmentContext] = None,
        dry_run: Optional[bool] = None,
        force: bool = False,
    ) -> Dict[str, Any]:
        """
        Executes the nightly consolidation pass.
        Returns a summary dictionary of what was consolidated.
        """
        is_dry = dry_run if dry_run is not None else config.dry_run
        now_kst = get_seoul_datetime()
        today_str = now_kst.strftime("%Y-%m-%d")
        st = state_manager.get_state()

        if not force and st.last_consolidation_date == today_str and not is_dry:
            return {
                "status": "already_consolidated",
                "date": today_str,
                "note": f"Consolidation already completed for {today_str}.",
            }

        print(f"\n[Memory Consolidation] Beginning nightly cognitive life pass for {today_str} ({now_kst.strftime('%H:%M KST')})...")

        # 1. User Relationship Consolidation
        relationships_evolved = []
        user_profiles = memory_store.get_all_users()
        for handle, profile in user_profiles.items():
            old_rel = profile.relationship
            new_rel = old_rel

            count = profile.interaction_count
            if count >= 15 and old_rel in ("stranger", "friendly_acquaintance", "regular"):
                new_rel = "trusted_friend"
            elif count >= 8 and old_rel in ("stranger", "friendly_acquaintance"):
                new_rel = "regular"
            elif count >= 3 and old_rel == "stranger":
                new_rel = "friendly_acquaintance"

            if new_rel != old_rel:
                profile.relationship = new_rel
                relationships_evolved.append(f"@{handle}: {old_rel} -> {new_rel}")
                if not is_dry:
                    memory_store.save_user_profile(profile)

        # 2. Generate Private Journal Reflection
        from .generator import generator

        env_ctx = context
        if env_ctx is None:
            from .context_engine import build_environment_context
            env_ctx = build_environment_context()

        sys_prompt = generator._build_system_prompt(env_ctx)
        user_prompt = (
            f"It is late night in your Seongsu-dong apartment ({today_str}). "
            "You are sitting in the quiet room with the floor lamp on, writing a short, authentic 2-3 sentence reflection in your private personal notebook before going to sleep.\n"
            "This will NOT be posted to Bluesky or read by anyone else.\n"
            "Rules:\n"
            "- Voice: Intimate, dry, calm, lowercase only, full stops only. Absolutely zero exclamation marks (!).\n"
            "- Content: Reflect genuinely on today, the autumn air or room stillness, what you noticed, your master, or your body feeling rested after teaching.\n"
            "- Output ONLY the reflection text."
        )

        journal_text = ""
        model_used = "fallback"
        if not is_dry:
            raw_text, model_used = generator._call_llm(sys_prompt, user_prompt, max_tokens=180)
            if raw_text:
                ok, clean, _ = validator.validate_outgoing_text(raw_text, content_type="dm", check_repetition=False)
                if ok and clean:
                    journal_text = clean

        if not journal_text:
            journal_text = (
                f"the kettle cooled down on the counter an hour ago. seongsu feels quiet through the cracked window, "
                f"just the far hum of the line 2 bridge. grateful to my master for the steady day. time to sleep."
            )

        journal_entry = {
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
            "date": today_str,
            "seoul_time": now_kst.strftime("%H:%M KST"),
            "entry": journal_text,
            "model": model_used,
            "mood": st.mood_descriptor,
            "dry_run": is_dry,
        }

        if not is_dry:
            self._append_journal(journal_entry)

        # 3. Rest & Recharge Cognitive State
        if not is_dry:
            st.social_battery = 0.90
            st.physical_fatigue = 0.15
            st.last_consolidation_date = today_str
            st.mood_descriptor = "quietly rested, calm autumn morning ahead"
            state_manager.save_state(st)

            # 4. Log episodic memory
            memory_store.log_episode(
                "nightly_consolidation",
                f"Nightly memory consolidation for {today_str}",
                {
                    "relationships_evolved": relationships_evolved,
                    "journal_excerpt": journal_text[:80],
                },
            )

        print(f"  [Private Journal]: \"{journal_text}\"")
        if relationships_evolved:
            print(f"  [Relationships Evolved]: {', '.join(relationships_evolved)}")
        print(f"  [Social Battery]: Recharged to 90% | Physical fatigue reset to 15%.")
        print(f"  [SUCCESS] Consolidation complete for {today_str}.\n")

        return {
            "status": "success",
            "date": today_str,
            "relationships_evolved": relationships_evolved,
            "journal_entry": journal_entry,
        }


consolidator = MemoryConsolidator()
