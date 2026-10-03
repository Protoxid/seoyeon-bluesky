#!/usr/bin/env python3
"""
reroll_w38_pass2.py — Reroll the 6 Sentry-rejected W38 shot/assets (pass 2, final).

QC rejection payload: growth/qc_rejection_w38_nsfw.json
Reroll count: 1 → 2 (cap 2 per shot). If same defect persists, mark blocked.

Budget: 6 shots × $0.07 = $0.42. Verified via kie.credit() before generating.
"""
import json
import os
import pathlib
import sys
import time
from datetime import datetime, timezone

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

# The 6 rejected shots — each with Sentry's prompt fix from the QC rejection payload,
# plus the task's required placement sentence and side disambiguation.
SHOTS = [
    # ===== 1. WEDNESDAY — Poplin Shirt / 03_midnight_chair =====
    # Defect: TATTOO ON WRONG SIDE (was right ribcage; must be left, viewer's right when front-facing)
    {
        "out_path": ASSETS_DIR / "sets" / "w38_wed_poplin_shirt" / "03_midnight_chair.png",
        "drop_id": "w38_wed_poplin_shirt",
        "gallery_idx": 2,
        "exclude_body_ref": False,
        "prompt": (
            "A sultry candid midnight photograph in the dark oak lounge armchair with warm amber reading lamp. "
            "A 26-year-old Korean woman with a natural athletic Pilates physique reclining back in the chair completely nude, "
            "knees drawn up loosely to one side, the white poplin shirt completely slid off and discarded across the arm of the chair. "
            "Her bare breasts, toned midriff, bare stomach, and bare left ribcage are fully exposed in the warm amber reading lamp glow. "
            "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
            "In this front-facing angle her left ribcage appears on the viewer's right side of the frame; her right flank on the viewer's left must be completely unblemished and unmarked clean skin. "
            "Tousled honey-amber waves draped over the back of the chair. "
            "Relaxed parted lips with a soft alluring expression, looking directly into the camera. "
            "One hand rests on her knee with clean natural fingers. "
            "Unrecognisable neutral dark midnight ambience with warm intimate lamplight. "
            + FILM_SUFFIX
        ),
    },

    # ===== 2. THURSDAY — Silk Robe / TEASER =====
    # Defect: VISIBLE "AI generated" WATERMARK badge in lower-right corner
    # Clothed tier-2: NO nudity, NO word "tattoo", exclude_body_ref True (only a1_front)
    {
        "out_path": ASSETS_DIR / "w38_thu_silk_robe.png",
        "drop_id": "w38_thu_silk_robe",
        "gallery_idx": 0,
        "exclude_body_ref": True,
        "prompt": (
            "A natural candid mirror selfie in a dressing corner at dusk. "
            "A 26-year-old Korean woman with a natural athletic Pilates physique standing in front of a leaning floor mirror, "
            "wearing a blush pink silk wrap robe tied at the waist, holding a white iPhone 15 Pro in a plain clear case. "
            "Her honey-blonde gradient balayage hair falls in loose waves over her shoulders. "
            "Her eyes look directly into her own reflection in the mirror glass with a quiet, relaxed expression. "
            "Her arm holds the phone up and still, the phone's lens pointing at the mirror. "
            "Natural lighting, warm dusk interior glow. "
            "Clean unbranded frame — no watermarks, no text overlay, no badges, no platform logos, no AI-generated labels, no rectangular badges. "
            "Neutral minimalist background with soft interior twilight shadows. "
            + FILM_SUFFIX
        ),
    },

    # ===== 3. THURSDAY — Silk Robe / 03_vanity_mirror =====
    # Defect: REAR VIEW — tattoo on viewer's RIGHT (her anatomical right); must be viewer's LEFT (her left)
    {
        "out_path": ASSETS_DIR / "sets" / "w38_thu_silk_robe" / "03_vanity_mirror.png",
        "drop_id": "w38_thu_silk_robe",
        "gallery_idx": 2,
        "exclude_body_ref": False,
        "prompt": (
            "A sensual candid twilight photograph in the dressing area. "
            "A 26-year-old Korean woman with a natural athletic Pilates physique turned with her back facing the camera, "
            "looking over her bare shoulder into the leaning mirror reflection with soft alluring eyes and relaxed parted lips. "
            "She is completely nude, the discarded blush silk robe lying on the floor behind her. "
            "Her bare back, bare hips, bare shoulders, and bare left ribcage with the delicate fine-line botanical sprig tattoo "
            "are fully exposed to the dim dusk ambient light. "
            "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
            "In this rear-facing angle the left ribcage is on the viewer's left side of the frame; her right flank on the viewer's right must be completely unmarked clean skin with no tattoo. "
            "Her honey-blonde hair cascades smoothly over one shoulder. "
            "One arm crosses naturally across her stomach with five clean fingers. "
            "Neutral unrecognisable plaster walls with deep twilight indigo tones. "
            + FILM_SUFFIX
        ),
    },

    # ===== 4. FRIDAY — Navy Slip / 03_midnight_recline =====
    # Defect: BREASTS CONCEALED by crossed arm; must be fully exposed, arms open/raised
    {
        "out_path": ASSETS_DIR / "sets" / "w38_fri_navy_slip" / "03_midnight_recline.png",
        "drop_id": "w38_fri_navy_slip",
        "gallery_idx": 2,
        "exclude_body_ref": False,
        "prompt": (
            "A stunning, seductive low-light photograph on the dark velvet platform lounger late Friday night. "
            "A 26-year-old Korean woman with a natural athletic Pilates physique fully reclining back on the dark velvet lounger, "
            "body angled 3/4 to the lens, completely nude, the navy silk slip dress discarded beside her on the velvet. "
            "Both arms resting open along the cushion or raised overhead, fully exposing her bare breasts and bare torso "
            "in warm moody midnight rim lighting. "
            "Her bare breasts rest naturally uncovered; her toned athletic midriff, bare stomach, and bare left ribcage with "
            "the delicate fine-line botanical sprig tattoo are fully visible. "
            "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
            "In this three-quarter angle her left ribcage appears on the viewer's right side of the frame; her right flank must be unmarked clean skin. "
            "Her side-parted honey-blonde waves cascade across the dark cushion. "
            "Both hands rest open beside her head with five natural relaxed fingers. "
            "Intimate parted lips, warm honey-hazel gaze into the lens. "
            "Neutral soft-focus midnight sanctuary with rich warm ambient rim lighting. "
            + FILM_SUFFIX
        ),
    },

    # ===== 5. SATURDAY — Black Lace / 03_slate_intimate =====
    # Defect: STILL WEARING lace bra; must be fully topless/bare, bra discarded
    {
        "out_path": ASSETS_DIR / "sets" / "w38_sat_black_lace" / "03_slate_intimate.png",
        "drop_id": "w38_sat_black_lace",
        "gallery_idx": 2,
        "exclude_body_ref": False,
        "prompt": (
            "A breathtaking, intimate midnight photograph in the dark slate vanity sanctuary. "
            "A 26-year-old Korean woman with a natural athletic Pilates physique seated on a low dark charcoal slate ledge "
            "with knees pulled loosely to the side, completely nude and fully topless, "
            "the black lace bralette discarded on the stone ledge beside her. "
            "Her bare breasts are completely exposed and natural; her toned stomach, hips, and bare left ribcage with "
            "the delicate fine-line botanical sprig tattoo are in intimate warm amber spotlight. "
            "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
            "In this three-quarter angle her left ribcage appears on the viewer's right side of the frame; her right flank must be unmarked clean skin. "
            "Her wet-look textured honey-blonde waves frame her face and shoulders. "
            "Both hands rest naturally on the slate beside her with clean natural fingers. "
            "Bedroom eyes looking directly at the camera with a quiet, alluring, seductive expression and relaxed parted lips. "
            "Neutral unrecognisable dark midnight atmosphere with fine filmic sensor texture. "
            + FILM_SUFFIX
        ),
    },

    # ===== 6. SUNDAY — Waffle Henley / 02_henley_lift =====
    # Defect: GARMENT CONTINUITY BREAK (sleeveless tank instead of henley) AND breasts not exposed
    {
        "out_path": ASSETS_DIR / "sets" / "w38_sun_waffle_henley" / "02_henley_lift.png",
        "drop_id": "w38_sun_waffle_henley",
        "gallery_idx": 1,
        "exclude_body_ref": False,
        "prompt": (
            "An intimate candid morning photograph in a sunlit modern apartment bedroom in Seongsu with woven tatami floor. "
            "A 26-year-old Korean woman with a natural athletic Pilates physique standing in warm golden morning light near a sheer-curtained window. "
            "She has pulled the cream waffle-knit long-sleeve henley completely off over her head and discarded it onto the floor cushion beside her, "
            "standing fully bare from the waist up — her bare breasts, toned abdomen, bare stomach, and bare left ribcage exposed to the warm morning air. "
            "The cream waffle-knit long-sleeve henley is visible on the floor cushion, discarded. "
            "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
            "In this front-facing angle her left ribcage appears on the viewer's right side of the frame; her right flank on the viewer's left must be unmarked clean skin. "
            "Her honey-balayage hair is loose and slightly tangled from sleep, falling softly over her bare shoulders. "
            "She looks directly at the camera with a quiet, intimate, confident half-smile. "
            "Both hands naturally at her sides with clean natural fingers. "
            "Soft golden morning sunbeams cast gentle warm shadows across her bare skin. "
            + FILM_SUFFIX
        ),
    },
]


