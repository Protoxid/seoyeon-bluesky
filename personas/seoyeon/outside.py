#!/usr/bin/env python3
"""
outside.py — the majority of the feed. Places nobody expects to see twice.

A park, a restaurant, a gym, a street: a viewer has no memory of what that
corner looked like last week, so room coherence costs nothing and we can
re-render freely on Seedream instead of editing. That buys real variety in
pose, framing and distance — the thing edits could not give us.

Home stays on hero+edit (`session.py`) and is now the minority of the grid.

    python outside.py --list
    python outside.py park --dry-run
    python outside.py --all --budget 3

Runs at 1K. 2K was for the master stack, where per-crop detail had to survive
being used as a reference. A feed image is viewed at 1080px wide.
"""
from __future__ import annotations
import argparse, hashlib, os, pathlib, sys
from concurrent.futures import ThreadPoolExecutor, as_completed

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from kie_api import Kie, load_key, MODEL_I2I
# (was MODEL_T2I_SD, a seedream fallback for no-face shots. Removed: the
#  no-face path uses gpt text-to-image, in-family, so the grid stays one
#  camera. Seedream is retired and does not get a back door.)
# --model gpt swaps BOTH halves of the pair, so a no-face shot and a
# reference shot stay inside one family and the test compares like with
# like. gpt-image-2's i2i reference field is INFERRED, not documented —
# if identity comes back wrong, that is the first thing to suspect.
# fal endpoint ids. The reference field is `image_urls` here — on Kie the same
# model read `input_urls`, and sending the wrong one generated from text alone
# with no error. THE FIELD IS A PROPERTY OF THE PROVIDER, not just the model.
# Prices are Kie's published per-image rates (gpt-image-2 $0.09, seedream
# $0.07). They were 0.0 during the fal era because fal published none, and a
# guessed number in a budget guard is worse than no number: run one image, read
# the dashboard, then fill these in.
# Kie ids. FLAT price per generation, reference images included — which is the
# whole reason we came back: fal billed output tokens AND an input-token charge
# for every reference frame, so a referenced image was $0.3106 against $0.09.
#
# SEEDREAM IS NOT HERE AND MUST NOT COME BACK. It is retired in HANDOFF.md with
# the reason "pulls editorial", which is the exact failure this project exists
# to avoid, and the bake-off it supposedly won was invalid — it was scored
# while gpt-image-2's references were going to a field it does not read.
# I reintroduced it as a plate renderer purely because Kie's gpt TEXT-to-image
# enum lacks 4:3. That was a mechanical argument that never weighed why the
# model was dropped, AND THE CONSTRAINT DID NOT EVEN APPLY: every plate was
# already generated, and gpt image-to-image does take 4:3, 16:9 and 21:9 if a
# wide plate is ever needed again.
FAMILIES = {
 "gpt": ("gpt-image-2-image-to-image", "gpt-image-2-text-to-image", 0.09),
}


# uploads are a method on the client now: kie.upload(path)
# (was: from content import IPHONE_LEAN -- unused, and content.py is now
#  retired. An unused import is how a live file inherits a dead file's
#  dependencies: this one line took the whole grid down with kie_api.)

# The indoor lens line talks about "the room" and repeats the off-level note
# that the camera lines already carry. Outdoors needs its own.
LENS = ("Shot on an iPhone 15 Pro: flat HDR contrast, low saturation, deep "
        "focus so the background stays legible, fine noise in the shadows. "
        "Skin shows pores and small unevenness.")

# The front camera is a different sensor, so it gets its own processing line
# rather than inheriting the rear one — and this keeps the selfie prompts short.
LENS_FRONT = ("Shot on an iPhone 15 Pro front camera: flat HDR contrast, low "
              "saturation, softer and noisier than the rear lens. Skin shows "
              "pores and small unevenness.")

ROOT = pathlib.Path(__file__).parent
MASTER = ROOT / "master" / "a"
OUT = ROOT / "content" / "outside"
# "1k" means one MEGAPIXEL, not 1080 on the long edge: at 3:4 it returns
# 896x1184, at 9:16 768x1376. Instagram's floor is 1080 wide, so a 1k shot
# uploads soft and resizing up is worse than useless. 2k is the minimum
# publishable tier. The saving was $0.03 an image; it cost the batch.
TIER = "2k"

