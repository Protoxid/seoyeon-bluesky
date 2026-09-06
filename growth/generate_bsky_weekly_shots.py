#!/usr/bin/env python3
"""
generate_bsky_weekly_shots.py — Generates soft-NSFW images via Kie (seedream/5-pro-image-to-image).
Strict Canon Rules:
- ZERO body prompting in text: anatomy is 100% inherited from master references.
- Authentic candid snapshot, real matte skin, white iPhone 15 Pro with clear case.
"""
import json
import os
import pathlib
import sys
import time

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

GROWTH_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = GROWTH_DIR.parent
PERSONAS_DIR = PROJECT_ROOT / "personas" / "seoyeon"

sys.path.insert(0, str(PERSONAS_DIR))
from kie_api import Kie, load_key

load_key(PERSONAS_DIR)
key = os.environ.get("KIE_API_KEY", "")
if not key:
    sys.exit("Error: KIE_API_KEY not found in kie_key.txt or .env")

kie = Kie(key)

MASTER_A1 = PERSONAS_DIR / "master" / "a" / "a1_front.png"
MASTER_A2 = PERSONAS_DIR / "master" / "a" / "a2_tq_left.png"
MASTER_C5 = PERSONAS_DIR / "master" / "c" / "c5_relax_front.png"

ASSETS_DIR = GROWTH_DIR / "schedule_assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

NEW_SHOTS = [
    {
        "id": "tue_cozy_knit",
        "story": "Cozy rainy evening in Seongsu, oversized slouchy knit sweater slipping off shoulder.",
        "prompt": (
            "An authentic candid front-camera snapshot of the woman in her Seongsu apartment living room on a rainy evening. "
            "Wearing a slouchy oversized oatmeal-beige ribbed knit sweater draped loosely off one shoulder over a neutral silk bralette. "
            "Bare legs visible as she sits comfortably on the living room rug holding a warm ceramic mug with both hands. "
            "Soft warm ambient lamp light in the background, gentle rain on the dark window pane behind her. "
            "Authentic matte skin texture with visible natural pores, candid snapshot, zero CGI, iPhone 15 Pro front camera."
        ),
        "aspect": "3:4",
        "tier": "2k"
    },
    {
        "id": "thu_silk_slip",
        "story": "Golden hour glow in living room, champagne silk slip dress.",
        "prompt": (
            "An authentic candid golden hour snapshot of the 26-year-old Korean woman in her Seongsu apartment. "
            "She is wearing a delicate solid plain champagne-toned silk slip dress with clean, single, thin spaghetti straps resting neatly on each shoulder with zero duplicate straps or loose cords. "
            "The dress is tailored from pure smooth solid champagne satin silk with a completely plain, clean, unprinted surface with zero designs, zero graphics, and zero markings on the solid silk fabric. "
            "Sitting comfortably on the warm wooden floor by the balcony window as late afternoon sunlight streams through sheer curtains. "
            "Hair loosely pinned up with a tortoiseshell claw clip with soft loose tendrils framing her neck. "
            "Holding her white iPhone 15 Pro in a plain clear case in one hand, other hand resting naturally on her knee with five clean relaxed fingers. "
            "Authentic matte skin texture, visible natural pores, candid unretouched photo, zero CGI."
        ),
        "aspect": "3:4",
        "tier": "1k",
        "exclude_body_ref": True
    },
    {
        "id": "sun_sunday_bed",
        "story": "Lazy Sunday morning bed stretch, grey cotton crop tank top and sleep shorts.",
        "prompt": (
            "An authentic candid morning bed snapshot in a bright Seongsu bedroom. "
            "The woman is sitting up in bed on rumpled white linen sheets, wearing a soft grey ribbed cotton crop tank top and white cotton sleep shorts. "
            "Messy bed hair falling naturally around her shoulders with a soft sleepy smile toward the camera. "
            "Morning sunlight casting warm light across the white duvet and pillows. Her hands rest naturally on the sheets. "
            "Authentic matte skin, subtle natural pores, casual candid morning photograph, zero CGI, iPhone 15 Pro camera."
        ),
        "aspect": "3:4",
        "tier": "1k"
    }
]

def generate_shots(model="seedream/5-pro-image-to-image", only_id=None):
    print(f"[*] Checking Kie balance...", flush=True)
    credit = kie.credit()
    print(f"[*] Available Kie credits: {credit}", flush=True)

    print(f"[*] Uploading reference masters...", flush=True)
    a1_url = kie.upload(MASTER_A1.resolve())
    c5_url = kie.upload(MASTER_C5.resolve()) if MASTER_C5.exists() else None

    refs = [a1_url]
    if c5_url:
        refs.append(c5_url)
    print(f"[+] References uploaded: {len(refs)}", flush=True)

    for shot in NEW_SHOTS:
        shot_id = shot["id"]
        if only_id and shot_id != only_id:
            continue
        out_file = ASSETS_DIR / f"{shot_id}.png"
        print(f"\n[+] Generating {shot_id} via {model}...", flush=True)
        active_refs = [a1_url] if shot.get("exclude_body_ref", False) else refs
        if shot.get("exclude_body_ref", False):
            print(f"  [*] Clothed torso: Using face master only ({len(active_refs)} ref) to prevent tattoo bleed on dress.", flush=True)
        try:
            urls = kie.generate(
                prompt=shot["prompt"],
                aspect=shot["aspect"],
                image_urls=active_refs,
                model=model,
                tier=shot["tier"]
            )
            if not urls:
                print(f"[!] No URL returned for {shot_id}", flush=True)
                continue
            
            n_bytes = kie.download(urls[0], out_file)
            print(f"[✔] Downloaded {out_file.name} ({n_bytes // 1024} KB)", flush=True)

            meta_file = ASSETS_DIR / f"{shot_id}.json"
            meta_file.write_text(json.dumps({
                "id": shot_id,
                "story": shot["story"],
                "prompt": shot["prompt"],
                "aspect": shot["aspect"],
                "tier": shot["tier"],
                "model": model,
                "remote_url": urls[0],
                "created_at": time.time()
            }, indent=2), encoding="utf-8")
        except Exception as e:
            print(f"[!] Generation failed for {shot_id}: {e}", flush=True)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", type=str, default=None, help="Generate only specified shot ID")
    args = parser.parse_args()
    generate_shots(only_id=args.only)
