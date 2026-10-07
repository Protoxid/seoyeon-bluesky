"""
agent/context_engine.py — Real-World Environment & Temporal Context Engine for Seoul.

Provides accurate contextual information:
  - Seoul local date, time, weekday/weekend, circadian phase.
  - Real-time weather in Seoul (temperature, rain/snow, sky condition) via Open-Meteo with caching.
  - Korean seasonal and calendar context (holidays, seasons).
  - Agent recency state (hours since last post, activity today).
"""

from __future__ import annotations

import datetime as dt
import json
import pathlib
import urllib.request
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional

from .config import DATA_DIR

WEATHER_CACHE_FILE = DATA_DIR / "weather_cache.json"

# WMO Weather interpretation codes
WMO_CODES: Dict[int, str] = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "foggy",
    48: "depositing rime fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    61: "slight rain",
    63: "moderate rain",
    65: "heavy rain",
    71: "slight snow fall",
    73: "moderate snow fall",
    75: "heavy snow fall",
    80: "slight rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    95: "thunderstorm",
}


@dataclass
class WeatherSnapshot:
    temperature_c: float
    description: str
    is_raining: bool
    is_snowing: bool
    windspeed_kmh: float
    retrieved_at: str

    def summary(self) -> str:
        precip = ""
        if self.is_raining:
            precip = ", raining"
        elif self.is_snowing:
            precip = ", snowing"
        return f"{self.temperature_c:.1f}°C, {self.description}{precip}"


@dataclass
class EnvironmentContext:
    seoul_time_iso: str
    seoul_time_display: str
    date_display: str
    day_of_week: str
    is_weekend: bool
    circadian_phase: str  # dawn, morning, midday, afternoon, evening, night, deep_night
    season: str
    holiday_note: Optional[str]
    weather: WeatherSnapshot
    hours_since_last_post: float
    hours_since_last_action: float
    posts_today: int
    replies_today: int
    dms_today: int
    city_texture: str = ""
    internal_state_desc: str = ""

    def to_prompt_context(self) -> str:
        """Renders natural-language context summary for cognition and decision prompts."""
        lines = [
            f"- Seoul Time: {self.seoul_time_display} ({self.day_of_week}, {self.date_display})",
            f"- Circadian Phase: {self.circadian_phase} ({'weekend' if self.is_weekend else 'weekday'})",
            f"- Season: {self.season}",
            f"- Weather in Seoul: {self.weather.summary()}",
        ]
        if self.city_texture:
            lines.append(f"- Ambient Seoul Textures: {self.city_texture}")
        if self.holiday_note:
            lines.append(f"- Calendar / Observance: {self.holiday_note}")
        lines.append(f"- Recent Activity: last post {self.hours_since_last_post:.1f}h ago; {self.posts_today} posts today, {self.replies_today} replies today.")
        if self.internal_state_desc:
            lines.append(self.internal_state_desc)
        return "\n".join(lines)


def get_seoul_datetime() -> dt.datetime:
    """Returns the current datetime in Seoul (KST = UTC+9)."""
    utc_now = dt.datetime.now(dt.timezone.utc)
    kst_tz = dt.timezone(dt.timedelta(hours=9))
    return utc_now.astimezone(kst_tz)


def get_circadian_phase(hour: int) -> str:
    """Categorizes the hour into natural human circadian phases."""
    if 5 <= hour < 7:
        return "dawn"
    elif 7 <= hour < 12:
        return "morning"
    elif 12 <= hour < 14:
        return "midday"
    elif 14 <= hour < 18:
        return "afternoon"
    elif 18 <= hour < 22:
        return "evening"
    elif 22 <= hour or hour < 1:
        return "night"
    else:
        return "deep_night"


def get_season(month: int) -> str:
    if month in (3, 4, 5):
        return "spring"
    elif month in (6, 7, 8):
        return "summer"
    elif month in (9, 10, 11):
        return "autumn"
    else:
        return "winter"


