#!/usr/bin/env python3
"""
masters.py — regenerate the master frames we ACTUALLY use, on GPT Image 2.

WHY. a1 is the seed, a2 and a3 were regenerated on gpt-image-2, everything else
is from the old process. The stack is therefore two different renderings of the
same woman, canonical.npy averages across both, and every generation pulls
references in two directions. This makes it one stack again.

ALL FOUR ARE NOW keep=True. The operator looked at the existing frames and
kept them. --all therefore does nothing; --only still runs any of them. The
prompts stay here because the next time a master needs remaking, the wording
and the reference pairing are already worked out and paid for.

ONLY WHAT IS USED. outside.py reads a1 + a2 for the face and c5 for the body.
The b/ frames are about to be wired in per shot for expression. Nothing else in
master/ is referenced by a live script, so nothing else is regenerated.

EXPRESSIONS ARE NOT REFERENCED. Operator's call, and the test supports it:
gpt-image-2 produced a blank stare, a yawn and a real laugh from text alone.
Every reference attached is another thing that can fight the prompt, so the
face frames stay NEUTRAL and expression is asked for in words per shot.

THE TATTOO. Canon says LEFT ribcage and the model keeps mirroring it, because
her left is the viewer's right and nothing holds that reliably. So c5's prompt
does NOT name a side: it goes on "one side of her ribcage". Look at where it
lands and rewrite body_block.txt to match. It has to be CONSISTENT, not
predetermined — and a picture holds a side better than a sentence ever has.
c5 is also the frame every wide shot attaches, so the tattoo belongs HERE or it
propagates nowhere. Caveat: front-on, a ribcage tattoo is near edge-on, so her
arms are held away from her sides to keep it unobstructed.

    python masters.py --dry-run
    python masters.py --all --budget 0.6
"""
from __future__ import annotations
import argparse, os, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from kie_api import Kie, load_key

ROOT = pathlib.Path(__file__).parent
MODEL = "gpt-image-2-image-to-image"   # Kie. ref field is input_urls
SEED_FACE = "master/a/a1_front.png"
PRICE = 0.09

# SAY ONLY THE DELTA. The operator's prompt for a2 was, in full:
#     "THREE-QUARTER LEFT 45 degrees."
# Seven words, and it produced the best frame in the stack. a1 already carries
# the background, the light, the styling, the skin and the hair — re-describing
# any of it invites the model to RE-DERIVE it, which is exactly how drift
# starts. State only what the reference cannot show.
#   angle change  -> just the angle
#   body frame    -> the body, because a face frame does not contain one

FRAMES = [
 # KEEP=TRUE — the operator looked at these and they are good. Skipped by
 # --all; still runnable with --only if that ever changes.
 # They are old-process, so the a-folder is strictly still mixed. That only
 # matters if it SHOWS: the calibration standard deviation is the test. If it
 # comes back tight, the stack is effectively unified whatever made each frame,
 # and provenance is bookkeeping. If it comes back wide, these two are the
 # outliers and the prompts below are ready.
 # (a2 is 45 degrees left, so 90 left would be an extrapolation along a known
 # path rather than a leap from a front-on frame. Same for a3 and the right.)
 dict(id="a4_prof_left", keep=True, dest="master/a", aspect="3:4", refs=["a1", "a2"],
      why="full profile left; a1 at 0 and a2 at 45 give the rotation",
      text="FULL PROFILE LEFT, 90 degrees."),

 dict(id="a5_prof_right", keep=True, dest="master/a", aspect="3:4", refs=["a1", "a3"],
      why="full profile right; a1 at 0 and a3 at 45 give the rotation",
      text="FULL PROFILE RIGHT, 90 degrees."),

 dict(id="b7_half", keep=True, dest="master/b", aspect="3:4", refs=["a1"],
      why="waist-up; bridges the face frames and the full-length one",
      text="WAIST UP, facing camera, arms loose. Matte bone-white "
           "scoop-neck sports bra, no logos or contrast seams."),

 # a1 ONLY. The old c5 is from the previous process and feeding it back in
 # would pull the rendering we are replacing straight into the new stack —
 # which is the whole problem this run exists to fix.
 # A face frame contains no body, so the body IS the delta and gets described.
 # Build numbers AND the wardrobe come from body_block.txt. THE WARDROBE WAS
 # ALREADY WRITTEN THERE and the first version of this file said "plain black"
 # because it was invented instead of read. gpt-image-2 produced the bone-white
 # set regardless — it followed a1 over the text and was right to.
 # The tattoo does NOT get a side: look at where it lands and rewrite
 # body_block.txt to match. Consistent, not predetermined.
 dict(id="c5_relax_front", keep=True, dest="master/c", aspect="3:4", refs=["a1"],
      why="THE body ref outside.py attaches on wide shots — now with the tattoo",
      text="FULL LENGTH, standing relaxed and facing camera, arms held a "
           "little away from her sides, weight even, barefoot. A matte "
           "bone-white fitted athletic set: scoop-neck sports bra and "
           "high-waisted mid-thigh shorts, no logos, no contrast seams. "
           "165 cm and seven and a half head-heights, narrow waist, long "
           "torso, legs a little over half her height, lean pilates "
           "conditioning with no bulk, shoulders naturally back. A botanical "
           "tattoo on one side of her ribcage: a single upright sprig of "
           "leaves about as long as her hand, starting just below the bra "
           "line and running down along the ribs, drawn in clean confident "
           "single-weight black linework, every leaf clearly separated and "
           "legible."),
]

