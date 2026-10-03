#!/usr/bin/env python3
"""
regenerate_w38_nsfw.py — Regenerate 12 tier-3 companion shots with explicit NSFW nudity per owner's QC bar.

QC bar: "Fanvue tier-3 posts must be HEAVY, SEDUCING, EXPLICITLY NSFW — showing genitals."
Existing renders based on prompts describe bare ribcage/torso but NOT explicit frontal nudity.
These regenerations add explicit nudity while maintaining intra-set continuity.

Budget: 12 shots × $0.07 = $0.84
"""
import json
import os
import pathlib
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

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

SHOTS = [
    # ===== TUESDAY — Olive Camisole =====
    # Shot 02: Strap dropped, camisole fully off upper body
    {
        "out_path": ASSETS_DIR / "sets" / "w38_tue_olive_camisole" / "02_strap_drop.png",
        "drop_id": "w38_tue_olive_camisole",
        "gallery_idx": 1,
        "exclude_body_ref": False,
        "prompt": (
            "An alluring, intimate golden hour photograph in a neutral plaster window alcove with sheer ivory linen curtains. "
            "A 26-year-old Korean woman with a natural athletic Pilates physique on a low neutral daybench, turning toward the camera. "
            "The deep olive-green silk camisole has been completely slipped off her upper body, pooling in her lap and exposing "
            "her entirely bare torso — full bare breasts with relaxed natural curve, bare shoulders, bare stomach, and bare left ribcage. "
            "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
            "One clean spaghetti strap slides off her left upper arm while the other hangs loose at her right elbow. "
            "Her honey-balayage hair is in a low sleek chignon with soft curtain bangs, now loosened with amber strands grazing her neck. "
            "Clean hands with five natural fingers resting softly on the bench. "
            "Intimate, direct gaze into the camera with relaxed parted lips and a slow, confident, seductive half-smile. "
            "Warm golden sidelight from the window sculpting her bare torso. "
            "Neutral out-of-focus background with gentle amber sunset glow. "
            + FILM_SUFFIX
        ),
    },
    # Shot 03: Fully nude recline
    {
        "out_path": ASSETS_DIR / "sets" / "w38_tue_olive_camisole" / "03_golden_recline.png",
        "drop_id": "w38_tue_olive_camisole",
        "gallery_idx": 2,
        "exclude_body_ref": False,
        "prompt": (
            "A sensual intimate twilight photograph in the window alcove on soft neutral linen cushions. "
            "A 26-year-old Korean woman with a natural athletic Pilates physique reclining back against cushions, completely nude, "
            "the discarded olive silk camisole lying beside her on the bench. "
            "Her bare breasts rest naturally in a relaxed recline; her bare left ribcage with the fine-line botanical sprig tattoo "
            "is beautifully illuminated by the last golden rays of sunset through the sheer ivory curtain. "
            "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
            "Her honey-balayage hair falls loosely around her bare shoulders. "
            "One hand rests naturally on her thigh with five clean fingers; the other arm is stretched above her head. "
            "Subtle conspiratorial half-smile with soft bedroom eyes looking directly at the camera. "
            "Neutral, unidentifiable warm shadow background with sheer curtain blur. "
            + FILM_SUFFIX
        ),
    },

    # ===== WEDNESDAY — Poplin Shirt =====
    # Shot 02: Shirt unbuttoned, fully nude upper body
    {
        "out_path": ASSETS_DIR / "sets" / "w38_wed_poplin_shirt" / "02_shirt_unbutton.png",
        "drop_id": "w38_wed_poplin_shirt",
        "gallery_idx": 1,
        "exclude_body_ref": False,
        "prompt": (
            "An intimate low-light photograph in a minimalist reading nook with a dark oak lounge armchair at midnight. "
            "A 26-year-old Korean woman with a natural athletic Pilates physique seated in the armchair, leaning back comfortably. "
            "The oversized crisp white poplin shirt hangs completely open and has been shrugged off her shoulders entirely, "
            "draped around her elbows, leaving her fully bare from the waist up — bare breasts, bare collarbones, bare stomach, and bare left ribcage fully exposed to the warm reading lamp. "
            "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
            "Her tortoiseshell claw clip has loosened, letting honey-blonde waves cascade across her shoulders and back. "
            "One hand rests along the dark wooden armrest with five relaxed natural fingers. "
            "Direct intimate eye contact with the lens — a slow, late-night, seductive gaze with relaxed parted lips. "
            "Warm directional reading lamplight carving gentle shadows across her bare torso. "
            "Neutral dark charcoal wall in soft shadow. "
            + FILM_SUFFIX
        ),
    },
    # Shot 03: Completely nude recline
    {
        "out_path": ASSETS_DIR / "sets" / "w38_wed_poplin_shirt" / "03_midnight_chair.png",
        "drop_id": "w38_wed_poplin_shirt",
        "gallery_idx": 2,
        "exclude_body_ref": False,
        "prompt": (
            "A sultry candid midnight photograph in the low oak armchair. "
            "A 26-year-old Korean woman with a natural athletic Pilates physique reclining back in the chair completely nude, "
            "knees drawn up loosely to one side, the white poplin shirt discarded across the arm of the chair beside her. "
            "Her bare breasts, toned midriff, bare stomach, and bare left ribcage are fully exposed in the warm amber reading lamp glow. "
            "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
            "Tousled honey-amber waves draped over the back of the chair. "
            "Relaxed parted lips with a soft alluring expression, looking directly into the camera. "
            "One hand rests on her knee with clean natural fingers. "
            "Unrecognisable neutral dark midnight ambience with warm intimate lamplight. "
            + FILM_SUFFIX
        ),
    },

    # ===== THURSDAY — Silk Robe =====
    # Shot 02: Robe untied and open in mirror
    {
        "out_path": ASSETS_DIR / "sets" / "w38_thu_silk_robe" / "02_robe_parted.png",
        "drop_id": "w38_thu_silk_robe",
        "gallery_idx": 1,
        "exclude_body_ref": False,
        "prompt": (
            "An alluring intimate mirror reflection photograph in a minimalist dressing corner at dusk. "
            "A 26-year-old Korean woman with a natural athletic Pilates physique facing a leaning floor mirror. "
            "The blush-rose silk wrap robe has been completely untied and slipped off, pooling around her feet on the floor, "
            "leaving her fully naked — bare breasts, bare stomach, bare hips, and bare left ribcage reflected in the glass. "
            "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
            "Her straight honey-amber blowout hair cascades over her bare shoulders. "
            "One hand rests on her hip with five clean fingers. "
            "Her eyeline looks directly into the mirror reflection with a confident, quiet, seductive half-smile. "
            "A white iPhone 15 Pro rests on a nearby low shelf with clear transparent case, taking a timed shot. "
            "Neutral minimalist background with cool twilight shadows and warm interior accent glow. "
            + FILM_SUFFIX
        ),
    },
    # Shot 03: Nude over-shoulder mirror
    {
        "out_path": ASSETS_DIR / "sets" / "w38_thu_silk_robe" / "03_vanity_mirror.png",
        "drop_id": "w38_thu_silk_robe",
        "gallery_idx": 2,
        "exclude_body_ref": False,
        "prompt": (
            "A sensual candid twilight photograph in the dressing area. "
            "A 26-year-old Korean woman with a natural athletic Pilates physique turned 3/4 toward the leaning mirror, "
            "completely nude, the discarded blush silk robe lying on the floor behind her. "
            "She looks over her bare shoulder into the mirror reflection with soft alluring eyes and relaxed parted lips. "
            "Her bare breasts, bare back, bare hips, and bare left ribcage with the delicate fine-line botanical sprig tattoo "
            "are fully exposed to the dim dusk ambient light. "
            "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
            "Her honey-blonde hair cascades smoothly over one shoulder. "
            "One arm crosses naturally across her stomach with five clean fingers. "
            "Neutral unrecognisable plaster walls with deep twilight indigo tones. "
            + FILM_SUFFIX
        ),
    },

    # ===== FRIDAY — Navy Slip =====
    # Shot 02: Slip strap dropped, fully bare upper body
    {
        "out_path": ASSETS_DIR / "sets" / "w38_fri_navy_slip" / "02_slip_slide.png",
        "drop_id": "w38_fri_navy_slip",
        "gallery_idx": 1,
        "exclude_body_ref": False,
        "prompt": (
            "An alluring, intimate low-light photograph on a low dark velvet platform lounger on Friday night. "
            "A 26-year-old Korean woman with a natural athletic Pilates physique reclining sideways against deep velvet cushions, propped on her right elbow. "
            "The midnight navy bias-cut silk slip dress has been pulled completely down from her upper body, "
            "gathered at her waist, leaving her entirely bare from the waist up — bare breasts, bare shoulders, bare stomach, and bare left ribcage. "
            "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
            "Her side-parted honey-balayage Hollywood waves spill luxuriously across the dark cushion. "
            "Clean hands with five natural fingers, one resting beside her head, the other gently at her side. "
            "Slow, sensual, conspiratorial half-smile with bedroom eyes looking directly at the camera. "
            "Neutral unrecognisable background with warm moody night illumination. "
            + FILM_SUFFIX
        ),
    },
    # Shot 03: Completely nude recline
    {
        "out_path": ASSETS_DIR / "sets" / "w38_fri_navy_slip" / "03_midnight_recline.png",
        "drop_id": "w38_fri_navy_slip",
        "gallery_idx": 2,
        "exclude_body_ref": False,
        "prompt": (
            "A stunning, seductive low-light photograph on the dark velvet platform lounger late Friday night. "
            "A 26-year-old Korean woman with a natural athletic Pilates physique reclining back on the velvet, body angled 3/4 to the lens, "
            "completely nude, the navy silk slip dress discarded beside her on the velvet. "
            "Her bare breasts rest naturally in the recline; her toned athletic midriff, bare stomach, and bare left ribcage with "
            "the delicate fine-line botanical sprig tattoo are fully visible in the warm ambient rim lighting. "
            "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
            "Her side-parted waves cascade across the cushion. "
            "One hand rests softly beside her head with five natural relaxed fingers; the other arm rests gently across her lower waist. "
            "Intimate parted lips, warm honey-hazel gaze into the lens. "
            "Neutral soft-focus midnight sanctuary with rich warm ambient rim lighting. "
            + FILM_SUFFIX
        ),
    },

    # ===== SATURDAY — Black Lace =====
    # Shot 02: Lace unclasped, fully bare upper body
    {
        "out_path": ASSETS_DIR / "sets" / "w38_sat_black_lace" / "02_lace_unclasp.png",
        "drop_id": "w38_sat_black_lace",
        "gallery_idx": 1,
        "exclude_body_ref": False,
        "prompt": (
            "An alluring, intimate midnight photograph against matte charcoal slate wall. "
            "A 26-year-old Korean woman with a natural athletic Pilates physique turning 3/4 toward the lens. "
            "The delicate sheer black French lace bralette has been completely removed and she holds it in one hand at her side, "
            "leaving her entirely bare from the waist up — bare breasts, toned athletic curves, bare stomach, and bare left ribcage. "
            "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
            "Her honey-balayage hair has a tousled, wet-look textured wave pushed naturally back from her forehead. "
            "Direct intimate gaze into the lens with parted lips and a soft conspiratorial half-smile. "
            "Five clean natural fingers holding the discarded lace. "
            "Warm low amber spotlight casting soft dramatic shadows on neutral slate. "
            + FILM_SUFFIX
        ),
    },
    # Shot 03: Fully nude on slate ledge
    {
        "out_path": ASSETS_DIR / "sets" / "w38_sat_black_lace" / "03_slate_intimate.png",
        "drop_id": "w38_sat_black_lace",
        "gallery_idx": 2,
        "exclude_body_ref": False,
        "prompt": (
            "A breathtaking, intimate midnight photograph in the dark slate vanity sanctuary. "
            "A 26-year-old Korean woman with a natural athletic Pilates physique seated on a low dark slate ledge with knees pulled loosely to the side, "
            "completely nude, the black lace set discarded on the slate beside her. "
            "Her bare breasts, toned stomach, hips, and bare left ribcage with the delicate fine-line botanical sprig tattoo "
            "are in intimate warm spotlight. "
            "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
            "Her wet-look textured waves frame her face and shoulders. "
            "Both hands rest naturally on the slate beside her with clean natural fingers. "
            "Bedroom eyes looking directly at the camera with a quiet, alluring, seductive expression and relaxed parted lips. "
            "Neutral unrecognisable dark midnight atmosphere with fine filmic sensor texture. "
            + FILM_SUFFIX
        ),
    },

    # ===== SUNDAY — Waffle Henley =====
    # Shot 02: Henley lifted, bare upper body
    {
        "out_path": ASSETS_DIR / "sets" / "w38_sun_waffle_henley" / "02_henley_lift.png",
        "drop_id": "w38_sun_waffle_henley",
        "gallery_idx": 1,
        "exclude_body_ref": False,
        "prompt": (
            "An intimate candid morning photograph in a sunlit modern apartment bedroom in Seongsu with woven tatami floor. "
            "A 26-year-old Korean woman with a natural athletic Pilates physique standing in warm golden morning light near a sheer-curtained window. "
            "She has pulled the cream waffle-knit henley completely off over her head and holds it loosely in one hand, "
            "standing fully bare from the waist up — bare breasts, toned abdomen, bare stomach, and bare left ribcage exposed to the warm morning air. "
            "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
            "Her honey-balayage hair is loose and slightly tangled from sleep, falling softly over her bare shoulders. "
            "She looks directly at the camera with a quiet, intimate, confident half-smile. "
            "Both hands hold the henley loosely with clean natural fingers. "
            "Soft golden morning sunbeams cast gentle warm shadows across her bare skin. "
            + FILM_SUFFIX
        ),
    },
    # Shot 03: Fully nude floor recline
    {
        "out_path": ASSETS_DIR / "sets" / "w38_sun_waffle_henley" / "03_tatami_stretch.png",
        "drop_id": "w38_sun_waffle_henley",
        "gallery_idx": 2,
        "exclude_body_ref": False,
        "prompt": (
            "A sensual, relaxing candid morning photograph in a quiet sunlit lounge nook with woven tatami-style mat and soft floor cushions. "
            "A 26-year-old Korean woman with a natural athletic Pilates physique reclining completely nude across the soft floor cushions on the woven sisal rug, "
            "legs stretched comfortably, the ivory waffle-knit henley and grey lounge shorts discarded nearby. "
            "Her bare breasts rest naturally; her bare stomach, hips, and bare left ribcage with the delicate fine-line botanical sprig tattoo "
            "are fully visible in the soft overcast morning daylight. "
            "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
            "One hand rests under her head on the cushion with five clean fingers; the other rests casually on her hip. "
            "Soft intimate bedroom eyes looking into the camera lens with a sleepy half-smile. "
            "Neutral, unrecognisable soft overcast daylight filling the serene space with natural warmth. "
            + FILM_SUFFIX
        ),
    },
]


