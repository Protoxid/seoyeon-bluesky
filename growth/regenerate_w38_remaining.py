#!/usr/bin/env python3
"""
regenerate_w38_remaining.py — Fix 864px shots + generate remaining 8 explicit NSFW tier-3 shots.

Phase 1: Upscale 4 already-regenerated shots from 864×1152 to 1080×1440
Phase 2: Generate remaining 8 shots (Thu-Sun) with explicit nudity
"""
import json
import os
import pathlib
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

try:
    from PIL import Image
except ImportError:
    Image = None

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
    """Upscale to at least min_w width preserving aspect ratio."""
    if Image is None or not image_path.exists():
        return
    try:
        with Image.open(image_path) as im:
            w, h = im.size
            if w < min_w:
                target_w = min_w
                target_h = int(round(min_w * h / w))
                print(f"    Upscaling from {w}x{h} to {target_w}x{target_h}")
                resized = im.resize((target_w, target_h), Image.LANCZOS)
                resized.save(image_path)
    except Exception as e:
        print(f"    [!] Warning during upscale: {e}")


# Phase 1: Fix the 4 already-regenerated shots
PHASE1 = [
    ASSETS_DIR / "sets" / "w38_tue_olive_camisole" / "02_strap_drop.png",
    ASSETS_DIR / "sets" / "w38_tue_olive_camisole" / "03_golden_recline.png",
    ASSETS_DIR / "sets" / "w38_wed_poplin_shirt" / "02_shirt_unbutton.png",
    ASSETS_DIR / "sets" / "w38_wed_poplin_shirt" / "03_midnight_chair.png",
]

print("=" * 60)
print("  PHASE 1: Upscaling 4 regenerated shots to 1080px")
print("=" * 60)
for p in PHASE1:
    if p.exists():
        with Image.open(p) as im:
            w, h = im.size
        if w < 1080:
            ensure_min_1080(p)
            with Image.open(p) as im:
                print(f"  [FIXED] {p.name}: now {im.size[0]}x{im.size[1]}")
        else:
            print(f"  [OK] {p.name}: {w}x{h}")
    else:
        print(f"  [MISSING] {p.name}")


# Phase 2: Generate remaining 8 shots (Thu-Sun) with explicit NSFW prompts
# Note: Thursday's teaser uses mirror selfie — must maintain continuity

