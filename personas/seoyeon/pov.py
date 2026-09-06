"""
pov.py — first-person Reels. She holds the camera and is never in the picture.

THE IDEA, AND WHY IT IS A GOOD ONE. Seedance refuses real-person identity
references. If she is not in frame there IS no identity to refuse, so the
restriction stops applying — and at the same time the hardest thing in
generated video to get past a viewer, a human face in motion, is simply absent.
No drift, no mirroring, no glossy skin, no gate to pass. A POV clip is the
cheapest believable video this account can make.

BUT THE PREMISE HAS TO SURVIVE THE CAMERA QUESTION, and the obvious version
does not. "She films her class" cannot happen: she is TEACHING it. You cannot
cue a room and hold a phone. That is the same rule that governs the stills —
a frame needs an owner, and the owner has to have a free hand and a reason.

What works instead, all of it already established in week.md:
  * the empty studio BEFORE anyone arrives — she has a key and nothing else
    to do (this is `n_studio_dawn`, which people have already seen)
  * the walk in from the street, up the stairs
  * after class, packing up, room emptying
  * as a PARTICIPANT rather than the teacher — she still takes classes
  * not the studio at all: the river path, the market aisle, the subway

TWO TRAPS SPECIFIC TO POV, both of which cost nothing to avoid and would each
ruin the clip:

1. MIRRORS. A pilates studio is full of them, and a first-person camera in a
   mirrored room PHOTOGRAPHS THE PERSON HOLDING IT. Either frame away from the
   mirrored wall or say so in the negatives. This is the video version of
   "never name the photographer — they will appear in the frame".

2. HANDS. The moment a hand enters frame it is an unreferenced limb, and an
   unreferenced limb came back as a MAN'S LEG in `n_desk_late`. Either keep
   hands out entirely, or attach the body plate as a second reference and say
   whose hand it is. Prefer keeping them out: a POV clip does not need them.

FIELD NAMES DIFFER FROM H3. All three of these fail quietly rather than
erroring, which is the whole reason they are written down:

    | thing              | H3 ref2v                | Seedance 2.5 ref2v |
    | references         | reference_image_urls    | image_urls         |
    | resolution casing  | 480P 768P 2K 4K         | 480p 720p 1080p    |
    | prompt reference   | "Image 1"               | "@Image1"          |

`generate_audio` defaults TRUE and costs the same either way — we send FALSE.
Generated ambience is a tell, and the music goes on in Instagram, where a
Creator account keeps the full catalogue.
"""

