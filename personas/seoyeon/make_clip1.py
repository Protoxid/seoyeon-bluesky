#!/usr/bin/env python3
"""
make_clip1.py — R1 clip 1: her, front camera, SILENT. H3 ref2v on Kie.

    python make_clip1.py --dry-run        free, prints exactly what is sent
    python make_clip1.py                  ~$0.40

She does not speak in this clip. Her voice runs over the top as a voice-over,
so nothing has to sync — which removes the single most likely way this whole
reel could scream AI. A mouth moving out of time with a voice-over is worse
than a mouth that never moves: it reads as badly dubbed, which is louder than
simply not watching someone speak.

WHY THE NEGATIVES ARE BACK INSIDE THE PROMPT. The ComfyUI version of this splits
positive and negative, because ComfyUI has a real negative conditioning input.
The Kie API does not, and H3 has a DESIGNATED elements-to-avoid section that its
own prompting guide recommends using. Model-specific rules do not transfer, and
this is the transfer: same content, different container.

SAY ONLY THE DELTA. This prompt was 1,788 characters and is now about 850. The
references carry her face; the room carries the room. Everything cut was text
describing what the pixels already show, and text that argues with pixels
loses — that is the most important prompting rule in this project and the
second render broke it hard.
LIGHTING IS THE CLEAREST CASE AND IT IS GONE ENTIRELY. "Bright overcast
daylight from the window, slightly blown out where it hits the glass, and the
room is light rather than dim" bought nothing: light comes from the scene and
the references, not from a sentence about it. The first render was dark, and
the fix for that is not more adjectives about brightness — it was the "flat
contrast, low saturation" and "cool daylight" that were dragging it down, so
they are cut rather than argued with.

WHAT SURVIVED THE CUT, AND ONLY BECAUSE IT IS NOT IN THE REFERENCES:
  * the SETTING — face masters do not carry a studio
  * the SKIN — a video model re-renders skin every frame and its prior is
    glossy, so the still's matte skin is genuinely not inherited
  * DEEP FOCUS — the last render blurred the background, our loudest AI tell
  * the FRAMING ERROR — the default is a centred passport frame
  * the BEATS — H3's documented fix for floaty motion
  * that she is NOT SPEAKING — the entire point of the clip

WHAT THE FIRST RENDER GOT WRONG, and two of the three were instructions:

  * BLURRED BACKGROUND. The prompt said "a window a little out of focus behind
    her". That was a deliberate override of this project's own deep-focus rule,
    argued on the grounds that a front camera really does throw a background
    soft. It does — and background blur is still the single loudest AI tell we
    have, so the argument was true and irrelevant. Everything is sharp now.
  * DEAD-CENTRE SYMMETRY. Nothing in the prompt asked for a framing error, so
    the model produced the default: face centred, shoulders level, head
    straight, equal margin either side. A real front-camera selfie is never
    that composed. The framing is now off centre, off level, above eye line,
    with her face turned slightly away from the lens.
  * DARK. "flat contrast, low saturation" plus "cool daylight" gave murk. The
    light is now bright overcast and the room is explicitly light rather than
    dim.

NO PHONE, NO HAND, NO ARM ANYWHERE IN THE POSITIVE. The POV skeleton opened
"filmed on an iPhone held in one hand ... the person holding the phone is not
visible" and a phone duly appeared in frame — three summons in two sentences,
the denial being the worst of them. The device is named only as a lens spec
here, which has never summoned one, and the motion is described by its shape.
"""
from __future__ import annotations
import argparse, os, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from kie_api import Kie, load_key, ref_video_cost      # noqa: E402

