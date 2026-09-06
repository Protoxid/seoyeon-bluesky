#!/usr/bin/env python3
"""
audit_video.py — run the realism rules against VIDEO prompts.

`audit.py` has always checked the still pools. The video prompts have never
been checked by anything: they were written by hand, read by eye, and declared
ready. Every rule below is already in the playbook and was already paid for on
the stills side; none of it was being enforced on the thing that actually got
published as a reel.

    python audit_video.py

THREE THINGS THE FIRST VERSION OF THIS FILE GOT WRONG, kept here because a
checker that cries wolf gets ignored and then a real flag gets ignored with it:

  1. A FIXED-WIDTH LOOKBACK CANNOT FIND "Avoid:". Every one of our prompts ends
     with one long "Avoid: a, b, c, d, ..." sentence. "shallow depth of field"
     sits 180 characters into it, and a 60-character lookback sees only ", slow
     motion, colour grading, ". The negation test has to run over the whole
     SENTENCE, because that is the unit the negation actually scopes over.
  2. NO PERSON IN FRAME MEANS NO SKIN RULES. A POV clip has no face in it, so
     demanding a skin block and a wardrobe clause is demanding text that would
     only compete with the pixels. "If she is not in frame, the identity
     problem does not exist" is already a playbook rule.
  3. NEVER INVENT THE PARAMETERS. The first version assumed every prompt found
     in a doc had two references attached, then flagged it for not saying what
     Image 1 was for. The reference count is not knowable from a blockquote, so
     the rule does not run there.

And one it MISSED, which is worse. "the light goes across her face" did not
fire HARD LIGHT ON THE FACE because the regex wanted a hardness adjective in
the same sentence. The hardness was declared one sentence earlier, on the room.
Any sentence that aims light AT HER FACE is the failure, adjective or not.
"""
from __future__ import annotations
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent
FAIL: list[tuple[str, str, str]] = []

# a prompt that says this has no person in it, so the skin and wardrobe rules
# have nothing to bite on
NO_PERSON = re.compile(
    r"nobody in shot|nobody is in the room|no one is in shot|"
    r"is not visible and is never in shot|nobody enters|"
    # the avoid-list form. Trimming the prose left only this, and it is the
    # stronger statement of the two, so the checker has to read it.
    r"avoid:[^.]{0,300}\bany person\b|"
    # A CLIP CAN CONTAIN A PERSON AND STILL HAVE NO SKIN AND NO FACE IN IT.
    # pov_river_walk shows her SHADOW and her SHOES and nothing else, and it
    # says so twice — in the beats and in the avoid list. The old pattern only
    # recognised rooms with nobody in them, so it flagged a missing skin block
    # for a clip with no skin in it and a missing framing error for a clip with
    # no face to frame. Both flags were real rules firing on the wrong shot,
    # which is the failure mode this checker has already produced once.
    # Deliberately narrow: it wants BOTH the body and the face excluded, so a
    # prompt that hides the face but shows bare arms still gets the skin rule.
    r"avoid:[^.]{0,300}\bher body\b[^.]{0,200}\bher face\b", re.I)


def flag(where: str, rule: str, why: str) -> None:
    FAIL.append((where, rule, why))


def negated(low: str, at: int) -> bool:
    """Is the term at `at` inside a negation?

    Scoped over the whole sentence, not a fixed window, because our negations
    live in one long comma list that opens with 'Avoid:'.
    """
    # A BARE NEWLINE IS NOT A SENTENCE BREAK. The docs hard-wrap, so the
    # "Avoid:" that scopes the whole list can sit two lines above the term it
    # negates. Only whitespace PRECEDED BY sentence punctuation ends a
    # sentence; a blank line ends a paragraph.
    bounds = [m.end() for m in re.finditer(r"(?<=[.!?])\s|\n\s*\n", low[:at])]
    seg = low[(bounds[-1] if bounds else 0):at]
    return bool(re.search(r"\bavoid\b|\bno\b|\bnot\b|\bwithout\b|\bnever\b",
                          seg))