SHOTS = [
    # ===== THURSDAY — Silk Robe =====
    # Shot 02: Robe untied, fully open, naked in mirror
    {
        "out_path": ASSETS_DIR / "sets" / "w38_thu_silk_robe" / "02_robe_parted.png",
        "description": "Blush silk robe untied, fully naked in mirror",
        "exclude_body_ref": False,
        "prompt": (
            "An alluring intimate mirror reflection photograph in a minimalist dressing corner at dusk. "
            "A 26-year-old Korean woman with a natural athletic Pilates physique facing a full-length leaning floor mirror. "
            "The blush-rose washed-silk wrap robe has been completely untied and slipped off, pooling around her bare feet on the floor, "
            "leaving her completely naked — bare breasts, bare hips, bare toned stomach, and bare left ribcage fully visible in the mirror. "
            "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
            "Her straight honey-amber blowout hair is tucked neatly behind both ears, showing small gold huggie earrings. "
            "Her eyeline looks directly into the mirror reflection with a confident, quiet, seductive half-smile. "
            "Fresh post-shower glow on her face with subtle natural freckles across the nose bridge. "
            "Five clean natural fingers resting lightly at her hip. "
            "A white iPhone 15 Pro with plain clear case rests face-up on a nearby low shelf. "
            "Neutral minimalist background with cool twilight shadows and warm interior accent glow. "
            + FILM_SUFFIX
        ),
    },
    # Shot 03: Nude over-shoulder mirror gaze
    {
        "out_path": ASSETS_DIR / "sets" / "w38_thu_silk_robe" / "03_vanity_mirror.png",
        "description": "Nude over-shoulder mirror, silk robe on floor",
        "exclude_body_ref": False,
        "prompt": (
            "A sensual candid twilight photograph in the dressing area. "
            "A 26-year-old Korean woman with a natural athletic Pilates physique turned 3/4 away from the camera toward the leaning mirror, "
            "completely naked, the discarded blush-rose silk robe lying pooled on the floor at her feet. "
            "She looks over her bare shoulder into the mirror reflection with soft alluring bedroom eyes and relaxed parted lips. "
            "Her bare back, bare hips, bare breasts in profile, and bare left ribcage with the fine-line botanical sprig tattoo "
            "are fully exposed in the dim dusk ambient light. "
            "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
            "Her honey-blonde hair cascades smoothly over one shoulder. "
            "One arm crosses naturally across her stomach with five clean relaxed fingers. "
            "Neutral unrecognisable plaster walls with deep twilight indigo tones. "
            + FILM_SUFFIX
        ),
    },

    # ===== FRIDAY — Navy Slip =====
    # Shot 02: Slip pulled down, bare breasts
    {
        "out_path": ASSETS_DIR / "sets" / "w38_fri_navy_slip" / "02_slip_slide.png",
        "description": "Navy slip pulled down to waist, bare torso",
        "exclude_body_ref": False,
        "prompt": (
            "An alluring, intimate low-light photograph on a low dark velvet platform lounger on Friday night. "
            "A 26-year-old Korean woman with a natural athletic Pilates physique reclining sideways against deep velvet cushions, propped on her right elbow. "
            "The midnight navy bias-cut silk slip dress has been pulled completely down from her upper body, "
            "gathered loosely at her waist, leaving her entirely bare from the waist up — bare breasts, bare shoulders, bare stomach, and bare left ribcage. "
            "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
            "Her side-parted honey-balayage Hollywood waves cascade luxuriously across the dark cushion. "
            "Clean hands with five natural fingers, one resting beside her head on the cushion, the other gently at her side. "
            "Slow, sensual, conspiratorial half-smile with bedroom eyes looking directly at the camera. "
            "Neutral unrecognisable dark interior background with warm moody indirect floor lighting. "
            + FILM_SUFFIX
        ),
    },
    # Shot 03: Fully nude recline
    {
        "out_path": ASSETS_DIR / "sets" / "w38_fri_navy_slip" / "03_midnight_recline.png",
        "description": "Fully nude on velvet lounger with slip discarded",
        "exclude_body_ref": False,
        "prompt": (
            "A stunning, seductive low-light photograph on the dark velvet platform lounger late Friday night. "
            "A 26-year-old Korean woman with a natural athletic Pilates physique reclining back on the velvet, body angled 3/4 to the lens, "
            "completely nude, the midnight navy silk slip dress discarded beside her on the dark velvet. "
            "Her bare breasts rest naturally; her toned athletic midriff, bare stomach, and bare left ribcage with "
            "the delicate fine-line botanical sprig tattoo are fully visible in the warm ambient rim lighting. "
            "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
            "Her side-parted waves cascade across the cushion. "
            "One hand rests softly beside her head with five natural relaxed fingers; the other arm rests gently across her lower waist. "
            "Intimate parted lips, warm honey-hazel gaze looking directly into the lens. "
            "Neutral soft-focus midnight sanctuary with rich warm ambient rim lighting. "
            + FILM_SUFFIX
        ),
    },

    # ===== SATURDAY — Black Lace =====
    # Shot 02: Lace bralette removed, bare from waist up
    {
        "out_path": ASSETS_DIR / "sets" / "w38_sat_black_lace" / "02_lace_unclasp.png",
        "description": "Black lace bralette removed, bare torso against slate",
        "exclude_body_ref": False,
        "prompt": (
            "An alluring, intimate midnight photograph against matte dark charcoal slate wall. "
            "A 26-year-old Korean woman with a natural athletic Pilates physique turning 3/4 toward the lens. "
            "The delicate sheer black French lace bralette has been completely removed and she holds it loosely in one hand at her side, "
            "leaving her entirely bare from the waist up — bare breasts, toned athletic curves, bare stomach, and bare left ribcage. "
            "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
            "Her honey-balayage hair has a tousled, wet-look textured wave pushed naturally back from her forehead. "
            "Direct intimate gaze into the lens with relaxed parted lips and a soft conspiratorial half-smile. "
            "Five clean natural fingers of one hand hold the discarded lace; the other hand rests on her hip. "
            "Warm low amber spotlight casting soft dramatic shadows on neutral slate backdrop. "
            + FILM_SUFFIX
        ),
    },
    # Shot 03: Fully nude on slate ledge
    {
        "out_path": ASSETS_DIR / "sets" / "w38_sat_black_lace" / "03_slate_intimate.png",
        "description": "Fully nude seated on slate ledge",
        "exclude_body_ref": False,
        "prompt": (
            "A breathtaking, intimate midnight photograph in the dark slate vanity sanctuary. "
            "A 26-year-old Korean woman with a natural athletic Pilates physique seated on a low dark slate ledge with knees pulled loosely to the side, "
            "completely nude, the black French lace set discarded on the slate beside her. "
            "Her bare breasts, toned stomach, smooth hips, and bare left ribcage with the delicate fine-line botanical sprig tattoo "
            "are bathed in intimate warm low spotlight. "
            "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
            "Her wet-look textured waves frame her glowing cheekbones and bare shoulders. "
            "Both hands rest naturally on the slate ledge beside her with clean natural fingers. "
            "Bedroom eyes looking directly at the camera with a quiet, alluring, seductive expression and relaxed parted lips. "
            "Neutral unrecognisable dark midnight atmosphere with fine filmic sensor texture. "
            + FILM_SUFFIX
        ),
    },

    # ===== SUNDAY — Waffle Henley =====
    # Shot 02: Henley lifted completely over head, bare torso
    {
        "out_path": ASSETS_DIR / "sets" / "w38_sun_waffle_henley" / "02_henley_lift.png",
        "description": "Cream henley lifted off over head, bare torso standing in morning light",
        "exclude_body_ref": False,
        "prompt": (
            "An intimate candid morning photograph in a sunlit modern apartment bedroom in Seongsu with woven natural tatami-style mat. "
            "A 26-year-old Korean woman with a natural athletic Pilates physique standing in warm golden morning light near a sheer-curtained window. "
            "She has pulled the loose cream waffle-knit henley completely off over her head and holds it bunched in both hands, "
            "standing completely bare from the waist up — bare breasts, smooth toned abdomen, bare stomach, and bare left ribcage exposed to the warm morning air. "
            "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
            "Her honey-balayage hair is delightfully messy from pulling the henley off, loose and slightly tangled from sleep, falling softly over her bare shoulders. "
            "She looks directly at the camera with a quiet, intimate, confident half-smile. "
            "Both hands hold the gathered henley fabric with clean natural fingers. "
            "Soft golden morning sunbeams cast gentle warm shadows across her bare skin. "
            + FILM_SUFFIX
        ),
    },
    # Shot 03: Fully nude floor stretch on tatami
    {
        "out_path": ASSETS_DIR / "sets" / "w38_sun_waffle_henley" / "03_tatami_stretch.png",
        "description": "Fully nude stretched on tatami floor, morning light",
        "exclude_body_ref": False,
        "prompt": (
            "A sensual, relaxing candid morning photograph in a quiet sunlit lounge nook with natural woven tatami-style mat and soft floor cushions. "
            "A 26-year-old Korean woman with a natural athletic Pilates physique reclining completely nude across the soft floor cushions on the woven sisal rug, "
            "legs stretched comfortably, the cream waffle-knit henley and soft grey lounge shorts discarded on the tatami nearby. "
            "Her bare breasts rest naturally in the relaxed recline; her bare stomach, smooth hips, and bare left ribcage with the delicate fine-line botanical sprig tattoo "
            "are fully visible in the soft warm overcast morning daylight. "
            "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
            "Her honey-blonde hair is loose and slightly tangled, falling softly around her bare shoulders and the cushion. "
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
    if not key:
        sys.exit("Error: KIE_API_KEY not found.")

    print(f"\n{'=' * 60}")
    print(f"  PHASE 2: {len(SHOTS)} explicit NSFW companion shots")
    print(f"  Budget: {len(SHOTS)} × $0.07 = ${len(SHOTS) * 0.07:.2f}")
    print(f"{'=' * 60}")

    kie = Kie(key, timeout=180.0, poll=3.0)
    print(f"[*] Credits: {kie.credit()}")

    print(f"[*] Uploading master references...")
    # Use cached URLs via Kie's internal _uploads dict
    a1_url = kie.upload(MASTER_A1.resolve())
    c5_url = kie.upload(MASTER_C5.resolve())
    tattoo_url = kie.upload(MASTER_TATTOO.resolve())
    refs_bare = [a1_url, c5_url, tattoo_url]
    refs_clothed = [a1_url]

    generated = 0
    for i, shot in enumerate(SHOTS):
        out_path = shot["out_path"]
        out_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"\n  [{i + 1}/{len(SHOTS)}] {out_path.parent.name}/{out_path.name}")
        print(f"  → {shot['description']}")

        use_refs = refs_bare if not shot["exclude_body_ref"] else refs_clothed

        t0 = time.time()
        try:
            urls = kie.generate(
                prompt=shot["prompt"],
                aspect="3:4",
                tier="1k",
                image_urls=use_refs,
                model="seedream/5-pro-image-to-image",
            )
            if urls and urls[0]:
                n_bytes = kie.download(urls[0], out_path)
                ensure_min_1080(out_path)
                elapsed = time.time() - t0
                final_size = out_path.stat().st_size
                with Image.open(out_path) as im:
                    dims = f"{im.size[0]}x{im.size[1]}"
                print(f"  ✓ {dims}, {final_size // 1024} KB, {elapsed:.1f}s")
                generated += 1
            else:
                print(f"  ✗ No URL returned")
        except Exception as e:
            print(f"  ✗ FAIL: {e}")

    print(f"\n{'=' * 60}")
    print(f"  DONE: {generated}/{len(SHOTS)} shots generated")
    print(f"  Running cost: ${generated * 0.07:.2f}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()