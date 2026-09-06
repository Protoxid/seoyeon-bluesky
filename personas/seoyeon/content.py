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
content.py — generate feed content from the locked reference stack.

SCOPE CHANGED. For any room that RECURS in the feed, do not use this file:
a generated room is a new room every time, which failed QC. Use
    hero.py     one generated photo per room  ->  heroes/<scene>.png
    session.py  every other frame in that room, as an EDIT of the hero
content.py stays for one-off places nobody expects to see twice (street,
cafe, gym, shop) and for generating hero candidates via hero.py, which
imports SCENES, REF_SETS, ROLE and IPHONE_LEAN from here.

This is the production tool. Everything before it built the references; this
turns them into posts.

    python content.py --list
    python content.py morning_window --dry-run
    python content.py morning_window --n 4 --budget 0.5

The prompt is the SCENE and nothing else. Her face, hair, colouring and skin
are in the attached references — describing them again only competes with the
photographs. Wardrobe IS described, because it changes per post and the
references all show the same white top.
"""
from __future__ import annotations
import argparse, hashlib, json, os, pathlib, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from kie_api import Kie, load_key, MODEL_I2I
from kie_upload import upload as kie_upload
from locations import PLACES as ROOMS

ROOT = pathlib.Path(__file__).parent
MASTER = ROOT / "master" / "a"
OUT = ROOT / "content"

# Which reference frames to attach, by how much of her is in shot. A reference
# anchors what it depicts: a head shot cannot hold a half-body pose, and a
# body frame cannot hold her eyes.
# Two references, not three. Kie's docs allow Seedream up to 10, but a
# comparison review claims it handles only 1-2 well — untested either way, so
# start at two and add a third only if identity slips. --refs overrides.
# Seedream reads references BY INDEX, in upload order, and expects each one to
# be given a job. Attaching three photographs and saying nothing lets the model
# decide what each is for — which is how a room plate ends up used as the frame
# and how wardrobe leaks out of an identity shot. One clause per image.
ROLE = {
    "a1_front.png":         "her face — the features, the skin, the hair colour",
    "a2_tq_left.png":       "her face at an angle",
    "../b/b7_half.png":     "her build and proportions",
    "../c/c5_relax_front.png": "her build and proportions",
    "PLATE":                "the room — its furniture, materials, wall colour and daylight",
}

REF_SETS = {
    "close":  ["a1_front.png", "a2_tq_left.png"],
    "half":   ["a1_front.png", "../b/b7_half.png"],
    "full":   ["a1_front.png", "../c/c5_relax_front.png"],
}

# The locked visual system: five locations, two lighting states, one wardrobe
# vocabulary. Restricting the range is what makes a feed look authored.
# One prompt resampled gives you the same photo N times — the model finds the
# obvious solution and returns to it. Variety has to be WRITTEN, as a list of
# distinct actions per place. Each action becomes its own generation.
# Two things the reference cannot vary for you: her EXPRESSION and the emotional
# register of the shot. a1_front is neutral, so without an explicit expression
# every frame inherits it. And a list of six contemplative actions produces six
# contemplative photos even if each face differs — the register has to vary too.
SCENES = {
 "morning_window": dict(place="window", framing="half", aspect="3:4", actions=[
    "Holding a ceramic mug with both hands, looking out of the window, face soft and unfocused, somewhere else entirely.",
    "Turning back from the window toward camera, caught mid-turn, eyebrows slightly up as if someone just said her name.",
    "Seen from behind at the window, one hand on the frame, face not visible.",
    "Sitting sideways on the windowsill with her knees drawn up, mug on the sill, quietly amused at something outside.",
    "Reaching up to push the curtain further open, squinting slightly against the light, mouth a little open with the effort.",
    "Leaning a shoulder against the window frame, arms folded, looking down, tired and content, the beginning of a smile.",
 ], wardrobe="She is wearing an oversized cream cardigan, sitting properly on both shoulders with both arms through the sleeves, over a fitted white ribbed top."),

 "reformer": dict(place="studio", framing="full", aspect="3:4", actions=[
    "Mid-movement on the reformer, legs extended, jaw set, genuinely working.",
    "Sitting on the end of the reformer between sets, out of breath, head tipped back, eyes half closed.",
    "Standing beside the reformer adjusting the spring settings, looking down, brow slightly furrowed in concentration.",
    "Stretching forward over the carriage, spine long, face relaxed and released.",
    "Rolling up a mat against the studio wall, seen from the side, mouth pressed in a small satisfied line.",
    "Standing at the studio window afterwards, hands on hips, flushed, half-smiling to herself.",
 ], wardrobe="She is wearing a matte sage ribbed two-piece activewear set, barefoot, hair in a low bun."),

 "cafe": dict(place="cafe", framing="close", aspect="3:4", actions=[
    "One elbow on the table, listening to someone out of frame, eyebrows raised, on the edge of laughing.",
    "Both hands around a matcha, reading, absorbed, lips slightly parted.",
    "Glancing up at the camera as if just noticed, caught off guard, small startled smile.",
    "Looking out of the cafe window, chin on her hand, expression flat and far away.",
    "Mid-laugh, head tipped, eyes crinkled almost shut, hand near her mouth.",
    "Reaching across the table for the cup, not looking at camera, mouth relaxed, unaware.",
 ], wardrobe="She is wearing an oat knit sweater, both arms through the sleeves, sitting normally on both shoulders."),

 "bathroom_mirror": dict(place="bathroom", framing="close", aspect="9:16", actions=[
    "Patting product onto her cheek, mouth slightly open in that unconscious way people do at a mirror.",
    "Leaning close to the mirror checking her skin, eyes narrowed, faintly critical.",
    "Tying her hair up with both hands, elbows out, chin lifted, concentrating.",
    "Holding a white iPhone up to take the mirror photo, looking at the lens, deadpan.",
    "Applying something under her eyes with a fingertip, one eye closed, brow lifted.",
 ], wardrobe="She is wearing a white ribbed tank top, hair clipped back off her face."),

 "rooftop": dict(place="rooftop", framing="half", aspect="3:4", actions=[
    "Forearms on the railing looking out over the skyline, face still, thinking about nothing.",
    "Turning toward camera from the railing, hair across her face in the wind, laughing and pushing it away.",
    "Seen from behind at the railing, wind in her cardigan, face not visible.",
    "Sitting on the concrete step, knees up, coffee beside her, squinting into the light, small smile.",
    "Walking toward camera across the rooftop, unposed, mid-stride, looking off to one side.",
 ], wardrobe="She is wearing a cream knit jumper, both arms through the sleeves, with wide-leg linen trousers."),

 "bedroom": dict(place="bedroom", framing="half", aspect="3:4", actions=[
    "Sitting on the edge of the bed, feet on the floor, just woken, eyes puffy, hair flattened on one side.",
    "Making the bed, smoothing the linen with one hand, face neutral and unthinking.",
    "Lying on her side across the bed reading, propped on an elbow, absorbed, faintly smiling at the page.",
    "Reaching for the bedside lamp, seen from the side, eyes already half closed.",
    "Sitting cross-legged on the bed with a book in her lap, looking up as if interrupted, eyebrows raised.",
 ], wardrobe="She is wearing a soft oatmeal knit jumper, both arms through the sleeves, with loose linen shorts."),

 "kitchen": dict(place="kitchen", framing="half", aspect="3:4", actions=[
    "Pouring hot water from a kettle into a mug, watching it closely, brow slightly drawn.",
    "Leaning back against the counter with the mug in both hands, shoulders down, quietly content.",
    "Reaching up to the open shelf for a bowl, on tiptoe, mouth open with the stretch.",
    "Chopping something on a board, looking down, absorbed, unaware of the camera.",
    "Standing at the counter eating, one hip against the edge, mid-bite, caught looking at the camera.",
 ], wardrobe="She is wearing a white ribbed tank top and wide linen trousers."),
}

# Seedream's documented aspect_ratio enum. 4:5 is NOT in it — Instagram's feed
# ratio has to be reached by cropping 3:4 locally, not requested from the API.
ALLOWED_ASPECTS = {"1:1", "16:9", "21:9", "2:3", "3:2", "3:4", "4:3", "9:16"}

# What actually reads as AI is not the subject — it is the RENDER. Creamy
# f/1.4 bokeh, flawless composition, tack-sharp everything, clean shadows with
# no noise, and a room with nothing accidental in it. Real photographs are
# messier than that, and the mess is what sells them.
#
# "editorial", "photorealistic" and a fast prime were all pulling the wrong way.
# HER GEAR: a white iPhone 16 Pro. Naming the actual device beats "a recent
# phone" — the model has seen millions of iPhone photographs and knows the look.
#
# The iPhone 16 Pro signature, from reviews: relatively LOW saturation with
# aggressive HDR (highlights held, shadows lifted, so contrast reads flat),
# accurate white balance even in mixed light, detail that favours character
# over naturalism, lively skin tones, and a 1/1.28" sensor at f/1.8 — real but
# modest background separation, nothing like a fast full-frame prime.
# Focal lengths: 24mm (1x), 48mm (2x, the portrait one), 120mm (5x), 13mm (0.5x).
IPHONE = (
    "Shot on an iPhone 16 Pro at 2x (48mm equivalent). Apple's processing: "
    "relatively low saturation with strong HDR, so the shadows are lifted and "
    "the highlights hold — contrast reads flat rather than punchy. Accurate "
    "white balance. Crisp, slightly over-sharpened detail. Modest background "
    "separation from a small sensor: the room stays legible, never dissolved. "
    "Fine noise in the shadows. Framing a degree off level, as someone actually "
    "holding it. Ordinary domestic clutter left where it is. Skin shows pores, "
    "fine hair and small unevenness.")

# CAMERA POSITION. A propped phone sits at the height of whatever surface the
# room has — 45 cm for a stool, 90 cm for a counter — and most of those look UP
# at her. "Chest height" is where a photographer puts a tripod and reads as one.
# NEVER NAME THE DEVICE. Saying "the phone is propped on the stool" puts a
# phone in the frame, every time, sometimes in a tripod mount. Describe only
# the viewpoint and the framing error it causes; the camera stays invisible.
# The framing error matters as much as the height: perfect composition is an
# AI tell. Real propped shots are off-centre, tilted, and crop badly.
PROP = {
 "window":   "Seen from about 45 cm off the floor, looking up at her. She sits "
             "off to one side with more empty room than she needs on the other.",
 "studio":   "Seen from floor level, looking up the length of the reformer. The "
             "ceiling takes more of the frame than it should and the horizon "
             "rolls a degree or two.",
 "cafe":     "Seen from just above the tabletop, looking up, the near edge of "
             "the table cutting across the bottom of the frame.",
 "bathroom": "Her own reflection at chest height in the mirror, slightly "
             "rolled, her head close to the top edge of the frame.",
 "rooftop":  "Seen from waist height on the parapet, tilted up, so there is a "
             "lot of sky and she sits low in the frame.",
 "bedroom":  "Seen from about 60 cm up, slightly below her and off to the side, "
             "the near edge of the bed running out of the bottom corner.",
 "kitchen":  "Seen from about 90 cm, just below her eyeline, the worktop "
             "cutting low across the frame and her a little off centre.",
}

# The lean lens line. IPHONE above is the full spec; it is 700 characters of
# instruction competing with two photographs. This says the same thing in the
# words that actually change the output.
IPHONE_LEAN = ("Shot on an iPhone 16 Pro: flat HDR contrast, low saturation, "
    "deep focus so the room stays legible, fine shadow noise, framing a "
    "degree off level. Skin shows pores and small unevenness.")

LOOKS = {
    # Most of the feed. Her own phone, propped or held by a friend.
    "phone": IPHONE,

    # Wide, close, slight perspective stretch — a selfie or an arm's-length shot.
    "phone_wide": IPHONE.replace("at 2x (48mm equivalent)", "at 1x (24mm "
        "equivalent), close to her, with the mild perspective stretch a wide "
        "phone lens gives at that distance"),

    # Occasional posts. Someone with a real camera took this.
    "camera": (
        "A photograph on a 35mm camera at f/4, fine film grain, slight vignette. "
        "The background stays legible rather than dissolving. One strand of hair "
        "out of place. Skin shows pores and texture. Natural light with a real "
        "falloff, slightly uneven across the frame."),
}

# CONTINUITY: if her iPhone is visible in a shot, it is not the thing taking the
# shot. Only two situations are consistent —
#   mirror  : the phone is in her hand, in the mirror, and IS the camera
#   friend  : her phone is somewhere in the room and someone else is shooting
# Any other frame that shows her phone lying on a table implies a second device
# nobody has established. Keep it out of frame instead.
PHONE_VISIBLE_OK = {"bathroom_mirror"}

# The plate is a REFERENCE, not a backplate. Left to itself the model takes the
# cheapest path: keep the room photograph as a background layer and place the
# subject in front of it. That reads as a collage — no shared light, no contact
# shadow, no shared air. Three things stop it, and all three are prompt-side:
#   1. tell it the plate is a different photograph of the same room
#   2. commit to a camera position that is NOT the plate's
#   3. state the room's light source and how it falls on HER
# More room coverage does not fix this. A 360 gives the model more backplates
# to copy, not a reason to re-render the room.
PLATE_NOTE = (
    "One attached photograph is a wide establishing view of the whole room, "
    "taken from a corner with nobody in it. Use it ONLY to know what this room "
    "contains and what it is made of — the furniture, the fabrics, the wood, "
    "the wall colour, the daylight. It is not this frame, not this camera "
    "position and NOT THIS LENS. That reference was taken on a wide lens; this "
    "photograph is not. Do not carry its wide-angle geometry across: nothing "
    "stretches toward the edges, no wall leans, no line bends, the floor does "
    "not fan open. Only a small part of what the wide view shows falls inside "
    "this frame, seen from a different angle and a different distance.")

# Per place: the light, and where the camera is standing. Both are what tie a
# subject into a room. Written once here rather than per action.
SITE = {
 "window":   dict(light="The window is the only light source. It rakes across "
                        "her from one side, bright on that cheek and shoulder "
                        "and falling off into open shadow on the other, with a "
                        "weak bounce back from the wall behind the camera.",
                  cam="The camera is inside the room, standing a couple of "
                      "metres back, roughly at her chest height."),
 "studio":   dict(light="Flat, even daylight from the studio's tall windows, "
                        "wrapping her from the front-left, floor and walls "
                        "bouncing a cool fill back into the shadows.",
                  cam="The camera is low, at reformer height, a couple of "
                      "metres away along the length of the machine."),
 "cafe":     dict(light="Daylight from the shopfront window behind her rims "
                        "her hair and shoulders; the warm interior lamps fill "
                        "her face weakly, so the front of her is the darker "
                        "side.",
                  cam="The camera is across the small table from her, at "
                      "sitting height, about a metre and a half away."),
 "bathroom": dict(light="A warm bulb above the mirror drops light down onto "
                        "her forehead, nose and cheekbones, leaving soft "
                        "shadow under the brow and jaw; the tiles bounce a "
                        "little of it back.",
                  cam="The camera is her own phone, held at chest height, "
                      "seen in the mirror."),
 "rooftop":  dict(light="Open sky. Low sun from one side gives a warm edge "
                        "along her arm and jaw, and the sky fills the shadows "
                        "cool and soft — a clear warm/cool split across her "
                        "face.",
                  cam="The camera is on the roof with her, standing height, "
                      "three or four metres away."),
 "bedroom":  dict(light="Soft daylight through a curtain, weak and directional "
                        "from one side, and the pale bedding throwing a large "
                        "gentle fill up into her face from below.",
                  cam="The camera is at bed height, a couple of metres away, "
                      "level with her rather than looking down at her."),
 "kitchen":  dict(light="Daylight from the kitchen window plus the cool strip "
                        "under the wall units; the worktop bounces light back "
                        "up under her chin.",
                  cam="The camera is on the far side of the counter, standing "
                      "height, a couple of metres back."),
}

# The frame's own geometry, stated once. Two attached photographs disagree
# about the lens (a wide room plate, a portrait-lens face), so the frame has
# to declare which one it is or the model splits the difference and warps.
GEOMETRY = (
    "A vertical portrait frame with normal, undistorted perspective — a "
    "short telephoto view, not a wide one. Straight edges stay straight, "
    "walls stay vertical, the window frame and the floor line run true. She "
    "is about two and a half metres from the lens and reads at natural "
    "proportion: no enlarged near hand, no stretched limb, no bulge toward "
    "the corners.")

# The seam is always the same three failures: light that does not match, no
# contact with anything, and a subject sharper than the room she is in.
INTEGRATION = (
    "She is physically inside this room and the room's light is the light on "
    "her: same colour, same direction, same softness. Where she touches "
    "anything there is contact — a shadow under her hand, weight in the "
    "cushion, her feet on the floor. Her edges are not cut out: hair breaks up "
    "against the background, and the room shares her light, her haze, her "
    "white balance and her grain — one photograph, not two.")

TAIL = LOOKS["phone"]


def refs_for(framing: str, key: str, place: str | None = None) -> list[str]:
    """Identity references, plus the location plate if one is locked.

    The plate goes LAST: the face references are what must dominate. If
    identity slips once a plate is attached, drop back to --refs 1 so only the
    strongest face frame and the plate are sent.
    """
    out = []
    if place:
        plate = (ROOT / "locations" / f"{place}.png")
        if plate.exists():
            print(f"  location plate: {plate.name} (attached)")
        else:
            print(f"  no locked plate for '{place}' — the room will be "
                  f"reinvented each run.\n  Fix: python locations.py {place} "
                  f"--n 4   then --lock {place} <NN>")
    for name in REF_SETS[framing]:
        p = (MASTER / name).resolve()
        if not p.exists():
            print(f"  ! missing reference {p.name} — skipping it")
            continue
        out.append(kie_upload(p, key))
    if place:
        plate = (ROOT / "locations" / f"{place}.png")
        if plate.exists():
            out.append(kie_upload(plate, key))
    if not out:
        sys.exit("no references found. Has phase a run?")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scene", nargs="?")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--n", type=int, default=1,
                    help="images per action (default 1 — variety comes from "
                         "the action list, not from resampling one prompt)")
    ap.add_argument("--action", type=int,
                    help="run only action N (0-indexed), for a cheap test")
    ap.add_argument("--aspect", help="override: 3:4 for feed, 9:16 for Reel stills")
    ap.add_argument("--look", choices=list(LOOKS), default="phone",
                    help="phone = what her own phone would produce (default) · "
                         "camera = a friend shot it on a real camera")
    ap.add_argument("--budget", type=float, default=0.5)
    ap.add_argument("--refs", type=int, default=0,
                    help="cap the number of reference images attached "
                         "(default: whatever the framing calls for)")
    # VERDICT: attaching the plate makes the model composite — subject in
    # front of a copied backplate. The same room in TEXT blends perfectly.
    # Room identity now comes from words; the plate is opt-in only.
    ap.add_argument("--plate", action="store_true",
                    help="also attach the locked room plate. OFF by default: "
                         "it makes the model paste the subject onto the plate "
                         "instead of photographing her in the room")
    ap.add_argument("--full", action="store_true",
                    help="add the camera/light/geometry/integration blocks. "
                         "OFF by default: long prompts compete with the "
                         "attached references and warp the result")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if a.list or not a.scene:
        print("\n  scenes:")
        for k, v in SCENES.items():
            print(f"    {k:<18}{v['framing']:<6}{v['aspect']:<6}"
                  f"{len(v['actions'])} actions")
        return 0
    if a.scene not in SCENES:
        sys.exit(f"unknown scene. Options: {', '.join(SCENES)}")

    sc = SCENES[a.scene]
    actions = sc["actions"]
    if a.action is not None:
        actions = [actions[a.action]]
    if sc["aspect"] not in ALLOWED_ASPECTS:
        sys.exit(f"aspect {sc['aspect']} is not one of Seedream's allowed "
                 f"values: {', '.join(sorted(ALLOWED_ASPECTS))}")
    look = LOOKS[a.look]
    if a.scene in PHONE_VISIBLE_OK:
        look += (" She is holding a white iPhone 16 Pro, which is the camera "
                 "taking this photograph — it appears in the mirror.")
    else:
        look += " Her phone is not visible anywhere in the frame."
    site = SITE.get(sc.get("place"), {})
    plate = (ROOT / "locations" / f"{sc.get('place')}.png")
    # The room in WORDS as well as in pixels. The plate alone cannot survive
    # being told "a different position in the same room" — asked to re-render,
    # the model needs to know what it is re-rendering. Without this, --no-plate
    # invents a room from scratch.
    room = ROOMS.get(sc.get("place"), "")
    if a.full:
        parts_tail = [room, sc["wardrobe"], site.get("cam", ""),
                      site.get("light", "")]
        if plate.exists() and a.plate:
            parts_tail.append(PLATE_NOTE)
        parts_tail += [GEOMETRY, INTEGRATION, look]
    else:
        # LEAN (default). Only what the references cannot carry: what she is
        # doing, what she is wearing, what room, what shot it. Everything the
        # --full blocks add is instruction competing with photographs.
        # Room text and plate are ALTERNATIVES, never both. A one-line
        # description is a worse account of the room than the photograph is,
        # so sending both makes the model average them and the room drifts.
        # Plate attached -> the plate IS the room, say nothing about it.
        names = list(REF_SETS[sc["framing"]])
        if plate.exists() and a.plate:
            names.append("PLATE")
        roles = " ".join(f"Use Image {i} for {ROLE[n]}."
                         for i, n in enumerate(names, 1)
                         if n in ROLE)
        parts_tail = [roles] if roles else []
        if not (plate.exists() and a.plate):
            parts_tail.append(room)
        parts_tail += [sc["wardrobe"],
                       look if a.look != "phone" else IPHONE_LEAN]
    tail = "\n\n".join(x for x in parts_tail if x)
    prompts = [f"{act}\n\n{tail}" for act in actions]
    print(f"  scene    {a.scene}")
    print(f"  framing  {sc['framing']}  ({', '.join(REF_SETS[sc['framing']])})")
    print(f"  place    {sc.get('place','—')}")
    print(f"  look     {a.look}")
    print(f"  aspect   {sc['aspect']}")
    print(f"  actions  {len(actions)}  ({a.n} image(s) each = "
          f"{len(actions)*a.n} total, ~${0.07*len(actions)*a.n:.2f})")
    print(f"  prompt   ~{sum(map(len,prompts))//len(prompts)} chars each\n")

    if a.dry_run:
        for i, pr in enumerate(prompts):
            print("=" * 66); print(f"[{i}] {pr}")
        print("=" * 66)
        print(f"\n  DRY RUN — nothing sent")
        return 0

    load_key(ROOT)
    key = os.environ.get("KIE_API_KEY", "")
    if not key or key.startswith("PASTE"):
        sys.exit("no API key in kie_key.txt")
    kie = Kie(key)
    refs = refs_for(sc["framing"], key,
                    sc.get("place") if a.plate else None)
    if a.refs:
        refs = refs[:a.refs]
    print(f"  {len(refs)} references attached\n")

    outdir = OUT / a.scene
    outdir.mkdir(parents=True, exist_ok=True)
    tag = hashlib.sha256("".join(prompts).encode()).hexdigest()[:6]
    spent = [0.0]

    jobs = [(ai, vi, pr) for ai, pr in enumerate(prompts)
            for vi in range(1, a.n + 1)]

    def one(job):
        ai, vi, prompt = job
        i = f"{ai}.{vi}"
        if spent[0] + 0.07 > a.budget:
            return i, "skip", "budget cap"
        spent[0] += 0.07
        dest = outdir / f"{a.scene}_{tag}_a{ai:02d}_{vi:02d}.png"
        try:
            urls = kie.generate(prompt, a.aspect or sc["aspect"], refs,
                                model=MODEL_I2I)
            n = kie.download(urls[0], dest)
            return i, "ok", f"{dest.name}  {n//1024} KB"
        except Exception as e:
            spent[0] -= 0.07
            return i, "fail", str(e)[:120]

    with ThreadPoolExecutor(max_workers=3) as ex:
        for f in as_completed([ex.submit(one, j) for j in jobs]):
            i, st, msg = f.result()
            print(f"  [{i:>5}] {'  ok  ' if st=='ok' else ' FAIL ' if st=='fail' else ' skip '} {msg}")

    print(f"\n  ~${spent[0]:.2f} spent -> {outdir}")
    print(f"  Now: python drift_gate.py --in {outdir.relative_to(ROOT)}")
    print("  A content shot is the real test — if identity holds when the "
          "background,\n  wardrobe and lighting all change at once, the stack works.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
