#!/usr/bin/env python3
"""generate_w39_ig.py — Generate all 7 Instagram tier-1 images for 2026-W39.

Engine: Kie gpt-image-2-5-sunburst-image-to-image (Tier 1 SFW).
Resolution: 1K (1024×1365), tier: 1k, aspect: 3:4.

Plate Policy (Strictly Enforced):
- Plateless default: Avoid using plates as much as possible.
- Max couple per week (~2): Reserved strictly for recurring indoor anchor spaces
  (Monday Studio & Sunday Flat).
- All other shots (streets, cafes, balcony, parks) are Plateless, relying on natural
  environmental prompts and face reference MASTER_A1 to prevent glued-on composite artifacts.
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
        "plate": "plate_studio_wide_4e68ba_1.png",  # Plate 1 of 2: Recurring workplace
        "has_person": True,
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
        "plate": None,  # Plateless: outdoor street market
        "has_person": True,
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
        "plate": None,  # Plateless: fresh natural perspective
        "has_person": True,
    },
    {
        "id": "w39_thu_cafe_sketch",
        "caption": "iced americano condensation on the sketchbook. working through reformer spring tension diagrams.\n\n#seongsu #seoul #daily #filmphoto #everyday",
        "prompt": (
            "A quiet cafe corner in Seongsu-dong, Seoul. A small round wooden table with an iced americano glass "
            "showing water droplets, an open grid notebook with handwritten anatomical diagrams, and a black gel pen. "
            "In the background, concrete walls and warm pendant lighting. Lived-in, realistic cafe texture, no person in frame. " + FILM
        ),
        "plate": None,  # Plateless: still-life cafe texture
        "has_person": False,
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
        "plate": None,  # Plateless: outdoor alleyway
        "has_person": True,
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
        "plate": None,  # Plateless: outdoor park
        "has_person": True,
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
        "plate": "plate_room_ecc050_1.png",  # Plate 2 of 2: Recurring home flat
        "has_person": False,
    },
]

def main():
    load_key(PERSONA)
    kie = Kie(os.environ.get("KIE_API_KEY", ""))
    print("✓ Kie initialized for W39 Instagram generator.")
    print("  Model: gpt-image-2-5-sunburst-image-to-image (1K tier)")
    print("  Plates attached: 2 of 7 (studio Monday, flat Sunday; 5 plateless)")

    # Save captions
    for s in SHOTS:
        cap_path = CAPS_DIR / f"{s['id']}.txt"
        cap_path.write_text(s["caption"], encoding="utf-8")
        print(f"  ✓ Caption saved: {cap_path.name}")

    if "--generate" in sys.argv:
        print("\n[*] Uploading required references and executing generation...")
        uploaded_urls = {}

        # Upload face master
        face_url = kie.upload(MASTER_A1)
        print(f"  Uploaded face master → {face_url[:60]}...")

        # Upload the couple of locked plates
        plate_urls = {}
        for s in SHOTS:
            if s["plate"]:
                p_path = PLATES / s["plate"]
                if str(p_path) not in plate_urls:
                    p_url = kie.upload(str(p_path))
                    plate_urls[str(p_path)] = p_url
                    print(f"  Uploaded plate {s['plate']} → {p_url[:60]}...")

        for s in SHOTS:
            sid = s["id"]
            dest = OUT_DIR / f"{sid}.png"
            if dest.exists():
                print(f"  SKIP {sid} — already exists on disk")
                continue

            refs = []
            if s["plate"]:
                refs.append(plate_urls[str(PLATES / s["plate"])])
            if s["has_person"]:
                refs.append(face_url)

            print(f"\n--- Generating {sid} ---")
            print(f"  Plate: {s['plate'] or 'NONE (Plateless)'} | Refs: {len(refs)}")

            if refs:
                urls = kie.generate(
                    prompt=s["prompt"],
                    aspect="3:4",
                    image_urls=refs,
                    model="gpt-image-2-5-sunburst-image-to-image",
                    tier="1k",
                )
            else:
                urls = kie.generate(
                    prompt=s["prompt"],
                    aspect="3:4",
                    image_urls=None,
                    model="gpt-image-2-text-to-image",
                    tier="1k",
                )

            if urls:
                n = kie.download(urls[0], dest)
                print(f"  ✓ Downloaded {n} bytes → {dest}")

    print("\n=== W39 IG Ready ===")

if __name__ == "__main__":
    main()