# WIDE SHOTS RUN AT 2K. A full-body frame gives the face a fraction of the
# pixel budget, so fine detail degrades however good the references are — this
# is a resolution problem, not a reference problem. Naming the wide shots
# explicitly beats guessing from the text, and keeps the cost visible: these
# cost 0.07 instead of 0.04.
WIDE = {
 ("park", 0), ("park", 2), ("park", 3),
 ("gym", 1), ("gym", 2),
 ("street", 0), ("street", 1), ("street", 4),
 ("market", 1),
 ("river", 0), ("river", 1), ("river", 3),
}
PRICE = 0.07          # 2k everywhere: 1k is under the platform floor

# Two face references, front plus three-quarter, as established.
FACE = ["a1_front.png", "a2_tq_left.png"]
ROLES = ("Images 1 and 2 are her face from two angles — use them for her "
         "features and the pale freckles on her nose and inner cheeks.")

# HEAD-TO-BODY PROPORTION. Two face references are both head shots, and on a
# full-length frame the model scales the head to honour them — giving a head
# too large for the body. `master/c/c5_relax_front.png` is the full-body
# reference the stack already contains; attaching it on wide frames gives the
# proportion something to anchor to. Shots opt in with body=True.
# SKIN. The model defaults to a "glass skin" specular sheen — bright highlights
# on the cheekbones, nose bridge and forehead in every single frame. It reads as
# heavy highlighter or oil, it is uniform across shots so it compounds, and it
# is one of the most reliable AI tells there is. "Skin shows pores" does not
# touch it: pores are texture, this is specular response.
# Stated positively, and with a small amount of shine kept — completely matte
# skin is its own tell.
# REWRITTEN. The previous version read "no wet highlight on the cheekbones or
# brow" — a NEGATION naming the exact artifact, sitting in every prompt this
# project has ever sent. Our most expensive rule is that naming a thing summons
# it, and the block written to suppress the highlight was naming it, on the
# cheekbones and brow specifically, in every single generation.
# Stated positively now: the sheen is BOUNDED to where it belongs instead of
# forbidden where it does not.
# TRIMMED. Same four instructions — matte, dry, textured, sheen bounded to the
# nose — in half the words. It was 275 characters against a 400-character shot.
SKIN = ("Her skin is matte from brow to jaw and reads slightly dry: visible "
        "pores, uneven tone, the only sheen a faint one along the nose.")

# ARM COUNT. A close selfie with a busy free hand comes back with an extra
# limb. Counting them explicitly is the only thing that has held.
# REWRITTEN after Qwen returned both arms reaching for the lens. The old text
# counted to two but never said what the second arm is DOING, so the model gave
# it the same job as the first. Counting is not placing.
ARMS = ("She has two arms and only one of them reaches toward the camera. The "
        "other stays down against her body.")

BODY_REF = "master/c/c5_relax_front.png"
ROLES_BODY = ("Images 1 and 2 are her face from two angles — use them for her "
              "features and the pale freckles on her nose and inner cheeks. "
              "Image 3 is her full length — use it only for build and "
              "head-to-body proportion.")

# HAIR. She has a default and she changes it, the way anyone does. Stated per
# shot rather than left to the reference, because the reference will hold the
# default forever otherwise. Colour never changes — the balayage is signature.
HAIR = {
 "default": "Her hair is down in soft natural waves, centre-parted with curtain bangs.",
 "bun":     "Her hair is up in a low bun with a few pieces escaping at the nape.",
 "clip":    "Her hair is half-up in a claw clip, the lengths loose below it.",
 "pony":    "Her hair is in a high ponytail, bangs still forward.",
 "tucked":  "Her hair is down but tucked behind both ears.",
 "cap":     "Her hair is pulled through the back of a plain black cap, the ends loose.",
}

