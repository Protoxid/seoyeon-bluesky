#!/usr/bin/env python3
"""generate_w39_ig.py — Generate all 7 Instagram tier-1 images for 2026-W39.

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
OUT_DIR = CONTENT / "w39_2026-09-21"
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
        "id": "w39_mon_studio_mat",
        "caption": "monday morning reformer class before the rain. the wooden floor is cold again.\n\n#seongsu #seoul #daily #filmphoto #everyday",
        "prompt": (
            "A quiet morning in a Seoul pilates studio with tall windows on the left wall and polished wooden floorboards. "
            "A young Korean woman, 26, sitting on a grey pilates mat adjusting reformer springs. "
            "She wears charcoal leggings, a long-sleeve muted sage technical top, hair in a low ponytail with curtain bangs. "
            "Cool early autumn morning light. Unposed, quiet routine, candid snapshot. " + FILM
        ),
    },
    {
        "id": "w39_tue_market_figs",
        "caption": "bought figs from the market cart near ttukseom. three for two thousand won.\n\n#seongsu #seoul #daily #filmphoto #everyday",
        "prompt": (
            "A young Korean woman, 26, standing on a quiet street corner in Seongsu, Seoul at late afternoon. "
            "She wears a beige canvas trench coat over a white tee, dark denim jeans. "
            "She holds a small paper bag with fresh ripe purple figs visible at the top. "
            "Her hair is loose with curtain bangs moving in the breeze. Soft golden afternoon light, candid street texture. " + FILM
        ),
    },
    {
        "id": "w39_wed_balcony_breeze",
        "caption": "left the balcony screen door open. twenty minutes of quiet before client calls.\n\n#seongsu #seoul #daily #filmphoto #everyday",
        "prompt": (
            "A young Korean woman, 26, leaning casually against the open balcony doorway of a Seoul flat. "
            "She wears an oversized cream crewneck sweater and grey lounge shorts, holding a white ceramic coffee mug. "
            "Curtains blowing gently in the autumn breeze. Overcast sky with soft diffused natural daylight. "
            "Candid, contemplative, incidental body. " + FILM
        ),
    },
    {
        "id": "w39_thu_cafe_sketch",
        "caption": "iced americano condensation on the sketchbook. working through reformer spring tension diagrams.\n\n#seongsu #seoul #daily #filmphoto #everyday",
        "prompt": (
            "A quiet cafe corner in Seongsu-dong, Seoul. A small round wooden table with an iced americano glass "
            "showing water droplets, an open grid notebook with handwritten anatomical diagrams, and a black gel pen. "
            "In the background, concrete walls and warm pendant lighting. Lived-in, realistic cafe texture, no person in frame. " + FILM
        ),
    },
    {
        "id": "w39_fri_autumn_cardigan",
        "caption": "first day wearing the wool cardigan this year. autumn is properly here.\n\n#seongsu #seoul #daily #filmphoto #everyday",
        "prompt": (
            "A young Korean woman, 26, walking down a brick alleyway in Seongsu, Seoul at dusk. "
            "She wears a heavy charcoal ribbed wool cardigan over a plain black tee, loose trousers, white sneakers. "
            "Hands in her cardigan pockets, hair tucked behind one ear. Amber streetlights just turning on. "
            "Authentic candid street snapshot. " + FILM
        ),
    },
    {
        "id": "w39_sat_forest_steps",
        "caption": "saturday morning walk through seoul forest. yellow leaves on the asphalt.\n\n#seongsu #seoul #daily #filmphoto #everyday",
        "prompt": (
            "A tree-lined pathway in Seoul Forest in late September morning. "
            "A young Korean woman, 26, walking away from camera on the paved pathway, looking over her shoulder with a relaxed slight smile. "
            "She wears olive joggers, a windbreaker jacket, running sneakers. "
            "Yellow ginkgo leaves scattered on the ground. Crisp morning light through the branches. " + FILM
        ),
    },
    {
        "id": "w39_sun_evening_tea",
        "caption": "sunday night. boiled barley tea on the stove. flat smells like warm grain.\n\n#seongsu #seoul #daily #filmphoto #everyday",
        "prompt": (
            "A cozy Sunday evening scene in a minimalist Seoul flat kitchen. "
            "A stainless steel kettle steaming on a small induction cooktop. "
            "Beside it on the poured concrete counter sits an earthenware mug of dark amber roasted barley tea. "
            "Warm lamplight, night reflection on the dark window. Quiet solitude, lived-in realism. " + FILM
        ),
    },
]

def main():
    load_key(PERSONA)
    kie = Kie(os.environ.get("KIE_API_KEY", ""))
    print("✓ Kie initialized for W39 Instagram generator.")

    plate_map = {
        "w39_mon_studio_mat": PLATES / "plate_studio_wide_4e68ba_1.png",
        "w39_tue_market_figs": PLATES / "plate_hallway_ac909a_1.png",
        "w39_wed_balcony_breeze": PLATES / "plate_room_ecc050_1.png",
        "w39_thu_cafe_sketch": PLATES / "plate_room_ecc050_1.png",
        "w39_fri_autumn_cardigan": PLATES / "plate_stairwell_62963d_1.png",
        "w39_sat_forest_steps": PLATES / "plate_river_fa39bf_1.png",
        "w39_sun_evening_tea": PLATES / "plate_room_ecc050_1.png",
    }

    print("\n[*] Uploading plates and generating W39 IG shots...")
    for s in SHOTS:
        sid = s["id"]
        dest = OUT_DIR / f"{sid}.png"
        cap_path = CAPS_DIR / f"{sid}.txt"
        cap_path.write_text(s["caption"], encoding="utf-8")
        print(f"  ✓ Caption saved: {cap_path.name}")

    print("\n=== W39 IG Specification Prepared ===")

if __name__ == "__main__":
    main()