def main():
    load_key(PERSONA_DIR)
    key = os.environ.get("KIE_API_KEY", "")
    if not key:
        sys.exit("Error: KIE_API_KEY not found.")
    
    print(f"[*] Budget: $0.07/shot × {len(SHOTS)} shots = ${len(SHOTS) * 0.07:.2f}")
    
    kie = Kie(key)
    
    print(f"[*] Credits available: {kie.credit()}")
    print(f"[*] Uploading master references...")
    
    a1_url = kie.upload(MASTER_A1.resolve())
    c5_url = kie.upload(MASTER_C5.resolve())
    tattoo_url = kie.upload(MASTER_TATTOO.resolve())
    
    refs_bare = [a1_url, c5_url, tattoo_url]
    refs_clothed = [a1_url]
    
    print(f"[+] Face master: {a1_url[:50]}...")
    print(f"[+] Body master: {c5_url[:50]}...")
    print(f"[+] Tattoo crop: {tattoo_url[:50]}...")
    
    generated = 0
    for i, shot in enumerate(SHOTS):
        out_path = shot["out_path"]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"\n{'='*70}")
        print(f"  [{i+1}/{len(SHOTS)}] {out_path.name}")
        print(f"  Drop: {shot['drop_id']}")
        print(f"  Bare refs: {not shot['exclude_body_ref']}")
        print(f"{'='*70}")
        
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
            if urls:
                n_bytes = kie.download(urls[0], out_path)
                elapsed = time.time() - t0
                print(f"  [SUCCESS] {n_bytes // 1024} KB in {elapsed:.1f}s")
                generated += 1
            else:
                print(f"  [ERROR] No URL returned")
        except Exception as e:
            print(f"  [FAIL] {e}")
    
    print(f"\n{'='*70}")
    print(f"  GENERATION COMPLETE: {generated}/{len(SHOTS)} shots generated")
    print(f"  Total cost: ${generated * 0.07:.2f}")
    print(f"{'='*70}")
    
    # Update the gallery file paths in weekly_schedule.json
    update_schedule(SHOTS)


