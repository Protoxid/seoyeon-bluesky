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
locations.py — build the location bible.

Her face is locked because a photograph of it is attached to every call. Her
apartment is not: it exists only as words, so the model redecorates it every
time. Viewers notice — a bedroom that changes shape between posts is the same
tell as a face that does.

The fix is the same one that worked for identity: generate each place ONCE,
pick the best plate, and attach it as a reference thereafter.

    python locations.py --list
    python locations.py bedroom --n 4        # candidates, pick one
    python locations.py --lock bedroom 02    # promote a candidate to canonical

Plates are generated EMPTY — no person in frame. A plate with someone in it
would fight the face reference for control of the same pixels.
"""
from __future__ import annotations
import argparse, os, pathlib, shutil, sys
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from kie_api import Kie, load_key, MODEL_T2I

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "locations"

STYLE = ("Interior photograph, no people, shot on an iPhone 16 Pro at 1x (24mm "
         "equivalent) — the same phone and processing as every other photo in "
         "this account. Low saturation, strong HDR so shadows lift and "
         "highlights hold, deep depth of field, fine shadow noise. "
         "A comfortable Seoul apartment belonging to a woman in her late "
         "twenties who earns well: warm pale wood, white walls, clean lines, a "
         "few good pieces chosen with care. It reads as real because someone is "
         "living in it right now — a cushion still holding the shape of "
         "somebody, an object set down mid-task and left there, curtains drawn "
         "by hand rather than evenly. Sockets, switches and skirting sit where "
         "they would really be.")

# A room description must NOT contain props the actions also introduce. The
# window room said "a mug on a low wooden stool" while action 0 says "holding a
# ceramic mug" — every hero came back with two mugs. The room holds furniture
# and fixtures; anything she picks up belongs to the action, never to both.
PLACES = {
    "bedroom": "A bright bedroom corner in a Seoul apartment: a low bed in "
               "white linen, the duvet pulled roughly up and still holding "
               "its creases, a pale oak bedside table with a small ceramic "
               "lamp and a hair tie beside it, a sheer curtain drawn by hand "
               "at a tall window. Morning light.",
    "window": "A living-room corner in a Seoul apartment: a soft cream "
               "armchair with the cushion still dented, a linen curtain half "
               "drawn, a healthy sage plant on the sill in a terracotta pot, "
               "a small oak stool used as a side table. Soft early-morning "
               "light.",
    "kitchen": "A compact kitchen corner in a Seoul apartment: pale wood "
               "worktop, an open shelf with stacked ceramic bowls in three "
               "quiet patterns, a small vase of dried grasses, a linen tea "
               "towel hung slightly crooked over the oven handle. Overcast "
               "daylight from a window out of frame.",
    "bathroom": "A clean white-tiled bathroom vanity in a Seoul apartment: a "
               "round mirror, skincare bottles grouped at one end with two "
               "left standing where they were last used, a folded linen "
               "towel, a brushed steel tap. Diffuse cool daylight.",
    "studio": "A small bright pilates studio: one reformer on pale wood, "
               "white walls, a large window along one side, a rolled mat and "
               "a neat stack of blocks against the wall. Flat overcast "
               "daylight.",
    "cafe": "A corner table in a small neighbourhood cafe in Seoul: warm "
               "wood, brass fittings, a window seat with a cushion somebody "
               "has just got up from, a shelf of well-kept plants, a small "
               "folded card standing on the table. Warm afternoon light.",
    "rooftop": "A city rooftop terrace in Seoul: smooth pale concrete, a "
               "simple metal railing, two potted olive trees, a low bench "
               "with a cushion left on it, the Seoul skyline muted behind. "
               "Flat overcast midday light.",
}


def canonical(name: str) -> pathlib.Path:
    return OUT / f"{name}.png"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("place", nargs="?")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--all", action="store_true",
                    help="generate candidates for every place not yet locked")
    ap.add_argument("--lock", nargs=2, metavar=("PLACE", "NN"),
                    help="promote candidate NN to the canonical plate")
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--budget", type=float, default=0.5)
    ap.add_argument("--aspect", default="3:4",
                    help="3:4 = one corner (default) · 21:9 = a wide plate "
                         "covering most of the room, which is harder for the "
                         "model to copy verbatim as a backplate")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if a.lock:
        place, nn = a.lock
        src = OUT / place / f"{place}_{int(nn):02d}.png"
        if not src.exists():
            sys.exit(f"no candidate {src}")
        shutil.copy(src, canonical(place))
        print(f"  locked {src.name} -> {canonical(place).name}")
        print("  content.py will now attach this as the environment reference.")
        return 0

    if a.all:
        todo = [k for k in PLACES if not canonical(k).exists()]
        if not todo:
            print("  every place already has a locked plate."); return 0
        print(f"  {len(todo)} places x {a.n} candidates = {len(todo)*a.n} images "
              f"(~${0.07*len(todo)*a.n:.2f})\n")
        import subprocess, sys as _s
        for k in todo:
            print(f"\n{'='*54}\n  {k}\n{'='*54}")
            subprocess.run([_s.executable, __file__, k, "--n", str(a.n),
                            "--budget", str(a.budget), "--aspect", a.aspect])
        print("\n  Now pick one per place:")
        for k in todo:
            print(f"    python locations.py --lock {k} <NN>")
        return 0

    if a.list or not a.place:
        print("\n  places            canonical plate")
        for k in PLACES:
            c = canonical(k)
            print(f"    {k:<16}{'LOCKED  ' + c.name if c.exists() else '— not yet locked'}")
        return 0

    if a.place not in PLACES:
        sys.exit(f"unknown place. Options: {', '.join(PLACES)}")
    prompt = f"{PLACES[a.place]}\n\n{STYLE}"
    if a.aspect in ("21:9", "16:9"):
        prompt += (" A wide view from one corner of the room taking in two "
                   "walls and most of the floor, so the whole space and how "
                   "its parts sit relative to each other is legible. Straight "
                   "lines stay straight — a wide rectilinear view, not a "
                   "curved or stitched panorama.")
    print(f"  place   {a.place}\n  prompt  {len(prompt)} chars\n")
    if a.dry_run:
        print("="*66); print(prompt); print("="*66)
        print(f"\n  DRY RUN — {a.n} plates would cost ~${0.07*a.n:.2f}")
        return 0

    load_key(ROOT)
    key = os.environ.get("KIE_API_KEY", "")
    if not key or key.startswith("PASTE"):
        sys.exit("no API key")
    kie = Kie(key)
    d = OUT / a.place; d.mkdir(parents=True, exist_ok=True)
    spent = [0.0]

    def one(i):
        if spent[0] + 0.07 > a.budget:
            return i, "skip", "budget cap"
        spent[0] += 0.07
        dest = d / f"{a.place}_{i:02d}.png"
        try:
            urls = kie.generate(prompt, a.aspect, None, model=MODEL_T2I)
            n = kie.download(urls[0], dest)
            return i, "ok", f"{dest.name}  {n//1024} KB"
        except Exception as e:
            spent[0] -= 0.07
            return i, "fail", str(e)[:120]

    with ThreadPoolExecutor(max_workers=3) as ex:
        for f in as_completed([ex.submit(one, i) for i in range(1, a.n+1)]):
            i, st, msg = f.result()
            print(f"  [{i}] {'  ok  ' if st=='ok' else ' FAIL ' if st=='fail' else ' skip '} {msg}")

    print(f"\n  ~${spent[0]:.2f} spent -> {d}")
    print(f"  Pick one, then: python locations.py --lock {a.place} <NN>")
    print("  Choose the one you would be happy seeing a hundred times.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
