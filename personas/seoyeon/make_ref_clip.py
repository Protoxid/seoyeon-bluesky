#!/usr/bin/env python3
"""
make_ref_clip.py — Reel 01, on H3 reference-to-video.

    python make_ref_clip.py --dry-run          free, prints exactly what is sent
    python make_ref_clip.py --budget 0.80

Identity comes from three stills rather than one first frame, so the model has
her face from two angles and her build from a third. Everything H3's own
guidance asks for is here and each part is doing a job:

  * VISUAL LANGUAGE FIRST, and ours is a phone rather than a camera. The guide
    opens with "a Wes Anderson-inspired 35mm film look"; ours has to open with
    the opposite, because a cinematic look is the failure mode.
  * TIMECODED BEATS. [0-3s] [3-6s] [6-8s]. The documented fix for the floaty
    drift, and the same thing we worked out the expensive way.
  * EVERY REFERENCE GETS AN EXPLICIT JOB, addressed by ordinal.
  * IDENTITY LOCKED IN TEXT as well as by reference — the guide is explicit
    that listing defining features holds a character better than the reference
    alone.
  * SPECIFIC NEGATIVES. Our stills rule is never to negate; that was learned on
    Seedream, and H3 has a designated elements-to-avoid section. "No soft
    dissolves or fluid morphs" is a direct instruction against the exact
    floatiness that got published.
"""
from __future__ import annotations
import argparse, os, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from kie_api import Kie, load_key, ref_video_cost      # noqa: E402

REFS = ["master/a/a1_front.png",
        "master/a/a2_tq_left.png",
        "master/c/c5_relax_front.png"]

PROMPT = """Vertical phone video, 9:16, filmed on an iPhone 15 Pro: flat contrast, low saturation, visible sensor noise in the shadows, no colour grade and no cinematic look. It should read as a clip somebody set their phone down to film of themselves in an empty studio, and never edited.

Image 1 and Image 2 are the same woman's face from two angles — use them as a strict identity reference for her features and the pale freckles across her nose and inner cheeks. Image 3 is her full length — use it only for build and head-to-body proportion, not for wardrobe or setting.

She is a Korean woman in her mid twenties in a black sports bra and black leggings, hair in a low bun coming loose at the sides. Her skin is matte from brow to jaw and reads slightly dry: visible pores, uneven tone, the only sheen a faint one along the nose.

An empty pilates studio in Seongsu, Seoul, just after seven in the morning. Pale wood floor, reformer frames, a tall window along one side with hard low sun coming through it in a band across the boards. Nobody else is in the room.

[0-3 seconds] She walks in from the left carrying a rolled mat, crosses the band of sun lying across the boards, briefly brighter as she passes through it and dim again on the other side.
[3-6 seconds] She drops the mat, sits down on it and pulls one knee in toward her chest, looking down, breathing out.
[6-8 seconds] She looks up toward the camera for about a second, mouth closed, then away again.

The camera does not move at all. The viewpoint is low, at about knee height and slightly off level, and she is not centred in the frame. No pan, no zoom, no push in, no orbit, no gimbal.

Avoid: soft dissolves, fluid morphing, limbs changing length, the face smoothing or brightening between frames, glossy or wet-looking skin, shallow depth of field, background blur, slow motion, colour grading, film grain overlay, lens flare, a second person, any reflection of a person in a mirror, black frames, and any cut. One continuous take.

Audio: room tone only, distant air conditioning and one person moving on a mat. No music and no speech."""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--secs", type=int, default=8)
    ap.add_argument("--res", default="768P", choices=["768P", "2K"])
    ap.add_argument("--budget", type=float, default=None)
    ap.add_argument("--out", default="clips/r01_seven_am_raw.mp4")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    paths = [ROOT / r for r in REFS]
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
    print(f"  {a.secs}s at {a.res}, 9:16   ~${cost:.2f}")
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
        return int(bool(sys.stderr.write("no API key in kie_key.txt\n"))) or 2
    k = Kie(key)
    print("  queued — a few minutes")
    url = k.ref_video(PROMPT, paths, duration=a.secs, resolution=a.res,
                      aspect_ratio="9:16", log=ROOT / "h3_ref2v.jsonl")
    dest = ROOT / a.out
    n = k.download(url, dest)
    print(f"\n  {a.out}  {n // 1024} KB")
    print("  WATCH THE FIRST TWELVE FRAMES AT QUARTER SPEED — face wobble")
    print("  lives there or nowhere. Then:")
    print(f"      python make_reel_text.py --video {a.out} "
          f"--out clips/r01_seven_am.mp4")
    return 0


if __name__ == "__main__":
    sys.exit(main())
