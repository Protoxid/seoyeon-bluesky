# RETIRED — NOT MIGRATED TO FAL.AI (25 Aug 2026).
#
# This file belongs to the hero+edit ROOM pipeline, which the grid stopped
# using. It still imports kie_api and would call an endpoint this project no
# longer has a key for. Kept because the playbook references the reasoning in
# it, not because it runs.
#
# To bring it back: swap `from kie_api import ...` for `from fal_api import
# Fal as Kie, load_key`, change the model id to a fal endpoint, and replace
# `kie_upload(p, key)` with `kie.upload(p)`. See migrate_fal.py.
#
#!/usr/bin/env python3
"""
session.py — one hero photo, many frames, by EDITING not regenerating.

Room consistency cannot be prompted. A model asked to draw a room from a
description invents a new one every time. So we stop asking: generate ONE hero
image of her in the room, then produce every other frame in that room as an
EDIT of that exact file. The room persists because it is the same pixels.

    python session.py --list
    python session.py window --dry-run
    python session.py window --n 4 --budget 0.3

RULES
  * Always edit FROM THE HERO. Never from an edit. One generation deep, always.
  * One change per edit. Pose OR wardrobe OR light — not three at once.
  * Never describe the room. The hero is the room.
"""
from __future__ import annotations
import argparse, hashlib, os, pathlib, sys
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from kie_api import Kie, load_key, MODEL_I2I
from kie_upload import upload as kie_upload

MODEL_EDIT = "nano-banana-pro"     # ref_key image_input; verified
MODEL_RENDER = MODEL_I2I           # gpt-image-2-image-to-image (kie_api)

# WHICH MODEL, PER FRAME. Nano Banana is an editor: it preserves, which is why
# the room holds and also why a "later in the day" frame came back as the same
# photograph with a colour shift. An edit cannot move far from its source.
# Seedream re-renders from references instead, so it gives a genuinely
# different pose — at some cost to room fidelity, which the hero reference and
# an explicit role clause are there to hold.
#   EDIT   composition survives: light, time of day, wardrobe
#   RENDER composition changes: a different pose, position or framing
# RENDER IS THE DEFAULT. A verb whitelist was the wrong shape — "mid-laugh,
# head tipped" and "chin on her hand" are different poses with no verb in them,
# and they were being routed to the editor, which returns the same photograph.
# Every frame changes the composition unless it is a pure delta, so every frame
# re-renders unless something says otherwise.
# The editor stays available for the one thing it is better at: holding a room
# exactly. If a rendered frame drifts the room, re-run that frame with
# --model edit and accept a smaller change.
PURE_DELTA = ()      # frame text fragments to force onto the editor


def mode_for(frame: str) -> str:
    low = frame.lower()
    return "edit" if any(w in low for w in PURE_DELTA) else "render"

# The hero alone is not enough. It carries the room perfectly, but on a
# full-body scene there is barely any face in it to work from, and fine detail
# — the freckles above all — degrades every time the model re-renders her.
# So a face reference rides along, with an explicit role so it cannot leak the
# room or the wardrobe. Order matters: the hero is Image 1 because it is the
# photograph being edited, not a source of ideas.
# TWO face references on every frame: front plus a second angle. One reference
# anchors only the angle it depicts, and a single front shot left the profile
# and three-quarter frames unsupported. The second slot follows the frame — the
# profile crop where she is side-on, three-quarter everywhere else.
# This is three images per call. More than that reintroduced the averaging that
# caused the compositing problems, so three is the ceiling.
FACE_FRONT = "master/a/a1_front.png"
PROFILE_WORDS = ("in profile", "from the side", "side-on", "seen from the side")
FACE_SECOND_DEFAULT = "master/a/a2_tq_left.png"
FACE_SECOND_PROFILE = "master/a/a4_prof_left.png"

# Frames where her face is genuinely not in shot. Sending face references here
# invites the model to turn her round to satisfy them. --faces-everywhere
# overrides, for when a back frame comes out wrong.
NO_FACE_WORDS = ("from behind", "face not visible", "back to the camera")


def faces_for(frame: str, always: bool = False) -> list[str]:
    low = frame.lower()
    if not always and any(w in low for w in NO_FACE_WORDS):
        return []
    second = (FACE_SECOND_PROFILE if any(w in low for w in PROFILE_WORDS)
              else FACE_SECOND_DEFAULT)
    return [FACE_FRONT, second]


ROLES = ("Image 1 is the photograph to edit: keep its room, furniture, light, "
         "framing and wardrobe. Images 2 and 3 are the same woman's face from "
         "two angles — use them for her face only: the features, the skin and "
         "the small pale freckles across her nose and inner cheeks.")
ROLES_NOFACE = ("Image 1 is the photograph to edit: keep its room, furniture, "
                "light, framing and wardrobe exactly as they are.")

