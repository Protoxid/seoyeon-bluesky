#!/usr/bin/env python3
"""
make_fit_clip.py — Reel 01, the fit check. H3 image-to-video.

    python make_fit_clip.py --dry-run          free, prints exactly what is sent
    python make_fit_clip.py

WHY IMAGE-TO-VIDEO AND NOT REFERENCE-TO-VIDEO, which is what the parked pilates
reel used. Reference-to-video costs $0.76 and asks the model to invent the
outfit, the room, the light and the face from three head-and-shoulders stills.
Here all four of those are already correct in ONE approved frame, so the only
thing left to generate is movement:

    ref2v  8s, 3 refs, 768P   $0.76   identity re-derived every frame
    i2v    6s, 1 frame, 768P  $0.52   identity locked to a frame we approved

Cheaper AND stronger, and that is not a coincidence — the frame carries more
information than the prompt can, which is the whole of SAY ONLY THE DELTA
applied to video. The prompt below therefore describes almost nothing about how
she looks. It describes what moves.

THE MIRROR IS NOT THE USUAL PROBLEM HERE. The playbook warns that a
first-person camera in a mirrored room photographs the person holding it — but
that rule is about a room where she is NOT meant to be visible. In a fit check
the reflection IS the subject and the phone in frame is the format, not a
failure. The risk that remains is the model rendering her twice, once as a body
and once as a reflection, so the prompt says the mirror fills the frame and the
avoid list names the failure directly.

MINIMUM MOTION IS MINIMUM DRIFT. Six seconds, three small beats, no walking and
no camera move. Every clip that came out floaty was a clip that asked for more
movement than the format needed.
"""
# RETIRED — superseded by the ComfyUI ref2v build (30 Aug 2026).
# This is the image-to-video path. It was run once and produced the three
# faults that moved R4 off Kie entirely: the camera pushed in despite "no
# zoom" being in the prompt (naming a thing in a positive prompt summons it,
# and the API has no negative field to put it in), the tattoo vanished because
# neither the still nor the face masters carry it, and the motion was floaty.
# The published fit check was made in ComfyUI from
# wiki/domains/publishing/reel-r4-comfyui.md, where positive and negative are
# separate inputs. Kept for the reasoning, not as a route.
from __future__ import annotations

RETIRED = True
import argparse, glob, os, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from kie_api import Kie, load_key, video_cost  # noqa: F401          # noqa: E402

STILL_GLOB = "content/week2_reel/w2r_fit_door_*.png"

# THE LENS CLAUSE IS GONE, AND IT WAS THE DOCUMENTED CAUSE. "flat contrast,
# low saturation, visible sensor noise in the shadows" produced a render that
# was dark, noisy throughout, and pushed her skin tone darker. make_clip1.py
# had already cut exactly those words for exactly that reason and its docstring
# says so: the fix for a dark render is not adjectives about brightness, it is
# deleting what darkens it. This file kept them and shipped them to R4.
# "in the shadows" limited nothing — the model applied the noise globally.
# NOT changed in make_clips234.py, deliberately: those are ROOMS with no face,
# the texture line earned itself there when its removal produced glide-cam
# render footage, and nobody has called those clips dark. Same words, opposite
# verdicts, because the shots are not the same shot.
PROMPT = """Vertical phone video, 9:16, a full-length mirror in a one-room flat in Seongsu, Seoul: no colour grade and no cinematic look. The mirror fills the whole frame and everything visible is her reflection. She is holding the phone low at her hip and it stays there.

Her skin stays matte from brow to jaw and slightly dry: visible pores, uneven tone, the only sheen a faint one along the nose. It does not smooth or brighten at any point.

[0-2 seconds] She shifts her weight from one leg onto the other and pulls the hem of the open shirt straight with her free hand.
[2-4 seconds] She turns a little to one side, looks down at the shorts in the reflection, then straightens again.
[4-6 seconds] She lifts her chin and looks at herself in the mirror for about a second, mouth closed, then glances down at the phone.

Nothing else in the room moves. The framing does not change: no pan, no zoom, no push in, no orbit. Small natural handheld drift only, because the phone is in her hand.

Avoid: a second person, her body appearing anywhere outside the mirror, a second phone, the outfit changing, the shirt changing colour, soft dissolves, fluid morphing, limbs changing length, the face smoothing or brightening between frames, glossy or wet-looking skin, shallow depth of field, background blur, slow motion, colour grading, film grain overlay, lens flare, black frames, and any cut. One continuous take.

Audio: room tone only. No music and no speech."""

