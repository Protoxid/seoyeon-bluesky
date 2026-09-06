#!/usr/bin/env python3
"""
make_clips234.py — R1 clips 2, 3, 4: POV of the studio. H3 ref2v on Kie.

    python make_clips234.py --dry-run
    python make_clips234.py --only c2
    python make_clips234.py --all

Her voice runs over these. Nobody is in them, which means no identity to hold,
no provider that can refuse them, and nothing to lip-sync.

EACH SHOT IS THE THING ITS LINE DESCRIBES — the spring bar under "fewer springs
is harder", the carriage under "control the return", the socks under "grip
socks are not optional". That is what separates this from footage playing
behind a voice.

SAY ONLY THE DELTA. Image 1 is the studio plate, so the room is not described
at all: no floor, no windows, no mirror, no light. Naming any of it would put
text in competition with the pixels that already show it. There is no lighting
sentence anywhere in this file on purpose — light comes from the plate.

SEEDANCE PRODUCED THE ACCEPTABLE CLIP AND IS NOT THE DEFAULT — operator's
call, on cost. It works and it is 3.7x the price, so it is the fallback for a
shot H3 cannot do rather than the first thing reached for. --engine seedance
still selects it deliberately.

SEEDANCE IS AVAILABLE BUT IT IS NOT THE CHEAP OPTION, and the real numbers
change the recommendation. For these three clips, 24 seconds in total:

    H3 768P            $2.04
    Seedance 480p      $3.36
    Seedance 720p      $7.56      <- 3.7x H3
    Seedance 1080p    $13.68

Seedance publishes two rates and the low one is not ours. "With video input" is
cheaper per second only because it bills Price x (Input + Output) rather than
Price x Output, and it applies when you supply a reference VIDEO. The plate is
an IMAGE, so every clip here bills at the no-video rate.

AND THE RENDER LOOK WAS DIAGNOSED AS THE CAMERA, NOT THE MODEL. The motion was
described abstractly enough that a smooth glide satisfied it; it now asks for
handheld shake, uneven pan speed, mid-pan corrections and overshoot. That fix
applies to BOTH engines, so H3 deserves a re-run before $7.56 does — it was
never given a fair attempt with a correct prompt.

THESE COST REAL MONEY AND DO NOT HAVE TO. There is no face in any of them, so
nothing here needs Kie: a local ComfyUI run is free and the prompts in
wiki/domains/publishing/reel-r1-voiceover.md are the same shots with the
negatives split out into their own field. This script exists for when matching
clip 1's renderer matters more than $2.
"""
from __future__ import annotations
import argparse, os, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from kie_api import Kie, load_key, ref_video_cost, seedance_cost      # noqa: E402

# Durations track the voice takes: tip1 ~8.5s, tip2 ~7.7s, tip3 ~6.5s, each
# rounded up a second so the picture outlasts the words rather than the reverse.
# THE TRIM WENT ONE LINE TOO FAR. This was cut down to "shot on an iPhone" on
# the grounds that the plate carries the look — and the first renders came back
# looking like architectural visualisations. The plate is a STILL: it carries
# the room, not how a moving sensor renders it. A video model re-renders every
# frame from scratch, so photographic texture is a genuine delta, exactly like
# the skin block on a face. SAY ONLY THE DELTA means cut what the references
# already show, not cut until it is short.
LENS = ("Vertical phone video, 9:16, shot on an iPhone: flat contrast, low "
        "saturation, visible sensor noise in the shadows, no colour grade and "
        "no cinematic look. It should look like a clip somebody took on their "
        "way through the room, not like a rendering.\n\n")
ROLE = ("Image 1 is the room this is filmed in. Keep it exactly: the same "
        "room, not a similar one.\n\n")
# HANDHELD IS BACK, AND REMOVING IT WAS MY OVER-CORRECTION. The rule that
# earned itself is that the camera must not be an OBJECT IN THE SCENE: "held in
# one hand", "the person holding the phone". "Handheld" is not that — it is a
# description of how the camera MOVES, it is standard vocabulary, and H3's own
# prompting guide uses "subtle handheld shake". It never summoned a phone;
# the holder sentences did.
#
# What replaced it — "the view never settles, a drift off level" — is abstract
# enough to be satisfied by a smooth slow glide, which is exactly what came
# back and exactly why it read as a render. A rendered camera moves at constant
# velocity along a path. A hand does not: it shakes at high frequency, it is
# never still even when the move stops, it changes speed mid-pan and corrects.
# Those are the things to say.
MOTION = ("\n\nHandheld throughout, filmed while walking through the room: a "
          "constant small shake from the hands holding it, so the frame is "
          "never completely still even when the movement stops. The pan is "
          "uneven in speed, with small corrections part way through and a "
          "slight overshoot when it settles. Natural motion blur while it "
          "moves, and the exposure lifts and settles half a second behind the "
          "movement rather than staying even. Everything sharp front to back "
          "when it is still.\n\n"
          "Avoid: any person, a reflection of a person, hands or arms in "
          "frame, a phone or camera in the picture, a smooth constant-speed "
          "camera move, a camera on rails, a dolly, a crane, a drone shot, a "
          "gimbal, a tripod, zooming, morphing, background blur, a clean even "
          "exposure, 3D rendering, CGI, architectural visualisation, video "
          "game look, black frames, and any cut.")