# Seedream is not editing, it is generating. The room has to be claimed
# explicitly or it invents one, which is the failure this whole design exists
# to avoid.
RENDER_ROLES = ("Image 1 is a photograph of the room this takes place in: use "
                "it for the room, the furniture, the surfaces and the light, "
                "which stay exactly as they are. Images 2 and 3 are the same "
                "woman's face from two angles — use them for her face only: "
                "the features, the skin and the small pale freckles across her "
                "nose and inner cheeks. This is a new photograph taken in that "
                "same room, not a copy of it.")
RENDER_ROLES_NOFACE = ("Image 1 is a photograph of the room this takes place "
                       "in: use it for the room, the furniture, the surfaces "
                       "and the light, which stay exactly as they are. This is "
                       "a new photograph taken in that same room.")
ROOT = pathlib.Path(__file__).parent
HEROES = ROOT / "heroes"
OUT = ROOT / "content"

# The edit instruction is the WHOLE prompt. No room, no identity, no lens —
# all three are already in the hero. Anything else added here competes with it.
# What the edit must NOT touch. Built per frame: a clause that contradicts the
# frame's own instruction has to come out, or the model gets told to change the
# light and keep the light in the same breath and picks one at random.
def keep_for(frame: str) -> str:
    f = frame.lower()
    parts = ["the room", "the furniture", "the window"]
    if not any(w in f for w in ("light", "shadow", "later in the day", "lamp",
                                "evening", "morning", "sun", "night", "dark",
                                "golden hour", "afternoon")):
        parts.append("the light")
    if not any(w in f for w in ("face not visible", "from behind",
                                "back to the camera")):
        parts.append("her face")
    return f"Keep {', '.join(parts[:-1])} and {parts[-1]} exactly as they are."

# Frames are derived from content.SCENES: action 0 becomes the HERO (generated
# by hero.py), actions 1..n become edits of it. One list, no duplication.
from content import SCENES as _SC
SESSIONS = {k: dict(hero=f"{k}.png", aspect=v["aspect"], frames=v["actions"][1:])
            for k, v in _SC.items()}