# SEEDANCE PROMPT. Its rationale is NOT here -- it is in main() at the
# `if a.engine == "seedance":` branch, beside the reference-slot decision
# that produced it, because the two are one argument: two slots, the
# approved still plus the turntable, and a prompt whose job is to tell the
# model what to take from each. Read that block before touching this string.
#
# THIS IS THE ONLY PROMPT IN THIS FILE THAT PASSES audit_video.py CLEAN.
# PROMPT and KLING_PROMPT each raise three or more issues. If an edit here
# adds one, the edit is wrong, not the checker.
#
# THE AVOID LIST STAYS, AND IT IS NOT THE SAME CALL AS KLING'S. Kie's
# seedance-2-5 schema has no negative_prompt field either, so a negative has
# nowhere to go but the prose -- unlike ComfyUI, which has a negative node,
# and unlike Kling, where the list was deleted rather than moved because
# Kling's own guide never mentions negatives at all. Standing caveat, stated
# because this file's own header documents the opposite outcome on H3:
# "no zoom" in a positive-only prompt was blamed for a push-in. The same
# risk applies to every line of the avoid list below. It survived one
# Seedance render without summoning what it names; that is one data point,
# not a proof. If a future render reproduces a named failure, shortening the
# list is the first experiment to run.
SEEDANCE_PROMPT = """Image 1 is the scene: keep the hallway, the mirror, the light and the clothes in it exactly as they are.

Image 2 is a reference sheet of the same woman's head from twelve angles. Take ONLY her face, her hair and her colouring from it, so that her features stay the same when she turns. Ignore everything else about it: it is a reference sheet, not a scene. Do not copy its grey background, its panels or grid, the words printed on it, or the white top she wears in it. The video is one continuous shot of the room in Image 1, never a grid and never a studio backdrop.

She is the same woman in both images.

A woman films her own reflection in a full-length mirror in the hallway of a small flat. The whole frame is the mirror and everything in it is her reflection.

THE PHONE IN THE MIRROR IS THE CAMERA. She holds it in her right hand, low at her hip, and it is the phone taking this video. Her right hand and forearm stay exactly where they are for the whole clip: she does not raise the phone, lower it, or turn it. Because the phone is the camera, the framing moves only the small amount her hand does — a slight, slow, unsteady drift, never a deliberate move, and everything in the mirror drifts together with it.

Her skin stays matte from brow to jaw and slightly dry: visible pores, uneven tone, the only sheen a faint one along the nose. It does not smooth or brighten at any point.

[0-2 seconds] She shifts her weight onto her other leg. Her LEFT hand — the empty one, not the hand holding the phone — comes up and tugs the hem of the open shirt straight, a clear deliberate movement of the whole hand and forearm, then drops again.
[2-4 seconds] She turns a little to one side. Her head tips down a few degrees and her eyes travel down the mirror to the reflection of her shorts. Her eyes stay on the mirror. Then she straightens.
[4-6 seconds] Her head comes back level and her eyes come up the mirror to her own face in it. She looks straight into her own eyes in the reflection and holds that. She is still looking at her own face in the mirror when it ends.

Her eyes are on the mirror for the whole clip. She never looks up, never looks past the mirror, and never looks at anything in the room.

She is the only person in the room, holding one phone, and her reflection is the only place she appears.

The framing is slightly off level and off centre, the way a phone held at hip height in one hand is never square to a mirror, and it stays that way.

Her body, her left arm and her head move throughout. The phone does not. One continuous take, no cuts.

Avoid: the phone moving while the framing stays still, the framing moving while the phone stays still, her raising or lowering the phone, the phone-holding arm moving, her looking upward, her looking at the ceiling, her eyes leaving the mirror, her looking off to one side past the mirror, a different face, her face changing between frames, her body outside the mirror, a second person, a second phone, the outfit changing, extra fingers, glossy or wet-looking skin, background blur, slow motion, any cut."""

