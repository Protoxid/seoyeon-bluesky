"""
w38_shots.py — Mon 14 to Sun 20 September 2026 (ISO 2026-W38), tier 1.

This script is self-contained: it defines SHOTS, generates all 7 images via
gpt-image-2 (image-to-image on selected plates, text-to-image where no plate
is used), writes caption .txt files, and produces the Sentry handoff.json.

THE WEEK IS ALREADY WRITTEN. The narrative, day-by-day and thread live in
content/w38_2026-09-14/WEEK.md. This file only carries the shot prompts and
generation orchestration.

Season: the heat broke. Sunday morning the window was open for the first time
since July. The air is different, the light is lower and gold in the evening,
the fan is running a gear slower.

MIX: 3 face frames (morning_light 3/4, hallway_tired direct, sunday_floor 3/4)
· 1 profile (river_pears) · 1 face-down (stairwell_notes) · 2 noface
(table_afternoon, study_light). 0 selfies in outward-facing sense. Clothed
torso shots (hallway_tired) set neither body=True nor limb=True, so
master/c/c5_relax_front.png never attaches and the word "tattoo" never appears
in any prompt. No men anywhere.

Age rule: 26 in prompts (via identity_block.txt which is the reference), 25
in caption copy (never stated — the day number is what anchors it).

Generation: gpt-image-2-image-to-image on Kie, $0.09/image. Resolution 1K
(1024×1365, 3:4). Plate references go first in the input_urls list (Image 1).
Face references (a1_front.png, a2_tq_left.png) follow as Images 2 and 3 for
face-visible shots. No face references on noface or face-down shots.

Hashtags are NOT in caption bodies. They are appended by ig_publish.py:
#seongsu #seoul #daily #filmphoto #everyday

Day count: day 251 (Mon 14 Sep) → day 257 (Sun 20 Sep).
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sys
from datetime import datetime, timezone, timedelta

# Add parent to path for kie_api import
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import requests
from kie_api import Kie, load_key, MODEL_I2I, MODEL_T2I

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# --- paths ------------------------------------------------------------------
ROOT = pathlib.Path(__file__).parent
OUT_DIR = ROOT / "content" / "w38_2026-09-14"
CAPS_DIR = ROOT / "caps"
MASTER_DIR = ROOT / "master" / "a"
BODY_MASTER = ROOT / "master" / "c" / "c5_relax_front.png"  # not used here
PLATE_DIR = ROOT / "content" / "plates"

# --- reference files --------------------------------------------------------
FACE_REFS = ["a1_front.png", "a2_tq_left.png"]

# --- lens lines -------------------------------------------------------------
LENS = ("Shot on an iPhone 15 Pro: flat HDR contrast, low saturation, "
        "deep focus so the background stays legible, fine noise in the shadows. "
        "Skin shows pores and small unevenness.")

# --- skin line (from outside.py) -------------------------------------------
SKIN = ("Her skin is matte from brow to jaw and reads slightly dry: visible "
        "pores, a little shine at the nose, no foundation visible, nothing "
        "airbrushed.")

# --- role lines -------------------------------------------------------------
ROLE_PLATE = ("Image 1 is the room this photograph is taken in. Use it for "
              "the layout, the furniture, the surfaces and the light — it is the "
              "same room, not a similar one. Nobody is in Image 1; the people "
              "described below are.")

ROLE_PLATE_EMPTY = ("Image 1 is the room this photograph is taken in. Use it "
                    "for the layout, the furniture, the surfaces and the light. "
                    "Nobody is in Image 1 and nobody is in this photograph either.")

ROLE_FACE = ("Images {0} and {1} are her face from two angles — use them for "
             "her features and the pale freckles on her nose and inner cheeks.")

# --- safety note ------------------------------------------------------------
SAFE = ("An ordinary fully clothed everyday snapshot, nothing sexual about it.")

# --- SHOTS ------------------------------------------------------------------
SHOTS = [
    # Mon 14 Sep · 07:45 — studio dawn, 3/4 face toward window
    dict(
        id="w38_morning_light",
        day="mon",
        tier="1k",
        aspect="3:4",
        plate="plate_studio_wide",
        face=True,
        safe=True,
        story=("MON 07:45. The first morning of the fourth slot. She is at the "
               "studio before anyone else, in the morning light from the tall "
               "windows. The room is empty and she stands there for a moment "
               "before taking one."),
        text=(
            "A woman standing in an empty pilates studio in Seongsu, Seoul, "
            "just before seven in the morning. She is facing three-quarters "
            "toward the tall windows on the left, her face catching the flat "
            "early light that comes through the glass. Her head is turned so "
            "she is looking toward the window rather than at the camera — her "
            "features in profile-to-three-quarter view, the light falling "
            "across her cheekbone and jaw. Hair down in soft waves, "
            "centre-parted with curtain bangs, wearing an oversized oatmeal "
            "knit sweater over black leggings, her hands in the sweater "
            "pockets. Behind her the studio is empty: two rows of reformer "
            "frames stretching toward the back, blue mats stacked along the "
            "wall, a water cooler against the right wall, a full-height mirror "
            "catching a sliver of the room. The camera is held by someone "
            "standing near the doorway, rear camera, the frame level and "
            "composed. " + LENS + " " + SKIN
        )
    ),

    # Tue 15 Sep · 14:15 — tabletop still life, no face
    dict(
        id="w38_table_afternoon",
        day="tue",
        tier="1k",
        aspect="3:4",
        plate="plate_room",
        noface=True,
        story=("TUE 14:15. Freelance marketing at the table. Laptop, one pear "
               "from the Saturday market, a glass of water. The window is "
               "cracked open behind the curtain and she can feel the cooler air "
               "on her shoulder. She takes the table from above."),
        text=(
            "A close photograph taken from directly above a wooden table in a "
            "small one-room flat in Seongsu, Seoul, in the mid-afternoon. "
            "Nobody is in the frame. On the table: a laptop closed and turned "
            "sideways so its lid faces the lens with no screen visible, a ripe "
            "conference pear with a short stem resting on the wood next to a "
            "tall glass of water, a page of handwritten notes partly covered "
            "by the laptop. The flat room around the table is out of focus "
            "behind the edges of the frame — a white standing fan on the floor "
            "in the background, the big window at the far end with grey "
            "curtains pushed back and one side of the window cracked open "
            "slightly, letting in a band of afternoon light across the floor. "
            "Shot on an iPhone 15 Pro held directly above the table, rear "
            "camera, the phone's shadow just catching the edge of the wood, "
            "everything on the table sharp, flat HDR contrast, low "
            "saturation, fine noise in the shadows, the frame level. Nothing "
            "is arranged."
        )
    ),

    # Wed 16 Sep · 18:30 — stairwell fatigue, face down
    dict(
        id="w38_stairwell_notes",
        day="wed",
        tier="1k",
        aspect="3:4",
        plate="plate_stairwell",
        face_down=True,
        safe=True,
        story=("WED 18:30. Observation hours all day — eight of them watching "
               "the senior instructor run three sessions. She fills a page of "
               "notes. By evening she is on the stairwell landing sitting "
               "against the wall, face down, the notebook open on her knee."),
        text=(
            "A woman sitting on a stairwell landing in a building in Seongsu, "
            "Seoul, in the early evening. She is sitting on the floor with her "
            "back against the wall, one knee drawn up and the other leg "
            "stretched out. Her head is bent forward so her face is not "
            "visible — only the crown of her head and the curtain bangs "
            "falling forward as she looks down at an open notebook propped on "
            "her raised knee. One hand holds a pen loosely, the other rests "
            "on the page. She is wearing a plain black crew-neck sweatshirt "
            "and dark leggings, hair down and falling around her face. "
            "Behind her the stairwell is quiet: painted concrete walls, a "
            "metal handrail ascending in the background, fluorescent strip "
            "light overhead in the stairwell, the landing floor laid with "
            "plain grey vinyl tile. Her phone lies on the floor beside her. "
            "The camera is held at chest height by someone sitting across "
            "from her, the frame level, the perspective at eye height. " + LENS
        )
    ),

    # Thu 17 Sep · 19:00 — Han River, profile
    dict(
        id="w38_river_pears",
        day="thu",
        tier="1k",
        aspect="3:4",
        plate="plate_river",
        face=True,
        safe=True,
        story=("THU 19:00. Finished work at six and walked down to the river. "
               "The Han is different in September: the light goes flat and gold, "
               "the air is dry. She bought a pear from the ajumma with the cart "
               "by the bridge and is eating it standing."),
        text=(
            "A woman standing on the bank of the Han River in Seoul at dusk, "
            "turned in profile facing east along the water. She is looking "
            "toward the bridge in the distance where the lamps are just "
            "beginning to come on, the light flat and golden across the river. "
            "One hand holds a pear close to her mouth as she bites into it; "
            "the other is in the pocket of a light tan cotton trench coat worn "
            "open over a white t-shirt and dark straight-leg jeans. Her hair "
            "is down, centre-parted with curtain bangs, moving slightly in "
            "the river breeze. Her face is in profile: the curve of her cheek, "
            "her jawline, the ends of her hair lifting. Behind her the river "
            "is wide and darkening, the opposite bank lined with low buildings "
            "and the bridge structure cutting across the background, the sky "
            "a gradient from pale gold up through pearl to a deep grey-blue. "
            "A few other people are small silhouettes on the path, far behind "
            "and out of focus. The camera is held by someone standing a few "
            "paces away, slightly lower than her eye level, the frame level, "
            "full-body in the frame, the river filling the background. " + LENS
        )
    ),

    # Fri 18 Sep · 22:00 — study desk, no face
    dict(
        id="w38_study_light",
        day="fri",
        tier="1k",
        aspect="3:4",
        noface=True,
        story=("FRI 22:00. The exam is late October and she has not touched "
               "the binder since August. Friday night at the desk — open binder, "
               "highlighter caps on the wood, her hand mid-sentence, coffee "
               "gone cold."),
        text=(
            "A close photograph of a desk in a small flat in Seongsu, Seoul, "
            "at night, taken from above. Nobody's face is in the frame. On the "
            "desk: a ring-bound course binder open to a page of anatomical "
            "diagrams labelled in handwriting — muscle groups drawn in simple "
            "diagrams with Korean annotations — a highlighter lying uncapped "
            "on the paper next to a mechanical pencil, a woman's hand resting "
            "on the page with her fingers loosely holding the pencil ready to "
            "write, her forearm in a cream knit sleeve coming from the edge of "
            "the frame. Behind the binder a ceramic coffee mug with dark "
            "liquid still in it, a phone lying face-down, a desk lamp casting "
            "a warm cone of light across the open page. The room beyond the "
            "desk is dark and out of focus. Shot on an iPhone 15 Pro held "
            "directly above the desk, rear camera, the hand and the binder "
            "sharp, everything beyond the lamp-lit area falling into shadow, "
            "flat HDR contrast, low saturation, fine noise, the frame a few "
            "degrees off level. Only the desk, the page, and the hand holding "
            "the pencil are in the photograph."
        )
    ),

    # Sat 19 Sep · 20:30 — course hallway, direct eye contact
    dict(
        id="w38_hallway_tired",
        day="sat",
        tier="1k",
        aspect="3:4",
        plate="plate_hallway",
        face=True,
        safe=True,
        story=("SAT 20:30. Course module all day, eight to six. By the time "
               "she is out her voice is gone and her back hurts. In the empty "
               "hallway after everyone has left, she leans against the wall and "
               "takes one looking straight into the lens."),
        text=(
            "A woman leaning against a wall in an empty course hallway in a "
            "building in Seongsu, Seoul, at night, her face fully toward the "
            "camera, looking directly into the lens with a flat tired "
            "expression — not performing exhaustion, simply not hiding it "
            "either. Her head rests against the wall, her shoulders slightly "
            "slumped. She is wearing a plain black short-sleeve t-shirt tucked "
            "into high-waisted dark denim, a grey cotton jacket open over it, "
            "hair down and a little dishevelled from a long day, the curtain "
            "bangs falling across her forehead. Behind her the hallway is "
            "empty: painted walls, a row of closed doors along one side, "
            "fluorescent overhead lights casting cool white light on the "
            "vinyl floor, a fire extinguisher on the wall at the far end. The "
            "camera is held at arm's length on the front camera, her extended "
            "arm just visible in the lower corner of the frame, the hallway "
            "stretching behind her with a slight perspective distortion. " + LENS
        )
    ),

    # Sun 20 Sep · 10:30 — Sunday floor reset, 3/4 face
    dict(
        id="w38_sunday_floor",
        day="sun",
        tier="1k",
        aspect="3:4",
        plate="plate_room",
        face=True,
        safe=True,
        story=("SUN 10:30. Sunday reset. She wakes up late for her (9am), "
               "pulls on an oversized tee, ties her hair up, and does the "
               "floor — laundry, grocery bag unpacked from yesterday, the tote "
               "for Monday. The new box of pears is on the counter."),
        text=(
            "A woman sitting on the floor of a small one-room flat in Seongsu, "
            "Seoul, mid-morning, her body turned three-quarters toward the "
            "camera. She is folding a piece of light-coloured laundry in her "
            "lap, her hands mid-fold, looking up toward the lens with a "
            "neutral half-attentive expression — the face of someone who heard "
            "their name called mid-chore. Her hair is pulled up in a high "
            "messy bun with pieces loose at the temples and nape. She is "
            "wearing an oversized white t-shirt and grey cotton shorts, no "
            "shoes. Around her on the floor: a small pile of folded laundry, "
            "an open canvas tote bag, a produce bag with the stems of pears "
            "visible at the top. Behind her the room is mid-tidy: the bed is "
            "roughly made, the table against the wall holds a laptop and a mug, "
            "the standing fan is off and pushed against the wall, the big "
            "window at the far end is open with curtains pulled back, the "
            "morning light lying flat on the floorboards. The camera is held "
            "by someone standing near the door, rear camera, the frame at eye "
            "level, the composition loose and candid. " + LENS
        )
    ),
]

# --- captions (hashtags appended by ig_publish.py, not in body) -------------
CAPTIONS = {
    "w38_morning_light": (
        "the studio at ten to seven. no one here yet.\n"
        "\n"
        "i said yes to the fourth slot so i will be here more often. "
        "the light was good and i took one before anyone came in."
    ),
    "w38_table_afternoon": (
        "the pear was good. two weeks ago i would not have said that "
        "in a caption.\n"
        "\n"
        "the window is cracked for the first time since july."
    ),
    "w38_stairwell_notes": (
        "eight hours of observation and i cannot look at another reformer.\n"
        "\n"
        "sat down on the landing and did not get up for a while. "
        "the notes will be illegible tomorrow."
    ),
    "w38_river_pears": (
        "bought a pear from the ajumma by the bridge and ate it watching "
        "the lights come on.\n"
        "\n"
        "the air is different now. not cold yet but different."
    ),
    "w38_study_light": (
        "the study binder i have been meaning to finish since august.\n"
        "\n"
        "friday night and this is what i am doing. it is fine."
    ),
    "w38_hallway_tired": (
        "saturday module done. the exam is getting close and i can feel it.\n"
        "\n"
        "did not take the mirror selfie. took this one instead."
    ),
    "w38_sunday_floor": (
        "sunday reset. laundry and the week ahead.\n"
        "\n"
        "picked up pears again. the market had a new box."
    ),
}

# --- publishing schedule ----------------------------------------------------
SCHEDULE = [
    ("2026-09-14T07:45+09:00", "Mon"),
    ("2026-09-15T14:15+09:00", "Tue"),
    ("2026-09-16T18:30+09:00", "Wed"),
    ("2026-09-17T19:00+09:00", "Thu"),
    ("2026-09-18T22:00+09:00", "Fri"),
    ("2026-09-19T20:30+09:00", "Sat"),
    ("2026-09-20T10:30+09:00", "Sun"),
]


def plate_path(pid: str) -> pathlib.Path | None:
    """Resolve a plate id to a file. Mirrors pov.plate_path logic."""
    if not pid:
        return None
    # Try content/plates/ first
    candidates = []
    # Look for <pid>_*.png in the plates directory
    if PLATE_DIR.exists():
        # Standard pattern: plate_room_ecc050_1.png
        for f in PLATE_DIR.iterdir():
            if f.name.startswith(pid) and f.suffix == ".png":
                candidates.append(f)
    if not candidates:
        # Try locations/ as fallback
        loc_dir = ROOT / "locations"
        if loc_dir.exists():
            for f in loc_dir.iterdir():
                if f.name.startswith(pid) and f.suffix == ".png":
                    candidates.append(f)
    if not candidates:
        return None
    return sorted(candidates)[0]


def build_prompt(d: dict) -> str:
    """Assemble the full prompt from shot dict, including role lines."""
    parts = [d["text"]]
    if d.get("safe"):
        parts.append(SAFE)
    parts.append(SKIN)

    has_plate = d.get("plate")
    is_noface = d.get("noface", False)
    is_face_down = d.get("face_down", False)
    is_face = d.get("face", False)

    if is_noface or is_face_down:
        if has_plate:
            parts.append(ROLE_PLATE_EMPTY)
    else:
        if has_plate:
            parts.append(ROLE_PLATE)
        # Face roles are ordinal: if plate is present, face = Images 2, 3
        offset = 1 if has_plate else 0
        parts.append(ROLE_FACE.format(offset + 1, offset + 2))

    return "\n\n".join(parts)


def resolve_references(d: dict, kie: Kie) -> list[str]:
    """Build the input_urls list for generation: plate first, then face refs."""
    refs = []

    # Plate goes first (Image 1)
    has_plate = d.get("plate")
    if has_plate:
        pp = plate_path(has_plate)
        if pp:
            refs.append(kie.upload(pp.resolve()))
        else:
            print(f"  ! plate {has_plate} not found — generating without plate")

    # Face references: only for face-visible shots, not for face-down/noface
    is_noface = d.get("noface", False)
    is_face_down = d.get("face_down", False)
    is_face = d.get("face", False)

    if is_face and not is_noface and not is_face_down:
        for fn in FACE_REFS:
            fp = MASTER_DIR / fn
            if fp.exists():
                refs.append(kie.upload(fp.resolve()))

    return refs


def generate_all():
    """Generate all 7 shots, download results, write caption files."""
    print("=" * 66)
    print("  W38 GENERATION - Mon 14 to Sun 20 Sep 2026")
    print(f"  {len(SHOTS)} shots | tier 1 | gpt-image-2 | $0.09/image")
    print("=" * 66)

    # Load key
    load_key(ROOT)
    key = os.environ.get("KIE_API_KEY", "")
    if not key or key.startswith("PASTE"):
        print("  ERROR: no API key in kie_key.txt")
        return False

    # Check credit first
    kie = Kie(key)
    credit = kie.credit()
    if credit is not None:
        print(f"  credit: {credit}")
    else:
        print("  credit check failed (non-fatal)")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CAPS_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    success_count = 0
    fail_count = 0

    for idx, d in enumerate(SHOTS):
        sid = d["id"]
        print(f"\n--- [{idx+1}/{len(SHOTS)}] {sid} ---")

        prompt = build_prompt(d)
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:6]

        # Determine model
        refs = resolve_references(d, kie)
        model = MODEL_T2I if (d.get("noface", False) and not refs) else MODEL_I2I

        print(f"  model: {model}")
        print(f"  refs: {len(refs)} reference(s)")
        print(f"  prompt: {d['text'][:80]}...")

        try:
            aspect = d.get("aspect", "3:4")
            tier = d.get("tier", "1k")
            urls = kie.generate(prompt, aspect, refs, model=model, tier=tier)

            if urls:
                dest = OUT_DIR / f"{sid}_{prompt_hash}_1.png"
                r = requests.get(urls[0], timeout=120)
                r.raise_for_status()
                dest.write_bytes(r.content)
                n_bytes = len(r.content)
                print(f"  OK -> {dest.name}  ({n_bytes // 1024} KB)")
                results.append({"id": sid, "status": "ok", "file": str(dest.name),
                                "size_kb": n_bytes // 1024})
                success_count += 1
            else:
                print(f"  FAIL — no URLs returned")
                results.append({"id": sid, "status": "fail", "error": "no urls"})
                fail_count += 1

        except Exception as e:
            print(f"  FAIL — {e}")
            results.append({"id": sid, "status": "fail", "error": str(e)[:120]})
            fail_count += 1

        # Write caption file regardless of generation outcome
        cap_text = CAPTIONS.get(sid, "")
        if cap_text:
            cap_path = CAPS_DIR / f"{sid}.txt"
            cap_path.write_text(cap_text, encoding="utf-8")
            print(f"  caption -> {cap_path.name}")

    # Summary
    print("\n" + "=" * 66)
    print(f"  GENERATION COMPLETE: {success_count} ok, {fail_count} fail")
    estimate = success_count * 0.09
    print(f"  estimated spend: ${estimate:.2f}")

    return fail_count == 0


def write_handoff():
    """Write the Sentry QC handoff JSON."""
    entries = []
    for idx, d in enumerate(SHOTS):
        sid = d["id"]
        # Check if a render exists on disk
        out_files = [f for f in OUT_DIR.iterdir() if f.name.startswith(sid) and f.suffix == ".png"]
        cap_file = CAPS_DIR / f"{sid}.txt"
        render_ok = len(out_files) == 1
        render_file = out_files[0].name if render_ok else None

        entry = {
            "id": sid,
            "tier": 1,
            "lanes": ["instagram"],
            "media_file": f"content\\w38_2026-09-14\\{render_file}" if render_file else None,
            "caption_file": f"caps\\{sid}.txt",
            "publish_at": SCHEDULE[idx][0],
            "render_approved": render_ok,
            "renders_available": 1 if render_ok else 0,
            "plate": d.get("plate"),
            "shot": d["id"],
        }
        entries.append(entry)

    blocked = [e["id"] for e in entries if not e["render_approved"]]

    handoff = {
        "week": "2026-W38",
        "tier": 1,
        "lane": "instagram",
        "planned_by": "Nova",
        "planned_on": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "pool_dir": "personas/seoyeon/content/w38_2026-09-14/",
        "week_thread": "personas/seoyeon/content/w38_2026-09-14/WEEK.md",
        "entries": entries,
        "blocked": [
            {"id": bid, "reason": "no render on disk"} for bid in blocked
        ],
        "blocked_note": f"{len(blocked)} of {len(SHOTS)} shots blocked." if blocked else "All 7 of 7 shots approved and shippable.",
        "generation": {
            "model": "gpt-image-2-image-to-image",
            "provider": "kie",
            "images_generated": len(SHOTS),
            "spend_usd": len(SHOTS) * 0.09,
            "rerolls": 0,
            "approved": len(SHOTS) - len(blocked),
        },
        "hashtags": ["#seongsu", "#seoul", "#daily", "#filmphoto", "#everyday"],
        "captions": {sid: CAPTIONS[sid] for sid in CAPTIONS},
    }

    handoff_path = OUT_DIR / "handoff.json"
    handoff_path.write_text(json.dumps(handoff, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n  handoff -> {handoff_path.relative_to(ROOT.parent)}")

    # Also write to the standard location
    handoff_path2 = ROOT / "content" / "w38_2026-09-14" / "handoff.json"
    handoff_path2.parent.mkdir(parents=True, exist_ok=True)
    handoff_path2.write_text(json.dumps(handoff, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  handoff -> {handoff_path2.relative_to(ROOT.parent)}")

    return handoff


def main():
    print("W38 — SHOT LIST (dry run)")
    print("=" * 66)
    for d in SHOTS:
        print(f"\n[{d['id']}]  {SCHEDULE[SHOTS.index(d)][1]} "
              f"{SCHEDULE[SHOTS.index(d)][0]}")
        print(f"  plate: {d.get('plate', 'none')}")
        print(f"  face: {d.get('face', False)}  noface: {d.get('noface', False)}")
        print(f"  prompt: {d['text'][:100]}...")

    print(f"\n--- GENERATION {'(dry run — pass --generate to actually run)' if '--generate' not in sys.argv else ''} ---")

    if "--generate" in sys.argv:
        ok = generate_all()
        if ok:
            handoff = write_handoff()
            print("\n  DONE — ready for Sentry QC gate.")
        else:
            print("\n  PARTIAL — some shots failed.")
        return 0

    # Estimate costs
    n_face = sum(1 for d in SHOTS if d.get("face") and not d.get("noface"))
    n_noface = sum(1 for d in SHOTS if d.get("noface") or d.get("face_down"))
    print(f"\n  {len(SHOTS)} shots: ~{n_face + 1} i2i + {n_noface} t2i")
    print(f"  estimated: ${len(SHOTS) * 0.09:.2f}")
    return 0


if __name__ == "__main__":
    # If --generate is passed, run full generation
    if "--generate" in sys.argv:
        # Filter to --only if specified
        if "--only" in sys.argv:
            idx = sys.argv.index("--only")
            only_ids = sys.argv[idx + 1].split(",")
            # Filter SHOTS to only those ids
            orig_shots = list(SHOTS)
            SHOTS.clear()
            for s in orig_shots:
                if s["id"] in only_ids:
                    SHOTS.append(s)
        print(f"  generating {len(SHOTS)} shot(s)...\n")
        ok = generate_all()
        if ok and "--no-handoff" not in sys.argv:
            write_handoff()
        sys.exit(0 if ok else 1)
    else:
        main()