# WHO IS HOLDING THE CAMERA. Outside, "propped on the furniture" stops working.
# Three honest answers, and each one changes the framing.
# WHO IS HOLDING THE CAMERA. Outdoors, "propped on the furniture" stops
# working. The arm's-length front selfie is the DEFAULT — it is how a woman out
# on her own actually photographs herself, and it should be the majority.
# The front camera is a different lens from the rear one: ~23mm equivalent,
# 12MP, softer and noisier, with real perspective stretch at arm's length.
# A selfie that renders like the rear camera reads wrong without anyone being
# able to say why.
FRONT = ("Front camera at arm's length: a 23mm-equivalent lens close to her "
         "face, so her features "
         "stretch very slightly. Her extended arm cuts into a corner and is "
         "holding the only phone in the picture; her other hand is free. "
         "Horizon a few degrees off level.")

CAM = {
 "selfie": FRONT + " She is looking into the lens.",
 "selfie_away": FRONT + " She is looking past the lens rather than into it, at something off to the side.",
 "mirror": ("Her reflection in a mirror, the phone held at chest height in one "
            "hand and visible in the shot, the room reversed behind her, "
            "slightly rolled."),
 "friend": "Taken by somebody walking with her, from a step or two away, slightly off-centre and a degree off level.",
 "stranger": "Taken by somebody she asked, standing further back than she would have chosen, a lot of the place in frame around her.",
 "alone": "Set down on something nearby and left running, low and slightly wrong, with more space on one side than she needs.",
}

# Prompts live in outside_shots.py, one authored description each. No field
# assembly: a coat cannot appear in a scene without one, a selfie cannot have
# folded arms, a wall cannot carry writing the lens is meant to blur, because
# each prompt was written as a single thought rather than five fields collided.
from outside_shots import SHOTS
# The Exclusive / Subscriber set — private, intimate, SFW moments (Plan B).
try:
    from exclusive_shots import SHOTS as EX_SHOTS
except Exception:
    EX_SHOTS = []
# The Fanvue set is a different tier and a different destination — kept in its
# own file and its own output folder so it can never reach the Instagram bank.
try:
    from fanvue_shots import SHOTS as FV_SHOTS
except Exception:
    FV_SHOTS = []

# 9:16 first frames for the Reel. Same pipeline, own pool, own folder: these
# are seeds for video, not feed posts, and must never enter the grid bank or
# the audit's distribution counts.
try:
    from reel_frames import SHOTS as RF_SHOTS
except Exception:
    RF_SHOTS = []

# Shots written from week.md — each carries a story= premise naming a slot.
try:
    from week_shots import SHOTS as WK_SHOTS
except Exception:
    WK_SHOTS = []

# Location plates for POV clips and room conditioning. Nobody is in them.
try:
    from pov import PLATES as POV_PLATES
except Exception:
    POV_PLATES = []

# Week two. Same shape as grid_shots: feed frames plus 9:16 reel frames.
try:
    from week2_shots import SHOTS as W2_SHOTS, REEL as W2_REEL
except Exception:
    W2_SHOTS, W2_REEL = [], []

# W37 (Mon 7 - Sun 13 Sep). The pool the week-31 plan could not render: the
# shots live in content/w37_2026-09-07 and the prompts in w37_shots.py. Same
# dict shape as week2_shots, own destination, no reel set.
try:
    from w37_shots import SHOTS as W37_SHOTS
except Exception:
    W37_SHOTS = []

# The grid rebuild. Feed frames and the reel's 9:16 first frames.
try:
    from grid_shots import SHOTS as GRID_SHOTS, REEL as GRID_REEL
except Exception:
    GRID_SHOTS, GRID_REEL = [], []

# The identity LoRA training set. 30 shots, own destination, never mixed into
# the feed pools — these are training data, not posts.
try:
    from lora_shots import SHOTS as LORA_SHOTS
except Exception:
    LORA_SHOTS = []