# Even this is probably more than needed — a2 was made with no role line at
# all. Kept only where a SECOND reference exists and the two need separating.
# a2 was made with NO role line at all. Two face frames of the same woman at
# two angles need no explaining — they are self-evidently the same head.
ROLE_2REF = ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="comma-separated ids")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--budget", type=float, default=0.3)
    ap.add_argument("--tier", default="2k", choices=["1k", "2k", "4k", "max"])
    ap.add_argument("--into", help="write to master/<this> instead of the "
                                   "normal dest — for side-by-side tests")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    want = ([f for f in FRAMES if not f.get("keep")] if a.all
            else [f for f in FRAMES if a.only and f["id"] in a.only.split(",")])
    if not want:
        print(f"\n  {'id':<16}{'dest':<12}{'ar':<7}why")
        for f in FRAMES:
            tag = "KEEP" if f.get("keep") else ""
            print(f"  {f['id']:<16}{f['dest']:<12}{f['aspect']:<7}{tag:<6}{f['why']}")
        n = len([f for f in FRAMES if not f.get("keep")])
        print(f"\n  --all = {n} frames, ~${n*PRICE:.2f}"
              f"   (KEEP frames are skipped; --only overrides)")
        return 0

    cost = PRICE * len(want)
    print(f"\n  model   {MODEL}   tier {a.tier}"
          + (f"   -> master/{a.into}" if a.into else ""))
    print(f"  seed    {SEED_FACE}")
    print(f"  COST    ~${cost:.2f}  ({len(want)} x ${PRICE:.2f})\n")
    for f in want:
        print(f"  {f['id']:<16}{f['aspect']:<7}{len(f['text']):>4} chars  "
              f"refs={'+'.join(f['refs']):<7} -> {f['dest']}")
    if cost > a.budget:
        sys.exit(f"\n  ${cost:.2f} exceeds --budget {a.budget:.2f}")
    if a.dry_run:
        for f in want:
            extra = ("\n\n" + ROLE_2REF) if (len(f["refs"]) > 1 and ROLE_2REF) else ""
            print("\n" + "=" * 66)
            print(f"[{f['id']}  refs={'+'.join(f['refs'])}]\n{f['text']}{extra}")
        print("=" * 66)
        print(f"\n  DRY RUN — nothing sent, ${cost:.2f} not spent")
        return 0

    load_key(ROOT)
    key = os.environ.get("KIE_API_KEY", "")
    if not key or key.startswith("PASTE"):
        sys.exit("no API key in kie_key.txt")
    kie = Kie(key)
    SRC = {"a1": "master/a/a1_front.png",
           "a2": "master/a/a2_tq_left.png",
           "a3": "master/a/a3_tq_right.png"}
    urls = {}
    for k, rel in SRC.items():
        u = kie.upload((ROOT / rel).resolve())
        if not u:
            sys.exit(f"{rel} upload returned nothing — not spending")
        urls[k] = u

    for f in want:
        out = ROOT / "master" / a.into if a.into else ROOT / f["dest"]
        out.mkdir(parents=True, exist_ok=True)
        dest = out / f"{f['id']}.png"
        # never overwrite a locked master in place — the old one stays until
        # the new one has been looked at
        if dest.exists():
            dest = out / f"{f['id']}_new.png"
        try:
            refs = [urls[k] for k in f["refs"]]
            prompt = f["text"] + (("\n\n" + ROLE_2REF) if (len(refs) > 1 and ROLE_2REF) else "")
            got = kie.generate(prompt, f["aspect"], refs, model=MODEL, tier=a.tier)
            n = kie.download(got[0], dest)
            print(f"  [{f['id']:<16}]  ok   {dest.name}  {n//1024} KB")
        except Exception as e:
            print(f"  [{f['id']:<16}] FAIL  {str(e)[:150]}")

    if a.into:
        print(f"\n  Side-by-side test written to master/{a.into}. These are NOT")
        print("  masters until they have been scored. a1 is the SEED — a 4k")
        print("  render made FROM a1 is a new image, not a1 at more pixels.")
        print(f"     python drift_gate.py --in master/{a.into}")
        print(f"     python bone_gate.py  --in master/{a.into}")
        print("  Same woman with more detail, or a different woman rendered")
        print("  beautifully? The gates answer that; the eye alone will not.")
        return 0
    print(f"\n  {ROOT / 'master'}")
    print("  Files landed as *_new.png where one already existed. LOOK at them,")
    print("  then swap the names in yourself. After swapping:")
    print("     python drift_gate.py --calibrate")
    print("     python bone_gate.py --calibrate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