# ---------------------------------------------------------------- plates --
# Location plates. NOT published frames — they are references, so they are
# generated once and reused. 9:16 for POV video, 16:9 for conditioning stills.
# Custom pixel sizes make these possible at all: gpt-image-2's text-to-image
# ENUM has no wide or tall-empty option, but exact width/height does.
# Nobody is in a plate. That is the point of it.
PLATES = [

# ROOM PLATES — 4:3 or 3:4 at tier "max", the largest legal frame
# (3840x2880 / 2880x3840). Not published images. Generated once, reused
# forever, and nobody is in them. A plate exists so the room stops being
# reinvented every time it appears, which text alone never managed.

dict(id="plate_room", generated="fal", tier="max", aspect="4:3", noface=True,
 story="THE flat. One room: kitchenette along one wall, bed, table, window. "
       "In a one-room the kitchen shot and the desk shot are the same room, so "
       "this single plate carries both and they cannot drift apart. It has to "
       "match what is already public — the wooden table and the electric fan "
       "from n_desk_late.",
 text=
 "The interior of a small one-room officetel flat in Seoul, empty of people, "
 "seen wide from the doorway and taking in the whole room at once: a short "
 "kitchenette along one wall with two induction rings, a small sink, a "
 "microwave on a shelf and a few jars and a rice cooker on the counter; a "
 "low wooden table with a laptop closed on it and a chair pushed in; a bed "
 "against the far wall with a plain duvet not quite straight; a clothes rail "
 "with hanging clothes and a folding laundry rack beside it; an electric fan "
 "on the floor; a tall window with the wall of the building opposite close "
 "behind it. Pale wood-effect floor, white walls, one ceiling light. Lived in "
 "and slightly untidy, not styled. Nobody is in the room. Everything sharp. "
 "Flat daylight from the window, low contrast, fine noise."),

dict(id="plate_bathroom", generated="fal", tier="max", aspect="3:4", noface=True,
 story="The small wet-room bathroom that goes with a one-room. Shower over "
       "the drain, no bath, one basin. Its mirror makes it the natural "
       "location for a getting-ready mirror selfie.",
 text=
 "A very small bathroom in a Seoul one-room flat, empty of people, seen from "
 "the doorway taking in the whole room: a single basin with a mirrored "
 "cabinet above it, a shower head on a rail on the wall with no screen and a "
 "drain in the middle of the tiled floor, a toilet, a plastic shelf with "
 "shampoo and bottles on it, a towel on a hook, a squeegee leaning in the "
 "corner. Small square wall tiles, a little limescale around the tap. Nobody "
 "is in the room. Everything sharp. Cool overhead light, flat, fine noise."),

dict(id="plate_hallway", generated="fal", tier="max", aspect="3:4", noface=True,
 story="Already canon — n_mirror_dress was shot here and is live. Locking it "
       "so it stays the same hallway every time, including the shoes.",
 text=
 "The narrow entrance hallway of a small Seoul flat, empty of people, seen "
 "from inside looking toward the front door: a sunken tiled entry step with "
 "several pairs of shoes left on it including white trainers, a coat hook on "
 "the wall with a dark jacket and a tote bag on it, a light switch, a full "
 "length mirror leaning against one wall, a doorway into a dark room on one "
 "side and a folding laundry rack just visible through it. Narrow, not much "
 "more than shoulder width. Nobody is in the hallway. Everything sharp. Dim "
 "warm light, underexposed, grainy."),

dict(id="plate_stairwell", generated="fal", tier="max", aspect="3:4", noface=True,
 story="The bits between the flat and the street. Cheap, nobody in them, no "
       "mirrors anywhere — which makes them the safest POV footage we have.",
 text=
 "The internal corridor and stair landing of an older low-rise residential "
 "building in Seoul, empty of people: a tiled floor, painted walls with scuff "
 "marks, several flat doors with metal numbers and keypad locks, a fire "
 "extinguisher, a stack of flattened cardboard and a recycling bag by one "
 "door, a window at the half landing with frosted glass, concrete stairs with "
 "a metal handrail going up and down. A strip light overhead, one tube "
 "slightly dimmer than the other. No mirrors anywhere. Nobody is in the "
 "corridor. Everything sharp. Cool fluorescent cast, flat, fine noise."),

# THE STUDIO. Regenerated rather than inherited: locations/studio.png, which
# `plate_studio` used to resolve to, is a DOMESTIC LIVING ROOM with one
# reformer in it — rug, framed print, radiator, curtains. It was never a
# studio, and every POV clip that references the studio was going to render a
# flat. That file is now parked in locations/_superseded/ so it can no longer
# shadow this one.
#
# The mirrored wall stays IN, because a pilates studio has one and w2_class_two
# already shows it. It makes this the one plate where POV needs care: a
# first-person camera in a mirrored room photographs the person holding it, so
# POV shots point at equipment and floor and negate reflections. That is a
# constraint on the clips, not a reason to build a studio without mirrors.
# 1:1 AND 2k, NOT 4:3 AND "max", AND THE REASON MATTERS. The other four plates
# were generated on fal, where both were legal. On Kie a plate has no reference
# images, so it routes to gpt-image-2 TEXT-to-image, whose ratio enum is only
# 1:1, 3:4, 2:3 and 9:16 — 4:3 would have been rejected at the API after the
# round trip. Of those four, 1:1 is the ONLY one that is not portrait, so it is
# the widest frame available for a room that has to be seen wide. And "max" is
# a fal tier with no meaning on this path; every Kie shot uses 2k.
dict(id="plate_studio", tier="2k", aspect="1:1", noface=True,
     story=("The studio she teaches in. It recurs across the whole account — "
            "every teaching reel, every before-and-after-class still — so it "
            "is the plate that most needs to stop being reinvented. A viewer "
            "who sees it four times WILL notice it change, which is the test "
            "for whether a plate earns its cost."),
     text=("The interior of a small pilates studio on an upper floor of a "
           "building in Seongsu, Seoul, empty of people, seen wide from the "
           "doorway and taking in the whole room at once: eight reformers "
           "arranged in two rows of four on a pale wood floor with a walkway "
           "between the rows, their frames light grey, the springs "
           "visible underneath each carriage and the footbars up; a mirrored "
           "wall running down one side reflecting the machines and the empty "
           "floor; tall windows along the opposite wall with the building "
           "across the street close behind them; rolled mats stacked against "
           "the end wall beside a low wooden bench; a few small props in a "
           "corner — a box, a couple of rings, a short ladder barrel; a water "
           "dispenser and a shoe rack by the door; a ceiling track light. "
           "Clean and businesslike, used rather than styled. Nobody is in the "
           "room and nobody is reflected in the mirror. Everything sharp. "
           "Cool early daylight from the windows, low contrast, fine noise."),
     ),

# WIDER. The first studio plate came back tight, and two phrases did it:
# "a SMALL pilates studio" and "seen wide FROM THE DOORWAY". The model obeyed
# both — it put the door jamb in each edge, which crops the view and adds
# clutter, and it lined the three reformers up nose-to-tail down what reads as
# a corridor. The room itself is good and believable, so it is kept and
# re-shot rather than reinvented.
#
# THIS ONE IS IMAGE-TO-IMAGE, and that is what unlocks the aspect. A plate with
# no reference routes to gpt-image-2 text-to-image, whose widest legal ratio is
# 1:1. Attaching the existing plate as `plate=` makes it image-to-image, whose
# enum includes 3:2, 16:9 and 21:9 — so the room can finally be shot wide. It
# also keeps continuity for free: same floor, same mirror, same windows, same
# water dispenser, because they are in the reference rather than in a sentence.
#
# 3:2 rather than 16:9: at tier 2k a wider ratio spends its pixels sideways and
# loses the ceiling and floor that make a room read as a room.
# "USED RATHER THAN STYLED" IS AN ADJECTIVE, AND THE MODEL CANNOT RENDER ONE.
# The first wide plate said exactly that and came back a showroom: eight
# identical machines, identically parked, identically strapped, in two dead
# straight rows on an unmarked floor. The H3 clip shot against it read as a
# rendering even though the VIDEO prompt carried "no cinematic look", "not like
# a rendering" and "architectural visualisation" in its avoid list — because
# text arguing with pixels loses, and the pixels were a furniture plan.
#
# THE TELL IS NOT GRIME, IT IS UNIFORMITY. A renderer places one asset eight
# times; a photograph of a real room catches eight of the same machine in eight
# different states. So the wear is now named as specific facts a camera could
# see — carriages stopped at different points, straps at different lengths,
# springs not matching, two machines pushed off parallel — plus the things a
# real building has and a rendered one never does: sockets, a vent, a sprinkler
# head, scuffs at carriage height, a mirror that is not clean at the bottom.
# Objects left behind do the rest: a bottle, a towel, a sweatshirt, socks.
#
# It is i2i off plate_studio, which is itself pristine, so the mess has to be
# stated HERE. That is not a violation of say-only-the-delta — none of it is in
# Image 1, which is exactly what makes it the delta.
dict(id="plate_studio_wide", tier="2k", aspect="3:2", noface=True,
     plate="plate_studio",
     story=("The studio again, from the far corner instead of the doorway, so "
            "there is floor in front of the machines and both walls are "
            "visible. This is the one the POV clips reference: a camera "
            "panning inside a corridor has nowhere to go. EIGHT reformers, not "
            "three: a typical group class is 8-12 people and a mid-size "
            "studio runs 10-12 machines, so three reads as somebody's spare "
            "room rather than a business she teaches at. Two rows also force "
            "width into the frame, which is the other half of the fix for "
            "the room reading tight."),
     text=("The same pilates studio in Seongsu, Seoul as Image 1 — the same "
           "pale wood floor, the "
           "same light grey reformers, the same mirrored wall, the same "
           "tall windows with the building opposite behind them, the same "
           "water dispenser and shoe rack — photographed from the far corner "
           "of the room instead of from the door, so that two walls recede "
           "away and the whole floor is visible at once. Nothing is in the "
           "foreground and no door frame is at the edges. An open studio floor "
           "with clear space in front of the machines and between them: the "
           "studio is fitted out with EIGHT reformers, not three, arranged in two "
           "rows of four with a walkway down the middle and room to "
           "stand at the end of each machine. The ceiling is high and the "
           "far wall is a long way off.\n\n"
           "A class has just finished and nobody has tidied up. The machines "
           "do not match each other: the carriages are stopped at different "
           "points along their tracks instead of all parked at the footbar, "
           "the shoulder rests are set at different heights, and the straps "
           "and hand loops hang at different lengths, one pair twisted, one "
           "looped over a footbar. The springs are not the same colours from "
           "one machine to the next. Two of the reformers sit slightly out of "
           "line with their row, turned a few degrees off parallel where "
           "somebody pushed them. A water bottle stands on the floor at the "
           "end of one machine, a folded towel is left on another carriage, a "
           "sweatshirt hangs over a footbar, and a pair of grip socks sits on "
           "the bench beside the mats. The stack of rolled mats is not "
           "square.\n\n"
           "The building shows as well: scuff marks and fine scratches in the "
           "wood along the walkway, marks on the wall at carriage height, a "
           "plug socket and a light switch, a wall vent, a fire extinguisher "
           "on the wall, a smoke detector and a sprinkler head on the "
           "ceiling, and the mirror not perfectly clean towards the floor.\n\n"
           "Nobody is in the room and nobody is "
           "reflected in the mirror. Everything sharp, front to back. Cool "
           "early daylight from the windows, low contrast, fine noise."),
     ),

# NO RIVER PLATE. A plate exists so a place can be THE SAME every time — the
# studio has to be recognisable or the account stops being one person's life.
# The Han path is forty kilometres long and she walks a different bit of it
# each time, so there is nothing to keep consistent and a plate would only be
# nine cents spent to make every river clip the same river clip.
# THE PRICE OF DROPPING IT IS THAT THE TEXT HAS TO CARRY THE PLACE. Say only
# the delta means cut what the references show; with no reference, the river
# IS the delta, and pov_river_walk describes it in full for that reason.
]

