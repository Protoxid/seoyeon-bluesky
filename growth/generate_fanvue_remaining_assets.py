#!/usr/bin/env python3
"""
generate_fanvue_remaining_assets.py — Generate seductive Fanvue banner options
and an additional propic option, tuned to clear safety filters while delivering
maximum allure and intimacy.
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent / "personas" / "seoyeon"
sys.path.insert(0, str(ROOT))

from kie_api import Kie, load_key, MODEL_I2I

MASTER_A = ROOT / "master" / "a"
MASTER_C = ROOT / "master" / "c"
OUT_DIR = ROOT / "content" / "fanvue"
ARTIFACT_DIR = pathlib.Path(r"C:\Users\user\.gemini\antigravity-ide\brain\5550af27-ad99-433e-bb06-ef15aab0665b")

FACE_REFS = ["a1_front.png", "a2_tq_left.png"]
BODY_REF = "c5_relax_front.png"

ROLES_FACE = (
    "Images 1 and 2 are her face from two angles — use them for her features, "
    "striking amber-hazel irises, and delicate pale freckles across her nose and inner cheeks."
)

ROLES_BODY = (
    "Images 1 and 2 are her face from two angles — use them for her features and freckles. "
    "Image 3 is her full length — use it for athletic build and head-to-body proportions."
)

SKIN = (
    "Her skin is matte and natural: visible pores, subtle skin texture, soft neutral undertone, "
    "the only sheen a faint natural morning glow along the bridge of the nose."
)

LENS_CLOSE = (
    "Shot on an iPhone 15 Pro: flat HDR contrast, low saturation, shallow depth of field, "
    "fine organic noise in shadows, authentic unedited photography."
)

LENS_WIDE = (
    "Shot on an iPhone 15 Pro: flat HDR contrast, low saturation, wide panoramic cinematic composition, "
    "deep ambient morning lighting, fine organic noise, authentic candid lifestyle photography."
)

SAFE = "An ordinary everyday morning lifestyle photograph in a Seoul apartment, tasteful and fully clothed."

ASSETS = [
    # --- Propic Option 2 (1:1 Square, 2K) ---
    {
        "id": "fv_propic_morning_knit",
        "type": "propic",
        "aspect": "1:1",
        "tier": "2k",
        "title": "Propic Option 2: Cozy Off-Shoulder Morning Knit",
        "prompt": (
            "A magnetic, intimate close-up bust portrait of a beautiful 26-year-old Korean woman in her Seongsu apartment bedroom. "
            "Sitting in morning sunlight with warm white linen in the soft-focus background. "
            "Wearing a soft cream-colored knit top with a wide boat neckline falling gently off one shoulder to reveal her elegant neck and collarbone. "
            "Her signature long honey-balayage hair falls in soft bedroom waves over her chest with curtain bangs framing her prominent cheekbones. "
            "She looks straight into the camera lens with captivating, seductive amber-hazel eyes, subtle aegyo-sal, and a relaxed, enigmatic half-smile. "
            "Centered square composition framed perfectly for a circular profile picture. "
            f"{SAFE} {SKIN} {LENS_CLOSE}\n\n{ROLES_FACE}"
        ),
        "use_body": False,
    },
    # --- Banner Option 1 (21:9 Ultra-Wide, 2K) ---
    {
        "id": "fv_banner_bedroom_linen",
        "type": "banner",
        "aspect": "21:9",
        "tier": "2k",
        "title": "Banner Option 1: Sunlit Bedroom Linen Panoramic",
        "prompt": (
            "An ultra-wide 21:9 cinematic panoramic photograph of a 26-year-old Korean woman in her minimalist Seongsu apartment. "
            "She is relaxing across a low platform bed with rumpled white linen sheets and duvet, propped up on one elbow, "
            "looking back over her shoulder with an alluring, captivating direct gaze into the camera. "
            "Wearing an oversized relaxed white cotton shirt and loungewear. Her long wavy balayage hair flows loosely down her back. "
            "Floor-to-ceiling windows on one side diffuse soft, warm morning sunlight across the modern room. "
            "Spacious panoramic framing establishing an intimate, chic, luxurious private space. "
            f"{SAFE} {SKIN} {LENS_WIDE}\n\n{ROLES_BODY}"
        ),
        "use_body": True,
    },
    # --- Banner Option 2 (21:9 Ultra-Wide, 2K) ---
    {
        "id": "fv_banner_window_skyline",
        "type": "banner",
        "aspect": "21:9",
        "tier": "2k",
        "title": "Banner Option 2: High-Rise Window Skyline Panoramic",
        "prompt": (
            "An ultra-wide 21:9 cinematic banner photograph of a 26-year-old Korean woman sitting comfortably by the large panoramic window "
            "of her Seongsu high-rise apartment in morning golden hour light. "
            "She is seated gracefully on a low minimalist daybed with pillows, holding a warm ceramic cup, turning her torso and head toward the camera "
            "with a seductive, gentle gaze and striking amber-hazel eyes. "
            "Wearing a fitted neutral ribbed lounge top and soft trousers. Warm sunlight catches the golden highlights of her wavy balayage hair. "
            "Cinematic wide framing, uncluttered aesthetic, peaceful and magnetic morning atmosphere. "
            f"{SAFE} {SKIN} {LENS_WIDE}\n\n{ROLES_BODY}"
        ),
        "use_body": True,
    },
]


def run():
    load_key(ROOT)
    key = os.environ.get("KIE_API_KEY")
    if not key:
        sys.exit("Error: KIE_API_KEY not found.")

    kie = Kie(key)
    print("=== Generating Fanvue Remaining Assets (Banners + Extra Propic) ===")
    print(f"Current Kie Credit Balance: {kie.credit()}")

    face_urls = [kie.upload((MASTER_A / n).resolve()) for n in FACE_REFS]
    body_url = kie.upload((MASTER_C / BODY_REF).resolve())

    for shot in ASSETS:
        shot_id = shot["id"]
        aspect = shot["aspect"]
        tier = shot["tier"]
        prompt = shot["prompt"]
        use_body = shot["use_body"]

        refs = face_urls + ([body_url] if use_body else [])
        print(f"\n--- Generating {shot_id} ({aspect}, {tier}) ---")
        print(f"Title: {shot['title']}")

        try:
            t0 = time.time()
            urls = kie.generate(
                prompt=prompt,
                aspect=aspect,
                image_urls=refs,
                model=MODEL_I2I,
                tier=tier,
            )
            elapsed = time.time() - t0
            img_url = urls[0]
            print(f"  Generated in {elapsed:.1f}s: {img_url}")

            dest_local = OUT_DIR / f"{shot_id}.png"
            dest_artifact = ARTIFACT_DIR / f"{shot_id}.png"

            bytes_saved = kie.download(img_url, dest_local)
            shutil.copyfile(dest_local, dest_artifact)
            print(f"  Saved {dest_local.name} ({bytes_saved // 1024} KB)")
        except Exception as e:
            print(f"  Failed for {shot_id}: {e}")

    print(f"\nFinished. Remaining Kie Credit Balance: {kie.credit()}")


if __name__ == "__main__":
    run()