# KLING GETS A DIFFERENT PROMPT, AND IT IS BUILT TO KLING'S OWN FORMULA.
# Kling AI publishes one and it is not H3's shape:
#     Subject + Subject Description + Subject Movement + Scene
#     (+ Camera Language + Lighting + Atmosphere)
# So the SUBJECT leads. The old draft opened on "A full-length mirror selfie
# in a hallway" -- that is Scene first, with the person arriving late.
#
# THE AVOID LIST IS GONE, AND DELETING IT IS THE POINT. H3 has a DESIGNATED
# elements-to-avoid section its own guide tells you to use. Kling's docs
# mention negative prompts NOWHERE, and Kie's kling-3.0/video has no
# negative_prompt field. Pasting H3's nineteen-item avoid list in was carrying
# a model-specific convention across a model boundary -- the same class of
# error as assuming a field name transfers within a family.
# THE FAILURE MODES DID NOT GO AWAY, THEY CHANGED GRAMMAR. For a model with no
# negative handling, a negative has to be restated as a POSITIVE FACT ABOUT THE
# SCENE: not "avoid a second person", but "she is the only person in the room".
# The model can render a fact. It cannot render an absence.
#
# NO [0-2 SECONDS] BRACKETS EITHER. Kling's guide says subject movement should
# be "straightforward" and warns that the models "are not sensitive to
# numbers". Caveat, stated because it is a real tension: Kling's own 3.0 guide
# shows an example that DOES time camera moves to the second. So beats are not
# forbidden -- they are just not what the prompt guide asks for, and this shot
# is three small actions, not a timed sequence. Sequence words carry it.
#
# Kling also says to keep "visual content as simple as possible", which is the
# same instruction as SAY ONLY THE DELTA arriving from the other direction.
KLING_PROMPT = """A young woman stands in front of a full-length mirror in the hallway of a small flat, photographing her own reflection. Her skin is matte and slightly dry, with visible pores and uneven tone and only a faint sheen along the nose. She holds a white iPhone low at her hip, where it stays, and it does not cover her face.

She shifts her weight onto her other leg and pulls the hem of her open shirt straight. She turns a little to one side and looks down at her shorts in the mirror. Then she straightens, lifts her chin and looks at herself, and glances down at the phone.

The whole frame is the mirror, and everything in it is her reflection. She is the only person in the room, holding one phone, and her reflection is the only place she appears.

Static shot. The camera is locked off and does not move. One continuous take.

Even indoor light, steady throughout."""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--secs", type=int, default=6)
    ap.add_argument("--res", default="768P", choices=["768P", "2K"])
    ap.add_argument("--still", default=None, help="override the first frame")
    ap.add_argument("--budget", type=float, default=None)
    ap.add_argument("--out", default="clips/r4_fit_door_raw.mp4")
    ap.add_argument("--engine", default="h3",
                    choices=["h3", "kling", "seedance"])
    ap.add_argument("--mode", default="std", choices=["std", "pro", "4K"],
                    help="kling only")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if a.still:
        still = pathlib.Path(a.still)
    else:
        # NEWEST BY MTIME, NOT LAST ALPHABETICALLY. The filenames carry a hex
        # hash, not a counter, so sorting them is sorting noise: the regenerated
        # still w2r_fit_door_279a0c sorts BEFORE w2r_fit_door_36013e, and
        # sorted()[-1] would have quietly animated the superseded frame -- the
        # one with the cropped tank and the bare ribcage. A "latest" that is
        # alphabetical is not a latest.
        hits = sorted(glob.glob(str(ROOT / STILL_GLOB)),
                      key=lambda q: pathlib.Path(q).stat().st_mtime)
        still = pathlib.Path(hits[-1]) if hits else None
    # REFUSE RATHER THAN SUBSTITUTE. The whole cost argument for i2v is that
    # the first frame is one we LOOKED AT and approved; falling back to any
    # other frame would spend $0.52 to animate something unreviewed.
    if still is None or not still.is_file():
        print(f"  ! no approved still at {STILL_GLOB}\n"
              f"    Generate and QC it first, for $0.09:\n"
              f"        python outside.py --week2 --w2reel --all\n"
              f"    Then look at it before running this.")
        return 2

    if a.engine == "seedance":
        # SEEDANCE BECAUSE IT TAKES REFERENCES. Kling 3.0 lost her identity and
        # that was structural, not luck: on Kie it accepts `image_urls`, a
        # FIRST FRAME, and no identity input. A model given one frame and no
        # reference has to re-derive the face every frame with nothing to hold
        # it against. H3 held her face for exactly the opposite reason -- its
        # failure was skin, not identity.
        #   her on camera   -> reference conditioning, always
        #   no face in shot -> a first frame is fine, and Kling is good at it
        #
        # TWO REFERENCES, WHICH IS ALL KIE ALLOWS for Seedance 2.5. The pair
        # that carries the most: the APPROVED FIT STILL (her face, the outfit,
        # the hallway, the light, all already correct in one frame) and
        # a1_front for the face alone. c5 is dropped -- it exists to carry the
        # ribcage tattoo, and this outfit covers it.
