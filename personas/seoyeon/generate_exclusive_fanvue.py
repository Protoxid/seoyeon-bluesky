#!/usr/bin/env python3
"""
generate_exclusive_fanvue.py — Generates soft-NSFW exclusive shots for Fanvue subscribers.
Uses Kie.ai with nsfw_checker=False and reference conditioning against Seo-yeon's canonical masters.
"""
import os
import sys
import json
import pathlib
import hashlib
import time

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

ROOT = pathlib.Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT))

from kie_api import Kie, load_key

# Ensure API key is loaded
load_key(ROOT)
key = os.environ.get("KIE_API_KEY", "")
if not key:
    print("[!] Error: KIE_API_KEY not found in kie_key.txt or .env")
    sys.exit(1)

kie = Kie(key)

MASTER_A1 = ROOT / "master" / "a" / "a1_front.png"
MASTER_A2 = ROOT / "master" / "a" / "a2_tq_left.png"
MASTER_C5 = ROOT / "master" / "c" / "c5_relax_front.png"
OUT_DIR = ROOT / "content" / "fanvue"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Define 3 high-allure soft-NSFW exclusive shots tailored for Seo-yeon
SOFT_NSFW_SHOTS = [
    {
        "id": "fv_ex_lace_mirror",
        "story": "Intimate morning mirror check in Seongsu flat wearing delicate black lace lingerie set.",
        "prompt": (
            "An authentic candid mirror selfie of a 26-year-old Korean woman in her Seongsu apartment bedroom. "
            "She has a healthy natural athletic Pilates physique, realistic human proportions, a normal relaxed waist without extreme hourglass pinch, "
            "and a smooth natural abdomen. Her delicate botanical sprig tattoo is visible on her left side ribs. "
            "She is wearing a delicate black sheer lace bralette and matching lace briefs. "
            "Her relaxed neck and shoulders are soft and natural with no strained cords or tension. "
            "Her honey-balayage hair falls in loose slept-in waves over one shoulder. "
            "The phone in the picture is her own: a white iPhone 15 Pro with a plain clear case, slightly scuffed at one corner, "
            "held comfortably in one hand at waist height with five clean natural relaxed fingers. "
            "Her other arm rests loosely at her hip with natural fingers. "
            "Behind her, soft morning sunlight falls across unmade white linen bedding. "
            "Shot on iPhone 15 Pro through the glass: flat natural contrast, low saturation, subtle fine noise in shadows, "
            "real matte skin texture with visible natural pores, zero CGI, authentic candid snapshot."
        ),
        "aspect": "3:4",
        "tier": "2k",
        "caption": "quiet mornings in seongsu before the day starts... something a little more private for you 🖤☕"
    },
    {
        "id": "fv_ex_unbuttoned_linen",
        "story": "Morning bed selfie in unbuttoned oversized white shirt revealing lace undergarments.",
        "prompt": (
            "An alluring candid morning selfie from bed in Seongsu, Seoul. A 26-year-old athletic Korean woman sitting comfortably on white linen sheets, "
            "wearing an oversized crisp white cotton shirt completely unbuttoned and draped loosely off one shoulder, "
            "revealing a delicate black lace bra underneath, natural soft collarbones, and bare legs. "
            "She holds her phone with one arm extended for an authentic front-camera selfie (23mm lens), "
            "while her other hand rests naturally beside her on the bed. "
            "Soft warm morning backlighting makes the white cotton glow; messy hair falls over one cheek with a relaxed sleepy half-smile into the lens. "
            "Shot on iPhone 15 Pro front camera: natural human anatomy, subtle lens noise, real skin texture with small freckles across the bridge of her nose."
        ),
        "aspect": "3:4",
        "tier": "2k",
        "caption": "woke up slow today. linen sheets and morning sun... felt like sharing this side of me with you ✨"
    },
    {
        "id": "fv_ex_towel_steam",
        "story": "Post-shower bathroom intimacy with fogged mirror and loosely wrapped towel.",
        "prompt": (
            "A sensual candid post-shower mirror selfie in a warm bathroom in Seongsu, Seoul. A 26-year-old Korean woman "
            "wrapped securely in a plush white bath towel tucked snugly at her chest, bare shoulders and natural relaxed collarbones, "
            "damp dark hair tucked neatly behind her ears with loose strands framing her natural face. "
            "The phone in the picture is her own: a white iPhone 15 Pro with a plain clear case, slightly scuffed at one corner, "
            "held in one hand at chest height with five clean natural fingers. "
            "Her other hand holds the towel securely at her chest with five clean natural fingers. "
            "Warm vanity lighting, clean white ceramic tiles, light condensation on the outer edges of the mirror while her reflection remains clear. "
            "Shot on iPhone 15 Pro: natural skin texture, subtle water droplets, real pores, unretouched human aesthetic, zero extra digits."
        ),
        "aspect": "3:4",
        "tier": "2k",
        "caption": "fresh out of the shower... steam still on the glass. wanted you to see this first 🤍🚿"
    }
]

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--shot", type=str, default="all", help="Shot ID or 'all'")
    parser.add_argument("--model", type=str, default="seedream/5-pro-image-to-image", help="Model to use")
    parser.add_argument("--dry-run", action="store_true", help="Print prompts without generating")
    args = parser.parse_args()

    print(f"[*] Checking Kie balance...")
    credit = kie.credit()
    print(f"[*] Available Kie credits: {credit}")

    targets = SOFT_NSFW_SHOTS if args.shot == "all" else [s for s in SOFT_NSFW_SHOTS if s["id"] == args.shot]
    if not targets:
        print(f"[!] No shot matching '{args.shot}'")
        return 1

    if args.dry_run:
        print(f"\n[DRY RUN] {len(targets)} soft-NSFW shots queued:")
        for t in targets:
            print(f"--- {t['id']} ({t['aspect']}, {t['tier']}) ---")
            print(f"Prompt: {t['prompt']}")
            print(f"Caption: {t['caption']}\n")
        return 0

    # Upload reference masters
    print(f"[*] Uploading reference masters to Kie...")
    a1_url = kie.upload(MASTER_A1.resolve())
    a2_url = kie.upload(MASTER_A2.resolve()) if MASTER_A2.exists() else None
    c5_url = kie.upload(MASTER_C5.resolve()) if MASTER_C5.exists() else None

    refs = [a1_url]
    if a2_url:
        refs.append(a2_url)
    if c5_url:
        refs.append(c5_url)
    print(f"[+] {len(refs)} reference images uploaded.")

    generated_results = []

    for t in targets:
        shot_id = t["id"]
        print(f"\n[+] Generating soft-NSFW shot: {shot_id} using {args.model}...")
        try:
            urls = kie.generate(
                prompt=t["prompt"],
                aspect=t["aspect"],
                image_urls=refs,
                model=args.model,
                tier=t["tier"]
            )
            if not urls:
                print(f"[!] No URL returned for {shot_id}")
                continue

            out_path = OUT_DIR / f"{shot_id}.png"
            n_bytes = kie.download(urls[0], out_path)
            print(f"[✔] Downloaded {out_path.name} ({n_bytes // 1024} KB)")

            # Save metadata alongside image
            meta_path = OUT_DIR / f"{shot_id}.json"
            meta = {
                "id": shot_id,
                "story": t["story"],
                "prompt": t["prompt"],
                "caption": t["caption"],
                "aspect": t["aspect"],
                "tier": t["tier"],
                "model": args.model,
                "image_file": str(out_path.name),
                "remote_url": urls[0],
                "created_at": time.time()
            }
            meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
            generated_results.append((shot_id, out_path, t["caption"]))

        except Exception as e:
            print(f"[!] Generation failed for {shot_id}: {e}")

    print(f"\n==========================================")
    print(f"Successfully generated {len(generated_results)}/{len(targets)} soft-NSFW shots:")
    for sid, p, cap in generated_results:
        print(f"  - {sid} -> {p.name}")
        print(f"    Caption: \"{cap}\"")
    print(f"==========================================\n")

if __name__ == "__main__":
    main()
