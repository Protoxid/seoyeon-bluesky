#!/usr/bin/env python3
"""
generate_w38_final.py — Generate remaining Sat+Sun w38 images.

Generates 4 images:
  1. w38_sat_black_lace/03_slate_intimate.png  (black lace on bed)
  2. w38_sun_waffle_henley.png                 (teaser, clothed)
  3. w38_sun_waffle_henley/02_henley_lift.png  (henley lifted, tattoo)
  4. w38_sun_waffle_henley/03_tatami_stretch.png (floor stretch, clothed)
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
SCHEDULE_FILE = ASSETS_DIR / "weekly_schedule.json"

sys.path.insert(0, str(PERSONA_DIR))
from kie_api import Kie, load_key

MASTER_A1 = PERSONA_DIR / "master" / "a" / "a1_front.png"
MASTER_C5 = PERSONA_DIR / "master" / "c" / "c5_relax_front.png"
MASTER_TATTOO = PERSONA_DIR / "master" / "c" / "tattoo_crop.png"

# ==============================================================================
# SHOT CONFIGURATION
# ==============================================================================

SHOTS = [
    # --- SAT: 03_slate_intimate ---
    {
        "out_path": ASSETS_DIR / "sets" / "w38_sat_black_lace" / "03_slate_intimate.png",
        "drop_id": "w38_sat_black_lace",
        "gallery_rel": "growth/schedule_assets/sets/w38_sat_black_lace/03_slate_intimate.png",
        "description": "Black lace on bed, intimate angle",
        "exclude_body_ref": False,  # bare ribcage, show tattoo
        "prompt": (
            "An intimate candid low-light photograph in a dimly lit modern bedroom in Seoul at midnight. "
            "A 26-year-old Korean woman with a natural athletic Pilates physique lying on her side across a bed "
            "with dark charcoal washed linen sheets. "
            "Her honey-balayage hair is loose in textured, disheveled bedhead waves. "
            "She is wearing a delicate black French floral lace bralette and matching lace boy-shorts; "
            "the bralette has one thin spaghetti strap naturally slipped off her shoulder, "
            "revealing her bare shoulder, relaxed collarbones, and the curve of her breast. "
            "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line "
            "botanical sprig tattoo shown in the reference. "
            "She is propped up on one elbow, looking directly at the camera with a sleepy, intimate, "
            "soft-eyed gaze and lips gently parted. "
            "Her free hand rests naturally on the duvet beside her with clean relaxed fingers. "
            "The background is softly out of focus: a warm amber pool of light from one low ceramic bedside lamp, "
            "creating a quiet, confidential midnight atmosphere. "
            "Shot on iPhone 15 Pro: organic night tones, natural matte skin texture with visible pores, "
            "zero CGI plastic, candid snapshot."
        ),
    },
    # --- SUN: Teaser (clothed) ---
    {
        "out_path": ASSETS_DIR / "w38_sun_waffle_henley.png",
        "drop_id": "w38_sun_waffle_henley",
        "gallery_rel": "growth/schedule_assets/w38_sun_waffle_henley.png",
        "description": "Teaser: cream waffle henley, morning, fully clothed",
        "exclude_body_ref": True,  # clothed — prevent tattoo bleed
        "prompt": (
            "A calm candid morning photograph in a bright minimalist Seongsu apartment on Sunday. "
            "A 25-year-old Korean woman standing by an open kitchen window, morning sunlight streaming in. "
            "She is wearing a loose cream waffle-knit henley with three buttons at the neck, "
            "the top button undone, paired with soft grey cotton lounge shorts. "
            "Her honey-balayage hair is delightfully messy — slept-in texture, slightly tangled, "
            "with a few strands falling across her forehead. "
            "She holds a warm ceramic cup of barley tea in both hands, looking down at it "
            "with a peaceful, unhurried expression, not yet fully awake. "
            "Behind her: a simple kitchen counter with a clear glass kettle, a small potted succulent, "
            "and warm golden morning light filtering through sheer off-white curtains. "
            "The background is softly out of focus — neutral walls, warm wood tones, a quiet home interior. "
            "Shot on iPhone 15 Pro: natural daylight, authentic skin texture with visible pores, "
            "zero airbrushing, a genuine Sunday morning snapshot."
        ),
    },
    # --- SUN: 02_henley_lift (bare ribcage, tattoo) ---
    {
        "out_path": ASSETS_DIR / "sets" / "w38_sun_waffle_henley" / "02_henley_lift.png",
        "drop_id": "w38_sun_waffle_henley",
        "gallery_rel": "growth/schedule_assets/sets/w38_sun_waffle_henley/02_henley_lift.png",
        "description": "Henley lifted, ribcage exposed with tattoo",
        "exclude_body_ref": False,  # bare ribcage — use all 3 refs
        "prompt": (
            "An intimate candid morning photograph in a sunlit modern apartment bedroom in Seongsu. "
            "A 26-year-old Korean woman with a natural athletic Pilates physique standing in warm golden "
            "morning light near a sheer-curtained window. "
            "She is wearing a loose cream waffle-knit henley that she has lifted up with both hands, "
            "holding the hem gathered just below her bust, leaving her entire smooth toned abdomen, "
            "natural waist, and bare left ribcage exposed to the warm morning air. "
            "On her bare left ribcage, running vertically just below the breast line, is the delicate "
            "fine-line botanical sprig tattoo shown in the reference — a small minimalist two-branch "
            "botanical sprig rendered in soft fine lines. "
            "Her honey-balayage hair is loose and slightly tangled from sleep, falling softly over her "
            "bare shoulders. "
            "She looks down at her own ribcage with a quiet, thoughtful, introspective half-smile, "
            "as if examining the tattoo in the morning light. "
            "Both hands hold the gathered henley fabric with clean natural fingers. "
            "Soft golden morning sunbeams cast gentle warm shadows across her bare skin. "
            "Shot on iPhone 15 Pro: natural morning light, authentic matte skin with visible pores "
            "and faint freckles, zero CGI airbrushing, candid private photograph."
        ),
    },
    # --- SUN: 03_tatami_stretch (floor stretch, clothed) ---
    {
        "out_path": ASSETS_DIR / "sets" / "w38_sun_waffle_henley" / "03_tatami_stretch.png",
        "drop_id": "w38_sun_waffle_henley",
        "gallery_rel": "growth/schedule_assets/sets/w38_sun_waffle_henley/03_tatami_stretch.png",
        "description": "Floor stretch on tatami, morning light, clothed",
        "exclude_body_ref": True,  # clothed — prevent tattoo bleed on fabric
        "prompt": (
            "A candid morning photograph in a sunlit Seongsu apartment with a natural woven tatami-style "
            "floor mat. "
            "A 25-year-old Korean woman sitting on the floor on a soft grey tatami mat, legs extended "
            "forward in a gentle forward fold, reaching her hands toward her feet in a morning stretch. "
            "She is wearing the same cream waffle-knit henley and soft grey cotton lounge shorts; "
            "the henley has pulled slightly up at the lower back as she leans forward, revealing a "
            "small strip of her lower back. "
            "Her honey-balayage hair falls forward, loose and slightly messy from bed, hiding her face "
            "as she focuses on the stretch. "
            "Warm golden morning light streams in from a nearby window, illuminating the woven tatami "
            "texture and casting long soft shadows across the floor. "
            "Nearby: a half-empty ceramic mug of barley tea on a low wooden table, a folded open book, "
            "and a small white dish with orange slices. "
            "The background shows a calm, quiet corner of her flat — a neutral plaster wall, warm wood "
            "furniture, a trailing pothos plant on a shelf. "
            "Shot on iPhone 15 Pro: natural daylight, organic tones, real skin texture with visible pores, "
            "candid unedited personal snapshot."
        ),
    },
]


def main():
    load_key(PERSONA_DIR)
    key = os.environ.get("KIE_API_KEY", "")
    if not key:
        sys.exit("Error: KIE_API_KEY not found.")
    kie = Kie(key)

    print(f"[*] Credits: {kie.credit()}")
    print(f"[*] Uploading masters...")

    a1_url = kie.upload(MASTER_A1.resolve())
    c5_url = kie.upload(MASTER_C5.resolve())
    tattoo_url = kie.upload(MASTER_TATTOO.resolve())

    print(f"[+] Face master (a1_front): {a1_url[:50]}...")
    print(f"[+] Body master (c5_relax): {c5_url[:50]}...")
    print(f"[+] Tattoo crop: {tattoo_url[:50]}...")

    base_refs = [a1_url, c5_url, tattoo_url]
    face_only = [a1_url]

    for shot in SHOTS:
        out_path = shot["out_path"]
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if out_path.exists():
            print(f"\n[EXISTS] {out_path.name} — skipping. Use force=True to regenerate.")
            continue

        use_refs = face_only if shot["exclude_body_ref"] else base_refs
        label = "clothed (face+body excluded)" if shot["exclude_body_ref"] else "bare ribcage (all 3 refs)"
        print(f"\n{'='*70}")
        print(f"  GENERATING: {out_path.name}")
        print(f"  {shot['description']}")
        print(f"  Refs: {label} ({len(use_refs)})")
        print(f"{'='*70}")

        t0 = time.time()
        urls = kie.generate(
            prompt=shot["prompt"],
            aspect="3:4",
            tier="1k",
            image_urls=use_refs,
            model="seedream/5-pro-image-to-image",
        )
        if not urls:
            print(f"  [ERROR] No URLs returned")
            continue
        n_bytes = kie.download(urls[0], out_path)
        elapsed = time.time() - t0
        print(f"  [SUCCESS] {out_path.name} — {n_bytes // 1024} KB in {elapsed:.1f}s")

    # Update schedule JSON with gallery files
    if SCHEDULE_FILE.exists():
        schedule = json.loads(SCHEDULE_FILE.read_text(encoding="utf-8"))
        for shot in SHOTS:
            drop_id = shot["drop_id"]
            for d in schedule:
                if d.get("id") == drop_id:
                    existing = d.get("fanvue_gallery_files", [])
                    rel = shot["gallery_rel"]
                    if rel not in existing:
                        existing.append(rel)
                    d["fanvue_gallery_files"] = existing
                    break
        SCHEDULE_FILE.write_text(json.dumps(schedule, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\n[+] Updated weekly_schedule.json with gallery files.")

    print("\n[DONE] All generations complete.")


if __name__ == "__main__":
    main()