# "LOOKS DOWN AT HER SHORTS IN THE REFLECTION" IS TWO FRAMES OF
        # REFERENCE IN ONE SENTENCE, and the model had to choose. To see her
        # shorts IN A MIRROR she looks at the glass, not down at her own body;
        # the phrase implies both and the render looked up and away instead.
        # A mirror shot has to say where the EYES land ON THE MIRROR, not
        # where the object is in the room.
        # "Lifts her chin" made it worse -- an explicit upward cue sitting one
        # line below the beat that was already ambiguous. It is now "her head
        # comes back level", and a standing instruction says her eyes are on
        # the mirror for the whole clip.
        # BEATS ARE BACK FOR SEEDANCE, AND REMOVING THEM WAS A TRANSFER ERROR.
        # The first Seedance prompt used sequence words -- "then she
        # straightens" -- because KLING'S prompt guide says its models are
        # "not sensitive to numbers". That is Kling's guidance about Kling.
        # Seedance takes [0-2 seconds] beats and every working clip in
        # make_clips234.py uses them; without a time budget per action it
        # compressed three actions into a shrug and the hand barely moved.
        # MODEL-SPECIFIC RULES DO NOT TRANSFER -- the same rule that says a
        # field name belongs to a provider and a version.
        #
        # "STATIC SHOT" WAS READ AS "STATIC SCENE". The camera instruction and
        # the subject instruction have to be separated in words, or stillness
        # leaks from one to the other.
        #
        # AND THE LAST FRAME IS THE LOOP. The first version ended "then glances
        # down at the phone", so it ended looking away -- because that is what
        # it was told. On a reel the final frame is the one that loops back to
        # the first, so the clip now ENDS on her looking at herself, which is
        # also where the closing caption lands.
        # THE TURNTABLE INSTEAD OF a1_front, BECAUSE THE SLOTS ARE THE
        # CONSTRAINT. Kie allows Seedance 2.5 exactly TWO references. a1_front
        # is one angle; master/turntable.png is twelve -- front, both 3/4s,
        # both profiles, back, and three top-downs -- in a single slot. When a
        # model has to hold a face through a turn, more angles is the whole
        # game, and this is the cheapest way to buy them.
        #
        # AND IT IS A CONTACT SHEET, WHICH IS THE RISK. Grey studio backdrop,
        # burned-in labels reading "Front", "Left 3/4", and a white tank in
        # every panel. References bleed: a sheet handed over without
        # instructions can come back as a grid, as text on screen, as a grey
        # wall, or as the wrong top. So the prompt below does not merely name
        # Image 2 -- it says what to TAKE from it and what to IGNORE. A
        # reference needs a job, and a composite reference needs a narrow one.
        from kie_api import seedance_cost
        face = ROOT / "master/turntable.png"
        if not face.is_file():
            print(f"  ! {face} not found")
            return 2
        refs = [still.resolve(), face.resolve()]
        cost = seedance_cost(a.secs, "720p", has_video_ref=False)
        print(f"  model      bytedance/seedance-2-5  (reference-to-video)")
        print(f"  Image 1    {still.name}   (scene, outfit, face)")
        print(f"  Image 2    turntable.png  (12 angles of her face)")
        print(f"  {a.secs}s at 720p, 9:16   ~${cost:.2f}")
        print(f"  prompt     {len(SEEDANCE_PROMPT)} chars\n")
        if a.dry_run:
            print(SEEDANCE_PROMPT)
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
        url = k.seedance(SEEDANCE_PROMPT, refs, duration=a.secs,
                         resolution="720p", aspect_ratio="9:16",
                         generate_audio=False)
        dest = ROOT / a.out
        n = k.download(url, dest)
        print(f"\n  {a.out}  {n // 1024} KB")
        print("  CHECK: is it HER. That is the only question this engine is")
        print("  being asked. Then the hands, then the ribcage.")
        return 0

    if a.engine == "kling":
        # KIE DOES NOT PUBLISH KLING 3.0 PRICING -- not on the model page and
        # not in the docs. A budget cap computed from a rate nobody knows is
        # not a guard, it is a decoration, so this path REFUSES to run without
        # an explicit --budget. The operator states the cap or nothing is sent.
        if a.budget is None and not a.dry_run:
            print("  ! Kie publishes no rate for Kling 3.0, so this script "
                  "cannot price it.\n"
                  "    Re-run with an explicit cap you are willing to spend:\n"
                  "        python make_fit_clip.py --engine kling --budget 1.50")
            return 2
        print(f"  model      {Kie.KLING}  mode={a.mode}")
        print(f"  first frame  {still.name}")
        print(f"  {a.secs}s, 9:16   cost UNKNOWN — cap ${a.budget or 0:.2f}")
        print(f"  prompt     {len(KLING_PROMPT)} chars\n")
        if a.dry_run:
            print(KLING_PROMPT)
            print("\n  DRY RUN — nothing sent")
            return 0
        load_key(ROOT)
        key = os.environ.get("KIE_API_KEY", "")
        if not key or key.startswith("PASTE"):
            print("no API key in kie_key.txt", file=sys.stderr)
            return 2
        k = Kie(key)
        print("  queued — a few minutes")
        url = k.kling_video(KLING_PROMPT, [still.resolve()], duration=a.secs,
                            aspect_ratio="9:16", mode=a.mode, sound=False)
        dest = ROOT / a.out
        n = k.download(url, dest)
        print(f"\n  {a.out}  {n // 1024} KB")
        print("  CHECK: her face, the hands, and that the ribcage stayed")
        print("  covered. Then:")
        print(f"      python make_reel_text.py --video {a.out} "
              f"--out clips/r4_fit_door.mp4 --set fit --fit")
        return 0

    cost = video_cost(a.secs, a.res, 1)
    print(f"  model      minimax-h3/image-to-video")
    print(f"   first frame  {still.name}")
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
        print("no API key in kie_key.txt", file=sys.stderr)
        return 2
    k = Kie(key)
    url_first = k.upload(still.resolve())
    print("  queued — a few minutes")
    url = k.video(PROMPT, url_first, duration=a.secs, resolution=a.res)
    dest = ROOT / a.out
    n = k.download(url, dest)
    print(f"\n  {a.out}  {n // 1024} KB")
    print("  WATCH THE HANDS AND THE PHONE. A fit check fails on a second")
    print("  phone or a sixth finger before it fails on anything else. Then:")
    print(f"      python make_reel_text.py --video {a.out} "
          f"--out clips/r4_fit_door.mp4")
    return 0


if __name__ == "__main__":
    sys.exit(main())