# (The old note here claimed the studio plate already existed and did not need
# regenerating. It was wrong: the file it pointed at was a living room. See the
# plate_studio entry above.)

# `plate_path()` resolves an id to a file wherever it lives — locations/ first,
# so a hand-made plate always outranks a generated one.
FLAT_PLATES = ["plate_room", "plate_bathroom", "plate_hallway",
               "plate_stairwell"]
STUDIO_PLATES = ["plate_studio"]


def plate_path(pid: str):
    """Resolve a plate id to a file on disk, generated or hand-supplied.

    Checks content/plates/<id>.png first — the stable name a hand-made plate
    uses — then any generated file matching <id>_<hash>_*.png. Returns None if
    the plate does not exist, so a caller can refuse to spend rather than
    silently generating a room that was already made."""
    import glob, pathlib
    root = pathlib.Path(__file__).resolve().parent
    bare = pid[6:] if pid.startswith("plate_") else pid
    # locations/ is where the hand-made plates live and it wins, because a
    # plate the operator generated and looked at outranks one this pipeline
    # made. Then content/plates/<id>.png, then any generated <id>_<hash>_*.png.
    for cand in (root / "locations" / f"{bare}.png",
                 root / "content" / "plates" / f"{pid}.png",
                 root / "content" / "plates" / f"{bare}.png"):
        if cand.is_file():
            return cand
    # AN ID THAT IS A PREFIX OF ANOTHER ID STEALS ITS FILES. The glob
    # "plate_studio_*_*.png" happily matches plate_studio_WIDE_4e68ba_1.png, so
    # plate_studio and plate_studio_wide resolved to the same picture and a
    # re-render of the wide plate would have used ITSELF as its reference.
    # Generated names are always <id>_<six hex>_<n>.png, so the hash segment is
    # what disambiguates: match it exactly rather than with a wildcard.
    import re as _re
    pat = _re.compile(rf"^{_re.escape(pid)}_[0-9a-f]{{6}}_\d+\.png$")
    hits = sorted(q for q in (root / "content" / "plates").glob(f"{pid}_*.png")
                  if pat.match(q.name))
    return hits[-1] if hits else None


