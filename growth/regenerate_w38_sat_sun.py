#!/usr/bin/env python3
"""
regenerate_w38_sat_sun.py — Regenerate 4 remaining explicit NSFW tier-3 shots for Sat + Sun.
Reuses the canon-tested prompt structure from the successful Tue/Wed/Thu/Fri runs.
Budget: 4 × $0.07 = $0.28. Credits available: $758.
"""
import json, os, pathlib, sys, time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

try: from PIL import Image
except ImportError: Image = None

GROWTH_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = GROWTH_DIR.parent
PERSONA_DIR = PROJECT_ROOT / "personas" / "seoyeon"
ASSETS_DIR = GROWTH_DIR / "schedule_assets"

sys.path.insert(0, str(PERSONA_DIR))
from kie_api import Kie, load_key

MASTER_A1 = PERSONA_DIR / "master" / "a" / "a1_front.png"
MASTER_C5 = PERSONA_DIR / "master" / "c" / "c5_relax_front.png"
MASTER_TATTOO = PERSONA_DIR / "master" / "c" / "tattoo_crop.png"

FILM_SUFFIX = (
    "Shot on iPhone 15 Pro: flat natural contrast, low saturation, fine filmic shadow noise, "
    "natural matte skin texture with visible real pores and faint pale freckles across the nose bridge and inner cheeks, "
    "light amber-hazel irises with dark limbal ring and pronounced aegyo-sal, honey-blonde gradient balayage hair, "
    "clean hands with exactly five natural relaxed fingers, zero CGI plastic, authentic candid snapshot."
)

def ensure_min_1080(image_path, min_w=1080):
    if Image is None or not image_path.exists(): return
    try:
        with Image.open(image_path) as im:
            w, h = im.size
            if w < min_w or h < min_w or (w/h != 0.75 and abs(w/h - 0.75) > 0.01):
                target_w = min_w
                target_h = int(round(min_w * h / w))
                # force 3:4 if close
                if abs(target_w/target_h - 0.75) > 0.02:
                    target_w, target_h = 1080, 1440
                print(f"    Resizing from {w}x{h} to {target_w}x{target_h}")
                resized = im.resize((target_w, target_h), Image.LANCZOS)
                resized.save(image_path)
    except Exception as e:
        print(f"    [!] {e}")