# Naming the device as a LENS SPEC has never summoned one: "Shot on an iPhone
# 15 Pro: flat contrast..." is a description of the picture. Naming how it is
# HELD describes an object in the scene, and the model duly renders it. The POV
# skeleton opened "filmed on an iPhone held in one hand, first-person point of
# view. The person holding the phone is not visible and is never in shot" — a
# hand, a phone and a person, all in the positive prompt, and a phone appeared.
# The second sentence is the worse half: a denial still names the thing.
# "handheld" WAS IN THIS LIST AND SHOULD NOT HAVE BEEN. The failure was the
# camera as an OBJECT — "held in one hand", "the person holding the phone".
# "Handheld" describes MOTION, it is the standard word for it, H3's own guide
# uses "subtle handheld shake", and banning it produced smooth glide-cam
# footage that read as a render. A checker that enforces an over-correction is
# worse than no checker: it makes the mistake permanent and looks principled.
HOLDER = re.compile(
    r"held in (?:one|her|his|the) hand|the person holding|"
    r"holding the phone|phone (?:is )?held|\bin one hand\b", re.I)


def check(name: str, p: str, *, has_body_ref: bool = False,
          n_refs: int | None = None, phone_in_frame: bool = False,
          has_plate: bool = False) -> None:
    low = p.lower()
    peopled = not NO_PERSON.search(p)

    # MIRROR PHYSICS. In a mirror shot the camera is INSIDE THE FRAME: the
    # phone visible in the reflection IS the lens. So a sentence pinning the
    # camera and a sentence moving the phone are two instructions about ONE
    # object, and giving them opposite values asks for something physically
    # impossible. It renders as a phone that slides while the framing stays
    # nailed down, and a viewer feels that without being able to name it.
    # This cost three renders at $1.89 before anyone said the word "mirror".
    mirror = bool(re.search(r"\bmirror\b", low))
    if mirror:
        camera_pinned = re.search(
            r"camera does not move|static shot|framing (?:stays|does not)|"
            r"no pan, no zoom", low)
        phone_moves = re.search(
            r"(?:raises?|lifts?|lowers?|moves?|turns?|tilts?) the phone|"
            r"phone (?:hand|arm)[^.]{0,40}(?:moves|comes up|lifts)|"
            r"(?:her|the) (?:arm|hand)s? (?:and (?:her )?head )?move", low)
        if camera_pinned and phone_moves and not re.search(
                r"phone in the mirror is the camera|"
                r"whatever the phone does, the frame does|"
                r"the phone does not", low):
            flag(name, "MIRROR PHYSICS",
                 "the camera is pinned AND something moves the phone or the "
                 "arm holding it. In a mirror shot the phone IS the camera: "
                 "state that, pin the phone, and give the moving job to the "
                 "OTHER hand")
        # An eyeline in a mirror shot has to be stated ON THE GLASS. "looks
        # down at her shorts" mixes two frames of reference -- the shorts are
        # in the room, the reflection is on the mirror -- and the model has to
        # pick one. It picked wrong, at $1.89.
        if re.search(r"looks? (?:down|up) at (?:her|the)\s+(?!own)"
                     r"(?!reflection)(?!face)\w+", low) and not re.search(
                     r"eyes? (?:stay|travel|are) on the mirror|down the mirror",
                     low):
            flag(name, "MIRROR EYELINE",
                 "an eyeline is given relative to the room, not the glass. In "
                 "a mirror shot say where the eyes land ON THE MIRROR")


    # NAME THE PLACE, never the category — unless a PLATE is attached, in
    # which case the place arrives as pixels and naming it again in text is the
    # re-description that competes with them.
    if not has_plate and \
            not re.search(r"\b(seoul|seongsu|euljiro|ttukseom|han river)\b", low):
        flag(name, "NO PLACE NAMED",
             "an unqualified location renders as the training set's average, "
             "and the average is not Seoul")

    # the skin block — only if there is skin in the shot
    if peopled and not re.search(r"matte|visible pores|uneven tone", low):
        flag(name, "NO SKIN BLOCK",
             "a video model re-renders skin every frame and its own prior is "
             "glossy — the still's matte skin is NOT inherited")

    # words that compound the default glass-skin sheen
    for m in re.finditer(r"\b(shiny|sheen|glow|glowing|dewy|glossy|luminous|"
                         r"radiant|wet-looking)\b", low):
        if negated(low, m.start()) or "only sheen a faint one" in low:
            continue
        flag(name, "SHINE", f"'{m.group()}' compounds the default highlight")
        break

    # cinematic vocabulary as a POSITIVE instruction
    # "out of focus" as a POSITIVE instruction is the same class as "bokeh",
    # and it slipped through as prose rather than as a term: clip 1 said "a
    # window a little out of focus behind her" and came back with exactly the
    # soft background that is our loudest single AI tell.
    for w in ("cinematic", "film look", "filmic", "colour grade", "color grade",
              "anamorphic", "bokeh", "shallow depth", "out of focus",
              "soft focus", "blurred background", "blurry background"):
        for hit in re.finditer(re.escape(w), low):
            if negated(low, hit.start()):
                continue
            flag(name, "CINEMATIC",
                 f"'{w}' appears as an instruction, not a negation")
            break

    # THE CAMERA MUST NOT BE PLACED ON ANYTHING. Naming the placement is what
    # summons a phone or a tripod into the frame; naming the DEVICE as a lens
    # spec never did.
    for m in re.finditer(r"(propped|resting|sitting|set|placed|balanced|"
                         r"mounted)\s+(on|against|upon)\s+(a|the)\s+"
                         r"(bench|stool|table|ledge|shelf|chair|tripod|wall|"
                         r"floor|mat)", low):
        if negated(low, m.start()):
            continue
        flag(name, "CAMERA PLACED",
             f"'{m.group()}' — describe the VIEWPOINT and the framing error it "
             f"causes, never what the camera is sitting on. Every early hero "
             f"came back with a phone in frame, one in a tripod mount")
        break

    # THE CAMERA IS NOT AN OBJECT IN THE SCENE unless the shot is a mirror
    # shot, where the phone in frame IS the format. Everywhere else, describe
    # the viewpoint and the framing errors it causes and let the holder stay
    # unmentioned — including in denials, which name the thing just as loudly.
    # A MIRROR SHOT IS THE EXCEPTION AND IT IS NOT A LOOPHOLE. This rule
    # exists because a POV clip that names its holder summons a phone into
    # a frame that should not contain one. In a mirror shot the phone in
    # frame IS the format -- the reflection is the subject and a mirror
    # selfie without a visible phone is the suspicious one.
    if not phone_in_frame and not mirror:
        m = HOLDER.search(low)
        if m:
            flag(name, "CAMERA HELD",
                 f"'{m.group()}' puts a hand and a phone in the scene. Name "
                 f"the device only as a LENS SPEC and describe the motion by "
                 f"its shape — 'the view never settles, a drift off level, a "
                 f"slight overshoot when it stops'")

    # deep focus has to be asked for, because bokeh is the loudest AI tell
    if not re.search(r"background blur|shallow depth|deep focus|"
                     r"as much in focus", low):
        flag(name, "NO FOCUS INSTRUCTION",
             "background blur is the biggest single AI tell and the model "
             "defaults to it")

    # H3 wants timecoded beats; without them motion is under-specified.
    # (Kling AI documentation specifically asks for straightforward motion without numbers/seconds brackets)
    if "kling" not in name.lower() and len(re.findall(r"\[\d+\s*-\s*\d+\s*seconds?\]", p)) < 2:
        flag(name, "NO TIMED BEATS",
             "floaty motion is under-specified motion — H3's documented fix is "
             "a timecoded shot list")

    # a reference with no stated job is paid for and averaged in.
    # n_refs=None means the count is not knowable here — do not invent it.
    if n_refs and not re.search(r"image\s*1|@image1", low):
        flag(name, "REFERENCE WITHOUT A JOB",
             f"{n_refs} references attached and the prompt never says what "
             f"Image 1 is for")

    # the body reference wears bone-white sportswear; say so or it leaks
    if has_body_ref and peopled and \
            not re.search(r"not for wardrobe|only for build|"
                          r"build and head-to-body", low):
        flag(name, "WARDROBE LEAK",
             "a full-length reference carries its CLOTHES. n_noodles came back "
             "dressed in the reference's sportswear in a public restaurant")

    # LIGHT AIMED AT HER FACE is the mechanism behind the glass-skin highlight
    # that took four rounds to find. No hardness adjective required: the
    # hardness is usually declared a sentence earlier, on the room.
    if peopled:
        for m in re.finditer(r"(sun|light|sunlight|glare)[^.]{0,80}"
                             r"(across|on|over|onto|hits?|catches?|rakes?|"
                             r"falls on)[^.]{0,30}\bher face\b", low):
            if negated(low, m.start()):
                continue
            flag(name, "LIGHT ON THE FACE",
                 f"'{m.group()[:70]}...' — the highlight was never the skin "
                 f"block, it was the light. Light the ROOM and let her pass "
                 f"through it; do not put the beam on her face")
            break

    # A DEFAULT FRAMING IS A PERFECT FRAMING, and perfect reads as rendered.
    # Asked for nothing, the model centres the face, levels the shoulders and
    # squares the head — a passport photo. Every real phone frame has an error
    # in it, and the error has to be requested because it is not the default.
    if peopled and not re.search(
            r"off cent|not cent|off level|off-level|tilted|crooked|"
            r"slightly above|slightly below|above eye|below eye|"
            r"one shoulder|turned slightly|more space on one side|"
            r"not centred|not centered|askew", low):
        flag(name, "FRAMING TOO PERFECT",
             "nothing asks for a framing error, so the default arrives: face "
             "centred, shoulders level, head square. Name the error — off "
             "centre, off level, above eye line, face turned a few degrees")

    # night rules
    if re.search(r"midnight|at night|after dark", low) and \
            not re.search(r"noise|grain|underexposed|dark", low):
        flag(name, "NIGHT WITHOUT NOISE",
             "an outdoor night frame that is clean and sharp is a studio")