# Three extra frames per room, WRITTEN PER ROOM. A shared extras list is a trap:
# the same sentence in seven rooms puts her in the same grey top everywhere and
# gives the rooftop "long shadows across the wall" when it has no wall.
# Each room gets a second outfit that suits it, a light state that exists there,
# and a change of DISTANCE — the base actions all sit at one framing, so without
# this the whole bank reads at three crops.
EXTRAS = {
 "morning_window": [
   "Standing at the window with her back half to the camera, one hand on the sill, wearing a thin white t-shirt and grey sweat shorts instead.",
   "Sitting on the floor with her back against the armchair, knees up, late afternoon: the sun low and raking, long shadows across the floor.",
   "Much closer: head and shoulders only, the window light down one side of her face.",
 ],
 "reformer": [
   "Kneeling on the carriage tightening a strap, wearing a black cropped long-sleeve top and black leggings instead.",
   "Sitting on the floor beside the reformer unlacing her shoes, evening: the studio lights on and the window dark behind her.",
   "Much closer: her face and shoulders only, damp hair stuck at the temple.",
 ],
 "cafe": [
   "Standing at the counter waiting to pay, half turned away, wearing a black wool coat over a white shirt instead.",
   "Sitting back in the window seat with her arms folded, late afternoon: the sun behind the buildings and the cafe lamps doing the work.",
   "Wider: pulled back to take in the table, the window seat and the room around her.",
 ],
 "bathroom_mirror": [
   "Leaning on the vanity with both hands, shoulders forward, wearing a soft grey robe instead.",
   "Turning away from the mirror toward the door, at night: only the light above the mirror on, the rest of the room dark.",
   "Much closer: just her face and one hand, filling the mirror.",
 ],
 "rooftop": [
   "Sitting on the low bench with one leg drawn up, wearing a black puffer jacket over the jumper instead.",
   "Standing at the far corner of the terrace with her back to the city, golden hour: low sun straight across, everything warm and long-shadowed.",
   "Wider: pulled back so the railing, the olive trees and the skyline sit around her.",
 ],
 "bedroom": [
   "Sitting on the floor with her back against the bed, wearing a white cotton pyjama set instead.",
   "Lying on her back across the bed looking at the ceiling, at night: only the bedside lamp on, warm and small, the window dark.",
   "Much closer: head and shoulders against the linen.",
 ],
 "kitchen": [
   "Crouching to reach a low cupboard, wearing an oversized grey sweatshirt instead.",
   "Standing at the window with her back to the room, evening: the window dark and the strip light under the shelf the only source.",
   "Wider: pulled back to take in the whole kitchen corner.",
 ],
}
for _k, _v in SESSIONS.items():
    _v["frames"] = _v["frames"] + EXTRAS.get(_k, [])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("session", nargs="?")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--all", action="store_true",
                    help="run every session that has a locked hero")
    ap.add_argument("--frame", type=int, help="run only frame N (0-indexed)")
    ap.add_argument("--n", type=int, default=1, help="images per frame")
    ap.add_argument("--budget", type=float, default=0.3)
    ap.add_argument("--model", choices=("edit", "render"),
                    help="force every frame onto one model. Default picks per "
                         "frame: edit for light/wardrobe, render for pose")
    ap.add_argument("--faces-everywhere", action="store_true",
                    help="attach the face references even on from-behind "
                         "frames, where they normally invite the model to turn "
                         "her round")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if a.all:
        todo = [k for k, v in SESSIONS.items() if (HEROES / v["hero"]).exists()]
        if not todo:
            print("  no locked heroes. Run hero.py first."); return 0
        n = sum(len(SESSIONS[k]["frames"]) for k in todo) * a.n
        print(f"  {len(todo)} rooms, {n} frames (~${0.07*n:.2f})\n")
        import subprocess, sys as _s
        for k in todo:
            print(f"\n{'='*54}\n  {k}\n{'='*54}")
            subprocess.run([_s.executable, __file__, k, "--n", str(a.n),
                            "--budget", str(a.budget)])
        print(f"\n  Now: python drift_gate.py --in content")
        return 0

    if a.list or not a.session:
        for k, v in SESSIONS.items():
            hero = HEROES / v["hero"]
            print(f"  {k:<18}{len(v['frames'])} frames  hero "
                  f"{'OK' if hero.exists() else 'MISSING'}  {v['hero']}")
        print(f"\n  heroes live in {HEROES}/  — put the locked photo there.")
        return 0
    if a.session not in SESSIONS:
        sys.exit(f"unknown session. Options: {', '.join(SESSIONS)}")

    s = SESSIONS[a.session]
    hero = HEROES / s["hero"]
    if not hero.exists():
        sys.exit(f"no hero at {hero}. Lock one there first.")
    frames = s["frames"]
    if a.frame is not None:
        frames = [frames[a.frame]]
    faces = [faces_for(f, a.faces_everywhere) for f in frames]
    modes = [a.model or mode_for(f) for f in frames]
    def _roles(md, has_face):
        if md == "edit":
            return ROLES if has_face else ROLES_NOFACE
        return RENDER_ROLES if has_face else RENDER_ROLES_NOFACE
    prompts = [f"{f} {keep_for(f)}\n\n{_roles(md, bool(fr))}"
               for f, fr, md in zip(frames, faces, modes)]

    print(f"  session {a.session}\n  hero    {s['hero']}\n"
          f"  frames  {len(frames)} x {a.n} = {len(frames)*a.n} "
          f"(~${0.07*len(frames)*a.n:.2f})\n")
    if a.dry_run:
        for i, p in enumerate(prompts):
            print(f"[{i}] {p}")
        return 0

    load_key(ROOT)
    key = os.environ.get("KIE_API_KEY", "")
    if not key or key.startswith("PASTE"):
        sys.exit("no API key in kie_key.txt")
    kie = Kie(key)
    hero_url = kie_upload(hero, key)              # Image 1 — the photograph
    face_urls = {}
    for fr in {x for lst in faces for x in lst}:
        fp = (ROOT / fr).resolve()
        if fp.exists():
            face_urls[fr] = kie_upload(fp, key)   # Image 2 — her face only
        else:
            print(f"  ! {fr} missing — that frame runs on the hero alone")

    outdir = OUT / f"{a.session}_session"
    outdir.mkdir(parents=True, exist_ok=True)
    tag = hashlib.sha256("".join(prompts).encode()).hexdigest()[:6]
    spent = [0.0]

    def one(job):
        fi, vi, prompt = job
        md = modes[fi] if a.frame is None else modes[0]
        want = faces[fi] if a.frame is None else faces[0]
        ref = [hero_url] + [face_urls[x] for x in want if x in face_urls]
        i = f"{fi}.{vi}"
        if spent[0] + 0.07 > a.budget:
            return i, "skip", "budget cap"
        spent[0] += 0.07
        dest = outdir / f"{a.session}_{tag}_f{fi:02d}_{vi:02d}.png"
        try:
            urls = kie.generate(prompt, s["aspect"], ref,
                                model=MODEL_EDIT if md == "edit" else MODEL_RENDER)
            n = kie.download(urls[0], dest)
            return i, "ok", f"{dest.name}  {n//1024} KB"
        except Exception as e:
            spent[0] -= 0.07
            return i, "fail", str(e)[:120]

    jobs = [(fi, vi, p) for fi, p in enumerate(prompts)
            for vi in range(1, a.n + 1)]
    with ThreadPoolExecutor(max_workers=3) as ex:
        for f in as_completed([ex.submit(one, j) for j in jobs]):
            i, st, msg = f.result()
            print(f"  [{i:>5}] {'  ok  ' if st=='ok' else ' FAIL ' if st=='fail' else ' skip '} {msg}")

    print(f"\n  ~${spent[0]:.2f} -> {outdir}")
    print(f"  Now: python drift_gate.py --in {outdir.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