SHOTS = [
    # SAT 02 — black lace bralette removed, fully bare from waist up
    {
        "out_path": ASSETS_DIR / "sets" / "w38_sat_black_lace" / "02_lace_unclasp.png",
        "desc": "Black lace bralette removed, bare torso, slate wall midnight",
        "exclude_body_ref": False,
        "prompt": (
            "An alluring, intimate midnight photograph against matte dark charcoal slate wall. "
            "A 26-year-old Korean woman with a natural athletic Pilates physique turning 3/4 toward the lens. "
            "The delicate sheer black French floral lace bralette has been completely removed and she holds it loosely in one hand at her side, "
            "leaving her entirely bare from the waist up — bare breasts with relaxed natural curve, toned athletic stomach, and bare left ribcage. "
            "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
            "Her honey-balayage hair has a tousled, wet-look textured wave pushed naturally back from her forehead. "
            "Direct intimate gaze into the lens with relaxed parted lips and a soft conspiratorial half-smile. "
            "Five clean natural fingers of one hand hold the discarded lace; the other hand rests naturally on her hip. "
            "Warm low amber spotlight casting soft dramatic shadows on neutral slate backdrop. "
            + FILM_SUFFIX
        ),
    },
    # SAT 03 — fully nude on slate ledge
    {
        "out_path": ASSETS_DIR / "sets" / "w38_sat_black_lace" / "03_slate_intimate.png",
        "desc": "Fully nude seated on slate ledge, black lace discarded",
        "exclude_body_ref": False,
        "prompt": (
            "A breathtaking, intimate midnight photograph in the dark slate vanity sanctuary. "
            "A 26-year-old Korean woman with a natural athletic Pilates physique seated on a low dark slate ledge with knees pulled loosely to the side, "
            "completely nude, the black French floral lace set discarded on the slate beside her. "
            "Her bare breasts, smooth toned stomach, hips, and bare left ribcage with the delicate fine-line botanical sprig tattoo "
            "are bathed in intimate warm low amber spotlight. "
            "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
            "Her wet-look textured waves frame her glowing cheekbones and bare shoulders. "
            "Both hands rest naturally on the slate ledge beside her with clean natural fingers. "
            "Bedroom eyes looking directly at the camera with a quiet, alluring, seductive expression and relaxed parted lips. "
            "Neutral unrecognisable dark midnight atmosphere with fine filmic sensor texture. "
            + FILM_SUFFIX
        ),
    },
    # SUN 02 — henley pulled off over head, bare torso standing
    {
        "out_path": ASSETS_DIR / "sets" / "w38_sun_waffle_henley" / "02_henley_lift.png",
        "desc": "Cream henley pulled off over head, bare torso morning light",
        "exclude_body_ref": False,
        "prompt": (
            "An intimate candid morning photograph in a sunlit modern apartment bedroom in Seongsu with woven natural tatami-style floor mat. "
            "A 26-year-old Korean woman with a natural athletic Pilates physique standing in warm golden morning light near a sheer-curtained window. "
            "She has pulled the loose cream waffle-knit henley completely off over her head and holds it bunched in both hands, "
            "standing completely bare from the waist up — bare breasts with relaxed natural curve, smooth toned abdomen, bare stomach, and bare left ribcage exposed to the warm morning air. "
            "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
            "Her honey-balayage hair is delightfully messy from pulling the henley off, loose and slightly tangled from sleep, falling softly over her bare shoulders. "
            "She looks directly at the camera with a quiet, intimate, confident half-smile. "
            "Both hands hold the gathered henley fabric with clean natural fingers. "
            "Soft golden morning sunbeams cast gentle warm shadows across her bare skin. "
            + FILM_SUFFIX
        ),
    },
    # SUN 03 — fully nude floor stretch on tatami
    {
        "out_path": ASSETS_DIR / "sets" / "w38_sun_waffle_henley" / "03_tatami_stretch.png",
        "desc": "Fully nude stretched on tatami floor, morning light",
        "exclude_body_ref": False,
        "prompt": (
            "A sensual, relaxing candid morning photograph in a quiet sunlit lounge nook with natural woven tatami-style mat and soft floor cushions. "
            "A 26-year-old Korean woman with a natural athletic Pilates physique reclining completely nude across the soft floor cushions on the woven sisal rug, "
            "legs stretched comfortably, the cream waffle-knit henley and soft grey lounge shorts discarded on the tatami nearby. "
            "Her bare breasts rest naturally in the relaxed recline; her smooth toned stomach, hips, and bare left ribcage with the delicate fine-line botanical sprig tattoo "
            "are fully visible in the soft warm overcast morning daylight. "
            "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
            "Her honey-blonde hair is loose and slightly tangled, falling softly around her bare shoulders and the cushion beneath her head. "
            "One hand rests under her head on the cushion with five clean fingers; the other rests casually on her hip. "
            "Soft intimate bedroom eyes looking into the camera lens with a sleepy, tranquil half-smile. "
            "Neutral, unrecognisable soft overcast daylight filling the serene space with natural warmth. "
            "Nearby on a low wooden table: a half-empty ceramic mug of barley tea and a folded open book. "
            + FILM_SUFFIX
        ),
    },
]

def main():
    load_key(PERSONA_DIR)
    key = os.environ.get("KIE_API_KEY", "")
    if not key: sys.exit("Error: KIE_API_KEY not found.")

    print(f"[*] 4 shots × $0.07 = $0.28 (credit available: ~$758)")
    kie = Kie(key, timeout=180.0, poll=3.0)

    a1_url = kie.upload(MASTER_A1.resolve())
    c5_url = kie.upload(MASTER_C5.resolve())
    tattoo_url = kie.upload(MASTER_TATTOO.resolve())
    refs = [a1_url, c5_url, tattoo_url]

    for i, shot in enumerate(SHOTS):
        out_path = shot["out_path"]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"\n[{i+1}/4] {out_path.parent.name}/{out_path.name}")
        print(f"  → {shot['desc']}")
        t0 = time.time()
        try:
            urls = kie.generate(prompt=shot["prompt"], aspect="3:4", tier="1k",
                                image_urls=refs, model="seedream/5-pro-image-to-image")
            if urls and urls[0]:
                n = kie.download(urls[0], out_path)
                ensure_min_1080(out_path)
                with Image.open(out_path) as im:
                    d = f"{im.size[0]}x{im.size[1]}"
                print(f"  ✓ {d}, {out_path.stat().st_size//1024} KB, {time.time()-t0:.1f}s")
            else:
                print(f"  ✗ No URL")
        except Exception as e:
            print(f"  ✗ FAIL: {e}")

if __name__ == "__main__":
    main()