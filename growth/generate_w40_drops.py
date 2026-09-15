#!/usr/bin/env python3
"""
generate_w40_drops.py — Generation engine for 2026-W40 Bluesky teasers and Fanvue companion sets.

Week 2026-W40: Mon 28 Sep to Sun 04 Oct 2026.
Generated via Kie Seedream 5 Pro (tier: 1k, aspect: 3:4).
"""
import argparse
import json
import os
import pathlib
import sys
import time
from typing import Any, Dict, List

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
GROWTH_DIR = ROOT_DIR / "growth"
ASSETS_DIR = GROWTH_DIR / "schedule_assets"
SETS_DIR = ASSETS_DIR / "sets"
PERSONA_DIR = ROOT_DIR / "personas" / "seoyeon"
SCHEDULE_FILE = ASSETS_DIR / "weekly_schedule.json"

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

W40_DROPS: Dict[str, Dict[str, Any]] = {
    "mon": {
        "id": "w40_mon_heather_tank",
        "day": "Monday",
        "date": "2026-09-28",
        "slot": "morning",
        "time_kst": "10:30",
        "fanvue_publish_at": "2026-09-28T01:15:00.000Z",
        "tier": 2,
        "fanvue_tier": 3,
        "label": "suggestive",
        "platforms": ["bluesky", "fanvue"],
        "media_file": "growth/schedule_assets/w40_mon_heather_tank.png",
        "main_text": "quiet monday in seongsu. holiday week starting slow, coffee still hot.",
        "reply_text": "left the rest of the morning on my private feed... come say hi 🖤 https://www.fanvue.com/syeon.hn?c=fv-4",
        "fanvue_audience": "subscribers",
        "fanvue_price_cents": None,
        "fanvue_text": "holiday week starting quiet. light came in sideways at ten. what are you doing for chuseok this year? ☕",
        "teaser_exclude_body_ref": True,
        "teaser_prompt": (
            "A candid morning photograph in a light oak kitchen in Seongsu. "
            "A 26-year-old Korean woman leaning against the kitchen counter with both hands holding a steaming ceramic mug. "
            "She wears a heather grey ribbed cotton crop racerback tank top and matching soft boy-shorts. "
            "Messy morning bun with curtain bangs falling loose. Calm, candid morning gaze with a faint private smile. " + FILM_SUFFIX
        ),
        "shots": [
            {
                "filename": "02_tank_lift.png",
                "title": "Heather Tank Lifted",
                "exclude_body_ref": False,
                "prompt": (
                    "An intimate morning boudoir photograph in a sunlit kitchen corner. "
                    "A 26-year-old Korean woman pulling the heather grey tank top up above her breasts with both hands. "
                    "Her bare chest, athletic pilates torso and lean left ribcage are exposed in the soft morning sunlight. "
                    "Direct eye contact with the camera, faint playful half-smile, warm natural lighting, real skin pores. " + FILM_SUFFIX
                ),
            },
            {
                "filename": "03_sunlit_counter.png",
                "title": "Sunlit Counter Sit",
                "exclude_body_ref": False,
                "prompt": (
                    "A sensual candid photograph of a 26-year-old Korean woman seated on the counter beside the window. "
                    "Topless, arms resting casually in her lap, looking at the camera with bedroom eyes and parted lips. "
                    "Natural athletic pilates build, zero CGI plastic. " + FILM_SUFFIX
                ),
            },
        ],
    },
    "tue": {
        "id": "w40_tue_champagne_slip",
        "day": "Tuesday",
        "date": "2026-09-29",
        "slot": "evening",
        "time_kst": "17:30",
        "fanvue_publish_at": "2026-09-29T08:15:00.000Z",
        "tier": 2,
        "fanvue_tier": 3,
        "label": "suggestive",
        "platforms": ["bluesky", "fanvue"],
        "media_file": "growth/schedule_assets/w40_tue_champagne_slip.png",
        "main_text": "sunset through the balcony blinds. gold turns to slate in ten minutes now.",
        "reply_text": "slipped out of the champagne satin once the chill arrived... private gallery is live 🍯 https://www.fanvue.com/syeon.hn?c=fv-4",
        "fanvue_audience": "subscribers",
        "fanvue_price_cents": None,
        "fanvue_text": "twilight across the floorboards. let the strap drop as the room cooled down. do you like this time of year? 🖤",
        "teaser_exclude_body_ref": True,
        "teaser_prompt": (
            "A candid golden hour photograph standing near open balcony blinds in a Seoul flat. "
            "A 26-year-old Korean woman wearing an elegant champagne-toned satin slip dress with one clean, single delicate spaghetti strap on each shoulder. "
            "Sunset light slanting through horizontal blinds creating warm zebra shadows across her chest and shoulders. "
            "Holding a white iPhone 15 Pro in a clear case with relaxed hands. Soft golden twilight glow. " + FILM_SUFFIX
        ),
        "shots": [
            {
                "filename": "02_satin_slide.png",
                "title": "Champagne Satin Slipped",
                "exclude_body_ref": False,
                "prompt": (
                    "An alluring boudoir photograph in warm late afternoon twilight. "
                    "A 26-year-old Korean woman standing before the window, sliding the champagne satin dress down her hips. "
                    "Her bare upper body and breasts catch the warm copper light. "
                    ""
                    "Delicate natural clavicles, relaxed neck, soft film grain. " + FILM_SUFFIX
                ),
            },
            {
                "filename": "03_crepuscular_recline.png",
                "title": "Crepuscular Bed Recline",
                "exclude_body_ref": False,
                "prompt": (
                    "A sensual candid photograph of a 26-year-old Korean woman reclining back on a dark grey linen bedspread as dusk settles. "
                    "Topless, hair spread across the pillows, looking into the lens with parted lips. "
                    "Soft ambient blue and amber crepuscular light. " + FILM_SUFFIX
                ),
            },
        ],
    },
    "wed": {
        "id": "w40_wed_cashmere_shrug",
        "day": "Wednesday",
        "date": "2026-09-30",
        "slot": "night",
        "time_kst": "23:15",
        "fanvue_publish_at": "2026-09-30T14:00:00.000Z",
        "tier": 2,
        "fanvue_tier": 3,
        "label": "suggestive",
        "platforms": ["bluesky", "fanvue"],
        "media_file": "growth/schedule_assets/w40_wed_cashmere_shrug.png",
        "main_text": "eleven thirty. boiled water for roasted barley tea, cold breeze from the window.",
        "reply_text": "shrugged off the knit by midnight... shared the full private roll here 🖤 https://www.fanvue.com/syeon.hn?c=fv-4",
        "fanvue_audience": "subscribers",
        "fanvue_price_cents": None,
        "fanvue_text": "quiet late night with barley tea. dropped the knit shrug once the kettle whistled. do you drink tea or coffee before bed? 🤍",
        "teaser_exclude_body_ref": True,
        "teaser_prompt": (
            "A candid midnight photograph in a dimly lit bedroom alcove. "
            "A 26-year-old Korean woman seated on the edge of the bed wearing a soft charcoal cropped knit cashmere bolero shrug over bare shoulders and black silk lounge shorts. "
            "Holding an earthenware tea mug with both hands, steam rising. "
            "Deep warm bedside lamp lighting, dark window panes, calm contemplative expression. " + FILM_SUFFIX
        ),
        "shots": [
            {
                "filename": "02_shrug_drop.png",
                "title": "Cashmere Shrug Dropped",
                "exclude_body_ref": False,
                "prompt": (
                    "An intimate midnight photograph in a warm lamplit room. "
                    "A 26-year-old Korean woman letting the knit shrug slide off her shoulders down onto the bed behind her. "
                    "Her bare torso, breasts, and toned pilates midriff are fully exposed. "
                    ""
                    "Intimate, relaxed natural posture, warm ambient glow. " + FILM_SUFFIX
                ),
            },
            {
                "filename": "03_midnight_tatami.png",
                "title": "Midnight Rug Recline",
                "exclude_body_ref": False,
                "prompt": (
                    "A sensual photograph of a 26-year-old Korean woman lying on her side on a low woven bedroom rug. "
                    "Topless, head resting on one bent arm, looking up at camera with a sleepy seductive smirk. "
                    "Lived-in nocturnal bedroom ambiance. " + FILM_SUFFIX
                ),
            },
        ],
    },
    "thu": {
        "id": "w40_thu_slate_cami",
        "day": "Thursday",
        "date": "2026-10-01",
        "slot": "evening",
        "time_kst": "19:45",
        "fanvue_publish_at": "2026-10-01T10:30:00.000Z",
        "tier": 2,
        "fanvue_tier": 3,
        "label": "suggestive",
        "platforms": ["bluesky", "fanvue"],
        "media_file": "growth/schedule_assets/w40_thu_slate_cami.png",
        "main_text": "october first. warm shower after teaching four classes back to back.",
        "reply_text": "lingered by the vanity after towelling off... full mirror set on my private wall 🖤 https://www.fanvue.com/syeon.hn?c=fv-4",
        "fanvue_audience": "subscribers",
        "fanvue_price_cents": None,
        "fanvue_text": "october is here. fresh out of the shower in slate silk. what is your favorite thing about autumn? 🖤",
        "teaser_exclude_body_ref": True,
        "teaser_prompt": (
            "A candid post-shower vanity mirror selfie in a bathroom with steamed glass. "
            "A 26-year-old Korean woman standing before the vanity wearing a slate grey silk camisole with clean single delicate spaghetti straps. "
            "Damp hair pinned up in a loose clip with wet wisps around her neck. "
            "Holding her white iPhone 15 Pro, calm post-shower reflection in the clear glass. Soft warm vanity bulb lighting. " + FILM_SUFFIX
        ),
        "shots": [
            {
                "filename": "02_mirror_cami_drop.png",
                "title": "Vanity Cami Lowered",
                "exclude_body_ref": False,
                "prompt": (
                    "An intimate post-shower photograph before the steamed vanity mirror. "
                    "A 26-year-old Korean woman lowering the slate silk camisole down to her waist, revealing her bare chest and damp athletic torso. "
                    ""
                    "Warm diffuse vanity glow, moisture droplets on the glass, intimate candid realism. " + FILM_SUFFIX
                ),
            },
            {
                "filename": "03_vanity_recline.png",
                "title": "Steamed Bathroom Recline",
                "exclude_body_ref": False,
                "prompt": (
                    "A sensual photograph of a 26-year-old Korean woman seated on the wooden bath stool in the bathroom. "
                    "Topless, holding a white bath towel across her lap, looking toward the camera with parted lips. "
                    "Soft warm mist in the air. " + FILM_SUFFIX
                ),
            },
        ],
    },
    "fri": {
        "id": "w40_fri_burgundy_lace",
        "day": "Friday",
        "date": "2026-10-02",
        "slot": "night",
        "time_kst": "22:00",
        "fanvue_publish_at": "2026-10-02T12:45:00.000Z",
        "tier": 2,
        "fanvue_tier": 3,
        "label": "suggestive",
        "platforms": ["bluesky", "fanvue"],
        "media_file": "growth/schedule_assets/w40_fri_burgundy_lace.png",
        "main_text": "holiday weekend in the city. turned off my email notifications at eight.",
        "reply_text": "stayed on the living room rug tonight... private weekend feed is waiting for you 🍯 https://www.fanvue.com/syeon.hn?c=fv-4",
        "fanvue_audience": "subscribers",
        "fanvue_price_cents": None,
        "fanvue_text": "holiday silence in seongsu tonight. burgundy lace on the rug with the city lights outside. staying in or heading out tonight? 🖤",
        "teaser_exclude_body_ref": True,
        "teaser_prompt": (
            "A candid Friday night photograph on a dark wool living room rug. "
            "A 26-year-old Korean woman sitting leaning back against a low sofa, surrounded by warm floor pillows. "
            "She wears a dark burgundy lace camisole with delicate eyelash lace trim and matching silk tap shorts. "
            "Loose wavy balayage hair falling over one bare shoulder. Soft warm corner floor lamp lighting, city night through the dark glass. " + FILM_SUFFIX
        ),
        "shots": [
            {
                "filename": "02_lace_parted.png",
                "title": "Burgundy Lace Parted",
                "exclude_body_ref": False,
                "prompt": (
                    "An alluring boudoir photograph in a warm living room at night. "
                    "A 26-year-old Korean woman kneeling on the wool rug, pulling the burgundy lace camisole open over her breasts. "
                    "Bare athletic torso illuminated by the warm ambient floor lamp. "
                    ""
                    "Sensual, unforced gaze with parted lips. " + FILM_SUFFIX
                ),
            },
            {
                "filename": "03_carpet_intimate.png",
                "title": "Floor Lamp Recline",
                "exclude_body_ref": False,
                "prompt": (
                    "An alluring sensual candid photograph on the soft wool living room rug at night. "
                    "A 26-year-old Korean woman reclining lazily across the wool rug, resting back on her right elbow on a floor cushion with her right hand casually supporting her head. "
                    "Her lean athletic torso is naturally turned toward the camera, exposing her bare left ribcage and flank in the warm amber corner floor lamp glow. "
                    "Her left hand rests gently down along her hip. "
                    "Topless, wearing dark burgundy lace briefs, intimate bedroom eyes looking into the camera lens with soft parted lips. "
                    "Real skin pores, subtle sensor noise, warm moody shadows. " + FILM_SUFFIX
                ),
            },
        ],
    },
    "sat": {
        "id": "w40_sat_velvet_midnight",
        "day": "Saturday",
        "date": "2026-10-03",
        "slot": "night",
        "time_kst": "23:45",
        "fanvue_publish_at": "2026-10-03T14:30:00.000Z",
        "tier": 2,
        "fanvue_tier": 3,
        "label": "suggestive",
        "platforms": ["bluesky", "fanvue"],
        "media_file": "growth/schedule_assets/w40_sat_velvet_midnight.png",
        "main_text": "midnight in velvet. couldn't sleep so i took a few before slipping into bed.",
        "reply_text": "let the velvet slide onto the floor... my private midnight vault is open tonight 🖤 https://www.fanvue.com/syeon.hn?c=fv-4",
        "fanvue_audience": "subscribers",
        "fanvue_price_cents": 999,
        "fanvue_text": "saturday midnight in navy velvet. slipped it off right before getting into bed. are you awake to keep me company? 🖤",
        "teaser_exclude_body_ref": True,
        "teaser_prompt": (
            "A candid midnight bedroom mirror selfie in a Seongsu apartment. "
            "A 26-year-old Korean woman standing in front of a floor-length leaning mirror wearing a midnight navy crushed velvet slip dress with one clean single spaghetti strap on each shoulder. "
            "Holding her white iPhone 15 Pro with relaxed hands, direct sultry gaze into the glass. "
            "Deep warm bedside lamp casting rich textures on the velvet and her collarbone. " + FILM_SUFFIX
        ),
        "shots": [
            {
                "filename": "02_velvet_slide.png",
                "title": "Velvet Slip Slipped",
                "exclude_body_ref": False,
                "prompt": (
                    "An explicit high-heat boudoir photograph in a dimly lit bedroom at midnight. "
                    "A 26-year-old Korean woman sliding the midnight navy velvet dress down over her hips onto the floorboards. "
                    "Completely bare upper body and breasts, soft natural skin pores and clavicles. "
                    ""
                    "Rich midnight shadows, authentic filmic grain. " + FILM_SUFFIX
                ),
            },
            {
                "filename": "03_midnight_sanctuary.png",
                "title": "Midnight Sanctuary Recline",
                "exclude_body_ref": False,
                "prompt": (
                    "A provocative intimate photograph of a 26-year-old Korean woman lying diagonally across dark velvet throw pillows on her bed. "
                    "Topless, arched back slightly, looking down the camera with sleepy seductive bedroom eyes. "
                    "High-heat private subscriber unlock aesthetic. " + FILM_SUFFIX
                ),
            },
        ],
    },
    "sun": {
        "id": "w40_sun_linen_robe",
        "day": "Sunday",
        "date": "2026-10-04",
        "slot": "morning",
        "time_kst": "09:15",
        "fanvue_publish_at": "2026-10-04T00:00:00.000Z",
        "tier": 2,
        "fanvue_tier": 3,
        "label": "suggestive",
        "platforms": ["bluesky", "fanvue"],
        "media_file": "growth/schedule_assets/w40_sun_linen_robe.png",
        "main_text": "sunday morning. nowhere to be until tomorrow, sun cutting across the counter.",
        "reply_text": "untied the robe and poured a second cup... full lazy sunday set is on my page ☕ https://www.fanvue.com/syeon.hn?c=fv-4",
        "fanvue_audience": "subscribers",
        "fanvue_price_cents": None,
        "fanvue_text": "sunday morning in linen. nowhere to rush, coffee on the counter. how do you like to spend your sundays? 🤍",
        "teaser_exclude_body_ref": True,
        "teaser_prompt": (
            "A candid Sunday morning photograph in a bright minimalist apartment. "
            "A 26-year-old Korean woman leaning against a sunlit breakfast counter wrapped in a washed ivory linen lounge robe tied loosely at the waist. "
            "Holding a white ceramic mug, morning sun illuminating her honey-balayage hair. "
            "Warm golden morning beams, unbrushed natural hair, relaxed weekend expression. " + FILM_SUFFIX
        ),
        "shots": [
            {
                "filename": "02_robe_untied.png",
                "title": "Linen Robe Untied",
                "exclude_body_ref": False,
                "prompt": (
                    "An intimate candid morning photograph in a bright sunlit kitchen. "
                    "A 26-year-old Korean woman untying the linen robe sash and parting it wide, completely bare underneath. "
                    "Her bare full breasts and athletic pilates torso bathed in bright morning sun. "
                    ""
                    "Fresh morning glow, authentic skin pores and subtle freckles. " + FILM_SUFFIX
                ),
            },
            {
                "filename": "03_breakfast_sun.png",
                "title": "Sunday Morning Recline",
                "exclude_body_ref": False,
                "prompt": (
                    "A sensual candid photograph of a 26-year-old Korean woman seated on a low wooden stool beside the sunlit window. "
                    "The linen robe has slipped down her arms to her waist, topless, head tilted with a soft private smile looking at the camera. "
                    "Warm early October sunlight. " + FILM_SUFFIX
                ),
            },
        ],
    },
}

