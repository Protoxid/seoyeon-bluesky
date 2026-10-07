"""
agent/weekly_planner.py — Autonomous Weekly Life Planner for Han Seo-yeon.

Generates and maintains a persistent 7-day living itinerary (data/memory/weekly_schedule.json):
  - Every Sunday evening (or on-demand), synthesizes realistic daily rhythms for the upcoming week.
  - Covers 4 temporal phases per day: morning, afternoon, evening, deep_night.
  - Integrates her pilates instruction, ordinary errands, Seoul transit, urban walks, and quiet domestic rest.
  - Used by the Cognitive Scene Synthesizer to ground posts and photos in realistic space and time,
    favoring varied, anonymous outdoor and macro textures to avoid recurring room layout inconsistencies.
"""

from __future__ import annotations

import datetime as dt
import json
import pathlib
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional

from .config import DATA_DIR, config
from .context_engine import get_seoul_datetime

WEEKLY_SCHEDULE_FILE = DATA_DIR / "memory" / "weekly_schedule.json"


# Reliable baseline template used if LLM generation is unavailable or offline
BASELINE_SCHEDULE = {
    "monday": {
        "morning": {"activity": "teaching 07:30 and 09:00 reformer classes in Seongsu studio", "area": "Seongsu studio district", "vibe": "focused, energetic, cool morning"},
        "afternoon": {"activity": "stopping at neighborhood bakery for sourdough and walking along Seongsui-ro", "area": "Seongsu brick backstreets", "vibe": "observant, brisk breeze, dry leaves"},
        "evening": {"activity": "making simple radish and pollack soup, browsing typography monograph", "area": "flat kitchen / reading desk", "vibe": "quiet domestic ease, warm lamplight"},
        "deep_night": {"activity": "half-asleep in bed, duvet pulled up, phone screen on lowest brightness", "area": "bed in bedroom", "vibe": "sleepy, silent, late-night shadows"}
    },
    "tuesday": {
        "morning": {"activity": "personal foam roller stretching, walking through Ttukseom alleyways", "area": "Ttukseom outdoor pedestrian streets", "vibe": "quiet, fresh air, morning light"},
        "afternoon": {"activity": "subway Line 2 ride across Hangang bridge toward Euljiro print shops", "area": "Seoul Subway Line 2 elevated train car", "vibe": "rhythmic train rattle, river reflection"},
        "evening": {"activity": "dinner at small neighbourhood noodle counter, walking back past ginkgo trees", "area": "Seongsu alleyways", "vibe": "crisp autumn night, steam from kitchen doors"},
        "deep_night": {"activity": "asleep in bed, tangled in white linen, room dark and still", "area": "bed in bedroom", "vibe": "deep sleep, silence"}
    },
    "wednesday": {
        "morning": {"activity": "teaching mid-morning private reformer session, checking studio alignment ropes", "area": "pilates studio", "vibe": "patient, professional, warm wooden floor"},
        "afternoon": {"activity": "sitting with notebook outside small Seongsu cafe, sketching posture notes", "area": "small cafe outdoor bench", "vibe": "creative, observant, breeze"},
        "evening": {"activity": "organizing workout wardrobe laundry, boiling warm roasted tea", "area": "flat", "vibe": "grounded, slow domestic routine"},
        "deep_night": {"activity": "half-asleep in bed, looking through window at quiet street below", "area": "bed in bedroom", "vibe": "drowsy, resting, soft lamp glow"}
    },
    "thursday": {
        "morning": {"activity": "morning walk through Seoul Forest fringe, observing stray cats by the bench", "area": "Seoul Forest trail edge", "vibe": "peaceful, misty air, crunching fallen leaves"},
        "afternoon": {"activity": "running errands at local stationer near Konkuk University, picking up binder clips", "area": "Konkuk station sidewalk", "vibe": "bustling students, cool autumn sunshine"},
        "evening": {"activity": "watching 90s film on laptop with barley tea cooling on side table", "area": "living corner flat", "vibe": "nostalgic, cinematic, quiet darkness"},
        "deep_night": {"activity": "in bed half-asleep, pillow scrunched up, eyelids heavy", "area": "bed in bedroom", "vibe": "peaceful, warm duvet, sleep"}
    },
    "friday": {
        "morning": {"activity": "early morning private pilates client, walking past Seongsu roasteries", "area": "Yeonmujang-gil morning street", "vibe": "smell of coffee beans, brisk commute"},
        "afternoon": {"activity": "browsing vintage design posters and translated books at secondhand shop", "area": "Seongsu independent bookstore", "vibe": "smell of old paper, tactile, calm"},
        "evening": {"activity": "late light meal, listening to ambient music while stretching calves", "area": "flat wooden floor", "vibe": "weekend unwinding, physical release"},
        "deep_night": {"activity": "asleep under duvet, phone charging across room, quiet night", "area": "bed in bedroom", "vibe": "deep sleep, undisturbed"}
    },
    "saturday": {
        "morning": {"activity": "sleeping in slightly, walking down to local market for persimmons and tofu", "area": "Ttukseom traditional market street", "vibe": "unhurried, neighborhood chatter, cool air"},
        "afternoon": {"activity": "visiting small photo exhibition in converted Seongsu brick warehouse", "area": "Seongsu cultural gallery street", "vibe": "contemplative, aesthetic inspiration"},
        "evening": {"activity": "eating simple dinner, writing late-night thoughts in private notebook", "area": "kitchen table", "vibe": "introspective, quiet, settled"},
        "deep_night": {"activity": "half-asleep in bed propped on pillows, reading last few pages of novel", "area": "bed in bedroom", "vibe": "sleepy, soft pages, low warm lamp"}
    },
    "sunday": {
        "morning": {"activity": "gentle yoga mat flow at home, sunlight coming through kitchen window", "area": "flat sunlit corner", "vibe": "slow, restorative, golden morning light"},
        "afternoon": {"activity": "walking across Seongsu pedestrian bridge, watching Han River water glitter", "area": "Han River riverside promenade", "vibe": "open sky, river breeze, solitary clarity"},
        "evening": {"activity": "planning the coming week, cleaning pilates gear, quiet Sunday evening", "area": "flat desk", "vibe": "anticipation, organized, peaceful"},
        "deep_night": {"activity": "asleep early in bed, resting for Monday morning 07:30 class", "area": "bed in bedroom", "vibe": "restful sleep, clean sheets, dark room"}
    }
}