# THE PLATE GOES FIRST, and it was missing until now. Without it clip 1's
# studio is invented from the words "a pilates studio", while clips 2-4 build
# theirs from plate_studio_wide — two different rooms inside one 27-second
# reel, and the deep-focus fix makes that background legible enough to notice.
# Naming the room in text when a picture of it exists is also the exact thing
# SAY ONLY THE DELTA forbids.
# Ordinals follow the project's convention: plate is Image 1, face after it.
def _refs():
    import pov
    plate = pov.plate_path("plate_studio_wide")
    if plate is None:
        raise SystemExit(
            "  ! plate_studio_wide is not on disk. Generate it first:\n"
            "        python outside.py --plates --only plate_studio_wide")
    return [plate,
            ROOT / "master/a/a1_front.png",
            ROOT / "master/a/a2_tq_left.png"]

PROMPT = """Vertical phone video, 9:16, shot on an iPhone front camera.

Image 1 is the room she is in — keep its floor, its machines, its mirrored wall and its light. Images 2 and 3 are the same woman's face from two angles — use them as a strict identity reference.

She is in her studio in Seongsu, Seoul, in a black sports bra. Her skin is matte with visible pores and uneven tone, and it does not smooth or brighten. Everything sharp front to back.

Held above eye level and off to one side: she sits off centre, the frame a few degrees off level, her face turned slightly away while her eyes come back to the lens.

She is not speaking and her mouth stays closed.

[0-1 seconds] She looks into the lens with a small closed-mouth smile.
[1-2 seconds] She glances off to one side and back.
[2-4 seconds] One eyebrow lifts slightly, she blinks twice, and settles.

Avoid: any mouth movement, teeth, a phone or camera in the picture, zooming, panning, morphing, background blur, a second person, and any cut."""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--secs", type=int, default=4,
                    help="H3's minimum is 4; the hook take is 3.8s")
    ap.add_argument("--res", default="768P", choices=["768P", "2K"])
    ap.add_argument("--budget", type=float, default=None)
    ap.add_argument("--out", default="clips/r1_c1_hook_raw.mp4")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    paths = _refs()
    missing = [p.name for p in paths if not p.is_file()]
    if missing:
        print(f"  ! missing references: {missing}")
        return 2
    for p in paths:
        try:
            Kie.check_reference(p)
        except ValueError as e:
            print(f"  ! {e}")
            return 1

    cost = ref_video_cost(a.secs, a.res, len(paths))
    print(f"  model      minimax-h3/reference-to-video")
    print(f"  refs       {', '.join(p.name for p in paths)}")
    print(f"  {a.secs}s at {a.res}, 9:16   ~${cost:.2f}  (rate still unconfirmed)")
    print(f"  prompt     {len(PROMPT)} chars\n")

    if a.dry_run:
        print(PROMPT)
        print(f"\n  DRY RUN — nothing sent, ${cost:.2f} not spent")
        return 0

    cap = a.budget if a.budget is not None else round(cost * 1.02 + 0.01, 2)
    if cost > cap:
        print(f"  ${cost:.2f} exceeds the cap ${cap:.2f}")
        return 1

    load_key(ROOT)
    key = os.environ.get("KIE_API_KEY", "")
    if not key or key.startswith("PASTE"):
        print("no API key in kie_key.txt", file=sys.stderr)
        return 2
    k = Kie(key)
    print("  queued — a few minutes")
    url = k.ref_video(PROMPT, paths, duration=a.secs, resolution=a.res,
                      aspect_ratio="9:16", log=ROOT / "h3_ref2v.jsonl")
    dest = ROOT / a.out
    n = k.download(url, dest)
    print(f"\n  {a.out}  {n // 1024} KB")
    print("  CHECK THE MOUTH FIRST. If it moves at all, regenerate — a voice")
    print("  over a moving mouth is worse than a voice over a still one.")
    print("  Then note the credit deduction: it is the first real H3 number.")
    print(f"\n      python phone_audio.py --audio voice/hook.mp3 "
          f"--under {a.out} --mux {a.out} --out clips/r1_c1_hook.mp4")
    return 0


if __name__ == "__main__":
    sys.exit(main())
