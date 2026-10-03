#!/usr/bin/env python3
"""
generate_fanvue_profile_assets.py — Generate seductive, high-converting
profile picture (propic) and banner images for Fanvue creator @syeon.hn.

Strictly adheres to:
- SFW public surface rules (AUP §2.6 / Discover guidelines)
- Seo-yeon Han identity canon (26 yo, amber-hazel eyes, subtle freckles, balayage hair)
- Kie gpt-image-2-image-to-image pipeline with verified reference bindings
- 2K resolution for maximum sharpness on desktop and mobile
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import shutil
import sys
import time

# Ensure personas/seoyeon is in path
ROOT = pathlib.Path(__file__).resolve().parent.parent / "personas" / "seoyeon"
sys.path.insert(0, str(ROOT))

from kie_api import Kie, load_key, MODEL_I2I
from model_schemas import build_input

# Reference paths
MASTER_A = ROOT / "master" / "a"
MASTER_C = ROOT / "master" / "c"
OUT_DIR = ROOT / "content" / "fanvue"
ARTIFACT_DIR = pathlib.Path(r"C:\Users\user\.gemini\antigravity-ide\brain\5550af27-ad99-433e-bb06-ef15aab0665b")

FACE_REFS = ["a1_front.png", "a2_tq_left.png"]
BODY_REF = "c5_relax_front.png"

ROLES_FACE = (
    "Images 1 and 2 are her face from two angles — use them for her features, "
    "striking amber-hazel irises, and the delicate pale freckles across her nose and inner cheeks."
)

ROLES_BODY = (
    "Images 1 and 2 are her face from two angles — use them for her features and freckles. "
    "Image 3 is her full length — use it for athletic hourglass build and head-to-body proportions."
)

SKIN = (
    "Her skin is matte and natural: visible pores, subtle skin texture, soft neutral undertone, "
    "the only sheen a faint natural morning glow along the bridge of the nose."
)

LENS_CLOSE = (
    "Shot on an iPhone 15 Pro: flat HDR contrast, low saturation, shallow depth of field "
    "with soft creamy background blur, fine organic noise in shadows, natural real photography."
)

LENS_WIDE = (
    "Shot on an iPhone 15 Pro: flat HDR contrast, low saturation, wide cinematic composition, "
    "deep ambient morning lighting, fine organic noise, real authentic unedited photography."
)

# Seductive shot definitions tailored specifically for Fanvue's public surface
ASSETS = [
    # --- Profile Pictures (1:1 Square, 2K) ---
    {
        "id": "fv_propic_sultry_silk",
        "type": "propic",
        "aspect": "1:1",
        "tier": "2k",
        "title": "Propic Option 1: Sultry Silk Camisole in Bed",
        "prompt": (
            "A magnetic, intimate close-up bust portrait of a stunning 26-year-old Korean woman in her Seongsu apartment. "
            "Sitting up in bed against soft white linen pillows in warm, diffused morning sunlight. "
            "She is wearing a delicate champagne silk satin camisole with thin spaghetti straps slipping slightly off one bare shoulder, "
            "revealing her elegant long neck and defined collarbone. Her signature long balayage waves are casually tousled with bedroom texture, "
            "falling softly around her shoulders with curtain bangs framing her cheekbones. "
            "Her gaze is deeply alluring, seductive, and intimate, looking directly into the camera lens with hooded amber-hazel eyes "
            "and soft, relaxed parted lips with a natural rose tint. "
            "Centered composition perfectly framed for a circular avatar crop. "
            f"{SKIN} {LENS_CLOSE}\n\n{ROLES_FACE}"
        ),
        "use_body": False,
    },
    {
        "id": "fv_propic_white_shirt",
        "type": "propic",
        "aspect": "1:1",
        "tier": "2k",
        "title": "Propic Option 2: Oversized Crisp Shirt Falling Off Shoulder",
        "prompt": (
            "A captivating, seductive front-angle portrait of a beautiful 26-year-old Korean woman sitting in morning light in her Seoul apartment. "
            "Wearing an oversized crisp white cotton button-up shirt with the top buttons unfastened, the collar slumping casually off one shoulder "
            "to expose her bare shoulder, neck, and delicate collarbone. Her glossy honey-balayage hair falls in soft messy waves past her shoulders. "
            "She tilts her head slightly, offering a sultry, knowing, magnetic direct gaze straight into the viewer's eyes with warm amber-hazel irises "
            "and an enigmatic, playful half-smile. "
            "Tight bust crop centered for an avatar thumbnail, soft warm morning illumination. "
            f"{SKIN} {LENS_CLOSE}\n\n{ROLES_FACE}"
        ),
        "use_body": False,
    },
    # --- Banner Headers (21:9 Ultra-Wide Panoramic, 2K) ---
    {
        "id": "fv_banner_morning_lounge",
        "type": "banner",
        "aspect": "21:9",
        "tier": "2k",
        "title": "Banner Option 1: Sunlit Bedroom Lounge on White Linen",
        "prompt": (
            "An ultra-wide panoramic 21:9 cinematic photograph of a gorgeous 26-year-old Korean woman in her minimalist Seongsu Seoul flat. "
            "She is lounging across a low king bed covered in rumpled white linen sheets next to a large floor-to-ceiling window. "
            "Soft sheer curtains diffuse golden morning sunlight across the room. "
            "She is resting comfortably on her elbows in a slinky black silk slip dress, looking back over her shoulder directly at the camera "
            "with a captivating, seductive, relaxed gaze. Her long wavy balayage hair cascades down her back. "
            "Wide horizontal composition with generous breathing room, establishing an intimate, chic, luxurious private sanctuary. "
            f"{SKIN} {LENS_WIDE}\n\n{ROLES_BODY}"
        ),
        "use_body": True,
    },
    {
        "id": "fv_banner_window_daybed",
        "type": "banner",
        "aspect": "21:9",
        "tier": "2k",
        "title": "Banner Option 2: Window Daybed Morning Golden Hour",
        "prompt": (
            "An ultra-wide 21:9 cinematic banner photograph of a 26-year-old Korean woman sitting comfortably on a sleek modern daybed "
            "by a floor-to-ceiling window overlooking Seoul morning light. "
            "Wearing a cozy off-shoulder oatmeal knit lounge sweater slipping down one arm and matching ribbed lounge shorts. "
            "Her athletic hourglass silhouette is gently lit by soft side sunlight. She leans back against a stack of pillows, "
            "turning her head toward the camera with an alluring, inviting, warm expression and striking amber-hazel eyes. "
            "Cinematic wide framing, uncluttered aesthetic, peaceful and seductive morning atmosphere. "
            f"{SKIN} {LENS_WIDE}\n\n{ROLES_BODY}"
        ),
        "use_body": True,
    },
]


def run():
    load_key(ROOT)
    key = os.environ.get("KIE_API_KEY")
    if not key:
        sys.exit("Error: KIE_API_KEY not found in kie_key.txt or environment.")

    kie = Kie(key)
    credit = kie.credit()
    print(f"=== Starting Fanvue Profile Asset Generation ===")
    print(f"Current Kie Credit Balance: {credit}")

    # Ensure output directories
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    # Upload & verify references
    print("\n[1/3] Uploading and verifying master reference images...")
    face_urls = []
    for ref_name in FACE_REFS:
        ref_path = MASTER_A / ref_name
        if not ref_path.exists():
            sys.exit(f"Error: Face reference missing: {ref_path}")
        print(f"  Uploading face reference: {ref_name}...")
        url = kie.upload(ref_path.resolve())
        face_urls.append(url)
        print(f"    -> {url}")

    body_url = None
    body_path = MASTER_C / BODY_REF
    if body_path.exists():
        print(f"  Uploading body reference: {BODY_REF}...")
        body_url = kie.upload(body_path.resolve())
        print(f"    -> {body_url}")

    print("\n[2/3] Generating assets on Kie (gpt-image-2-image-to-image 2K)...")
    results = []

    for i, shot in enumerate(ASSETS, 1):
        shot_id = shot["id"]
        aspect = shot["aspect"]
        tier = shot["tier"]
        prompt = shot["prompt"]
        use_body = shot["use_body"] and (body_url is not None)

        refs = face_urls + ([body_url] if use_body else [])
        print(f"\n--- [{i}/{len(ASSETS)}] Generating {shot_id} ({aspect}, {tier}) ---")
        print(f"Title: {shot['title']}")
        print(f"References: {len(refs)} images")

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

            print(f"  Downloading to {dest_local.name}...")
            bytes_saved = kie.download(img_url, dest_local)
            # Also copy to artifacts dir for immediate IDE preview
            shutil.copyfile(dest_local, dest_artifact)

            print(f"  Saved ({bytes_saved // 1024} KB).")
            results.append({
                "id": shot_id,
                "type": shot["type"],
                "aspect": aspect,
                "title": shot["title"],
                "file_local": str(dest_local),
                "file_artifact": str(dest_artifact),
                "url": img_url,
                "status": "success",
            })
        except Exception as e:
            print(f"  Generation failed for {shot_id}: {e}")
            results.append({
                "id": shot_id,
                "type": shot["type"],
                "aspect": aspect,
                "title": shot["title"],
                "error": str(e),
                "status": "failed",
            })

    print("\n[3/3] Summary of generations:")
    for r in results:
        status = r["status"]
        if status == "success":
            print(f"  [OK] {r['id']} ({r['aspect']}): {r['file_local']}")
        else:
            print(f"  [FAIL] {r['id']}: {r.get('error')}")

    # Output manifest JSON
    manifest_path = OUT_DIR / "manifest_profile.json"
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nManifest saved to {manifest_path}")

    credit_after = kie.credit()
    print(f"Remaining Kie Credit Balance: {credit_after}")


if __name__ == "__main__":
    run()