class WeeklyPlanner:
    """Manages Seo-yeon's life itinerary for spatial-temporal and scene coherence."""

    def __init__(self):
        self.schedule_file = WEEKLY_SCHEDULE_FILE

    @staticmethod
    def get_iso_week_id(date_obj: dt.date) -> str:
        year, week_num, _ = date_obj.isocalendar()
        return f"{year}-W{week_num:02d}"

    def load_schedule(self) -> Optional[Dict[str, Any]]:
        if not self.schedule_file.exists():
            return None
        try:
            return json.loads(self.schedule_file.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[WeeklyPlanner] Error reading schedule: {e}")
            return None

    def save_schedule(self, schedule_data: Dict[str, Any]) -> None:
        self.schedule_file.parent.mkdir(parents=True, exist_ok=True)
        self.schedule_file.write_text(json.dumps(schedule_data, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_or_create_schedule(self, now_kst: Optional[dt.datetime] = None, force: bool = False) -> Dict[str, Any]:
        """
        Retrieves the active schedule for the current week, or generates a fresh one
        grounded in the current season and Seoul environment.
        """
        now = now_kst or get_seoul_datetime()
        target_week_id = self.get_iso_week_id(now.date())

        existing = self.load_schedule()
        if existing and existing.get("week_id") == target_week_id and not force:
            return existing

        print(f"[WeeklyPlanner] Generating fresh weekly itinerary for {target_week_id}...")
        fresh_schedule = self._generate_schedule_with_llm(now, target_week_id)
        self.save_schedule(fresh_schedule)
        return fresh_schedule

    def get_current_activity(self, now_kst: Optional[dt.datetime] = None) -> Dict[str, str]:
        """
        Returns what Seo-yeon is doing right now based on day of week and current Seoul hour:
        { 'activity': ..., 'area': ..., 'vibe': ..., 'phase': ... }
        """
        now = now_kst or get_seoul_datetime()
        schedule_data = self.get_or_create_schedule(now)
        days_data = schedule_data.get("days", {})

        day_name = now.strftime("%A").lower()
        today_plan = days_data.get(day_name, {})

        hour = now.hour
        # Map hour to 4 planner phases
        if 7 <= hour < 12:
            phase = "morning"
        elif 12 <= hour < 18:
            phase = "afternoon"
        elif 18 <= hour < 23:
            phase = "evening"
        else:
            phase = "deep_night"

        slot = today_plan.get(phase, {})
        if not slot:
            slot = BASELINE_SCHEDULE.get(day_name, {}).get(phase, {
                "activity": "ordinary daily rhythm in Seongsu",
                "area": "Seongsu neighborhood",
                "vibe": "calm, observant"
            })

        return {
            "phase": phase,
            "activity": slot.get("activity", "ordinary life in Seongsu"),
            "area": slot.get("area", "Seongsu neighborhood"),
            "vibe": slot.get("vibe", "natural, quiet"),
            "day": day_name,
        }

    def _generate_schedule_with_llm(self, now: dt.datetime, week_id: str) -> Dict[str, Any]:
        """Prompts OpenRouter LLM to synthesize a nuanced, diverse 7-day schedule."""
        from .generator import generator

        season = "autumn" if now.month in (9, 10, 11) else "winter" if now.month in (12, 1, 2) else "spring" if now.month in (3, 4, 5) else "summer"

        prompt = (
            f"You are synthesizing the realistic weekly life itinerary for Han Seo-yeon (25-year-old pilates instructor and culture lover living alone in Seongsu-dong, Seoul).\n"
            f"Week ID: {week_id} | Season: {season} in Seoul.\n\n"
            "Generate a realistic, diverse 7-day schedule (monday through sunday) across 4 temporal slots per day:\n"
            "- 'morning' (07:00 - 12:00)\n"
            "- 'afternoon' (12:00 - 18:00)\n"
            "- 'evening' (18:00 - 23:00)\n"
            "- 'deep_night' (23:00 - 07:00) -> ALWAYS in bed: asleep, half-asleep, or resting in bed under duvet in flat.\n\n"
            "CRITICAL DESIGN RULES:\n"
            "1. Realistic Variety: Pilates classes occur 3-4 mornings/afternoons a week, NOT all day. She also does errands, walks in Seoul Forest, visits stationery/bookshops, takes Line 2 subway, cooks simple soups, cleans studio.\n"
            "2. Anonymous & Natural Environments: Favor public and outdoor locations (subway platforms, street crosswalks, alleyway red-bricks, bakery counters, park benches) so photos look diverse and authentic without recurring room layout issues.\n"
            "3. Deep Night Invariant: 'deep_night' is strictly in bed (asleep or half-asleep under duvet in dark room).\n"
            "4. Output format: Pure valid JSON matching this structure without fences:\n"
            "{\n"
            '  "week_id": "' + week_id + '",\n'
            '  "weekly_theme": "...",\n'
            '  "days": {\n'
            '    "monday": {\n'
            '      "morning": {"activity": "...", "area": "...", "vibe": "..."},\n'
            '      "afternoon": {"activity": "...", "area": "...", "vibe": "..."},\n'
            '      "evening": {"activity": "...", "area": "...", "vibe": "..."},\n'
            '      "deep_night": {"activity": "in bed asleep under duvet", "area": "bed in bedroom", "vibe": "restful, dark"}\n'
            '    },\n'
            '    ... (tuesday through sunday)\n'
            '  }\n'
            '}'
        )

        # Call OpenRouter via generator's LLM engine
        try:
            raw_text, model = generator._call_llm(
                system_prompt="You are a realistic life simulator returning strictly valid JSON.",
                user_prompt=prompt,
                max_tokens=1800
            )
            if raw_text:
                # Strip code fences if present
                clean = raw_text.strip()
                if clean.startswith("```json"):
                    clean = clean[7:]
                if clean.startswith("```"):
                    clean = clean[3:]
                if clean.endswith("```"):
                    clean = clean[:-3]
                parsed = json.loads(clean.strip())
                if "days" in parsed and "monday" in parsed["days"]:
                    parsed["week_id"] = week_id
                    parsed["generated_at"] = now.isoformat()
                    return parsed
        except Exception as e:
            print(f"[WeeklyPlanner] LLM generation failed ({e}). Using baseline itinerary.")

        return {
            "week_id": week_id,
            "generated_at": now.isoformat(),
            "weekly_theme": "Autumn routines in Seongsu, studio sessions, and quiet walks along the river",
            "days": BASELINE_SCHEDULE,
        }

    def format_schedule_summary(self, schedule_data: Optional[Dict[str, Any]] = None) -> str:
        """Formats the weekly itinerary into a human-readable agenda."""
        data = schedule_data or self.get_or_create_schedule()
        week_id = data.get("week_id", "Current Week")
        theme = data.get("weekly_theme", "Autumn routines in Seongsu")
        days = data.get("days", {})

        lines = [
            f"=== Han Seo-yeon Weekly Life Itinerary ({week_id}) ===",
            f"Theme: {theme}\n",
        ]
        phase_labels = [("morning", "07:00-12:00"), ("afternoon", "12:00-18:00"), ("evening", "18:00-23:00"), ("deep_night", "23:00-07:00")]
        for day, phases in days.items():
            lines.append(f"[{day.upper()}]")
            for phase_key, hours in phase_labels:
                slot = phases.get(phase_key, {})
                act = slot.get("activity", "ordinary Seongsu rhythm")
                area = slot.get("area", "Seongsu")
                vibe = slot.get("vibe", "calm")
                lbl = phase_key.replace("_", " ").capitalize()
                lines.append(f"  * {lbl} ({hours}): {act} [{area}] ~ {vibe}")
            lines.append("")
        return "\n".join(lines).rstrip()


weekly_planner = WeeklyPlanner()

