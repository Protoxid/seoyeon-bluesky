#!/usr/bin/env python3
"""
generate_w38_drops.py — Generation engine for 2026-W38 Bluesky teasers and Fanvue companion sets.

Week 2026-W38: Mon 14 Sep to Sun 20 Sep 2026.
Generated via Kie Seedream 5 Pro (tier: 1k, aspect: 3:4).

Strict compliance rules:
1. FANVUE FIRST by 15 minutes.
2. DELIVER PROMISE: set matches teaser garment, setting, lighting, hair.
3. TIER 2 public teaser (opaque, suggestive), TIER 3 paywall companion set (intimate, 18+).
4. TATTOO RULE:
   - Clothed torso: exclude_body_ref=True, zero mention of "tattoo" in prompt.
   - Bare ribcage: condition on [a1_front, c5_relax_front, tattoo_crop], explicit placement sentence:
     "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference."
5. SINGLE STRAP: slips and camisoles explicitly specify "one clean, single delicate spaghetti strap on each shoulder (exactly one strap per shoulder, no duplicate or double straps)".
6. ZERO BODY PROMPTING: natural pilates physique from references, no "tiny waist" or "hourglass".
7. PROMPT AGE: 26 in prompts, 25 in copy.
8. VOICE: dry, concrete, lowercase, full stops, zero exclamation marks, zero hype/sales words, ?c=fv-4 on CTA.
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
try:
    from PIL import Image
except ImportError:
    Image = None


def ensure_min_1080(image_path: pathlib.Path, min_w: int = 1080) -> None:
    """Ensure image is at least min_w width while preserving aspect ratio, satisfying QC gate."""
    if Image is None or not image_path.exists():
        return
    try:
        with Image.open(image_path) as im:
            w, h = im.size
            if w < min_w:
                target_w = min_w
                target_h = int(round(min_w * h / w))
                resized = im.resize((target_w, target_h), Image.LANCZOS)
                resized.save(image_path)
    except Exception as e:
        print(f"  [!] Warning during ensure_min_1080 on {image_path}: {e}")

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

# Common prompt suffix ensuring authentic sensor texture and identity fidelity
FILM_SUFFIX = (
    "Shot on iPhone 15 Pro: flat natural contrast, low saturation, fine filmic shadow noise, "
    "natural matte skin texture with visible real pores and faint pale freckles across the nose bridge and inner cheeks, "
    "light amber-hazel irises with dark limbal ring and pronounced aegyo-sal, honey-blonde gradient balayage hair, "
    "clean hands with exactly five natural relaxed fingers, zero CGI plastic, authentic candid snapshot."
)

W38_DROPS: Dict[str, Dict[str, Any]] = {
    "mon": {
        "id": "w38_mon_ribbed_tank",
        "day": "Monday",
        "date": "2026-09-14",
        "slot": "morning",
        "time_kst": "10:30",
        "fanvue_publish_at": "2026-09-14T01:15:00.000Z",
        "tier": 2,
        "fanvue_tier": 3,
        "label": "suggestive",
        "platforms": ["bluesky", "fanvue"],
        "media_file": "growth/schedule_assets/w38_mon_ribbed_tank.png",
        "main_text": "drank the coffee before it cooled down for once. quiet morning in the flat.",
        "reply_text": "the rest of the morning is up on my private wall... come say hi 🖤 https://www.fanvue.com/syeon.hn?c=fv-4",
        "fanvue_text": "quiet monday morning. the light comes in sideways before 10am. left the rest of this set here for you.",
        "teaser_prompt": (
            "An authentic candid morning photograph in a minimalist open kitchen corner. "
            "A 26-year-old Korean woman sitting comfortably on a high minimalist wooden barstool by a poured concrete breakfast counter. "
            "She is wearing a heather grey finely ribbed cotton racerback crop tank top and matching soft charcoal lounge boy-shorts. "
            "Her honey-balayage hair is pinned up in a loose, high messy textured bun with wispy tendrils escaping naturally at the temples and jawline. "
            "One small gold huggie earring in each lobe. "
            "She holds a warm ceramic coffee mug with both hands, looking down with a relaxed, sleepy, candid morning expression and faint private smirk. "
            "Neutral, unrecognisable background with warm morning daylight filtering sideways across smooth plaster walls. "
            + FILM_SUFFIX
        ),
        "teaser_exclude_body_ref": True,
        "shots": [
            {
                "filename": "02_tank_roll.png",
                "title": "Tank Rolled Up Showing Bare Ribcage",
                "exclude_body_ref": False,
                "prompt": (
                    "An intimate candid morning photograph in the same minimalist open kitchen corner by the poured concrete counter. "
                    "A 26-year-old Korean woman seated on the wooden barstool in soft morning sunlight. "
                    "Her honey-balayage hair remains in the high messy bun with soft stray tendrils framing her face. "
                    "One hand is raised casually behind her neck adjusting the hair clip with five clean relaxed fingers; "
                    "her heather grey ribbed racerback tank has been pulled up to just below the breast line, exposing her toned midriff and bare left ribcage. "
                    "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
                    "Natural athletic Pilates physique, calm direct gaze into the lens with a quiet half-smile. "
                    "Neutral softly blurred architectural background with morning amber sunbeams. "
                    + FILM_SUFFIX
                ),
            },
            {
                "filename": "03_counter_stretch.png",
                "title": "Kitchen Counter Morning Intimacy",
                "exclude_body_ref": False,
                "prompt": (
                    "A sensual, alluring morning photograph in the minimalist kitchen nook. "
                    "A 26-year-old Korean woman leaning gently back against the neutral poured concrete island, body angled 3/4 toward the camera. "
                    "Her heather grey ribbed tank top hangs loosely ungathered, exposing her bare stomach and bare left ribcage. "
                    "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
                    "Her loose messy bun has relaxed with honey-amber strands grazing her neck and bare clavicles. "
                    "One hand rests flat on the concrete counter with five natural fingers; her other arm rests gently across her hip. "
                    "Soft intimate morning gaze with relaxed parted lips. Neutral out-of-focus background with quiet morning sunlight. "
                    + FILM_SUFFIX
                ),
            },
        ],
    },

    "tue": {
        "id": "w38_tue_olive_camisole",
        "day": "Tuesday",
        "date": "2026-09-15",
        "slot": "evening",
        "time_kst": "17:30",
        "fanvue_publish_at": "2026-09-15T08:15:00.000Z",
        "tier": 2,
        "fanvue_tier": 3,
        "label": "suggestive",
        "platforms": ["bluesky", "fanvue"],
        "media_file": "growth/schedule_assets/w38_tue_olive_camisole.png",
        "main_text": "sun goes down faster this week. twenty minutes of this light and then it is gone.",
        "reply_text": "slipped out of it once the sun went down. private roll is waiting 🍯 https://www.fanvue.com/syeon.hn?c=fv-4",
        "fanvue_text": "golden hour in the corner of the room. slipped the strap off as the light faded. private set for you.",
        "teaser_prompt": (
            "An authentic golden hour photograph in a neutral plaster window alcove with sheer ivory linen curtains. "
            "A 26-year-old Korean woman seated sideways on a low neutral daybench, bathed in warm amber late-afternoon sunlight. "
            "She is wearing a deep olive-green silk-satin camisole with one clean, single delicate spaghetti strap on each shoulder (exactly one strap per shoulder, no duplicate or double straps) "
            "and matching olive silk lounge shorts. "
            "Her honey-balayage hair is styled in a low sleek parted chignon with soft curtain bangs framing her face. "
            "One small gold huggie in each lobe. "
            "Her hands rest lightly on her knee with five clean natural fingers, looking out through the sheer linen curtain with a quiet contemplative gaze. "
            "Neutral, unrecognisable soft-focus background with warm golden sunset light raking across plaster. "
            + FILM_SUFFIX
        ),
        "teaser_exclude_body_ref": True,
        "shots": [
            {
                "filename": "02_strap_drop.png",
                "title": "Olive Camisole Strap Slid Off Shoulder",
                "exclude_body_ref": False,
                "prompt": (
                    "An alluring, intimate golden hour photograph in the neutral plaster alcove. "
                    "A 26-year-old Korean woman on the low neutral bench, turning toward the camera as the golden hour fades to warm amber. "
                    "The single delicate spaghetti strap on her left shoulder has slipped down smoothly onto her upper arm, "
                    "loosening the deep olive-green silk camisole and revealing her bare left shoulder, clavicle, and bare left ribcage. "
                    "The right shoulder retains its single delicate spaghetti strap (exactly one strap). "
                    "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
                    "Her low chignon has softened with loose amber strands grazing her neck. "
                    "Clean hands with five natural fingers resting softly on the bench fabric. "
                    "Intimate half-smile looking directly at the viewer, warm golden sidelight. "
                    + FILM_SUFFIX
                ),
            },
            {
                "filename": "03_golden_recline.png",
                "title": "Golden Hour Recline on Cushions",
                "exclude_body_ref": False,
                "prompt": (
                    "A sensual intimate photograph in the window alcove at twilight. "
                    "A 26-year-old Korean woman reclining back against soft neutral linen cushions, angled 3/4 to the lens. "
                    "The deep olive-green silk camisole is draped loosely across her chest with the left strap fully down, "
                    "leaving her bare left flank, stomach, and bare left ribcage beautifully illuminated by the last golden rays of sun. "
                    "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
                    "Her honey-balayage hair falls loosely around her bare shoulders. "
                    "Subtle conspiratorial half-smile with soft bedroom eyes. "
                    "Neutral, unidentifiable warm shadow background with sheer ivory curtain blur. "
                    + FILM_SUFFIX
                ),
            },
        ],
    },

    "wed": {
        "id": "w38_wed_poplin_shirt",
        "day": "Wednesday",
        "date": "2026-09-16",
        "slot": "night",
        "time_kst": "23:15",
        "fanvue_publish_at": "2026-09-16T14:00:00.000Z",
        "tier": 2,
        "fanvue_tier": 3,
        "label": "suggestive",
        "platforms": ["bluesky", "fanvue"],
        "media_file": "growth/schedule_assets/w38_wed_poplin_shirt.png",
        "main_text": "still awake at 11pm. put the kettle on twice and forgot both times.",
        "reply_text": "stayed up late in the dark. full set is on my private feed... come say hi 🖤 https://www.fanvue.com/syeon.hn?c=fv-4",
        "fanvue_text": "11pm and couldn't sleep. unbuttoned the shirt once the room got warm. whole midnight set for you.",
        "teaser_prompt": (
            "An authentic candid late-night photograph in a minimalist reading nook. "
            "A 26-year-old Korean woman curled comfortably into a low dark oak lounge armchair under the focused warm pool of a low reading lamp. "
            "She is wearing an oversized crisp white poplin collared button-down shirt, buttoned loosely at the midriff, falling casually over bare legs. "
            "Her honey-balayage hair is held up in a tortoiseshell claw clip with soft textured waves tumbling around her collarbones. "
            "One small gold huggie in each earlobe. "
            "She holds a white ceramic mug in both hands with clean natural fingers, knees tucked toward her, gazing thoughtfully off-camera with a quiet half-smile. "
            "Neutral, unrecognisable dark charcoal wall in soft shadow behind the armchair. "
            + FILM_SUFFIX
        ),
        "teaser_exclude_body_ref": True,
        "shots": [
            {
                "filename": "02_shirt_unbutton.png",
                "title": "Oversized Shirt Unbuttoned Showing Tattoo",
                "exclude_body_ref": False,
                "prompt": (
                    "An intimate low-light photograph in the minimalist dark oak armchair at midnight. "
                    "A 26-year-old Korean woman seated in the armchair, leaning back comfortably against the dark fabric. "
                    "The oversized crisp white poplin shirt is unbuttoned down the front and slipped casually off her left shoulder, "
                    "revealing her bare collarbone, bare left shoulder, and bare left ribcage. "
                    "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
                    "Her claw clip has loosened, letting honey-blonde waves spill across her right shoulder. "
                    "One hand rests along the dark wooden armrest with five relaxed natural fingers; her eyes meet the lens with an intimate, late-night gaze. "
                    "Warm directional reading lamplight carving gentle shadows against neutral dark background. "
                    + FILM_SUFFIX
                ),
            },
            {
                "filename": "03_midnight_chair.png",
                "title": "Late Night Shirt Draped Open",
                "exclude_body_ref": False,
                "prompt": (
                    "A sultry candid midnight photograph in the low oak armchair. "
                    "A 26-year-old Korean woman reclining back in the chair with knees drawn up loosely to one side. "
                    "The oversized white poplin shirt hangs completely open, draped around her forearms and shoulders like a light robe, "
                    "revealing her lean athletic pilates physique, toned stomach, and bare left ribcage. "
                    "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
                    "Tousled honey-amber waves draped over her back. "
                    "Relaxed parted lips and a soft alluring expression under the intimate warm amber reading lamp glow. "
                    "Unrecognisable neutral dark midnight ambience. "
                    + FILM_SUFFIX
                ),
            },
        ],
    },

    "thu": {
        "id": "w38_thu_silk_robe",
        "day": "Thursday",
        "date": "2026-09-17",
        "slot": "evening",
        "time_kst": "19:45",
        "fanvue_publish_at": "2026-09-17T10:30:00.000Z",
        "tier": 2,
        "fanvue_tier": 3,
        "label": "suggestive",
        "platforms": ["bluesky", "fanvue"],
        "media_file": "growth/schedule_assets/w38_thu_silk_robe.png",
        "main_text": "dusk comes early now. washed the salt off after training and put this on.",
        "reply_text": "untied the sash right after this... full mirror set on my private page 🖤 https://www.fanvue.com/syeon.hn?c=fv-4",
        "fanvue_text": "after training. shower, blush silk, and dusk light in the mirror. private set for tonight.",
        "teaser_prompt": (
            "An authentic mirror selfie in a neutral minimalist dressing corner at dusk. "
            "A 26-year-old Korean woman standing in front of a full-length leaning minimalist standing floor mirror. "
            "She holds a white iPhone 15 Pro with a plain clear transparent case at chest level, taking the mirror selfie; "
            "the phone in the reflection is the camera. Her eyeline is fixed directly on the glass reflection, not in the room. "
            "She is wearing a blush-rose washed-silk wrap robe loosely tied at the waist with a soft silk sash, draping naturally over bare legs. "
            "Her honey-balayage hair is worn down in a smooth, straight blowout tucked neatly behind both ears, showing small gold huggie earrings. "
            "Fresh clean post-shower glow on her face with subtle natural freckles across the nose bridge. "
            "Neutral, unrecognisable soft grey plastered dressing alcove with dim blue-hour twilight light outside. "
            + FILM_SUFFIX
        ),
        "teaser_exclude_body_ref": True,
        "shots": [
            {
                "filename": "02_robe_parted.png",
                "title": "Blush Silk Robe Untied in Mirror",
                "exclude_body_ref": False,
                "prompt": (
                    "An alluring intimate mirror reflection photograph in the same minimalist dressing corner. "
                    "A 26-year-old Korean woman facing the leaning floor mirror at dusk. "
                    "Her white iPhone 15 Pro rests face-up on a nearby low neutral shelf taking a timed shot. "
                    "The blush-rose silk wrap robe has been untied; she holds one edge lightly with five clean fingers, "
                    "letting the robe fall open along her left flank to reveal her bare left ribcage, toned waist, and bare hip. "
                    "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
                    "Her straight honey-amber hair cascades over her shoulders. "
                    "Her eyeline looks directly into the mirror reflection with a confident, quiet, seductive half-smile. "
                    "Neutral minimalist background with cool twilight shadows and warm interior accent glow. "
                    + FILM_SUFFIX
                ),
            },
            {
                "filename": "03_vanity_mirror.png",
                "title": "Silk Robe Draped Low at Twilight",
                "exclude_body_ref": False,
                "prompt": (
                    "A sensual candid twilight photograph in the dressing area. "
                    "A 26-year-old Korean woman turned 3/4 toward the leaning mirror, body angled so her profile and back are reflected in the glass. "
                    "The blush-rose washed-silk robe has slipped down around her elbows and hips, "
                    "leaving her bare back, shoulders, and bare left ribcage exposed to the gentle dusk ambient light. "
                    "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
                    "She looks over her shoulder toward the camera with soft alluring eyes and relaxed parted lips. "
                    "Five natural fingers resting lightly against the mirror frame. "
                    "Neutral unrecognisable plaster walls with deep twilight indigo tones. "
                    + FILM_SUFFIX
                ),
            },
        ],
    },

    "fri": {
        "id": "w38_fri_navy_slip",
        "day": "Friday",
        "date": "2026-09-18",
        "slot": "night",
        "time_kst": "22:00",
        "fanvue_publish_at": "2026-09-18T12:45:00.000Z",
        "tier": 2,
        "fanvue_tier": 3,
        "label": "suggestive",
        "platforms": ["bluesky", "fanvue"],
        "media_file": "growth/schedule_assets/w38_fri_navy_slip.png",
        "main_text": "friday night. turned the main lights off at eight.",
        "reply_text": "quiet weekend ahead. private feed is updated for tonight... link is here 🖤 https://www.fanvue.com/syeon.hn?c=fv-4",
        "fanvue_text": "friday night in navy silk. turned off the ceiling lights and stayed right here. whole weekend set for you.",
        "teaser_prompt": (
            "An authentic moody Friday night photograph on a low minimalist dark velvet platform lounger. "
            "A 26-year-old Korean woman seated on the edge of the dark velvet lounger, leaning slightly forward with elbows resting on her knees. "
            "She is wearing a midnight navy bias-cut silk slip dress with one clean, single delicate spaghetti strap on each shoulder (exactly one strap per shoulder, no duplicate or double straps). "
            "Her honey-balayage hair is styled with a deep side part and soft brushed-out Hollywood waves cascading luxuriously over her right shoulder. "
            "One small gold huggie earring in each lobe. "
            "Her hands are lightly clasped between her knees with ten clean natural relaxed fingers. "
            "She looks straight into the camera lens with a calm, alluring, direct gaze and subtle closed-lip smile. "
            "Neutral, unrecognisable dark minimalist interior with warm indirect floor lighting creating soft golden highlights on navy silk. "
            + FILM_SUFFIX
        ),
        "teaser_exclude_body_ref": True,
        "shots": [
            {
                "filename": "02_slip_slide.png",
                "title": "Navy Silk Slip Slipped Off Left Shoulder",
                "exclude_body_ref": False,
                "prompt": (
                    "An alluring, intimate low-light photograph on the low velvet platform lounger on Friday night. "
                    "A 26-year-old Korean woman reclining sideways against deep velvet cushions, propped on her right elbow. "
                    "The single delicate spaghetti strap on her left shoulder has slid down onto her upper arm, "
                    "draping the midnight navy silk loosely across her chest and revealing her bare left shoulder, clavicle, and bare left ribcage. "
                    "The right shoulder retains its single clean delicate spaghetti strap (exactly one strap). "
                    "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
                    "Her side-parted honey-balayage waves spill across the dark cushion. "
                    "Slow, sensual, conspiratorial half-smile with bedroom eyes. "
                    "Neutral unrecognisable background with warm moody night illumination. "
                    + FILM_SUFFIX
                ),
            },
            {
                "filename": "03_midnight_recline.png",
                "title": "Midnight Recline on Velvet Lounger",
                "exclude_body_ref": False,
                "prompt": (
                    "A stunning, seductive low-light photograph on the dark velvet lounger late Friday night. "
                    "A 26-year-old Korean woman reclining back on the velvet platform, body angled 3/4 to the lens. "
                    "The midnight navy silk slip is draped low across her hips, exposing her toned athletic midriff, bare stomach, and bare left ribcage. "
                    "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
                    "One hand rests softly beside her head with five natural relaxed fingers; the other arm rests gently across her lower waist. "
                    "Intimate parted lips, warm honey-hazel gaze into the lens. "
                    "Neutral soft-focus midnight sanctuary with rich warm ambient rim lighting. "
                    + FILM_SUFFIX
                ),
            },
        ],
    },

    "sat": {
        "id": "w38_sat_black_lace",
        "day": "Saturday",
        "date": "2026-09-19",
        "slot": "night",
        "time_kst": "23:45",
        "fanvue_publish_at": "2026-09-19T14:30:00.000Z",
        "tier": 2,
        "fanvue_tier": 3,
        "label": "suggestive",
        "platforms": ["bluesky", "fanvue"],
        "media_file": "growth/schedule_assets/w38_sat_black_lace.png",
        "main_text": "almost midnight. tried this on and didn't feel like taking it off yet.",
        "reply_text": "kept it on a little longer. the full saturday set is waiting for you 🖤 https://www.fanvue.com/syeon.hn?c=fv-4",
        "fanvue_text": "saturday midnight in black lace. took these before getting into bed. the full private roll for you.",
        "teaser_prompt": (
            "An authentic candid late-night photograph in a minimalist dry dark ceramic-tiled vanity area. "
            "A 26-year-old Korean woman standing leaning casually against a matte dark charcoal slate wall. "
            "She is wearing a delicate sheer black French lace bralette with fine floral embroidery and matching high-waist black briefs. "
            "Her arms are folded loosely under her chest, concealing her lower ribcage with natural posture, clean hands with five natural fingers each. "
            "Her honey-balayage hair has a tousled, wet-look textured wave pushed naturally back from her forehead. "
            "One small gold huggie earring in each ear. "
            "She looks toward the camera with a subtle, playful smirk, arched brow, and quiet midnight confidence. "
            "Neutral, unrecognisable dark slate backdrop with a single warm low spotlight creating moody cinematic contrast. "
            + FILM_SUFFIX
        ),
        "teaser_exclude_body_ref": True,
        "shots": [
            {
                "filename": "02_lace_unclasp.png",
                "title": "Black Lace Bralette Loosened at Ribcage",
                "exclude_body_ref": False,
                "prompt": (
                    "An alluring, intimate photograph against the matte charcoal slate wall at midnight. "
                    "A 26-year-old Korean woman turning 3/4 toward the lens, her body angled to highlight her left side. "
                    "One hand is reaching back lightly to unhook the sheer black lace bralette, loosening the lace cup away from her left flank, "
                    "revealing her bare left ribcage, toned athletic curves, and smooth skin. "
                    "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
                    "Her wet-look textured waves frame her glowing cheekbones. "
                    "Direct intimate gaze into the lens with parted lips and a soft conspiratorial half-smile. "
                    "Warm low amber spotlight casting soft dramatic shadows on neutral slate. "
                    + FILM_SUFFIX
                ),
            },
            {
                "filename": "03_slate_intimate.png",
                "title": "Seated on Slate Edge Midnight Boudoir",
                "exclude_body_ref": False,
                "prompt": (
                    "A breathtaking, intimate midnight photograph in the dark slate vanity sanctuary. "
                    "A 26-year-old Korean woman seated on a low dark slate ledge with knees pulled loosely to the side. "
                    "The black lace bralette hangs loosely untied around her upper arms, "
                    "leaving her bare chest, toned stomach, and bare left ribcage in intimate warm spotlight. "
                    "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
                    "Both hands rest naturally on the slate with clean natural fingers. "
                    "Bedroom eyes looking down and back toward the camera with a quiet, alluring expression. "
                    "Neutral unrecognisable dark midnight atmosphere with fine filmic sensor texture. "
                    + FILM_SUFFIX
                ),
            },
        ],
    },

    "sun": {
        "id": "w38_sun_waffle_henley",
        "day": "Sunday",
        "date": "2026-09-20",
        "slot": "morning",
        "time_kst": "09:15",
        "fanvue_publish_at": "2026-09-20T00:00:00.000Z",
        "tier": 2,
        "fanvue_tier": 3,
        "label": "suggestive",
        "platforms": ["bluesky", "fanvue"],
        "media_file": "growth/schedule_assets/w38_sun_waffle_henley.png",
        "main_text": "sunday morning. haven't looked at my phone since seven. brewed barley tea.",
        "reply_text": "lazy sunday set is on my private feed... come keep me company this morning 🖤 https://www.fanvue.com/syeon.hn?c=fv-4",
        "fanvue_text": "sunday morning. tea, waffle knit, and nowhere to be until tomorrow. left this whole morning set for you.",
        "teaser_prompt": (
            "An authentic cozy morning photograph in a neutral tatami and woven sisal rug lounge nook with low floor cushions. "
            "A 26-year-old Korean woman seated cross-legged on a natural woven floor cushion, softly lit by overcast morning daylight. "
            "She is wearing a slouchy ivory waffle-knit henley lounge top slipping off her right shoulder and matching soft ribbed lounge shorts. "
            "Her honey-balayage hair is styled in a loose, messy side braid draped casually over her left shoulder with soft tendrils around her ears. "
            "One small gold huggie in each lobe. "
            "She cradles a warm small ceramic tea bowl in both hands with clean natural fingers, "
            "looking up with a sleepy, gentle, serene morning smile. "
            "Neutral, unrecognisable soft beige plastered walls and quiet sunday morning tranquility. "
            + FILM_SUFFIX
        ),
        "teaser_exclude_body_ref": True,
        "shots": [
            {
                "filename": "02_henley_lift.png",
                "title": "Ivory Henley Raised in Morning Stretch",
                "exclude_body_ref": False,
                "prompt": (
                    "An intimate candid morning photograph in the woven rug lounge nook. "
                    "A 26-year-old Korean woman seated on the floor cushion, stretching both arms languidly overhead with clean open fingers. "
                    "The slouchy ivory waffle-knit henley rises naturally with the stretch, pulling up to underbust "
                    "and exposing her toned flat stomach and bare left ribcage. "
                    "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
                    "Her loose side braid rests against her collarbone. "
                    "She tilts her head back slightly with eyes closed in a peaceful morning stretch, then glances down with a slow warm smirk. "
                    "Neutral unrecognisable soft daylight background with woven textures. "
                    + FILM_SUFFIX
                ),
            },
            {
                "filename": "03_tatami_stretch.png",
                "title": "Lazy Sunday Morning Floor Recline",
                "exclude_body_ref": False,
                "prompt": (
                    "A sensual, relaxing candid morning photograph in the quiet lounge nook. "
                    "A 26-year-old Korean woman reclining back across the soft floor cushions on the woven sisal rug, legs stretched comfortably. "
                    "The ivory waffle-knit henley is unbuttoned down the front and draped open, "
                    "revealing her natural athletic pilates physique, bare torso, and bare left ribcage. "
                    "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
                    "One hand rests under her head on the cushion with five clean fingers; the other rests casually on her hip. "
                    "Soft intimate bedroom eyes looking into the camera lens with a sleepy half-smile. "
                    "Neutral, unrecognisable soft overcast daylight filling the serene space. "
                    + FILM_SUFFIX
                ),
            },
        ],
    },
}


def run_generation(day_filter: str = "all", force: bool = False, dry_run: bool = False) -> None:
    days = list(W38_DROPS.keys()) if day_filter == "all" else [day_filter.lower()]

    kie = None
    refs_bare: List[str] = []
    refs_clothed: List[str] = []

    if not dry_run:
        load_key(PERSONA_DIR)
        key = os.environ.get("KIE_API_KEY", "")
        if not key:
            sys.exit("Error: KIE_API_KEY not found in environment or .env / kie_key.txt")
        kie = Kie(key)
        print(f"[*] Connected to Kie. Available credit: {kie.credit()}")
        print("[*] Uploading/caching reference masters...")

        a1_url = kie.upload(MASTER_A1)
        c5_url = kie.upload(MASTER_C5) if MASTER_C5.exists() else None
        tattoo_url = kie.upload(MASTER_TATTOO) if MASTER_TATTOO.exists() else None

        refs_clothed = [a1_url]
        refs_bare = [a1_url]
        if c5_url:
            refs_bare.append(c5_url)
        if tattoo_url:
            refs_bare.append(tattoo_url)

        print(f"[+] Clothed references: {len(refs_clothed)} (face master only)")
        print(f"[+] Bare ribcage references: {len(refs_bare)} (face + relaxed body + tattoo crop)")

    for d_key in days:
        drop = W38_DROPS.get(d_key)
        if not drop:
            print(f"[!] Warning: Unknown day key '{d_key}'. Skipping.")
            continue

        drop_id = drop["id"]
        day_name = drop["day"]
        print("\n" + "=" * 80)
        print(f"  DROP: {day_name.upper()} ({drop_id}) — {drop['date']}")
        print(f"  Slot: {drop['slot']} | Bsky: {drop['time_kst']} KST | Fanvue: {drop['fanvue_publish_at']}")
        print("=" * 80)

        # 1. Teaser image (01_teaser)
        teaser_path = ROOT_DIR / drop["media_file"]
        teaser_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"\n[Shot 01 / Teaser]: {teaser_path.name}")
        print(f"  Tier: {drop['tier']} (Public suggestive teaser)")
        print(f"  Exclude body ref: {drop['teaser_exclude_body_ref']}")
        print(f"  Prompt: {drop['teaser_prompt'][:120]}...")

        if teaser_path.exists() and not force:
            print(f"  [EXISTS] {teaser_path.name} already exists. Skipping (use --force to overwrite).")
        else:
            if dry_run:
                print(f"  [DRY-RUN] Would generate teaser via Seedream 5 Pro (tier: 1k, aspect: 3:4).")
            else:
                active_refs = refs_clothed if drop["teaser_exclude_body_ref"] else refs_bare
                print(f"  [*] Submitting teaser to Kie (Seedream 5 Pro, 1k, refs={len(active_refs)})...", flush=True)
                t0 = time.time()
                urls = kie.generate(
                    prompt=drop["teaser_prompt"],
                    aspect="3:4",
                    tier="1k",
                    image_urls=active_refs,
                    model="seedream/5-pro-image-to-image",
                )
                if urls:
                    n = kie.download(urls[0], teaser_path)
                    ensure_min_1080(teaser_path)
                    print(f"  [SUCCESS] Downloaded and formatted {teaser_path.name} ({teaser_path.stat().st_size // 1024} KB) in {time.time() - t0:.1f}s")
                else:
                    print(f"  [ERROR] No URL returned for teaser {drop_id}")

        # 2. Companion shots (02 and 03)
        set_dir = SETS_DIR / drop_id
        set_dir.mkdir(parents=True, exist_ok=True)

        for i, shot in enumerate(drop["shots"], 2):
            shot_file = set_dir / shot["filename"]
            print(f"\n[Shot {i:02d} / Paywall]: {shot['filename']} — {shot['title']}")
            print(f"  Tier: {drop['fanvue_tier']} (Paywall intimate companion)")
            print(f"  Exclude body ref: {shot['exclude_body_ref']}")
            print(f"  Prompt: {shot['prompt'][:120]}...")

            if shot_file.exists() and not force:
                print(f"  [EXISTS] {shot_file.name} already exists. Skipping (use --force to overwrite).")
            else:
                if dry_run:
                    print(f"  [DRY-RUN] Would generate {shot['filename']} via Seedream 5 Pro (tier: 1k, aspect: 3:4).")
                else:
                    active_refs = refs_clothed if shot["exclude_body_ref"] else refs_bare
                    print(f"  [*] Submitting shot {i:02d} to Kie (Seedream 5 Pro, 1k, refs={len(active_refs)})...", flush=True)
                    t0 = time.time()
                    urls = kie.generate(
                        prompt=shot["prompt"],
                        aspect="3:4",
                        tier="1k",
                        image_urls=active_refs,
                        model="seedream/5-pro-image-to-image",
                    )
                    if urls:
                        n = kie.download(urls[0], shot_file)
                        ensure_min_1080(shot_file)
                        print(f"  [SUCCESS] Downloaded and formatted {shot_file.name} ({shot_file.stat().st_size // 1024} KB) in {time.time() - t0:.1f}s")
                    else:
                        print(f"  [ERROR] No URL returned for {shot['filename']}")

    # 3. Update weekly_schedule.json
    if not dry_run:
        update_weekly_schedule()


def update_weekly_schedule() -> None:
    """Register all 7 drops in weekly_schedule.json with full fields."""
    print("\n[*] Updating weekly_schedule.json...")
    schedule: List[Dict[str, Any]] = []
    if SCHEDULE_FILE.exists():
        try:
            schedule = json.loads(SCHEDULE_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[!] Warning reading schedule: {e}")

    # Build map of existing entries by id
    by_id = {item.get("id"): item for item in schedule if item.get("id")}

    for d_key, drop in W38_DROPS.items():
        drop_id = drop["id"]
        gallery = [
            drop["media_file"],
            f"growth/schedule_assets/sets/{drop_id}/02_{drop['shots'][0]['filename'].split('_', 1)[-1]}",
            f"growth/schedule_assets/sets/{drop_id}/03_{drop['shots'][1]['filename'].split('_', 1)[-1]}",
        ]

        entry = {
            "id": drop_id,
            "day": drop["day"],
            "date": drop["date"],
            "week": "2026-W38",
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
            "fanvue_audience": "subscribers",
            "fanvue_publish_at": drop["fanvue_publish_at"],
            "fanvue_text": drop["fanvue_text"],
            "fanvue_gallery_files": gallery,
        }

        by_id[drop_id] = entry

    # Write back preserved order (keep non-w38 first, then w38)
    non_w38 = [item for item in schedule if not str(item.get("id", "")).startswith("w38_")]
    w38_entries = [by_id[drop["id"]] for drop in W38_DROPS.values()]
    new_schedule = non_w38 + w38_entries

    SCHEDULE_FILE.write_text(json.dumps(new_schedule, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[+] weekly_schedule.json successfully updated with {len(w38_entries)} drops for week 2026-W38.")


def main():
    parser = argparse.ArgumentParser(description="Generate 2026-W38 drops for Bluesky + Fanvue")
    parser.add_argument("--day", type=str, default="all", help="mon, tue, wed, thu, fri, sat, sun, or all")
    parser.add_argument("--force", action="store_true", help="Force regenerate existing images")
    parser.add_argument("--dry-run", action="store_true", help="Simulate run and print prompts without calling Kie")
    args = parser.parse_args()

    run_generation(day_filter=args.day, force=args.force, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
