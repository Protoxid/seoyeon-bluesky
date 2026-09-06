#!/usr/bin/env python3
"""
make_river_clip.py — R3, "the Han at seven". H3 reference-to-video on Kie.

    python make_river_clip.py --dry-run      free, prints exactly what is sent
    python make_river_clip.py                one clip

NO REFERENCE AT ALL, AND THAT IS THE POINT. A plate exists so a place can be
THE SAME place every time — the studio has to be recognisable or the account
stops being one person's life. The Han path is forty kilometres long and she
walks a different stretch of it each time, so there is nothing to hold steady
and a plate would only be nine cents spent to make every river clip the same
river clip. The first version of this script demanded one and refused to run
without it; that was the studio's rule applied to a place that does not have it.

WHAT IT COSTS TO DROP IT: the text has to carry the river. Say only the delta
means cut what the REFERENCES already show — with no reference, the place is
the delta, which is why the prompt in pov.CLIPS describes the paving, the cycle
lane, the railing, the bridge and the far bank in full.

SHE IS NOT IN THIS CLIP, so there is no identity stack either. Her masters
would only hand the model a face to put somewhere.

THE PROMPT IS NOT IN THIS FILE. It lives in pov.CLIPS under `pov_river_walk`,
where audit_video.py can see it. A prompt copied into a runner is a prompt the
auditor stops checking, and this project has already shipped one of those.
"""
from __future__ import annotations
import argparse, os, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import pov                                              # noqa: E402
from kie_api import Kie, load_key, video_cost           # noqa: E402

SHOT = "pov_river_walk"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--secs", type=int, default=None)
    ap.add_argument("--res", default="768P", choices=["768P", "2K"])
    ap.add_argument("--plate", default=None, help="override the place plate")
    ap.add_argument("--budget", type=float, default=None)
    ap.add_argument("--out", default="clips/r3_river_raw.mp4")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    d = next((c for c in pov.CLIPS if c["id"] == SHOT), None)
    if d is None:
        print(f"  ! {SHOT} is not in pov.CLIPS")
        return 2
    secs = a.secs if a.secs is not None else d["seconds"]

    # --plate stays as an OVERRIDE, not a requirement. If a particular stretch
    # of the path ever does need to recur, one exists without a code change.
    plate = pathlib.Path(a.plate) if a.plate else None
    if plate is not None and not plate.is_file():
        print(f"  ! {plate} not found")
        return 2

    cost = video_cost(secs, a.res, 1 if plate else 0)
    print(f"  model      {Kie.H3_REF2V if plate else Kie.H3_T2V}")
    print(f"  place      {plate.name + '  (Image 1)' if plate else 'in the prompt — no reference'}")
    print(f"  {secs}s at {a.res}, {d['aspect']}   ~${cost:.2f}")
    print(f"  prompt     {len(d['prompt'])} chars\n")

    if a.dry_run:
        print(d["prompt"])
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
    if plate:
        url = k.ref_video(d["prompt"], [plate.resolve()], duration=secs,
                          resolution=a.res, aspect_ratio=d["aspect"])
    else:
        url = k.text_video(d["prompt"], duration=secs, resolution=a.res,
                           aspect_ratio=d["aspect"])
    dest = ROOT / a.out
    n = k.download(url, dest)
    print(f"\n  {a.out}  {n // 1024} KB")
    print("  WATCH THE SHADOW AND THE FEET. The shot is a river without them,")
    print("  and a person walking by a river with them. Also check nobody")
    print("  near the camera has a face. Then:")
    print(f"      python make_reel_text.py --video {a.out} "
          f"--out clips/r3_river.mp4 --set river --fit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
