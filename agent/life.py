"""Her fictional everyday life: a loose sketch of today plus a log of what she has said happened.

The operator decided (2026-11-11) that Seo-yeon may describe ordinary fictional experiences as her own,
provided they stay consistent. This module supplies that consistency:

- ``today()`` returns a loose, model-written sketch of plausible things in her day. It is regenerated
  per Seoul date, varies with weekday, weather and her ongoing life threads, and is explicitly
  "possibilities, not a schedule": nothing here obliges a post or a particular time.
- ``record()`` appends what she actually published about her own life, so later posts do not
  contradict earlier ones (the same dinner cannot happen twice, a finished module stays finished).

Everything here is fictional character continuity. It never describes real people, real meetings with
real Bluesky users, real purchases from named businesses, or professional credentials.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from .runtime import MODE
from .storage import file_lock, read_json, write_json

# Authored threads drawn from CANON.md. The day sketch may append short progress notes to them.
SEED_THREADS = [
    {"id": "pilates", "about": "retraining as a pilates instructor: course modules, anatomy study, practice teaching, "
                                "how cueing feels in her mouth, sore muscles, comparing herself with classmates"},
    {"id": "back", "about": "the old back injury that brought her to pilates; mostly a background fact now, "
                             "worth mentioning only on a genuinely bad day, not a daily check-in"},
    {"id": "money", "about": "living on limited savings after quitting marketing; rent, groceries, small splurges she weighs"},
    {"id": "after_marketing", "about": "leaving corporate marketing in january; what she misses and what she doesn't"},
    {"id": "jieun", "about": "jieun, a longtime friend (fictional); occasional meals, messages, being a practice client"},
    {"id": "family", "about": "family in daegu and busan; calls with her mother, holidays, being asked about her plans"},
    {"id": "home", "about": "living alone in seongsu-dong since january; small kitchen, cooking for one, the neighbourhood"},
    {"id": "culture", "about": "films, books, music and things she notices in the city; design and lettering when they catch her eye"},
]

MAX_LOG = 80
MAX_NOTES = 6


class LifeJournal:
    def __init__(self, path=None):
        self.checkpoint = lambda: None
        if path is None:
            from .vault import vault
            path = vault.vault_dir / "life.json"
            self.checkpoint = vault.save_vault
        self.path = Path(path)

    def load(self):
        data = read_json(self.path, {})
        data.setdefault("threads", [dict(t, notes=[]) for t in SEED_THREADS])
        data.setdefault("days", {})
        data.setdefault("log", [])
        return data

    def recent_log(self, days=7):
        cutoff = (dt.date.today() - dt.timedelta(days=days)).isoformat()
        return [e for e in self.load()["log"] if e.get("date", "") >= cutoff][-15:]

    def record(self, date, text, *, kind="post", uri=""):
        """Store what she published about her life so later posts stay consistent."""
        if not text:
            return
        with file_lock(self.path):
            data = self.load()
            data["log"].append({"date": date, "kind": kind, "text": text[:400], "uri": uri})
            data["log"] = data["log"][-MAX_LOG:]
            write_json(self.path, data)
        self.checkpoint()

    def today(self, context, generator=None):
        """Loose sketch of her fictional day; generated once per Seoul date, empty offline."""
        date = context.date_display
        data = self.load()
        if date in data["days"]:
            return data["days"][date]
        if MODE.get() == "offline":
            return {}
        if generator is None:
            from .generator import generator
        from .generator import parse_json_object
        from .memory_store import memory_store
        raw, _ = generator._call_llm(
            "You keep continuity for Han Seo-yeon, an openly fictional character (26, seongsu-dong, seoul) who left "
            "corporate marketing in january and is retraining as a pilates instructor on limited savings. "
            "Sketch a plausible, ordinary day for her today as loose possibilities, not a schedule. "
            "Use the weekday, season, weather and her ongoing life threads; let threads progress slowly and realistically "
            "(a course moves module by module, money stays tight, the back has good and bad days). "
            "Most days are unremarkable: errands, study, a class, cooking, a walk, a call, a film at home. "
            "Do not repeat the same events as recent days. No real named businesses, no real public figures, "
            "no real Bluesky users, no credentials or clients. "
            "Return JSON {moments:[{when:string,what:string}],mood:string,thread_notes:[{id:string,note:string}]}. "
            "2-5 moments in plain lowercase phrases; mood is a few words; thread_notes only when something genuinely moved. "
            "Output ONLY the raw JSON object.",
            json.dumps({
                "today": {"date": date, "weekday": context.day_of_week, "season": context.season,
                           "weather": context.weather.summary(), "phase": context.circadian_phase},
                "identity": memory_store.format_identity_prompt(),
                "threads": data["threads"],
                "recent_days": {d: data["days"][d] for d in sorted(data["days"])[-4:]},
                "what_she_already_posted": self.recent_log(),
            }, ensure_ascii=False),
            max_tokens=500,
        )
        try:
            sketch = parse_json_object(raw)
        except (ValueError, TypeError):
            return {}
        if not isinstance(sketch, dict) or not isinstance(sketch.get("moments"), list):
            return {}
        moments = [m for m in sketch["moments"] if isinstance(m, dict) and isinstance(m.get("what"), str)][:5]
        day = {"moments": [{"when": str(m.get("when", ""))[:40], "what": m["what"][:200]} for m in moments],
               "mood": str(sketch.get("mood", ""))[:80]}
        with file_lock(self.path):
            data = self.load()
            notes = sketch.get("thread_notes") if isinstance(sketch.get("thread_notes"), list) else []
            by_id = {t["id"]: t for t in data["threads"]}
            for n in notes:
                if isinstance(n, dict) and n.get("id") in by_id and isinstance(n.get("note"), str):
                    thread = by_id[n["id"]]
                    thread["notes"] = (thread.get("notes", []) + [f"{date}: {n['note'][:200]}"])[-MAX_NOTES:]
            data["days"][date] = day
            data["days"] = dict(sorted(data["days"].items())[-14:])
            write_json(self.path, data)
        self.checkpoint()
        return day

    def prompt_data(self, context, generator=None):
        """Public, fictional life context for drafting her own posts and choosing scenes."""
        data = self.load()
        return {
            "note": "fictional character continuity; possibilities for today, not a schedule or obligation",
            "today": self.today(context, generator),
            "threads": [{"id": t["id"], "about": t["about"], "recent": t.get("notes", [])[-2:]} for t in data["threads"]],
            "already_said_recently": self.recent_log(),
        }


life = LifeJournal.__new__(LifeJournal)


def journal():
    """Lazily bound journal so offline/preview isolation is established before the vault path is read."""
    if not getattr(life, "path", None):
        LifeJournal.__init__(life)
    return life