def update_weekly_schedule() -> None:
    """Appends/updates W40 drops in weekly_schedule.json."""
    schedule: List[Dict[str, Any]] = []
    if SCHEDULE_FILE.exists():
        try:
            schedule = json.loads(SCHEDULE_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"Error loading schedule: {e}")

    by_id = {item["id"]: item for item in schedule if "id" in item}

    for d_key, drop in W40_DROPS.items():
        drop_id = drop["id"]
        gallery = [drop["media_file"]] + [
            f"growth/schedule_assets/sets/{drop_id}/{shot['filename']}" for shot in drop["shots"]
        ]

        entry = {
            "id": drop_id,
            "day": drop["day"],
            "date": drop["date"],
            "week": "2026-W40",
            "tier": drop["tier"],
            "fanvue_tier": drop["fanvue_tier"],
            "lanes": drop["platforms"],
            "platforms": drop["platforms"],
            "slot": drop["slot"],
            "time_kst": drop["time_kst"],
            "status": "ready",
            "label": drop["label"],
            "media_type": "image",
            "media_file": drop["media_file"],
            "main_text": drop["main_text"],
            "reply_text": drop["reply_text"],
            "fanvue_audience": drop["fanvue_audience"],
            "fanvue_publish_at": drop["fanvue_publish_at"],
            "fanvue_text": drop["fanvue_text"],
            "fanvue_gallery_files": gallery,
            "fanvue_status": "ready",
            "fanvue_price_cents": drop["fanvue_price_cents"],
        }
        by_id[drop_id] = entry

    SCHEDULE_FILE.write_text(json.dumps(list(by_id.values()), indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓ Registered {len(W40_DROPS)} drops for 2026-W40 in weekly_schedule.json")


def generate_drops(day_filter: str = "all", force: bool = False, dry_run: bool = False, shot_filter: str = "") -> None:
    load_key(PERSONA_DIR)
    key = os.environ.get("KIE_API_KEY", "")
    if not key and not dry_run:
        sys.exit("Error: KIE_API_KEY not found.")

    kie = None
    all_refs = []
    a1_url = None
    if not dry_run:
        kie = Kie(key)
        print(f"[*] Available Kie credit: {kie.credit()}")
        print("[*] Uploading/caching reference masters...")
        a1_url = kie.upload(MASTER_A1.resolve())
        c5_url = kie.upload(MASTER_C5.resolve()) if MASTER_C5.exists() else None
        tattoo_url = kie.upload(MASTER_TATTOO.resolve()) if MASTER_TATTOO.exists() else None
        all_refs = [a1_url]
        if c5_url:
            all_refs.append(c5_url)
        if tattoo_url:
            all_refs.append(tattoo_url)
        print(f"[+] Active references: {len(all_refs)} master images")

    targets = list(W40_DROPS.keys()) if day_filter == "all" else [day_filter]
    for d_key in targets:
        if d_key not in W40_DROPS:
            print(f"Unknown day: {d_key}")
            continue
        drop = W40_DROPS[d_key]
        drop_id = drop["id"]
        print(f"\n{'='*70}\n  Generating 2026-W40 Drop: {drop_id} ({drop['day']})\n{'='*70}")

        # 1. Teaser Image (Shot 01)
        if not shot_filter:
            teaser_dest = ROOT_DIR / drop["media_file"]
            teaser_dest.parent.mkdir(parents=True, exist_ok=True)
            if teaser_dest.exists() and not force:
                print(f"  [EXISTS] Teaser: {teaser_dest.name} — skip")
            else:
                refs = [a1_url] if drop.get("teaser_exclude_body_ref", False) else all_refs
                print(f"  --> Rendering Teaser ({len(refs)} refs, exclude_body={drop.get('teaser_exclude_body_ref', False)})...")
                if dry_run:
                    print(f"      [DRY-RUN] Teaser prompt: {drop['teaser_prompt'][:80]}...")
                else:
                    t0 = time.time()
                    urls = kie.generate(
                        prompt=drop["teaser_prompt"],
                        aspect="3:4",
                        tier="1k",
                        image_urls=refs,
                        model="seedream/5-pro-image-to-image",
                    )
                    if urls:
                        n = kie.download(urls[0], teaser_dest)
                        print(f"      ✓ Teaser downloaded: {teaser_dest.name} ({n//1024} KB in {time.time()-t0:.1f}s)")

        # 2. Companion Images (Shots 02 & 03)
        drop_dir = SETS_DIR / drop_id
        drop_dir.mkdir(parents=True, exist_ok=True)
        for shot in drop["shots"]:
            if shot_filter and shot["filename"] != shot_filter:
                continue
            shot_dest = drop_dir / shot["filename"]
            if shot_dest.exists() and not force:
                print(f"  [EXISTS] Companion {shot['filename']} — skip")
                continue
            refs = [a1_url] if shot.get("exclude_body_ref", False) else all_refs
            print(f"  --> Rendering Companion {shot['filename']} ({len(refs)} refs, exclude_body={shot.get('exclude_body_ref', False)})...")
            if dry_run:
                print(f"      [DRY-RUN] Prompt: {shot['prompt'][:80]}...")
            else:
                t0 = time.time()
                urls = kie.generate(
                    prompt=shot["prompt"],
                    aspect="3:4",
                    tier="1k",
                    image_urls=refs,
                    model="seedream/5-pro-image-to-image",
                )
                if urls:
                    n = kie.download(urls[0], shot_dest)
                    print(f"      ✓ Companion downloaded: {shot_dest.name} ({n//1024} KB in {time.time()-t0:.1f}s)")


def main():
    parser = argparse.ArgumentParser(description="Generate and schedule 2026-W40 Bluesky/Fanvue companion drops")
    parser.add_argument("--sync-schedule", action="store_true", help="Sync metadata into weekly_schedule.json without generating media")
    parser.add_argument("--generate", action="store_true", help="Execute image generation on Kie")
    parser.add_argument("--day", type=str, default="all", help="Target specific day (mon, tue, wed, thu, fri, sat, sun, all)")
    parser.add_argument("--shot", type=str, default="", help="Target specific shot filename (e.g. 02_tank_lift.png)")
    parser.add_argument("--force", action="store_true", help="Force overwrite of existing files")
    parser.add_argument("--dry-run", action="store_true", help="Simulate generation without spending Kie credits")
    args = parser.parse_args()

    update_weekly_schedule()

    if args.generate or args.dry_run:
        generate_drops(day_filter=args.day, force=args.force, dry_run=args.dry_run, shot_filter=args.shot)
    else:
        print("\nSchedule synced. Pass --generate to execute image generation on Kie.")

if __name__ == "__main__":
    main()