# The only thing appended. It is an instruction about the attached files, not
# part of the description, so it stays outside the authored text.
ROLES = ("Images 1 and 2 are her face from two angles — use them for her "
         "features and the pale freckles on her nose and inner cheeks.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scene", nargs="?", help="id prefix, e.g. park, gym, river")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--only", help="comma-separated shot ids")
    ap.add_argument("--exclusive", action="store_true", help="run the exclusive_shots set into content/exclusive")
    ap.add_argument("--fanvue", action="store_true",
                    help="run the fanvue_shots set into content/fanvue")
    ap.add_argument("--reel-frames", action="store_true",
                    help="run the reel_frames set into content/reel_frames")
    ap.add_argument("--week", action="store_true",
                    help="run the week_shots set into content/week")
    ap.add_argument("--week2", action="store_true",
                    help="run week2_shots into content/week2")
    ap.add_argument("--week3", action="store_true",
                    help="run w37_shots into content/w37_2026-09-07")
    ap.add_argument("--lora", action="store_true",
                    help="run lora_shots into content/lora — the identity "
                         "LoRA training set")
    ap.add_argument("--plates", action="store_true",
                    help="run pov.PLATES into content/plates — location "
                         "references, generated once and reused")
    ap.add_argument("--w2reel", action="store_true",
                    help="with --week2: the 9:16 reel first frames instead")
    ap.add_argument("--day", help="filter to one day of her week: mon..sun")
    ap.add_argument("--grid", action="store_true",
                    help="run grid_shots into content/grid")
    ap.add_argument("--reel", action="store_true",
                    help="with --grid: the 9:16 reel stills instead of the feed set")
    ap.add_argument("--n", type=int, default=1)
    # NO ARBITRARY DEFAULT. A cap of 0.5 against a batch just quoted at $2.12
    # skipped every single shot and reported it as a budget decision, which
    # looks exactly like a guard working correctly.
    ap.add_argument("--budget", type=float, default=None,
                    help="hard cap in $. Defaults to the batch cost printed "
                         "above, so it stops a typo without refusing a run "
                         "you have already been quoted.")
    # GPT-IMAGE-2 IS THE DEFAULT. Qwen won the first three-way test, but that
    # test was run while gpt-image-2's references were going to the WRONG FIELD
    # (image_urls instead of input_urls), so gpt was generating from text alone
    # and losing on identity for a reason that had nothing to do with the
    # model. Re-run with the field fixed, it produced the best images of the
    # project: the market stall another AI argued was a real photograph, and a
    # studio selfie with correct skin, correct arm distortion and real people.
    # Qwen stays available and remains the only one with negative_prompt/seed.
    # KNOWN: gpt-image-2 refuses the mirror-selfie prompt. Cause unconfirmed.
    ap.add_argument("--model", choices=list(FAMILIES), default="gpt",
                    help="which model family to render with")
    ap.add_argument("--dry-run", action="store_true")
    # Kie publishes per-image prices, so FAMILIES carries real numbers and
    # --unit-price is no longer needed. (Under fal it carried 0.0, because
    # carries 0.0 rather than a guess. A zero unit price makes every estimate
    # $0.00, which does not make runs free -- it DISABLES THE BUDGET CAP, since
    # nothing can ever exceed it. The migration introduced that hole silently.
    # So: no price, no spending. Pass the real number once, read it off the fal
    # dashboard, then write it into FAMILIES and this stops being needed.
    ap.add_argument("--unit-price", type=float, default=None,
                    help="$ per image. REQUIRED while FAMILIES has 0.0 — the "
                         "budget cap is meaningless without it.")
    a = ap.parse_args()
    if a.model == "seedream":
        sys.exit("seedream is retired: it pulls editorial, and the bake-off it "
                 "won was scored on a broken integration. gpt-image-2 is the "
                 "renderer.")
    I2I, T2I, UNIT = FAMILIES[a.model]
    if a.unit_price is not None:
        UNIT = a.unit_price

    # --only must not fall into the listing branch: with no positional
    # scene and no --all it looked exactly like a bare invocation.
    if sum([a.fanvue, a.reel_frames, a.week, a.week2, a.week3, a.grid,
            a.plates, a.lora]) > 1:
        sys.exit("--fanvue, --reel-frames, --week, --week2, --week3, --lora "
                 "and --grid are different destinations")
    if a.reel and not a.grid:
        sys.exit("--reel only means anything with --grid")
    if a.w2reel and not a.week2:
        sys.exit("--w2reel only means anything with --week2")
    pool = (EX_SHOTS if (getattr(a, "exclusive", False) or a.fanvue) else RF_SHOTS if a.reel_frames
            else WK_SHOTS if a.week
            else POV_PLATES if a.plates
            else LORA_SHOTS if a.lora
            else (W2_REEL if a.w2reel else W2_SHOTS) if a.week2
            else W37_SHOTS if a.week3
            else (GRID_REEL if a.reel else GRID_SHOTS) if a.grid else SHOTS)
    if a.week2:
        globals()["OUT"] = ROOT / "content" / ("week2_reel" if a.w2reel
                                               else "week2")
    if a.week3:
        globals()["OUT"] = ROOT / "content" / "w37_2026-09-07"
        if not pool:
            sys.exit("w37_shots.py not found or empty")
        if not pool:
            sys.exit("week2_shots.py not found or empty")
    if a.lora:
        globals()["OUT"] = ROOT / "content" / "lora"
        if not pool:
            sys.exit("lora_shots.py not found or empty")
    if a.plates:
        globals()["OUT"] = ROOT / "content" / "plates"
        if not pool:
            sys.exit("pov.py not found or has no PLATES")
    if getattr(a, "exclusive", False) or a.fanvue:
        globals()["OUT"] = ROOT / "content" / ("exclusive" if getattr(a, "exclusive", False) else "fanvue")
        if not pool:
            sys.exit("fanvue_shots.py not found or empty")
    if a.reel_frames:
        globals()["OUT"] = ROOT / "content" / "reel_frames"
        if not pool:
            sys.exit("reel_frames.py not found or empty")
    if a.week:
        globals()["OUT"] = ROOT / "content" / "week"
        if not pool:
            sys.exit("week_shots.py not found or empty")
    if a.grid:
        globals()["OUT"] = ROOT / "content" / ("grid_reel" if a.reel else "grid")
        if not pool:
            sys.exit("grid_shots.py not found or empty")

    if a.list or (not a.scene and not a.all and not a.only):
        # UNIT, not a hardcoded Seedream price. It survived the migration
        # and quoted $0.07 an image for a provider that bills on tokens.
        cost = UNIT * len(pool)
        for d in pool:
            print(f"  {d['id']:<18}{d['tier']}  {d.get('aspect','3:4'):<5}"
                  f"{d['text'][:50]}...")
        print(f"\n  {len(pool)} shots, "
              + (f"~${cost:.2f}" if UNIT > 0 else
                 "price per image unknown — pass --unit-price"))
        return 0

    # A shot with nobody in it must not carry face references. ROLES tells the
    # model "images 1 and 2 are the same woman's face" — attach that to a photo
    # of a fruit stall and it will helpfully put her in the fruit stall.
    # A no-face shot with a LIMB in it still needs a reference. With none
    # attached and no person described, the model has nothing to say whose the
    # knee is — and n_desk_late came back with a MAN'S LEG. Words cannot fix
    # that ("a bare woman knee" invites a whole woman); a picture of her body
    # can. limb=True attaches the body frame and says what it is for.
    ROLE_LIMB = ("Image 1 is the same woman full length — the arm or leg "
                 "visible at the edge of this frame is hers. Nobody else is "
                 "in the picture.")

    # A ROOM IS NOW A PHOTOGRAPH, NOT A DESCRIPTION.
    # The old rule — "a location plate attached as a reference makes the model
    # composite" — was measured on Seedream and is false of gpt-image-2, which
    # puts her IN the room with shared light. So a shot can name a plate and
    # the room stops being reinvented every time it appears.
    # The plate goes FIRST in the reference list, and the text says so by
    # index, because an attached reference with no stated job is the mistake
    # that put a second woman in a frame.
    ROLE_PLATE = ("Image 1 is the room this photograph is taken in. Use it for "
                  "the layout, the furniture, the surfaces and the light — it "
                  "is the same room, not a similar one. Nobody is in Image 1; "
                  "the people described below are.")

    def roles_for(d):
        """Reference roles numbered from the ACTUAL upload order.

        THE BUG THIS REPLACES. The plate is prepended to the reference list at
        send time, so with a plate attached her face is Images 2 and 3 and her
        body is Image 4. ROLES/ROLES_BODY/ROLE_LIMB hardcoded 1/2/3 while
        ROLE_PLATE separately claimed Image 1 — so every plated shot shipped a
        prompt saying the ROOM was her face, and the room and the face were
        both Image 1 in the same breath.
        It affected w2_desk_rain, w2_kitchen_sun and w2_broken_machine, which
        were generated and passed QC anyway: the model recovered from the
        contradiction. THEY ARE NOT BEING REGENERATED — they passed, and a
        withdrawn judgement must not survive in a file. But a prompt that
        contradicts itself is not something to keep sending, and the next
        plated shot is a fit check where the room and the outfit both matter.
        An ordinal is a property of the LIST, so it gets computed from the list
        and never written down twice.
        """
        o = 1 if d.get("plate") else 0        # the plate occupies Image 1
        if d.get("limb"):
            return (f"Image {o+1} is the same woman full length — the arm or "
                    f"leg visible at the edge of this frame is hers. Nobody "
                    f"else is in the picture.")
        t = (f"Images {o+1} and {o+2} are her face from two angles — use them "
             f"for her features and the pale freckles on her nose and inner "
             f"cheeks.")
        if d.get("body"):
            t += (f" Image {o+3} is her full length — use it only for build "
                  f"and head-to-body proportion.")
        return t

    # ROLE_PLATE closes with "Nobody is in Image 1; the people described below
    # are." True for a shot of a person in a room. FALSE for a no-face frame,
    # where nobody is described below at all — there it reads as an instruction
    # to add someone, in exactly the frames whose entire job is to be empty.
    ROLE_PLATE_EMPTY = ROLE_PLATE.rsplit(". Nobody is in Image 1", 1)[0] + (
        ". Nobody is in Image 1 and nobody is in this photograph either.")

    def build_noface(d):
        p = []
        if d.get("phone"):
            p.append(PHONE)
        if d.get("plate"):
            p.append(ROLE_PLATE_EMPTY)
        if d.get("limb"):
            p.append(roles_for(d))
        return "\n\n".join([d["text"]] + p)

    # gpt-image-2 refused n_roof_posed as nsfw: a woman alone, short dress,
    # rooftop, midnight, full length. Nothing in the shot is sexual, so the
    # frame says so. Only appended where the filter has actually tripped —
    # adding it everywhere would be sixteen wasted characters a shot and would
    # put the word in prompts that never needed it.
    SAFE = ("An ordinary fully clothed everyday snapshot, nothing sexual "
            "about it.")

    # HER PHONE, when it is a PROP rather than the camera. She owns one phone
    # and it is the same phone in every picture, exactly like the towel and the
    # bag. Sent only on shots flagged phone=True: when the phone is the CAMERA
    # it is invisible and describing it summons it into the frame, which is the
    # "never name the camera device" rule and is still true.
    PHONE = ("The phone in the picture is her own: a white iPhone 15 Pro with "
             "a plain clear case, slightly scuffed at one corner.")

    def plate_ref(d):
        """Resolve a shot's plate= to a file, or refuse.

        A missing plate is a HARD ERROR rather than a silent fallback to a
        described room: the whole reason to name one is that the description
        was not holding the room still, so quietly reverting to it would
        reintroduce exactly the fault, invisibly, at full price."""
        pid = d.get("plate")
        if not pid:
            return None
        try:
            from pov import plate_path
        except Exception:
            sys.exit(f"{d['id']} names plate {pid!r} but pov.py will not import")
        p = plate_path(pid)
        if p is None:
            sys.exit(f"\n  {d['id']} needs plate {pid!r} and it is not on "
                     f"disk.\n"
                     f"  Put it at content/plates/{pid}.png, or generate it "
                     f"with:\n"
                     # Concrete numbers, not <placeholders>: in PowerShell
                     # `<` is a reserved redirection operator, so an angle
                     # bracket in a suggested command is a PARSE ERROR before
                     # it is ever a wrong value.
                     f"      python outside.py --plates --only {pid} "
                     f"--unit-price 1.50 --budget 1.60\n"
                     f"  Refusing to fall back to a described room — that is "
                     f"the fault plates exist to fix.")
        return p

    def build(d):
        """The prompt, assembled once. The dry run printed its own version and
        so hid two clauses that the real call was sending."""
        # The phrase can describe where the CAMERA sits rather than how she
        # is holding it ("resting on the mattress an arm's length from her"),
        # and the ARMS block then tells a sleeping woman to reach for the
        # lens. Shots may state it outright; the phrase is only the default.
        selfie = d.get("selfie", "arm's length" in d["text"].lower())
        parts = [d["text"]] + ([SAFE] if d.get("safe") else []) + [SKIN]
        if selfie:
            parts.append(ARMS)
        parts.append(roles_for(d))
        if d.get("phone"):
            parts.append(PHONE)
        if d.get("plate"):
            parts.insert(1, ROLE_PLATE)
        return "\n\n".join(parts)

    _build = build
    build = lambda d: build_noface(d) if d.get("noface") else _build(d)

    want = pool
    if a.only:
        # SPLIT ON COMMAS *AND* WHITESPACE, and strip. In PowerShell
        #     --only a, b
        # is two arguments: --only gets "a," and "b" lands on the positional
        # `scene`. The old code then ran ONE shot and said nothing, which is a
        # silent misread of what was asked for, with money attached.
        import re as _re3
        ids = [x for x in _re3.split(r"[,\s]+", a.only.strip()) if x]
        if a.scene:
            ids.append(a.scene)
            print(f"  note: '{a.scene}' was read as a separate argument and "
                  f"folded into --only.\n"
                  f"        In PowerShell use no spaces: --only a,b")
        known = {d["id"] for d in pool}
        unknown = [i for i in ids if i not in known]
        if unknown:
            # A TYPO USED TO COST A SILENT PARTIAL RUN: --only real,typo ran
            # one shot and reported success. Every id must exist or nothing
            # runs.
            sys.exit(f"\n  unknown shot id(s): {', '.join(unknown)}\n"
                     f"  nothing has been generated. Known ids in this pool:\n"
                     f"      {', '.join(sorted(known))}")
        want = [d for d in pool if d["id"] in ids]
        if not want:
            sys.exit(f"no shot id matching '{a.only}'. Try --list.")
    elif not a.all:
        want = [d for d in pool if d["id"].startswith(a.scene)]
        if not want:
            sys.exit(f"nothing starting '{a.scene}'. Try --list.")

    # She takes several pictures on a given day and posts one. --day gives
    # the batch a real day belongs to, so the choice is between three things
    # that could have happened to the same person between waking and bed.
    if a.day:
        want = [d for d in want if d.get("day") == a.day.lower()]
        if not want:
            sys.exit(f"no shots tagged day='{a.day.lower()}'")

    # VALIDATE EVERY PLATE BEFORE SPENDING ANYTHING. The check used to live
    # inside the worker, which meant a missing plate killed the run halfway
    # through — after paying for the shots that happened to sort first. A
    # precondition that is checked during the work is not a precondition.
    for d in want:
        plate_ref(d)

    # Per-image cost is per-PIXEL on this provider, so a single --unit-price
    # is wrong the moment a batch mixes sizes — a plate and a feed frame differ
    # by 6x. Price each shot by its own size and only fall back to a flat
    # figure if one was given explicitly.
    if a.unit_price is None:
        from kie_api import image_cost
        # A no-face shot with no limb attaches NOTHING and goes to
        # text-to-image, so it pays no input tokens. Pricing every shot as if
        # it carried references overstated a mixed batch by about a third.
        def _nrefs(d):
            if d.get("noface"):
                return 1 if (d.get("limb") or d.get("plate")) else 0
            return 2 + (1 if d.get("body") else 0) + (1 if d.get("plate") else 0)
        cost = sum(image_cost(d.get("aspect", "3:4"), d["tier"], _nrefs(d))
                   for d in want) * a.n
        UNIT = cost / max(1, len(want) * a.n)
    else:
        cost = UNIT * len(want) * a.n
    if a.budget is None:
        a.budget = round(cost * 1.02 + 0.01, 2)
    if cost <= 0 and not a.dry_run:
        sys.exit(
            f"\n  {len(want)*a.n} image(s), but the price per image is not "
            f"known.\n"
            f"  fal does not publish it and I will not guess one into a budget\n"
            f"  guard. Generate ONE image, read the deduction on the fal\n"
            f"  dashboard, then either:\n"
            f"      python outside.py ... --unit-price 0.04\n"
            f"  or put the real number in FAMILIES in this file.\n"
            f"  (--dry-run still works and costs nothing.)")
    print(f"  {len(want)*a.n} image(s)  ~${cost:.2f}\n")
    if a.dry_run:
        for d in want:
            print("=" * 66)
            print(f"[{d['id']}  {d['tier']}]\n{build(d)}")
        return 0

    load_key(ROOT)
    key = os.environ.get("KIE_API_KEY", "")
    if not key or key.startswith("PASTE"):
        sys.exit("no API key in kie_key.txt")
    kie = Kie(key)
    refs = [kie.upload((MASTER / n).resolve())
            for n in FACE if (MASTER / n).exists()]
    body_url = None
    bp = (ROOT / BODY_REF)
    if bp.exists():
        body_url = kie.upload(bp.resolve())
    elif any(d.get("body") for d in want):
        print(f"  ! {BODY_REF} missing — wide frames may come back "
              f"head-heavy")
    if len(refs) < 2:
        print("  ! fewer than two face references found — identity will be weaker")

    OUT.mkdir(parents=True, exist_ok=True)
    spent = [0.0]

    def one(job):
        d, vi = job
        # Each shot pays for ITS OWN pixels. Charging the batch average made
        # a cheap shot subsidise an expensive one against the cap, and on a
        # mixed batch the arithmetic was simply wrong.
        if a.unit_price is not None:
            price = a.unit_price
        else:
            from kie_api import image_cost as _ic
            price = _ic(d.get("aspect", "3:4"), d["tier"], _nrefs(d))
        if spent[0] + price > a.budget:
            return d["id"], "skip", "budget cap"
        spent[0] += price
        use_body = d.get("body") and body_url
        prompt = build(d)
        h = hashlib.sha256(prompt.encode()).hexdigest()[:6]
        dest = OUT / f"{d['id']}_{h}_{vi}.png"
        try:
            # A no-person shot sends no images, and Seedream image-to-image
            # requires one — that is the "This field is required" 500. It has
            # to go to TEXT-to-image. Staying inside the Seedream family keeps
            # the grid looking like one camera, and costs the same.
            nf = d.get("noface")
            if nf:
                these = [body_url] if (d.get("limb") and body_url) else []
            else:
                these = refs + ([body_url] if use_body else [])
            # The plate is Image 1. ROLE_PLATE addresses it by that index, so
            # it has to be first in the list and nowhere else.
            pp = plate_ref(d)
            if pp is not None:
                these = [kie.upload(pp.resolve())] + these
            urls = kie.generate(prompt, d.get("aspect", "3:4"), these,
                                model=(T2I if (nf and not these) else I2I),
                                tier=d["tier"])
            n = kie.download(urls[0], dest)
            return d["id"], "ok", f"{dest.name}  {n//1024} KB  [{d['tier']}]"
        except Exception as e:
            spent[0] -= price
            return d["id"], "fail", str(e)[:120]

    jobs = [(d, v) for d in want for v in range(1, a.n + 1)]
    with ThreadPoolExecutor(max_workers=3) as ex:
        for f in as_completed([ex.submit(one, j) for j in jobs]):
            i, st, msg = f.result()
            print(f"  [{i:<18}] {'  ok  ' if st=='ok' else ' FAIL ' if st=='fail' else ' skip '} {msg}")

    print(f"\n  ~${spent[0]:.2f} -> {OUT}")
    print(f"  Now: python drift_gate.py --in {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
