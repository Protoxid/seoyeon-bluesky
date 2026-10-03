"""
run_batch2.py — Nova's batch-2 runner for the two W37 shots the owner rebalanced
on 6 Sep (STOP-AND-ADJUST): `w37_table_sunday` and `w37_jieun_roof` went from
no-face room frames to FACE-IN frames.

Why a separate file: `w37_shots.py` is shared code and I was told not to edit
it, so the revised prompts live here. Everything else is deliberately the same
as `outside.py --week3`:
  * references go through kie_api.Kie.generate -> model_schemas.build_input,
    which puts them in gpt-image-2's `input_urls`. Nothing here hand-builds a
    request body.
  * the plate is Image 1 and the face masters follow it, so the ordinals in the
    role sentences match the actual upload order (the bug roles_for() replaced).
  * no body/limb reference attaches on these two: both are clothed-torso
    frames, and the word "tattoo" never appears.
  * model gpt-image-2-image-to-image, 3:4, 2k, $0.09/image.
  * second-person risk: an attached face reference with no stated job is the
    mistake that put a second woman in a frame, so ROLE_FACE says which of the
    two women the face belongs to, in the positive.

    python run_batch2.py --only w37_jieun_roof --n 1 --budget 0.20
    python run_batch2.py --dry-run
"""
import argparse, hashlib, os, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from kie_api import Kie, load_key, MODEL_I2I, image_cost
from outside import FACE, MASTER, ROOT, SKIN
from pov import plate_path

OUT = ROOT / "content" / "w37_2026-09-07"

# Same clause outside.py sends for a plated frame WITH people in it.
ROLE_PLATE = ("Image 1 is the room this photograph is taken in. Use it for the "
              "layout, the furniture, the surfaces and the light — it is the "
              "same room, not a similar one. Nobody is in Image 1; the people "
              "described below are.")
# Which woman the two face frames belong to. Stated as a positive assignment:
# the house rule is that naming a thing summons it, so this says whose face is
# whose rather than forbidding a shared one.
ROLE_FACE = ("Images 2 and 3 are HER face from two angles — use them for her "
             "features and the pale freckles on her nose and inner cheeks, and "
             "for the nearer woman only. The second woman is a different "
             "person with a face of her own: a wider brow, a different build, "
             "her hair worn another way.")
# The everyday-snapshot line outside.py appends where the filter has tripped
# before (rooftop at dusk, n_roof_posed).
SAFE = ("An ordinary fully clothed everyday snapshot, nothing sexual about it.")