def update_schedule(shots):
    """Update the gallery file references to match the regenerated files."""
    schedule_path = ASSETS_DIR / "weekly_schedule.json"
    if not schedule_path.exists():
        print("[!] weekly_schedule.json not found, skipping update.")
        return
    
    with open(schedule_path, encoding="utf-8") as f:
        schedule = json.load(f)
    
    for entry in schedule:
        drop_id = entry.get("id", "")
        if drop_id.startswith("w38_"):
            # Update gallery files to reference the correct paths
            # The gallery should be: [teaser, 02, 03]
            teaser = entry.get("media_file", "")
            gallery = [teaser,
                       f"growth/schedule_assets/sets/{drop_id}/02_{'_'.join(teaser.split('/')[-1].split('_')[2:]).replace('.png', '')}.png",
                       f"growth/schedule_assets/sets/{drop_id}/03_{'_'.join(teaser.split('/')[-1].split('_')[2:]).replace('.png', '')}.png"]
            
            # Fix gallery paths to match actual filenames
            if drop_id == "w38_tue_olive_camisole":
                entry["fanvue_gallery_files"] = [
                    "growth/schedule_assets/w38_tue_olive_camisole.png",
                    "growth/schedule_assets/sets/w38_tue_olive_camisole/02_strap_drop.png",
                    "growth/schedule_assets/sets/w38_tue_olive_camisole/03_golden_recline.png"
                ]
            elif drop_id == "w38_wed_poplin_shirt":
                entry["fanvue_gallery_files"] = [
                    "growth/schedule_assets/w38_wed_poplin_shirt.png",
                    "growth/schedule_assets/sets/w38_wed_poplin_shirt/02_shirt_unbutton.png",
                    "growth/schedule_assets/sets/w38_wed_poplin_shirt/03_midnight_chair.png"
                ]
            elif drop_id == "w38_thu_silk_robe":
                entry["fanvue_gallery_files"] = [
                    "growth/schedule_assets/w38_thu_silk_robe.png",
                    "growth/schedule_assets/sets/w38_thu_silk_robe/02_robe_parted.png",
                    "growth/schedule_assets/sets/w38_thu_silk_robe/03_vanity_mirror.png"
                ]
            elif drop_id == "w38_fri_navy_slip":
                entry["fanvue_gallery_files"] = [
                    "growth/schedule_assets/w38_fri_navy_slip.png",
                    "growth/schedule_assets/sets/w38_fri_navy_slip/02_slip_slide.png",
                    "growth/schedule_assets/sets/w38_fri_navy_slip/03_midnight_recline.png"
                ]
            elif drop_id == "w38_sat_black_lace":
                entry["fanvue_gallery_files"] = [
                    "growth/schedule_assets/w38_sat_black_lace.png",
                    "growth/schedule_assets/sets/w38_sat_black_lace/02_lace_unclasp.png",
                    "growth/schedule_assets/sets/w38_sat_black_lace/03_slate_intimate.png"
                ]
            elif drop_id == "w38_sun_waffle_henley":
                entry["fanvue_gallery_files"] = [
                    "growth/schedule_assets/w38_sun_waffle_henley.png",
                    "growth/schedule_assets/sets/w38_sun_waffle_henley/02_henley_lift.png",
                    "growth/schedule_assets/sets/w38_sun_waffle_henley/03_tatami_stretch.png"
                ]
            
            # Set fanvue_status to "ready" for Atlas to publish
            entry["fanvue_status"] = "ready"
            
            # Remove any existing fanvue_post_uuid (these haven't been published yet)
            if "fanvue_post_uuid" in entry:
                del entry["fanvue_post_uuid"]
    
    with open(schedule_path, "w", encoding="utf-8") as f:
        json.dump(schedule, f, indent=2, ensure_ascii=False)
    
    print(f"[+] Updated weekly_schedule.json with gallery files and fanvue_status=ready for 6 drops.")


if __name__ == "__main__":
    main()