# ------------------------------------------------------------- POV clips --
# Each is one Seedance reference-to-video call. `plate` names the reference.
# Duration is short on purpose: completion rate is the signal that matters at
# zero followers, and a 7-second clip completes where a 20-second one does not.
CLIPS = [

dict(id="pov_studio_open", plate="plate_studio", seconds=7,
 aspect="9:16", resolution="720p",
 story="MON 07:00. She has a key and she is the first one in. She is not "
       "teaching yet, she is putting a mat down, so both hands are free and "
       "the phone has a reason to be in one of them. This is the same seven "
       "o'clock slot people have already seen a photograph of.",
 prompt=
"Vertical phone video, 9:16. Shot on an iPhone 15 Pro: flat "
 "contrast, low saturation, everything sharp front to back, visible "
 "sensor noise in the shadows, no colour grade and no cinematic look.\n\n"
 "@Image1 is the room. Keep its layout, its light and its equipment exactly: "
 "the same floor, the same reformer frames, the same window.\n\n"
 "An empty pilates studio in Seongsu, Seoul, a few minutes after seven in the "
 "morning, before anyone else arrives.\n\n"
 "[0-2 seconds] The camera is low, looking down at the floor, and lifts "
 "slowly to standing height.\n"
 "[2-5 seconds] An uneven handheld pan to the left across the empty room: "
 "reformer frames, mats stacked against the wall, a bench, and then the tall "
 "window with a hard band of low sun lying across the boards.\n"
 "[5-7 seconds] The pan stops a little past the window and settles, and the "
 "exposure pulls down after blowing out briefly on the glass.\n\n"
 "Handheld throughout: a constant small shake from the hands holding it, "
 "so the frame is never completely still. The pan is uneven in speed, with "
 "a wobble at "
 "the start of the pan and a slight overshoot when it stops. Never smooth, "
 "never on a gimbal, never on a tripod.\n\n"
 "Nobody is in the room and nobody enters it.\n\n"
 "Avoid: any person appearing, any person reflected in glass or in a mirror, "
 "hands or arms entering the frame, soft dissolves, fluid morphing, smooth "
 "gimbal motion, slow motion, colour grading, film grain overlay, lens flare, "
 "shallow depth of field, background blur, black frames, and any cut. One "
 "continuous handheld take."),

# pov_river_walk. RELEASED FROM HOLD, AND THE GATE IT WAS WAITING ON FAILED —
# "build it only if the studio POV performs" and the studio POV got 118 views
# with nothing after them. It is built anyway because it was asked for, and the
# honest note is here rather than nowhere: a faceless beauty clip is the most
# oversupplied thing on the platform and has no reason to be pushed to anyone.
#
# SO SHE IS IN IT. Not her face — her SHADOW and her FEET. A walking POV where
# the walker never appears is drone stock; a long low-sun shadow thrown up the
# path ahead, and shoes entering the bottom of the frame at her stride, cost
# nothing, cannot fail a likeness check, and are the difference between "a
# river" and "someone walking by the river". They are also the hardest thing
# for the model to fake, which is the point.
#
# THE AVOID LIST IS REWRITTEN, NOT COPIED. Every other POV here bans "any
# person appearing" and "hands or arms entering the frame". Pasting that in
# would delete the only person in the shot. A list that contradicts the beats
# is worse than no list: it makes the model choose.
dict(id="pov_river_walk", seconds=7,
 aspect="9:16", resolution="720p",
 story="THU 19:00. The Thursday walk. She is not going anywhere — the path "
       "is the destination — and she stops for the light like everyone else "
       "on it, which is the whole reel: not that Seoul is beautiful, but that "
       "she has lived here long enough to still be stopping.",
 prompt=
"Vertical phone video, 9:16. Shot on an iPhone 15 Pro: flat "
 "contrast, low saturation, everything sharp front to back, visible "
 "sensor noise in the shadows, no colour grade and no cinematic look.\n\n"
 "A first-person walking view along the paved riverside path beside the Han "
 "in Seoul at about seven in the evening in late summer, carried by a woman "
 "walking at an ordinary pace. The path is a wide walkway of grey paving "
 "slabs with a painted cycle lane down one side, worn and patched where it "
 "has been repaired, a low railing and rough grass on the river side, and the "
 "water beyond. A long road bridge crosses the river ahead with traffic on it "
 "and its lights already on, and a line of tall apartment towers stands on "
 "the far bank. A litter bin and a lamp post pass on the path side.\n\n"
 "[0-2 seconds] The view is low, angled down at the paving a few steps "
 "ahead. Her own long shadow is thrown up the path in front of her by the low "
 "sun, and her feet in white trainers come into the bottom of the frame one "
 "after the other as she walks.\n"
 "[2-5 seconds] It lifts unevenly to look along the path: the railing and the "
 "water on one side, the bridge ahead with its lights on, the towers on the "
 "far bank, the sun low behind the bridge and the paving bright where the "
 "light lies along it.\n"
 "[5-7 seconds] The walking slows and stops, and the frame settles on the "
 "water and the bridge. The exposure pulls down a moment after it stops, "
 "having been blown out towards the sun.\n\n"
 "Handheld and walking: the frame rises and falls slightly with each step "
 "and never settles completely, the swing is uneven, and there is a small "
 "correction and a slight overshoot when the movement stops. Natural motion "
 "blur while it moves. Never smooth, never on a gimbal, never on a tripod, "
 "and it never travels at a constant speed.\n\n"
 "Her shadow and her feet are the only parts of her that appear. Anyone else "
 "on the path stays far away and small.\n\n"
 "Avoid: her body, her face or her reflection in frame, a phone or a camera "
 "in the picture, the hand or arm holding it, any other person close to the "
 "camera, any face, a drone shot, an aerial view, a crane, a dolly, rails, a "
 "gimbal, a tripod, zooming, morphing, slow motion, soft dissolves, colour "
 "grading, a film grain overlay, lens flare, shallow depth of field, "
 "background blur, black frames, and any cut. One continuous handheld take."),
]
