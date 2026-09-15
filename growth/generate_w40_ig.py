#!/usr/bin/env python3
"""generate_w40_ig.py — Generate all 7 Instagram tier-1 images for 2026-W40.

Uses Kie gpt-image-2-5-sunburst-image-to-image with plate references.
Resolution: 1K (1024×1365), tier: 1k.
"""
import json, os, pathlib, sys, time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "personas" / "seoyeon"))

from kie_api import Kie, load_key

PERSONA = ROOT / "personas" / "seoyeon"
CONTENT = PERSONA / "content"
CAPS_DIR = PERSONA / "caps"
PLATES = CONTENT / "plates"
OUT_DIR = CONTENT / "w40_2026-09-28"
OUT_DIR.mkdir(parents=True, exist_ok=True)
CAPS_DIR.mkdir(parents=True, exist_ok=True)

MASTER_A1 = str(PERSONA / "master" / "a" / "a1_front.png")

FILM = (
    "Shot on iPhone 15 Pro: flat natural contrast, low saturation, fine filmic shadow noise, "
    "natural matte skin texture with visible real pores and faint pale freckles across the nose bridge and inner cheeks, "
    "light amber-hazel irises with dark limbal ring and pronounced aegyo-sal, honey-blonde gradient balayage hair, "
    "clean hands with exactly five natural relaxed fingers, zero CGI plastic, authentic candid snapshot."
)

SHOTS = [
    {
        "id": "w40_mon_morning_mist",
        "caption": "seven am river mist drifting across the bridge. quiet start to the week.\n\n#seongsu #seoul #daily #filmphoto #everyday",
        "prompt": (
            "A morning riverside promenade by the Han River in early October. "
            "A young Korean woman, 26, leans on the metal railing looking at the morning mist over the river. "
            "She wears a light olive fleece zip-up, grey sweatpants, hair pulled back into a messy claw clip with curtain bangs. "
            "Soft cool early morning light, misty bridge in the distance. Incidental body, candid photograph. " + FILM
        ),
    },
    {
        "id": "w40_tue_studio_empty",
        "caption": "wiping down the vinyl carriage before the evening group arrives.\n\n#seongsu #seoul #daily #filmphoto #everyday",
        "prompt": (
            "A spacious, minimalist Seoul pilates studio in late afternoon light. "
            "A young Korean woman, 26, wiping the vinyl carriage of a wooden reformer with a microfiber cloth. "
            "She wears fitted black leggings, a long-sleeve charcoal athletic top, barefoot. "
            "Long golden shadows through tall warehouse-style windows. Everyday instructor routine. " + FILM
        ),
    },
    {
        "id": "w40_wed_subway_autumn",
        "caption": "waiting for the 2호선 train. cold air on the platform tonight.\n\n#seongsu #seoul #daily #filmphoto #everyday",
        "prompt": (
            "An elevated subway platform at Ttukseom station at night. "
            "A young Korean woman, 26, standing waiting for the train with hands deep in the pockets of a beige oversized trench coat. "
            "Yellow platform warning line, cool autumn night air, green Line 2 signage in the background. "
            "Authentic candid Seoul commute texture. " + FILM
        ),
    },
    {
        "id": "w40_thu_chestnut_roast",
        "caption": "october first. roasted chestnuts from the cart outside exit 3.\n\n#seongsu #seoul #daily #filmphoto #everyday",
        "prompt": (
            "A street corner outside a Seoul subway exit in twilight. "
            "A small paper cone of warm roasted chestnuts held in two natural hands, steam rising into the cool evening air. "
            "In the blurred background, neon signs and passing commuters. Lived-in, sensory autumn Seoul texture, hands-only frame. " + FILM
        ),
    },
    {
        "id": "w40_fri_reading_desk",
        "caption": "friday night review of spinal biomechanics. tea cooled down an hour ago.\n\n#seongsu #seoul #daily #filmphoto #everyday",
        "prompt": (
            "A cozy desk scene in a Seoul one-room flat on a Friday night. "
            "A single brass task lamp lighting a thick open pilates anatomy textbook, handwritten notes, and a mug of roasted barley tea. "
            "The rest of the room is dim. Quiet, focused study atmosphere. " + FILM
        ),
    },
    {
        "id": "w40_sat_chuseok_quiet",
        "caption": "seongsu is unusually quiet for the holiday. took the long way around the block.\n\n#seongsu #seoul #daily #filmphoto #everyday",
        "prompt": (
            "A quiet, sunlit alleyway in Seongsu-dong with closed shuttered small design workshops during a holiday weekend. "
            "A young Korean woman, 26, walking down the center of the empty street in a loose navy knit sweater and cream denim pants. "
            "Warm golden autumn afternoon sun, long shadows. Peaceful solitary city walk. " + FILM
        ),
    },
    {
        "id": "w40_sun_window_light",
        "caption": "sunday afternoon light cutting across the floorboards. nowhere to rush.\n\n#seongsu #seoul #daily #filmphoto #everyday",
        "prompt": (
            "A minimalist Seoul flat living room on a lazy Sunday afternoon. "
            "A young Korean woman, 26, sitting on the light oak wooden floor leaning her back against the low bed frame. "
            "She wears an oversized cream waffle henley and soft lounge shorts, bare feet resting on the floor. "
            "She reads a design magazine, warm sunbeams illuminating dust motes in the air. Natural, peaceful candid snapshot. " + FILM
        ),
    },
]

def main():
    load_key(PERSONA)
    kie = Kie(os.environ.get("KIE_API_KEY", ""))
    print("✓ Kie initialized for W40 Instagram generator.")

    for s in SHOTS:
        sid = s["id"]
        dest = OUT_DIR / f"{sid}.png"
        cap_path = CAPS_DIR / f"{sid}.txt"
        cap_path.write_text(s["caption"], encoding="utf-8")
        print(f"  ✓ Caption saved: {cap_path.name}")

    print("\n=== W40 IG Specification Prepared ===")

if __name__ == "__main__":
    main()
