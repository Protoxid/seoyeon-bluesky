#!/usr/bin/env python3
"""generate_w38_ig.py — Generate all 7 Instagram tier-1 images for 2026-W38.

Uses Kie gpt-image-2 image-to-image with plate references.
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
OUT_DIR = CONTENT / "w38_2026-09-14"
OUT_DIR.mkdir(parents=True, exist_ok=True)
CAPS_DIR.mkdir(parents=True, exist_ok=True)

MASTER_A1 = str(PERSONA / "master" / "a" / "a1_front.png")

# Filmic suffix
FILM = (
    "Shot on iPhone 15 Pro: flat natural contrast, low saturation, fine filmic shadow noise, "
    "natural matte skin texture with visible real pores and faint pale freckles across the nose bridge and inner cheeks, "
    "light amber-hazel irises with dark limbal ring and pronounced aegyo-sal, honey-blonde gradient balayage hair, "
    "clean hands with exactly five natural relaxed fingers, zero CGI plastic, authentic candid snapshot."
)

SHOTS = [
    {
        "id": "w38_morning_light",
        "caption": "the studio at ten to seven. no one here yet. i said yes to the fourth slot so i will be here more often\n\n#seongsu #seoul #daily #filmphoto #everyday",
        "prompt": (
            "A quiet morning in a Seoul pilates studio with tall windows on the left wall and a full-height mirror on the right. "
            "A young Korean woman, 26, stands in front of the mirror in grey leggings, a white cropped tank, and an unzipped charcoal hoodie. "
            "Her hair is in a loose low bun with curtain bangs. She is turned toward the windows, looking at the warm low-angled morning light "
            "falling across the far wall rather than at her own reflection. Three-quarter profile. "
            "Soft September morning light. Ambient, everyday feel. " + FILM
        ),
    },
    {
        "id": "w38_table_afternoon",
        "caption": "the pear was good. the window is cracked for the first time since july\n\n#seongsu #seoul #daily #filmphoto #everyday",
        "prompt": (
            "A quiet afternoon scene in a Seoul one-room flat. A small wooden table near a window with grey curtains, one chair. "
            "On the table, a white MacBook angled away so the screen is not readable, a chipped ceramic coffee mug, a notebook, a pen. "
            "The window is open, a slight breeze moves the curtain. Beside the table, a standing fan is visible and turned off — idle blades. "
            "Warm afternoon light falls across the tabletop. Natural, lived-in, quiet. No person in frame. " + FILM
        ),
    },
    {
        "id": "w38_stairwell_notes",
        "caption": "eight hours of observation and i cannot look at another reformer\n\n#seongsu #seoul #daily #filmphoto #everyday",
        "prompt": (
            "A young Korean woman, 26, sitting on a concrete stairwell landing in a Seoul building. Evening light comes through "
            "a narrow window behind her. She wears a charcoal hoodie and black leggings, her hair pinned up messily in a claw clip "
            "with curtain bangs falling loose. A spiral notebook is open on her knee, filled with handwritten notes. "
            "She holds a white iPhone in a clear scuffed case, looking down at the screen. "
            "Exhausted, relaxed. Concrete walls, metal railing. Candid, post-observation fatigue. "
            "Soft golden hour light. " + FILM
        ),
    },
    {
        "id": "w38_river_pears",
        "caption": "bought a pear from the ajumma by the bridge. ate it watching the lights\n\n#seongsu #seoul #daily #filmphoto #everyday",
        "prompt": (
            "A young Korean woman, 26, standing on a riverside path by the Han River in Seoul at golden hour. "
            "She wears a light beige cotton jacket over a white tee, loose blue jeans, white sneakers. "
            "She holds a small faded blue market bag with four Korean pears visible at the top. "
            "Her hair is down with curtain bangs. She looks toward the river, profile or three-quarter view, "
            "relaxed, watching the light on the water. The river is wide, the sky warm gold and soft blue. "
            "Late summer transitioning to autumn. Candid, everyday, peaceful. " + FILM
        ),
    },
    {
        "id": "w38_study_light",
        "caption": "the study binder i have been meaning to finish since august. friday night.\n\n#seongsu #seoul #daily #filmphoto #everyday",
        "prompt": (
            "A late-night study scene in a Seoul one-room flat. A wooden table with a single warm desk lamp illuminating the surface. "
            "An open pilates anatomy textbook cracked at the spine, handwritten index cards, a yellow highlighter, a glass of water. "
            "The rest of the room is dark — the window behind shows night sky. "
            "A woman's hands at the edge of frame, one holding the highlighter. "
            "Focus on the tabletop. Quiet, focused, late-night study atmosphere. " + FILM
        ),
    },
    {
        "id": "w38_hallway_tired",
        "caption": "saturday module done. the exam is close and i can feel it\n\n#seongsu #seoul #daily #filmphoto #everyday",
        "prompt": (
            "A young Korean woman, 26, leaning against a wall in a Seoul education building hallway. "
            "She wears a plain black long-sleeve tee, loose grey sweatpants, white sneakers. "
            "Her hair is pinned up messily in a claw clip with curtain bangs hanging loose. "
            "She looks tired — dark circles, flat expression, direct eye contact with the camera. "
            "She holds a half-empty transparent water bottle. The hallway has fluorescent ceiling lights, beige walls. "
            "The light is cool and institutional. Candid, exhausted, not posed. " + FILM
        ),
    },
    {
        "id": "w38_sunday_floor",
        "caption": "sunday reset. laundry and the week ahead. pears again.\n\n#seongsu #seoul #daily #filmphoto #everyday",
        "prompt": (
            "A young Korean woman, 26, sitting on the floor beside her bed in a Seoul one-room flat. Sunday morning light comes through "
            "an open window with grey curtains moving in a light breeze. She wears an oversized soft cream cotton shirt and loose beige "
            "lounge pants, barefoot. Her hair is down, messy from sleep, curtain bangs. "
            "She sits cross-legged, looking out the window, a quiet expression. "
            "A ceramic mug of barley tea sits on the floor beside her. "
            "A box of pears is visible on the counter beyond her. Peaceful, slow Sunday morning atmosphere. " + FILM
        ),
    },
]

def main():
    load_key(PERSONA)
    kie = Kie(os.environ["KIE_API_KEY"])
    cred = kie.credit()
    print(f"✓ Kie ready. Credit: {cred}")

    # Upload the plates that are shared across shots
    print("\n[*] Uploading plate images...")
    plate_urls = {}
    plates_needed = set(s["id"] for s in SHOTS)  # lazy mapping
    # Map shot_id -> plate file
    plate_map = {
        "w38_morning_light": PLATES / "plate_studio_wide_4e68ba_1.png",
        "w38_table_afternoon": PLATES / "plate_room_ecc050_1.png",
        "w38_stairwell_notes": PLATES / "plate_stairwell_62963d_1.png",
        "w38_river_pears": PLATES / "plate_river_fa39bf_1.png",
        "w38_study_light": PLATES / "plate_room_ecc050_1.png",
        "w38_hallway_tired": PLATES / "plate_hallway_ac909a_1.png",
        "w38_sunday_floor": PLATES / "plate_room_ecc050_1.png",
    }
    # Deduplicate by resolved path
    unique_plates = {}
    for sid, pp in plate_map.items():
        sp = str(pp.resolve())
        unique_plates[sp] = pp
    for sp, pp in unique_plates.items():
        url = kie.upload(sp)
        plate_urls[sp] = url
        print(f"  Uploaded {pp.name} → {url[:60]}...")

    # Generate each shot — plate-only reference for tier-1 SFW
    for s in SHOTS:
        sid = s["id"]
        dest = OUT_DIR / f"{sid}.png"
        if dest.exists():
            print(f"\n  SKIP {sid} — already exists")
            continue

        plate_path = str(plate_map[sid].resolve())
        refs = [plate_urls[plate_path]]

        print(f"\n--- {sid} ---")
        print(f"  Refs: {len(refs)} (plate only — tier 1 SFW)")

        try:
            urls = kie.generate(
                prompt=s["prompt"],
                aspect="3:4",
                image_urls=refs,
                tier="1k",
            )
            if urls:
                n = kie.download(urls[0], dest)
                print(f"  ✓ Downloaded {n} bytes → {dest}")

                # Write caption
                cap_path = CAPS_DIR / f"{sid}.txt"
                cap_path.write_text(s["caption"], encoding="utf-8")
                print(f"  ✓ Caption → {cap_path}")
        except Exception as e:
            print(f"  ✗ FAIL: {e}")
            continue

    print("\n=== IG Generation Complete ===")

if __name__ == "__main__":
    main()