def main():
    load_key(PERSONA_DIR)
    key = os.environ.get("KIE_API_KEY", "")
    if not key:
        sys.exit("Error: KIE_API_KEY not found.")

    expected_cost = len(SHOTS) * 0.07
    print(f"[*] Reroll Pass 2: {len(SHOTS)} shots × $0.07 = ${expected_cost:.2f}")

    kie = Kie(key)
    credits = kie.credit()
    print(f"[*] Credits available: {credits}")

    if credits is None or credits < expected_cost:
        sys.exit(f"Error: Insufficient credits ({credits} available, ${expected_cost:.2f} needed). Refusing to run.")

    print(f"[*] Budget guard: PASSED (${credits:.2f} >= ${expected_cost:.2f})")
    print(f"[*] Uploading master references...")

    a1_url = kie.upload(MASTER_A1.resolve())
    c5_url = kie.upload(MASTER_C5.resolve())
    tattoo_url = kie.upload(MASTER_TATTOO.resolve())

    refs_bare = [a1_url, c5_url, tattoo_url]
    refs_clothed = [a1_url]

    print(f"[+] Face master: {a1_url[:50]}...")
    print(f"[+] Body master: {c5_url[:50]}...")
    print(f"[+] Tattoo crop: {tattoo_url[:50]}...")

    from PIL import Image

    before_stats = []
    for i, shot in enumerate(SHOTS):
        out_path = shot["out_path"]
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # Record before size
        if out_path.exists():
            old_size = out_path.stat().st_size
            bef = "(existing)"
        else:
            old_size = 0
            bef = "(new)"

        use_refs = refs_bare if not shot["exclude_body_ref"] else refs_clothed

        print(f"\n{'='*70}")
        print(f"  [{i+1}/{len(SHOTS)}] {out_path.name}  →  {out_path}")
        print(f"  Drop: {shot['drop_id']}  |  Bare refs: {not shot['exclude_body_ref']}  |  {bef}")
        print(f"{'='*70}")

        t0 = time.time()
        try:
            urls = kie.generate(
                prompt=shot["prompt"],
                aspect="3:4",
                tier="1k",
                image_urls=use_refs,
                model="seedream/5-pro-image-to-image",
            )
            if not urls:
                print(f"  [ERROR] No URL returned — marking blocked.")
                before_stats.append({"shot": out_path.name, "drop": shot["drop_id"], "status": "blocked", "note": "No URL from generation"})
                continue

            # Download
            n_bytes = kie.download(urls[0], out_path)
            elapsed = time.time() - t0
            print(f"  [DOWNLOADED] {n_bytes // 1024} KB in {elapsed:.1f}s")

            # Upscale to 1080×1440 (3:4) — Seedream "1k" returns 864×1152
            im = Image.open(out_path)
            if im.size != (1080, 1440):
                print(f"  Original size: {im.size}, upscaling to 1080×1440...")
                im = im.resize((1080, 1440), Image.LANCZOS)
                im.save(out_path, "PNG")
                new_bytes = out_path.stat().st_size
                print(f"  [UPSCALED] {new_bytes // 1024} KB, final size: {im.size}")
            else:
                print(f"  Size OK: {im.size}")

            after_size = out_path.stat().st_size
            before_stats.append({
                "shot": out_path.name,
                "drop": shot["drop_id"],
                "status": "success",
                "old_bytes": old_size,
                "new_bytes": after_size,
                "dimensions": "1080×1440",
            })

        except Exception as e:
            print(f"  [FAIL] {e} — marking blocked.")
            before_stats.append({"shot": out_path.name, "drop": shot["drop_id"], "status": "blocked", "note": str(e)[:200]})

    # Report
    print(f"\n{'='*70}")
    print(f"  REROLL PASS 2 COMPLETE")
    print(f"{'='*70}")
    successes = sum(1 for s in before_stats if s["status"] == "success")
    blocked = sum(1 for s in before_stats if s["status"] == "blocked")
    print(f"  Generated: {successes}/{len(SHOTS)}")
    print(f"  Blocked:   {blocked}/{len(SHOTS)}")
    print(f"  Cost:      ${successes * 0.07:.2f}")
    for s in before_stats:
        print(f"  {'✓' if s['status']=='success' else '✗'} {s['shot']}: {s['status']} {s.get('note','')}")

    # Write stats to a temp file for the caller to read
    stats_path = GROWTH_DIR / ".reroll_pass2_stats.json"
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump({"timestamp": datetime.now(timezone.utc).isoformat(),
                    "shots": before_stats,
                    "total_cost": successes * 0.07,
                    "total_shots": len(SHOTS),
                    "successes": successes,
                    "blocked": blocked}, f, indent=2)
    print(f"\n[+] Stats written to {stats_path}")

    # Log spend to ledger
    if successes > 0:
        ledger_path = GROWTH_DIR / "ledger.jsonl"
        entry = {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f+00:00"),
            "surface": "kie",
            "action": "seedream_generation",
            "target": "reroll_w38_pass2",
            "note": f"Reroll pass 2: {successes} shots @ $0.07 = ${successes * 0.07:.2f} (rerolled 6 rejected W38 shots)"
        }
        with open(ledger_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(f"[+] Spend logged to ledger.jsonl")


if __name__ == "__main__":
    main()