def main() -> int:
    sys.path.insert(0, str(ROOT))

    # 1. the H3 reference-to-video prompt
    try:
        import make_ref_clip as M
        check("make_ref_clip.PROMPT", M.PROMPT, has_body_ref=True,
              n_refs=len(M.REFS))
    except Exception as e:                                   # noqa: BLE001
        print(f"  ! could not read make_ref_clip: {e}")

    # 1b. the fit-check image-to-video prompt. n_refs=0: i2v conditions on a
    # 1b. R1 clip 1 — her, silent, front camera. phone_in_frame stays FALSE:
    #     it is a front-camera selfie, so the device is behind the lens and must
    #     not be described as an object anywhere in the prose.
    try:
        import make_clip1 as C1
        check("make_clip1.PROMPT", C1.PROMPT, n_refs=3, has_plate=True)
        # make_fit_clip carries THREE prompts, one per engine:
        # H3 i2v uses first_frame (n_refs=0), Seedance uses scene+refs (n_refs=2, plate), Kling uses first frame (n_refs=0).
        import make_fit_clip as MFC
        if not getattr(MFC, "RETIRED", False):
            for nm, refs, has_pl in (("PROMPT", 0, False),
                                     ("SEEDANCE_PROMPT", 2, True),
                                     ("KLING_PROMPT", 0, False)):
                if hasattr(MFC, nm):
                    check(f"make_fit_clip.{nm}", getattr(MFC, nm),
                          n_refs=refs, has_plate=has_pl, phone_in_frame=True)
    except Exception as e:                                   # noqa: BLE001
        print(f"  ! could not read make_clip1 / make_fit_clip: {e}")

    # 1d. R1 clips 2-4. No person in any of them, so the skin, wardrobe and
    #     framing-error rules correctly do not apply — NO_PERSON handles that.
    try:
        import make_clips234 as C234
        for d in C234.SHOTS:
            check(f"make_clips234.{d['id']}", C234.prompt_for(d), n_refs=1,
                  has_plate=True)
    except ImportError:
        pass
    except Exception as e:                                   # noqa: BLE001
        print(f"  ! could not read make_clips234: {e}")

    # 2. the POV clips
    try:
        import pov
        for c in pov.CLIPS:
            # n_refs WAS HARDCODED TO 1, from when every POV clip had a plate.
            # pov_river_walk has none — the Han does not have to be the same
            # stretch twice — and the hardcoded 1 made the checker demand a job
            # for an Image 1 that is never sent. Read it off the clip.
            check(f"pov.{c['id']}", c["prompt"],
                  n_refs=1 if c.get("plate") else 0,
                  has_plate=bool(c.get("plate")))
    except Exception as e:                                   # noqa: BLE001
        print(f"  ! could not read pov: {e}")

    # 3. any prompt sitting in a publishing doc, in a blockquote. The reference
    #    count is NOT knowable from a blockquote, so that rule does not run.
    for md in sorted((ROOT / "wiki" / "domains" / "publishing").glob("*.md")):
        body = md.read_text(encoding="utf-8")
        # a retired concept's prompt is not going to be sent, and a permanent
        # flag on a dead prompt is how a checker gets ignored
        if re.search(r"^#.*\bRETIRED\b", body, re.M):
            continue
        for blk in re.findall(r"(?:^> .*\n)+", body, re.M):
            t = "\n".join(l[2:] for l in blk.strip().split("\n"))
            if len(t) > 400 and "second" in t.lower():
                check(f"{md.name} (in doc)", t, n_refs=None)

    if not FAIL:
        print("\n  no realism issues found in the video prompts")
        return 0
    print()
    for where, rule, why in FAIL:
        print(f"  [{rule}] {where}")
        print(f"      {why}")
    print(f"\n  {len(FAIL)} issue(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
