#!/usr/bin/env python3
"""
generate_w39_drops.py — Generation engine for 2026-W39 Bluesky teasers and Fanvue companion sets.

Week 2026-W39: Mon 21 Sep to Sun 27 Sep 2026.
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

W39_DROPS: Dict[str, Dict[str, Any]] = {
    "mon": {
        "id": "w39_mon_ribbed_knit",
        "day": "Monday",
        "date": "2026-09-21",
        "slot": "morning",
        "time_kst": "10:30",
        "fanvue_publish_at": "2026-09-21T01:15:00.000Z",
        "tier": 2,
        "fanvue_tier": 3,
        "label": "suggestive",
        "platforms": ["bluesky", "fanvue"],
        "media_file": "growth/schedule_assets/w39_mon_ribbed_knit.png",
        "main_text": "sun on the tatami mat at ten. brewed roasted barley tea and left the phone in the other room.",
        "reply_text": "stayed on the floor after the tea cooled... full morning set is on my private feed 🖤 https://www.fanvue.com/syeon.hn?c=fv-4",
        "fanvue_audience": "subscribers",
        "fanvue_price_cents": None,
        "fanvue_text": "warm morning light on the floorboards. slipped the ribbed knit off once the room heated up. do you prefer slow mornings or getting straight into things? ☕",
        "teaser_exclude_body_ref": True,
        "teaser_prompt": (
            "An authentic candid morning photograph in a sunlit tatami corner of a minimalist Seoul flat. "
            "A 26-year-old Korean woman sitting cross-legged on the woven straw mat, leaning back on one hand. "
            "She wears a cream finely ribbed knit tank top with a soft scoop neckline and matching ribbed boy-shorts. "
            "Her honey-balayage hair is in a messy high knot with loose tendrils framing her jawline. "
            "Warm morning sun cuts across the floor. Relaxed natural clavicles, sleepy morning gaze toward camera. " + FILM_SUFFIX
        ),
        "shots": [
            {
                "filename": "02_tank_slide.png",
                "title": "Knit Tank Slipped",
                "exclude_body_ref": False,
                "prompt": (
                    "An intimate boudoir photograph on a sunlit tatami mat in a minimalist room. "
                    "A 26-year-old Korean woman kneeling gracefully, sliding the cream ribbed tank top off over her head. "
                    "Her athletic pilates torso is exposed in the soft natural morning backlight, showing natural skin pores and subtle sensor grain. " + FILM_SUFFIX
                ),
            },
            {
                "filename": "03_tatami_intimate.png",
                "title": "Tatami Floor Recline",
                "exclude_body_ref": False,
                "prompt": (
                    "An alluring candid top-down photograph of a 26-year-old Korean woman reclining on her side on a tatami straw mat. "
                    "Topless, arms relaxed over her head with parted lips and bedroom eyes looking up at camera. "
                    ""
                    "Natural athletic pilates proportions, real skin pores, morning window glow. " + FILM_SUFFIX
                ),
            },
        ],
    },
    "tue": {
        "id": "w39_tue_charcoal_slip",
        "day": "Tuesday",
        "date": "2026-09-22",
        "slot": "evening",
        "time_kst": "17:30",
        "fanvue_publish_at": "2026-09-22T08:15:00.000Z",
        "tier": 2,
        "fanvue_tier": 3,
        "label": "suggestive",
        "platforms": ["bluesky", "fanvue"],
        "media_file": "growth/schedule_assets/w39_tue_charcoal_slip.png",
        "main_text": "the light goes copper at five. twenty minutes of quiet before dinner.",
        "reply_text": "slipped out of the silk once the shadows lengthened... private roll is waiting 🍯 https://www.fanvue.com/syeon.hn?c=fv-4",
        "fanvue_audience": "subscribers",
        "fanvue_price_cents": None,
        "fanvue_text": "twenty minutes of golden copper light across the flat. let the slip fall once the sun dipped below the rooflines. what did your evening look like? 🖤",
        "teaser_exclude_body_ref": True,
        "teaser_prompt": (
            "A candid golden hour bedroom mirror selfie in a minimalist Seongsu flat. "
            "A 26-year-old Korean woman standing in three-quarter view wearing a charcoal grey silk slip dress with one clean, single delicate spaghetti strap on each shoulder (exactly one strap per shoulder, no duplicate straps). "
            "She holds a white iPhone 15 Pro in a clear transparent case with relaxed hands. "
            "Deep amber twilight light streaming through tall windows, casting long shadows on the oak floor. " + FILM_SUFFIX
        ),
        "shots": [
            {
                "filename": "02_strap_drop.png",
                "title": "Charcoal Strap Drop",
                "exclude_body_ref": False,
                "prompt": (
                    "An intimate candid boudoir photograph in a bedroom during golden hour dusk. "
                    "A 26-year-old Korean woman sitting on the edge of the bed, having slipped the straps of the charcoal silk dress down to her waist. "
                    "Bare upper body, delicate natural breasts, looking sideways toward the window. "
                    ""
                    "Warm copper twilight light highlighting the curves of her ribs and collarbone. " + FILM_SUFFIX
                ),
            },
            {
                "filename": "03_dusk_recline.png",
                "title": "Dusk Silk Recline",
                "exclude_body_ref": False,
                "prompt": (
                    "A sensual candid bedroom photograph in deep twilight dusk. "
                    "A 26-year-old Korean woman lying back across dark crumpled linen bedsheets. "
                    "Topless, bare athletic torso. Soft dark amber lamp glow, authentic film grain, intimate gaze. " + FILM_SUFFIX
                ),
            },
        ],
    },
    "wed": {
        "id": "w39_wed_oversized_oxford",
        "day": "Wednesday",
        "date": "2026-09-23",
        "slot": "night",
        "time_kst": "23:15",
        "fanvue_publish_at": "2026-09-23T14:00:00.000Z",
        "tier": 2,
        "fanvue_tier": 3,
        "label": "suggestive",
        "platforms": ["bluesky", "fanvue"],
        "media_file": "growth/schedule_assets/w39_wed_oversized_oxford.png",
        "main_text": "midnight kettle. put on this cotton shirt and stayed up reading reformer anatomy.",
        "reply_text": "unbuttoned the shirt once the flat got warm. shared the whole midnight set for you... link is here 🖤 https://www.fanvue.com/syeon.hn?c=fv-4",
        "fanvue_audience": "subscribers",
        "fanvue_price_cents": None,
        "fanvue_text": "midnight in the kitchen. shirt unbuttoned and bare feet on the cool tile. are you usually a night owl or do you sleep early? 🤍",
        "teaser_exclude_body_ref": True,
        "teaser_prompt": (
            "A candid midnight photograph in a dim minimalist kitchen corner. "
            "A 26-year-old Korean woman leaning against a poured concrete breakfast counter holding a warm mug. "
            "She wears an oversized pale blue cotton oxford shirt unbuttoned halfway down to reveal a lace bralette beneath, sleeves rolled to elbows. "
            "Hair pinned up loosely in a claw clip. Only the warm stove hood light is on, creating moody shadows. " + FILM_SUFFIX
        ),
        "shots": [
            {
                "filename": "02_oxford_parted.png",
                "title": "Parted Oxford Shirt",
                "exclude_body_ref": False,
                "prompt": (
                    "An intimate late-night photograph in a dim kitchen. "
                    "A 26-year-old Korean woman standing by the counter, holding the pale blue oxford shirt open to her sides, completely bare beneath. "
                    "Her bare athletic torso is illuminated by the soft warm range hood light. "
                    ""
                    "Unforced bedroom eyes, authentic matte skin texture. " + FILM_SUFFIX
                ),
            },
            {
                "filename": "03_counter_intimate.png",
                "title": "Midnight Counter Sit",
                "exclude_body_ref": False,
                "prompt": (
                    "An alluring candid photograph of a 26-year-old Korean woman seated on the edge of the kitchen counter at midnight. "
                    "The blue oxford shirt has slipped off her shoulders down her arms, topless, bare breasts and torso. "
                    ""
                    "Sensual, quiet, moody nocturnal atmosphere. " + FILM_SUFFIX
                ),
            },
        ],
    },
    "thu": {
        "id": "w39_thu_terracotta_cami",
        "day": "Thursday",
        "date": "2026-09-24",
        "slot": "evening",
        "time_kst": "19:45",
        "fanvue_publish_at": "2026-09-24T10:30:00.000Z",
        "tier": 2,
        "fanvue_tier": 3,
        "label": "suggestive",
        "platforms": ["bluesky", "fanvue"],
        "media_file": "growth/schedule_assets/w39_thu_terracotta_cami.png",
        "main_text": "washed the studio floor after the last class. ten minutes of stretching before the walk home.",
        "reply_text": "cooled down on the mat in the private room... full camera roll is on my feed 🖤 https://www.fanvue.com/syeon.hn?c=fv-4",
        "fanvue_audience": "subscribers",
        "fanvue_price_cents": None,
        "fanvue_text": "empty studio after hours. cooled down on the mat with the lights dimmed. what helps you unwind after a long day? 🖤",
        "teaser_exclude_body_ref": True,
        "teaser_prompt": (
            "A candid post-workout photograph inside an empty, quiet pilates studio at twilight. "
            "A 26-year-old Korean woman sitting on a charcoal mat, leaning one hand against a wooden reformer frame. "
            "She wears a terracotta modal camisole with clean single delicate spaghetti straps and black fitted biker shorts. "
            "Faint glow of sweat on her collarbone and shoulders, hair in a low loose ponytail. Calm reflective expression. " + FILM_SUFFIX
        ),
        "shots": [
            {
                "filename": "02_mat_recline.png",
                "title": "Studio Mat Stretch",
                "exclude_body_ref": False,
                "prompt": (
                    "An intimate after-hours photograph in an empty dimly lit pilates studio. "
                    "A 26-year-old Korean woman seated on the mat, pulling the terracotta camisole up over her chest, revealing her bare athletic pilates ribcage and breasts. "
                    ""
                    "Dusk light through the tall studio windows, quiet solitary breathing. " + FILM_SUFFIX
                ),
            },
            {
                "filename": "03_mirror_intimate.png",
                "title": "Studio Mirror Intimacy",
                "exclude_body_ref": False,
                "prompt": (
                    "A sensual mirror selfie in a dim pilates studio. "
                    "A 26-year-old Korean woman kneeling before the full-height wall mirror. "
                    "Topless, holding her white iPhone 15 Pro with one hand while her other arm rests gently across her lap. "
                    "Authentic skin texture, zero plastic CGI. " + FILM_SUFFIX
                ),
            },
        ],
    },
    "fri": {
        "id": "w39_fri_emerald_silk",
        "day": "Friday",
        "date": "2026-09-25",
        "slot": "night",
        "time_kst": "22:00",
        "fanvue_publish_at": "2026-09-25T12:45:00.000Z",
        "tier": 2,
        "fanvue_tier": 3,
        "label": "suggestive",
        "platforms": ["bluesky", "fanvue"],
        "media_file": "growth/schedule_assets/w39_fri_emerald_silk.png",
        "main_text": "friday night. no alarms set for tomorrow. turned off the ceiling lights early.",
        "reply_text": "slipped under the linen sheets right after this... full weekend set is waiting for you 🍯 https://www.fanvue.com/syeon.hn?c=fv-4",
        "fanvue_audience": "subscribers",
        "fanvue_price_cents": None,
        "fanvue_text": "friday night in emerald silk. no alarms set for tomorrow and nowhere i need to be. have any quiet plans for the weekend? 🖤",
        "teaser_exclude_body_ref": True,
        "teaser_prompt": (
            "A seductive Friday night photograph in a cozy bedroom. "
            "A 26-year-old Korean woman sitting on the edge of an unmade bed with warm rumpled linen sheets. "
            "She wears a rich deep emerald green silk slip dress with one clean, single delicate spaghetti strap on each shoulder. "
            "One small gold huggie in each ear, honey-balayage hair loose over her shoulders. "
            "Warm bedside lamplight, dark night outside the window. Intimate, candid direct eye contact. " + FILM_SUFFIX
        ),
        "shots": [
            {
                "filename": "02_emerald_drop.png",
                "title": "Emerald Slip Slipped",
                "exclude_body_ref": False,
                "prompt": (
                    "An intimate boudoir photograph in a dimly lit bedroom on a Friday night. "
                    "A 26-year-old Korean woman sitting on the bed, holding the emerald silk slip bunched at her waist. "
                    "Bare breasts, relaxed natural posture with soft clavicles. "
                    ""
                    "Warm amber shadows, real skin texture. " + FILM_SUFFIX
                ),
            },
            {
                "filename": "03_midnight_sheets.png",
                "title": "Linen Sheets Recline",
                "exclude_body_ref": False,
                "prompt": (
                    "An alluring sensual photograph of a 26-year-old Korean woman lying on her back across messy linen duvet sheets. "
                    "Topless, looking down the lens with parted lips and sleepy bedroom eyes. "
                    "Her bare athletic torso is framed by the crumpled white sheets. "
                    "Sensual, quiet midnight atmosphere. " + FILM_SUFFIX
                ),
            },
        ],
    },
    "sat": {
        "id": "w39_sat_midnight_sheer",
        "day": "Saturday",
        "date": "2026-09-26",
        "slot": "night",
        "time_kst": "23:45",
        "fanvue_publish_at": "2026-09-26T14:30:00.000Z",
        "tier": 2,
        "fanvue_tier": 3,
        "label": "suggestive",
        "platforms": ["bluesky", "fanvue"],
        "media_file": "growth/schedule_assets/w39_sat_midnight_sheer.png",
        "main_text": "almost midnight. tried this on and decided to stay right here on the rug.",
        "reply_text": "unclasped the lace once the clock hit twelve... my most intimate saturday vault is open tonight 🖤 https://www.fanvue.com/syeon.hn?c=fv-4",
        "fanvue_audience": "subscribers",
        "fanvue_price_cents": 999,
        "fanvue_text": "midnight in black sheer lace. took these in the quiet of the flat before bed. what keeps you up this late? 🖤",
        "teaser_exclude_body_ref": True,
        "teaser_prompt": (
            "A candid midnight bedroom mirror selfie in a Seongsu studio flat. "
            "A 26-year-old Korean woman kneeling on a thick woven wool rug in front of a full-length leaning mirror. "
            "She wears a sheer black floral lace bralette with delicate triangle cups and matching low-rise lace boyshorts. "
            "She holds a white iPhone 15 Pro with both hands, looking into the mirror with a quiet, sensual gaze. "
            "Warm single-point bedside lamp lighting, pitch black window in the background. " + FILM_SUFFIX
        ),
        "shots": [
            {
                "filename": "02_sheer_unclasp.png",
                "title": "Lace Unclasped",
                "exclude_body_ref": False,
                "prompt": (
                    "An explicit high-heat boudoir photograph on a bedroom rug at midnight. "
                    "A 26-year-old Korean woman unhooking the sheer black lace bralette, parting it wide with her fingers. "
                    "Bare full breasts and athletic pilates midriff. Deep moody warm chiaroscuro lighting, authentic film grain. " + FILM_SUFFIX
                ),
            },
            {
                "filename": "03_boudoir_vault.png",
                "title": "Midnight Vault Recline",
                "exclude_body_ref": False,
                "prompt": (
                    "A provocative and intimate photograph of a 26-year-old Korean woman reclining against pillows on her bed. "
                    "Topless, wearing only sheer black lace briefs, arched back slightly with relaxed shoulders. "
                    ""
                    "Bedroom eyes, parted lips, authentic fine-grain 35mm film aesthetic. " + FILM_SUFFIX
                ),
            },
        ],
    },
    "sun": {
        "id": "w39_sun_waffle_lounge",
        "day": "Sunday",
        "date": "2026-09-27",
        "slot": "morning",
        "time_kst": "09:15",
        "fanvue_publish_at": "2026-09-27T00:00:00.000Z",
        "tier": 2,
        "fanvue_tier": 3,
        "label": "suggestive",
        "platforms": ["bluesky", "fanvue"],
        "media_file": "growth/schedule_assets/w39_sun_waffle_lounge.png",
        "main_text": "sunday morning. slow light through the curtain, warm coffee in hand.",
        "reply_text": "stayed under the covers for another hour... full lazy morning set is on my private wall ☕ https://www.fanvue.com/syeon.hn?c=fv-4",
        "fanvue_audience": "subscribers",
        "fanvue_price_cents": None,
        "fanvue_text": "sunday morning with nowhere to be. unbuttoned the waffle knit and stayed under the covers. do you take sundays slow or do you get outside? 🤍",
        "teaser_exclude_body_ref": True,
        "teaser_prompt": (
            "A candid Sunday morning photograph in a bright sunlit bedroom in Seongsu. "
            "A 26-year-old Korean woman sitting up in an unmade bed, wrapped in a soft oatmeal waffle-knit long-sleeve henley unbuttoned low at the throat. "
            "Bare legs peeking out from beneath a rumpled cream linen duvet. "
            "Holding a handmade ceramic coffee cup with steam curling into the morning light. Soft unbrushed hair, sleepy natural smile. " + FILM_SUFFIX
        ),
        "shots": [
            {
                "filename": "02_henley_parted.png",
                "title": "Waffle Henley Parted",
                "exclude_body_ref": False,
                "prompt": (
                    "An intimate candid morning photograph on white linen bedding. "
                    "A 26-year-old Korean woman kneeling on the mattress, unbuttoning the oatmeal waffle henley completely open. "
                    "Her bare breasts and athletic torso exposed in the bright morning sunbeams. "
                    ""
                    "Natural morning glow, authentic skin pores and freckles. " + FILM_SUFFIX
                ),
            },
            {
                "filename": "03_bed_stretch.png",
                "title": "Sunday Bed Stretch",
                "exclude_body_ref": False,
                "prompt": (
                    "A sensual candid photograph of a 26-year-old Korean woman stretching lazily on her back in bed on Sunday morning. "
                    "Topless, arms reaching above her head, showing off her natural pilates spine alignment and ribcage. "
                    "Soft golden sunbeams across the white linen sheets. " + FILM_SUFFIX
                ),
            },
        ],
    },
}

def update_weekly_schedule() -> None:
    """Appends/updates W39 drops in weekly_schedule.json."""
    schedule: List[Dict[str, Any]] = []
    if SCHEDULE_FILE.exists():
        try:
            schedule = json.loads(SCHEDULE_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"Error loading schedule: {e}")

    by_id = {item["id"]: item for item in schedule if "id" in item}

    for d_key, drop in W39_DROPS.items():
        drop_id = drop["id"]
        gallery = [drop["media_file"]] + [
            f"growth/schedule_assets/sets/{drop_id}/{shot['filename']}" for shot in drop["shots"]
        ]

        entry = {
            "id": drop_id,
            "day": drop["day"],
            "date": drop["date"],
            "week": "2026-W39",
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

    # Write back preserving order
    SCHEDULE_FILE.write_text(json.dumps(list(by_id.values()), indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓ Registered {len(W39_DROPS)} drops for 2026-W39 in weekly_schedule.json")


def generate_drops(day_filter: str = "all", force: bool = False, dry_run: bool = False) -> None:
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

    targets = list(W39_DROPS.keys()) if day_filter == "all" else [day_filter]
    for d_key in targets:
        if d_key not in W39_DROPS:
            print(f"Unknown day: {d_key}")
            continue
        drop = W39_DROPS[d_key]
        drop_id = drop["id"]
        print(f"\n{'='*70}\n  Generating 2026-W39 Drop: {drop_id} ({drop['day']})\n{'='*70}")

        # 1. Teaser Image (Shot 01)
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
    parser = argparse.ArgumentParser(description="Generate and schedule 2026-W39 Bluesky/Fanvue companion drops")
    parser.add_argument("--sync-schedule", action="store_true", help="Sync metadata into weekly_schedule.json without generating media")
    parser.add_argument("--generate", action="store_true", help="Execute image generation on Kie")
    parser.add_argument("--day", type=str, default="all", help="Target specific day (mon, tue, wed, thu, fri, sat, sun, all)")
    parser.add_argument("--force", action="store_true", help="Force overwrite of existing files")
    parser.add_argument("--dry-run", action="store_true", help="Simulate generation without spending Kie credits")
    args = parser.parse_args()

    update_weekly_schedule()

    if args.generate or args.dry_run:
        generate_drops(day_filter=args.day, force=args.force, dry_run=args.dry_run)
    else:
        print("\nSchedule synced. Pass --generate to execute image generation on Kie.")

if __name__ == "__main__":
    main()