SHOTS = {

# ---- THU 10 SEP · 20:40 ---- REBALANCED: both of them, faces in ------------
"w37_jieun_roof": dict(
    plate="plate_rooftop", aspect="3:4", tier="2k",
    text=
    "Two women sitting side by side on the low concrete parapet wall of a "
    "Seoul residential rooftop at dusk, photographed by a phone propped on the "
    "ledge opposite them at their own height. Both faces are in the frame and "
    "readable. The woman nearer the lens is the one in Images 2 and 3: her hair "
    "is down in soft natural waves, centre-parted with curtain bangs, she "
    "wears a plain dark grey t-shirt, and she is looking straight into the lens "
    "with the small tired half of a smile that is not really a smile. The "
    "woman beside her is a friend a few years older, her own face with a wider "
    "brow and a fuller jaw, hair pulled back off her forehead and tied low at "
    "the nape, an oversized short-sleeve button shirt over a white tee; she is "
    "turned three-quarters toward her friend, mid-sentence, laughing at "
    "something she just said, so her face reads in soft three-quarter rather "
    "than square to the camera. They are the only two people on the roof and no "
    "third person appears anywhere in the frame, including the stairwell door "
    "and the far edge. Between them on the wall: two cups, a round plastic food "
    "container with the lid resting beside it, a pair of chopsticks laid "
    "across it, a crumpled napkin. Behind them the skyline and a water tower on "
    "the neighbouring roof, the sky going from pale warm at the horizon to "
    "grey-blue above, a few windows lit in the blocks opposite. Rooftop clutter "
    "kept honest: a washing line with nothing on it, water tanks, a metal door, "
    "gravel underfoot. Late evening light, soft, no flash, everything a little "
    "flat and slightly underexposed, fine grain, the horizon a few degrees off "
    "level."),

# ---- SUN 13 SEP · 21:05 ---- REBALANCED: face in, numbers out --------------
"w37_table_sunday": dict(
    plate="plate_room", aspect="3:4", tier="2k",
    text=
    "A woman sitting alone at a small table in a one-room flat in Seoul late at "
    "night, photographed by a phone propped low at the near corner of the table "
    "facing her, so the frame runs across the tabletop at chin height. Her face "
    "is in the frame and she is looking straight into the lens: her hair is "
    "down and pushed behind one ear, an oversized pale washed t-shirt, both her "
    "hands resting flat on the wood in front of her, shoulders dropped, the "
    "plain unguarded face of someone who has been awake doing arithmetic since "
    "morning. She is the only person in the room and nobody else appears "
    "anywhere in the frame. Between the lens and her sits an open laptop with "
    "its LID TURNED TO THE CAMERA, so what shows is the plain back of the lid "
    "and its outer edge; the display faces away from the lens and reaches the "
    "frame only as a pale glow along the top of it, lighting her a little from "
    "the side. Beside the laptop a small open notebook lies at a shallow angle "
    "to the lens with one short faint pencil stroke on the page and nothing "
    "else, the stroke lying nearly edge-on to the camera; a pen rests loose "
    "next to it. A glass of water on a coaster. A lamp on at one end throwing "
    "warm light across the wood and leaving the rest of the room in shade. In "
    "the background, out of focus, the standing fan is still running at the bed "
    "and the window is dark and shut. Her face and the things on the table "
    "sharp, the room behind falling soft. Warm lamp light against cold dark, "
    "low contrast, heavy fine noise in the shadows, the frame slightly off "
    "level."),
}


def build(d):
    return "\n\n".join([d["text"], ROLE_PLATE, ROLE_FACE, SAFE, SKIN])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", required=True)
    ap.add_argument("--n", type=int, default=1)
    ap.add_argument("--budget", type=float, default=0.20)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    ids = [x for x in a.only.replace(",", " ").split() if x]
    for i in ids:
        if i not in SHOTS:
            sys.exit(f"unknown id {i}. known: {', '.join(SHOTS)}")

    kie = urls = None
    spent = 0.0
    for i in ids:
        d = SHOTS[i]
        prompt = build(d)
        h = hashlib.sha256(prompt.encode()).hexdigest()[:6]
        cost = image_cost(d["aspect"], d["tier"], 3)
        if a.dry_run:
            print("=" * 66)
            print(f"[{i}  {d['tier']}  {d['plate']}  {h}]\n{prompt}")
            continue
        if spent + cost > a.budget:
            print(f"  [{i:<18}]  skip  budget cap")
            continue
        spent += cost
        if kie is None:
            load_key(ROOT)
            key = os.environ.get("KIE_API_KEY", "")
            if not key or key.startswith("PASTE"):
                sys.exit("no API key in kie_key.txt")
            kie = Kie(key)
            urls = {}
        urls.setdefault("p:" + d["plate"],
                        kie.upload(plate_path(d["plate"]).resolve()))
        for n in FACE:                                   # Images 2 and 3
            urls.setdefault("f:" + n, kie.upload((MASTER / n).resolve()))
        refs = [urls["p:" + d["plate"]]] + [urls["f:" + n] for n in FACE]
        got = kie.generate(prompt, d["aspect"], refs, model=MODEL_I2I,
                           tier=d["tier"])
        dest = OUT / f"{i}_{h}_1.png"
        nb = kie.download(got[0], dest)
        print(f"  [{i:<18}]   ok    {dest.name}  {nb//1024} KB  [{d['tier']}]")
    if not a.dry_run:
        print(f"\n  ~${spent:.2f} -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
