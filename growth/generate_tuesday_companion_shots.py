#!/usr/bin/env python3
"""
generate_tuesday_companion_shots.py — Generates the 2 companion reveal shots
for Tuesday's 'Cozy Knit to Lingerie' full set on Fanvue.
Obeying all anti-defect rules: zero body prompting, relaxed neck, white iPhone 15 Pro,
and conditioned on canonical masters (c5_relax_front, a1_front).
"""
import json
import os
import pathlib
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

GROWTH_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = GROWTH_DIR.parent
PERSONA_DIR = PROJECT_ROOT / "personas" / "seoyeon"

sys.path.insert(0, str(PERSONA_DIR))
from kie_api import Kie, load_key

load_key(PERSONA_DIR)
key = os.environ.get("KIE_API_KEY", "")
if not key:
    sys.exit("Error: KIE_API_KEY not found.")

kie = Kie(key)

MASTER_A1 = PERSONA_DIR / "master" / "a" / "a1_front.png"
MASTER_C5 = PERSONA_DIR / "master" / "c" / "c5_relax_front.png"
OUT_DIR = GROWTH_DIR / "schedule_assets" / "sets" / "tue_cozy_knit"
OUT_DIR.mkdir(parents=True, exist_ok=True)

COMPANION_SHOTS = [
    {
        "filename": "02_knit_slide.png",
        "story": "Knit sweater sliding off shoulders revealing black lace bralette underneath.",
        "prompt": (
            "An authentic candid evening photograph in a minimalist warm Seongsu apartment. "
            "A 26-year-old Korean woman sitting on a low modern linen couch on a rainy evening. "
            "The room has warmed up and she has slid her oversized chunky oatmeal knit sweater down off both shoulders, "
            "draping loosely around her upper arms, revealing a delicate black floral lace bralette underneath, "
            "bare shoulders, and soft natural clavicles with zero strained cords or physical tension. "
            "Her honey-balayage hair falls in loose slept-in waves over one shoulder. "
            "One hand rests naturally on the couch cushion with exactly five clean relaxed fingers; "
            "her other hand rests loosely on her lap holding her white iPhone 15 Pro with a plain clear transparent case. "
            "The background is softly out of focus: warm indirect amber light from a floor lamp, neutral plaster walls, "
            "and soft rain streaks on the dark window in the distance. "
            "Shot on iPhone 15 Pro: flat natural contrast, low saturation, fine filmic shadow noise, "
            "natural matte skin texture with visible real pores and faint freckles over the nose bridge, zero CGI plastic, authentic candid snapshot."
        ),
        "aspect": "3:4",
        "tier": "2k"
    },
    {
        "filename": "03_lace_lounge.png",
        "story": "Slipped completely out of the knit into black lace lingerie lounge on the rug.",
        "prompt": (
            "An alluring candid low-light photograph in a cozy modern Seongsu flat late at night. "
            "A 26-year-old Korean woman seated comfortably on a neutral wool floor rug with legs curled loosely to one side. "
            "She has completely slipped out of her sweater; the oatmeal knit is draped casually on the couch behind her. "
            "She is wearing a delicate black French lace bralette and matching lace boy-shorts. "
            "A delicate minimalist botanical sprig tattoo is visible on her left ribcage. "
            "Relaxed neck and soft natural shoulders with zero tension. "
            "One hand rests on the floor beside her supporting her relaxed posture with five clean natural fingers; "
            "her other arm rests casually across her knee. Her phone—a white iPhone 15 Pro with clear case—rests face-up on the low table beside a glass of water. "
            "The background shows the cozy living room in warm amber lamplight, cream linen, and quiet midnight atmosphere. "
            "Shot on iPhone 15 Pro: natural low-light sensor grain, organic tones, authentic matte skin with visible natural pores, zero 3D gloss, candid unedited photograph."
        ),
        "aspect": "3:4",
        "tier": "2k"
    }
]

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate Tuesday companion reveal shots")
    parser.add_argument("--force", action="store_true", help="Force regenerate even if output files already exist")
    parser.add_argument("--shot", type=str, choices=["02", "03", "all"], default="all", help="Generate only shot '02', '03', or 'all'")
    args = parser.parse_args()

    print(f"[*] Available Kie credits: {kie.credit()}")
    print(f"[*] Uploading/caching reference masters...")
    a1_url = kie.upload(MASTER_A1.resolve())
    c5_url = kie.upload(MASTER_C5.resolve()) if MASTER_C5.exists() else None
    
    refs = [a1_url]
    if c5_url:
        refs.append(c5_url)
    print(f"[+] Using {len(refs)} master reference images.")

    targets = COMPANION_SHOTS
    if args.shot != "all":
        targets = [s for s in COMPANION_SHOTS if args.shot in s["filename"]]

    for shot in targets:
        out_file = OUT_DIR / shot["filename"]
        if out_file.exists() and out_file.stat().st_size > 100_000 and not args.force:
            print(f"[*] {out_file.name} already exists ({out_file.stat().st_size // 1024} KB). Skipping. (Use --force to overwrite)")
            continue

        print(f"\n[+] Generating {shot['filename']} via Seedream 5 Pro (2K)...")
        print(f"    Prompt excerpt: \"{shot['prompt'][:90]}...\"")
        
        t0 = time.time()
        urls = kie.generate(
            prompt=shot["prompt"],
            aspect=shot["aspect"],
            image_urls=refs,
            model="seedream/5-pro-image-to-image",
            tier=shot["tier"]
        )
        if not urls:
            print(f"[!] Generation failed: no URL returned for {shot['filename']}")
            continue

        n_bytes = kie.download(urls[0], out_file)
        elapsed = round(time.time() - t0, 1)
        print(f"[✔] Downloaded {out_file.name} ({n_bytes // 1024} KB) in {elapsed}s")

        # Save metadata
        meta_file = OUT_DIR / f"{out_file.stem}.json"
        meta_file.write_text(json.dumps({
            "filename": shot["filename"],
            "story": shot["story"],
            "prompt": shot["prompt"],
            "remote_url": urls[0],
            "timestamp": time.time()
        }, indent=2), encoding="utf-8")

    print("\n[✔] Tuesday companion shots generation process finished!")
    print(f"[*] Remaining Kie credits: {kie.credit()}")

if __name__ == "__main__":
    main()