def check_korean_holidays(date_obj: dt.date) -> Optional[str]:
    """Identifies key public holidays or cultural observances in Korea."""
    m, d = date_obj.month, date_obj.day
    fixed_holidays = {
        (1, 1): "New Year's Day (신정)",
        (3, 1): "Independence Movement Day (삼일절)",
        (5, 5): "Children's Day (어린이날)",
        (6, 6): "Memorial Day (현충일)",
        (8, 15): "National Liberation Day (광복절)",
        (10, 3): "National Foundation Day (개천절)",
        (10, 9): "Hangul Day (한글날)",
        (12, 25): "Christmas Day (크리스마스)",
    }
    if (m, d) in fixed_holidays:
        return fixed_holidays[(m, d)]
    # Early October Chuseok / autumn break season note
    if m == 10 and 1 <= d <= 5:
        return "Early October autumn holidays / brisk autumn transition"
    return None


def fetch_seoul_weather() -> WeatherSnapshot:
    """Fetches real-time weather for Seoul via Open-Meteo with local file cache."""
    now_utc = dt.datetime.now(dt.timezone.utc)

    # Check cache (valid for 60 minutes)
    if WEATHER_CACHE_FILE.exists():
        try:
            cached_data = json.loads(WEATHER_CACHE_FILE.read_text(encoding="utf-8"))
            cached_time = dt.datetime.fromisoformat(cached_data["retrieved_at"])
            if (now_utc - cached_time).total_seconds() < 3600:
                return WeatherSnapshot(**cached_data)
        except Exception:
            pass

    # Fetch from Open-Meteo (lat: 37.5665, lon: 126.9780 - Central Seoul)
    url = "https://api.open-meteo.com/v1/forecast?latitude=37.5665&longitude=126.9780&current_weather=true"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SeoYeonAgent/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            cw = data.get("current_weather", {})
            temp = float(cw.get("temperature", 18.0))
            code = int(cw.get("weathercode", 0))
            wind = float(cw.get("windspeed", 5.0))

            desc = WMO_CODES.get(code, "clear")
            is_rain = code in (51, 53, 55, 61, 63, 65, 80, 81, 82, 95)
            is_snow = code in (71, 73, 75)

            snapshot = WeatherSnapshot(
                temperature_c=temp,
                description=desc,
                is_raining=is_rain,
                is_snowing=is_snow,
                windspeed_kmh=wind,
                retrieved_at=now_utc.isoformat(),
            )

            DATA_DIR.mkdir(parents=True, exist_ok=True)
            WEATHER_CACHE_FILE.write_text(json.dumps(asdict(snapshot), indent=2), encoding="utf-8")
            return snapshot
    except Exception as e:
        # Fallback if network or API error
        return WeatherSnapshot(
            temperature_c=18.0,
            description="clear autumn weather",
            is_raining=False,
            is_snowing=False,
            windspeed_kmh=6.0,
            retrieved_at=now_utc.isoformat(),
        )


def build_environment_context(
    hours_since_last_post: float = 8.0,
    hours_since_last_action: float = 3.0,
    posts_today: int = 0,
    replies_today: int = 0,
    dms_today: int = 0,
) -> EnvironmentContext:
    """Builds a complete, rich EnvironmentContext snapshot."""
    now_kst = get_seoul_datetime()
    weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekday_str = weekday_names[now_kst.weekday()]
    is_weekend = now_kst.weekday() in (5, 6)
    circadian = get_circadian_phase(now_kst.hour)
    season = get_season(now_kst.month)
    holiday = check_korean_holidays(now_kst.date())
    weather = fetch_seoul_weather()

    # Dynamic ambient Seoul city micro-texture
    city_texture = "October in Seongsu: fallen yellow ginkgo fan-leaves on brick tiles, roasted barley tea steaming on the small counter, quiet circular rumble of Subway Line 2."

    # Update cognitive state & energy dynamics
    try:
        from .state_manager import state_manager
        state_manager.update_circadian_dynamics(now_kst.hour, now_kst.day, is_raining=weather.is_raining)
        state_desc = state_manager.format_prompt_state()
    except Exception:
        state_desc = ""

    return EnvironmentContext(
        seoul_time_iso=now_kst.isoformat(),
        seoul_time_display=now_kst.strftime("%H:%M KST"),
        date_display=now_kst.strftime("%Y-%m-%d"),
        day_of_week=weekday_str,
        is_weekend=is_weekend,
        circadian_phase=circadian,
        season=season,
        holiday_note=holiday,
        weather=weather,
        hours_since_last_post=hours_since_last_post,
        hours_since_last_action=hours_since_last_action,
        posts_today=posts_today,
        replies_today=replies_today,
        dms_today=dms_today,
        city_texture=city_texture,
        internal_state_desc=state_desc,
    )