SHOTS = [
    dict(id="c2", secs=9, over="tip1 · fewer springs is harder",
         out="clips/r1_c2_springs_raw.mp4",
         shot="[0-3 seconds] The view is low and close to the underside of a "
              "reformer, on the coloured springs.\n"
              "[3-7 seconds] It moves slowly along the spring bar and the "
              "springs pass through frame one after another.\n"
              "[7-9 seconds] It stops on the last one and holds."),
    dict(id="c3", secs=8, over="tip2 · control the return, you want it silent",
         out="clips/r1_c3_carriage_raw.mp4",
         shot="[0-2 seconds] The view looks down the length of a reformer from "
              "the foot end, the carriage at rest.\n"
              "[2-6 seconds] The carriage rolls slowly away along its tracks "
              "and slows as it goes.\n"
              "[6-8 seconds] It comes to rest against the stop without "
              "bouncing. Nothing else moves."),
    dict(id="c4", secs=7, over="tip3 · grip socks are not optional",
         out="clips/r1_c4_socks_raw.mp4",
         shot="[0-2 seconds] The view looks down at a folded pair of grip "
              "socks on a low wooden bench, next to a rolled mat.\n"
              "[2-5 seconds] It holds on the socks.\n"
              "[5-7 seconds] It tips up slowly to take in the room beyond."),
]


def prompt_for(d: dict) -> str:
    return LENS + ROLE + d["shot"] + MOTION


def plate() -> pathlib.Path:
    import pov
    p = pov.plate_path("plate_studio_wide")
    if p is None:
        raise SystemExit(
            "  ! plate_studio_wide is not on disk. Generate it first:\n"
            "        python outside.py --plates --only plate_studio_wide")
    return p


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--engine", default="h3",
                    choices=["seedance", "h3"],
                    help="seedance 2.5 or H3. Seedance refuses her FACE, and "
                         "there is no face in any of these")
    ap.add_argument("--res", default=None,
                    help="H3: 768P or 2K. Seedance: 720p or 1080p (its enum "
                         "is not documented, so it is not validated here)")
    ap.add_argument("--budget", type=float, default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    want = SHOTS
    if a.only:
        ids = {x for x in a.only.replace(",", " ").split() if x}
        known = {d["id"] for d in SHOTS}
        if ids - known:
            print(f"  ! unknown: {sorted(ids - known)}   known: {sorted(known)}")
            return 1
        want = [d for d in SHOTS if d["id"] in ids]
    elif not a.all:
        print("  pass --all or --only c2,c3,c4")
        return 1

    pl = plate()
    Kie.check_reference(pl)
    seed = a.engine == "seedance"
    res = a.res or ("720p" if seed else "768P")
    print(f"  model   {Kie.SEEDANCE if seed else 'minimax-h3/reference-to-video'}")
    print(f"  plate   {pl.name}")
    for d in want:
        line = f"  [{d['id']}] {d['secs']}s at {res}   over {d['over']}"
        if not seed:
            line += f"   ~${ref_video_cost(d['secs'], res, 1):.2f}"
        print(line)
    if seed:
        tot = sum(seedance_cost(d["secs"], res) for d in want)
        h3 = sum(ref_video_cost(d["secs"], "768P", 1) for d in want)
        print(f"  total   ~${tot:.2f}   vs ~${h3:.2f} for the same clips on H3")
        print("          Seedance bills the NO-VIDEO-INPUT rate here: the "
              "plate is an\n          image, and only a reference VIDEO gets "
              "the cheaper column.\n")
    else:
        total = sum(ref_video_cost(d["secs"], res, 1) for d in want)
        print(f"  total   ~${total:.2f}   (rate still unconfirmed)\n")

    if a.dry_run:
        for d in want:
            print("=" * 68)
            print(f"[{d['id']}]\n{prompt_for(d)}\n")
        print(f"  DRY RUN — nothing sent, ${total:.2f} not spent")
        return 0

    total = (sum(seedance_cost(d["secs"], res) for d in want) if seed
             else sum(ref_video_cost(d["secs"], res, 1) for d in want))
    cap = a.budget if a.budget is not None else round(total * 1.02 + 0.01, 2)
    if total > cap:
        print(f"  ${total:.2f} exceeds the cap ${cap:.2f} — pass --budget to "
              f"raise it deliberately")
        return 1

    load_key(ROOT)
    key = os.environ.get("KIE_API_KEY", "")
    if not key or key.startswith("PASTE"):
        print("no API key in kie_key.txt", file=sys.stderr)
        return 2
    k = Kie(key)
    for d in want:
        print(f"  [{d['id']}] queued — a few minutes")
        if seed:
            url = k.seedance(prompt_for(d), [pl], duration=d["secs"],
                             resolution=res, aspect_ratio="9:16",
                             generate_audio=False,
                             log=ROOT / "seedance.jsonl")
        else:
            url = k.ref_video(prompt_for(d), [pl], duration=d["secs"],
                              resolution=res, aspect_ratio="9:16",
                              log=ROOT / "h3_ref2v.jsonl")
        dest = ROOT / d["out"]
        n = k.download(url, dest)
        print(f"  [{d['id']}] {d['out']}  {n // 1024} KB")

    print("\n  CHECK FOR A PERSON IN THE MIRROR FIRST. A studio is full of")
    print("  mirrors and a first-person view in one photographs whoever is")
    print("  holding the camera. If anyone appears in glass, that is why.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
