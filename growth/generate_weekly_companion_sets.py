#!/usr/bin/env python3
"""
generate_weekly_companion_sets.py — Multi-Shot Companion Reveal Prompts for Fanvue.

Use this file to review, customize, and generate the progressive reveal shots (02 and 03)
for each weekly drop. When published on Fanvue, each drop becomes a 3-shot carousel
delivering on what was teased on Bluesky.

COMMANDS TO RUN:
    python growth/generate_weekly_companion_sets.py --dry-run               # Preview all prompts & filenames
    python growth/generate_weekly_companion_sets.py --day thu              # Generate Thursday companion shots
    python growth/generate_weekly_companion_sets.py --day fri              # Generate Friday companion shots
    python growth/generate_weekly_companion_sets.py --day sat              # Generate Saturday companion shots
    python growth/generate_weekly_companion_sets.py --day sun              # Generate Sunday companion shots
    python growth/generate_weekly_companion_sets.py --day all              # Generate all remaining sets

CANON ADHERENCE & ANTI-DEFECT INVARIANTS:
    1. ZERO BODY PROMPTING: Rely 100% on master references (c5_relax_front, a1_front) for her authentic
       natural Pilates physique. Never prompt 'sculpted waist', 'tiny waist', or 'curves' (causes wasp-waist AI artifacts).
    2. REALISTIC CAMERA LOGIC:
       - If she's holding her phone: ONLY in a mirror selfie (phone takes reflection).
       - If both hands free: Propped self-timer on table/shelf (camera is off-frame).
       - If front selfie: Single extended arm (phone is the lens, off-frame).
    3. PROP CANON: White iPhone 15 Pro with plain clear transparent case.
    4. TATTOO: Minimalist botanical sprig on her left ribcage.
    5. FACIAL EXPRESSIONS: Varied micro-expressions (amused smirk, subtle lip bite, looking at skyline, thoughtful half-smile).
    6. BACKGROUND VARIATION: Shaded rooftop terrace, open kitchen bar, minimalist marble bath, sunlit balcony garden.
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

GROWTH_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = GROWTH_DIR.parent
PERSONA_DIR = PROJECT_ROOT / "personas" / "seoyeon"
SCHEDULE_FILE = GROWTH_DIR / "schedule_assets" / "weekly_schedule.json"

sys.path.insert(0, str(PERSONA_DIR))
from kie_api import Kie, load_key

MASTER_A1 = PERSONA_DIR / "master" / "a" / "a1_front.png"
MASTER_C5 = PERSONA_DIR / "master" / "c" / "c5_relax_front.png"
MASTER_TATTOO = PERSONA_DIR / "master" / "c" / "tattoo_crop.png"


# ==============================================================================
# COMPANION SET PROMPTS (EDIT THESE PROMPTS FREELY BELOW)
# ==============================================================================

SETS_CONFIG: Dict[str, Dict[str, Any]] = {

    # --------------------------------------------------------------------------
    # TUESDAY: tue_cozy_knit (Teaser: Chunky oatmeal knit sweater in the flat)
    # --------------------------------------------------------------------------
    "tue": {
        "drop_id": "tue_cozy_knit",
        "day": "Tuesday",
        "folder": GROWTH_DIR / "schedule_assets" / "sets" / "tue_cozy_knit",
        "teaser_file": "growth/schedule_assets/sets/tue_cozy_knit/01_knit_cozy.png",
        "shots": [
            {
                "filename": "02_knit_slide.png",
                "title": "Knit Sliding Off Shoulders (Living Room Couch)",
                "hairstyle": "Loose slept-in honey-balayage waves falling over one shoulder",
                "expression": "Warm candid amused smile looking slightly downward",
                "setting": "Minimalist warm Seongsu apartment on a rainy evening, warm floor lamp light, rain on dark window",
                "camera_logic": "Propped on coffee table self-timer, one hand resting on couch cushion, other on lap holding white iPhone 15 Pro",
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
                "tier": "1k"
            },
            {
                "filename": "03_lace_lounge.png",
                "title": "Black Lace Lingerie Lounge (Rug & Couch)",
                "hairstyle": "Messy textured waves draped over back",
                "expression": "Subtle, quiet, intimate half-smile looking directly at the viewer",
                "setting": "Cozy Seongsu flat late at night, neutral wool floor rug, oatmeal knit draped on couch behind her",
                "camera_logic": "Phone resting face-up on low table beside glass of water, self-timer snapshot",
                "prompt": (
                    "An alluring candid low-light photograph in a cozy modern Seongsu flat late at night. "
                    "A 26-year-old Korean woman seated comfortably on a neutral wool floor rug with legs curled loosely to one side. "
                    "She has completely slipped out of her sweater; the oatmeal knit is draped casually on the couch behind her. "
                    "She is wearing a delicate black French lace bralette and matching lace boy-shorts. "
                    "A delicate minimalist botanical sprig tattoo is visible on her left ribcage. "
                    "Relaxed neck and soft natural shoulders with zero tension. "
                    "One hand rests on the floor beside her supporting her relaxed posture with five clean natural fingers; "
                    "her other arm rests casually across her knee. Her phone—a white iPhone 15 Pro with clear case—rests face-up on the low table beside a glass of water. "
                    "The background is an unrecognizable, soft-focus wash of warm amber lamplight, cream linen, and quiet midnight atmosphere. "
                    "Shot on iPhone 15 Pro: natural low-light sensor grain, organic tones, authentic matte skin with visible natural pores, zero 3D gloss, candid unedited photograph."
                ),
                "aspect": "3:4",
                "tier": "1k"
            }
        ]
    },

    # --------------------------------------------------------------------------
    # WEDNESDAY: wed_towel_steam (Teaser: Post-shower towel mirror in steamy bath)
    # --------------------------------------------------------------------------
    "wed": {
        "drop_id": "wed_towel_steam",
        "day": "Wednesday",
        "folder": GROWTH_DIR / "schedule_assets" / "sets" / "wed_towel_steam",
        "teaser_file": "growth/schedule_assets/wed_towel_steam.png",
        "shots": [
            {
                "filename": "02_vanity_towel_drop.png",
                "title": "Dressing Vanity Towel Loosened (Post-Bath Sanctuary)",
                "hairstyle": "Damp hair combed back with water droplets glinting, loose soft strands at nape",
                "expression": "Thoughtful, relaxed glance toward the vanity mirror reflection with a faint amused smirk",
                "setting": "Warm minimalist dressing nook with blonde oak vanity table, soft warm glow from frosted globe lamp, clean waffle cotton robe nearby",
                "camera_logic": "Propped on vanity shelf next to amber glass skincare bottles on self-timer",
                "prompt": (
                    "An intimate candid photograph in a minimalist warm apartment dressing nook in Seongsu late on a Wednesday night. "
                    "A 26-year-old Korean woman seated comfortably on a low wooden vanity stool after a long warm shower. "
                    "Her honey-balayage hair is damp and gently slicked back, with delicate wisps framing her jaw and dewy collarbones. "
                    "Her plush white bath towel has loosened completely and is gathered down in her lap around her hips and thighs, leaving her upper body, bare shoulders, breasts, waist, and entire ribcage completely bare. "
                    "On her left ribcage, running vertically on bare skin, is the delicate fine-line botanical sprig tattoo shown in the reference. "
                    "She is looking toward the wooden-framed vanity mirror with a soft, introspective half-smile. "
                    "One hand rests naturally on the smooth wooden vanity edge with five clean relaxed fingers; her other hand rests on the towel on her lap. "
                    "Warm diffused ambient light from a globe table lamp casts gentle shadows on the neutral lime-wash wall. "
                    "Shot on iPhone 15 Pro: natural low-light sensor noise, authentic matte skin texture with visible real pores, zero CGI airbrushing."
                ),
                "aspect": "3:4",
                "tier": "1k"
            },
            {
                "filename": "03_silk_robe_midnight.png",
                "title": "Silk Robe by Night Window (Balcony Breezeway)",
                "hairstyle": "Air-drying loose waves tumbling naturally over bare shoulder",
                "expression": "Looking back over her shoulder with an intimate, drowsy, knowing gaze and softly parted lips",
                "setting": "Dim bedroom near open balcony door, sheer curtain swaying in the midnight Seoul breeze, city lights glittering faintly outside",
                "camera_logic": "Self-timer propped on bedroom credenza, 28mm candid lens",
                "prompt": (
                    "An alluring candid late-night photograph in a dark Seongsu bedroom with the balcony door cracked open. "
                    "A 26-year-old Korean woman standing in the soft midnight breeze, holding a lightweight dark slate-silk kimono robe loosely around her frame. "
                    "One side of the silk robe has casually fallen off her shoulder, revealing her bare back and side, her natural Pilates waist, "
                    "and the delicate botanical sprig tattoo on her left ribcage. "
                    "Her honey-balayage hair is air-drying in loose, textured, damp waves falling over one shoulder. "
                    "She looks back over her shoulder toward the camera with soft, drowsy, playful eyes and parted lips. "
                    "Her hands are loosely holding the silk belt ties at her waist with natural relaxed fingers. "
                    "The sheer white curtain sways gently behind her, framing the soft distant city lights of nocturnal Seoul. "
                    "Shot on iPhone 15 Pro: authentic low-light texture, rich organic midnight tones, real skin with visible pores, candid unedited photograph."
                ),
                "aspect": "3:4",
                "tier": "1k"
            }
        ]
    },

    # --------------------------------------------------------------------------
    # THURSDAY: thu_silk_slip (Teaser: Champagne silk slip in the flat at golden hour)
    # --------------------------------------------------------------------------
    "thu": {
        "drop_id": "thu_silk_slip",
        "day": "Thursday",
        "folder": GROWTH_DIR / "schedule_assets" / "sets" / "thu_silk_slip",
        "teaser_file": "growth/schedule_assets/thu_silk_slip.png",
        "shots": [
            {
                "filename": "02_rooftop_sunset.png",
                "title": "Sunset on Private Rooftop Terrace (Outdoor)",
                "hairstyle": "Messy high updo secured with a matte tortoiseshell claw clip, loose soft tendrils blowing in the breeze",
                "expression": "Head tilted back slightly, looking out over the city skyline with a serene, amused half-smile",
                "setting": "Outdoor private rooftop terrace in Seongsu at sunset golden hour, weathered teak deck, large terracotta planters with olive shrubs, lavender and orange sunset sky over Seoul skyline",
                "camera_logic": "Propped self-timer on a low teak terrace table, both hands resting naturally on the warm ledge",
                "prompt": (
                    "An authentic golden hour candid photograph on a private wooden rooftop terrace overlooking Seoul at dusk. "
                    "A 26-year-old Korean woman with a healthy natural athletic Pilates physique, relaxed spine and smooth natural shoulders. "
                    "Her honey-balayage hair is swept up in a casual messy high updo secured with a tortoiseshell claw clip, "
                    "with soft loose tendrils framing her cheekbones and gently moving in the late-summer warm evening breeze. "
                    "She is wearing a delicate solid plain champagne silk slip dress with thin straps, softly backlit by the warm setting sun. "
                    "The dress is tailored from pure smooth solid champagne satin silk with a completely plain, clean, unprinted surface with zero designs, zero graphics, and zero markings on the solid silk fabric. "
                    "Her head is turned slightly toward the skyline with a calm, amused half-smile and relaxed eyes. "
                    "Both hands rest naturally and comfortably on the smooth wooden terrace railing with exactly five clean relaxed fingers each. "
                    "The background shows the soft-focus expanse of Seongsu rooftops and the warm orange and lavender twilight sky. "
                    "Shot on iPhone 15 Pro: natural low contrast, realistic matte skin with visible delicate pores, "
                    "zero artificial CGI sheen, authentic candid filmic snapshot."
                ),
                "aspect": "3:4",
                "tier": "1k",
                "exclude_body_ref": True
            },
            {
                "filename": "03_terrace_twilight.png",
                "title": "Terrace Lounge at Twilight (Semi-Outdoor)",
                "hairstyle": "Claw clip removed, loose wind-tossed waves falling softly over collarbones",
                "expression": "Playful side-eye toward the camera with lips softly parted in quiet intimacy",
                "setting": "Terrace outdoor daybed at dusk, minimalist glowing paper lantern on the deck, deep indigo twilight sky",
                "camera_logic": "Self-timer on low side table beside a glass of iced herbal tea, one arm resting across knee",
                "prompt": (
                    "An alluring candid twilight photograph on a private outdoor terrace lounge at blue hour. "
                    "A 26-year-old Korean woman lounging comfortably on a low charcoal linen outdoor cushion, body angled so her left side faces the camera. "
                    "Her honey-balayage hair is loose in wind-tumbled textured waves draped over one bare shoulder and nude breast. "
                    "She has slipped out of the silk dress, revealing her natural athletic Pilates proportions, healthy natural relaxed waist, and smooth abdomen. "
                    "On her left ribcage, running vertically just below the breast line, is the small, delicate fine-line botanical sprig tattoo shown in the reference. "
                    "She looks toward the camera with a subtle playful side-eye and relaxed parted lips. "
                    "One hand rests casually on the cushion supporting her posture with clean natural fingers; "
                    "her other arm rests across her knee. A soft warm glow from a small cordless lantern illuminates her face against the deep indigo evening sky. "
                    "Shot on iPhone 15 Pro: natural low-light grain, authentic organic skin texture with real pores, zero 3D plastic gloss."
                ),
                "aspect": "3:4",
                "tier": "1k"
            }
        ]
    },

    # --------------------------------------------------------------------------
    # FRIDAY: fri_morning_window (Teaser: Morning breeze video, slow weekend ahead)
    # --------------------------------------------------------------------------
    "fri": {
        "drop_id": "fri_morning_window",
        "day": "Friday",
        "folder": GROWTH_DIR / "schedule_assets" / "sets" / "fri_morning_window",
        "teaser_file": "growth/schedule_assets/fri_morning_window.mp4",
        "shots": [
            {
                "filename": "02_kitchen_counter.png",
                "title": "Kitchen Island Morning Tea (Modern Interior)",
                "hairstyle": "Sleek low ponytail tied with a simple thin black ribbon, clean parted front framing jawline",
                "expression": "Resting chin on hand with a faint wry, intelligent smirk, looking directly into lens",
                "setting": "Contemporary minimalist kitchen with matte black terrazzo island counter, warm pendant light, morning sun slicing through sheer blinds, ceramic kettle",
                "camera_logic": "Propped against a ceramic mug on the kitchen counter",
                "prompt": (
                    "A stunning candid morning photograph in a bright minimalist apartment kitchen in Seongsu. "
                    "A 26-year-old Korean woman with a healthy natural athletic posture sitting on a high wooden barstool at an island counter. "
                    "Her honey-balayage hair is tied back in a neat low ponytail with a simple black ribbon, a few loose strands tucked behind her ear. "
                    "She is wearing an oversized unbuttoned crisp white cotton shirt draping loosely off one shoulder, showing her breast, "
                    "and matching boy-shorts. "
                    "Natural smooth neck and clavicles without tension. "
                    "One elbow rests on the matte terrazzo counter with her chin resting in her hand, smiling with a dry playful smirk directly at the viewer; "
                    "her other hand rests on her lap with five clean relaxed fingers. "
                    "Soft morning sunlight filters through sheer vertical blinds casting graphic shadows on the neutral plaster wall behind her. "
                    "Shot on iPhone 15 Pro: crisp natural sharpness, matte skin texture with visible real pores, zero airbrushing or plastic CGI."
                ),
                "aspect": "3:4",
                "tier": "1k"
            },
            {
                "filename": "03_balcony_greenery.png",
                "title": "Sunlit Balcony Garden (Outdoor / Greenery)",
                "hairstyle": "Ponytail undone, effortless airy volume",
                "expression": "Eyes gently closed basking in morning sun, peaceful contented smile as breeze catches shirt",
                "setting": "Deep sheltered apartment balcony filled with lush potted plants (monstera, fig tree), bright morning air, urban greenery",
                "camera_logic": "Single extended arm selfie (23mm lens), other hand resting on balcony planter",
                "prompt": (
                    "A radiant candid outdoor morning photograph on a sunlit green balcony in Seongsu. "
                    "A 26-year-old Korean woman with natural human proportions and a relaxed Pilates posture leaning gently against a black metal balcony railing. "
                    "Surrounded by lush green potted tropical plants in terracotta pots. "
                    "Her honey-balayage hair is loose and airy, catching the morning breeze. "
                    "The unbuttoned white shirt has slipped down her arms in the morning warmth, showing her shoulders and breasts. "
                    "Her head is tilted up toward the warm morning sun with eyes softly closed and a genuine relaxed smile on her lips. "
                    "Her botanical sprig ribcage tattoo is subtly visible. "
                    "She holds her white iPhone 15 Pro with clear case in one extended arm taking an authentic high-angle front selfie, "
                    "while her other hand rests casually against a large plant pot with natural fingers. "
                    "Shot on iPhone 15 Pro: bright natural daylight, rich organic tones, real skin texture with visible pores and faint freckles."
                ),
                "aspect": "3:4",
                "tier": "1k"
            }
        ]
    },

    # --------------------------------------------------------------------------
    # SATURDAY: sat_lace_mirror (Teaser: Black lace try-on in bedroom mirror)
    # --------------------------------------------------------------------------
    "sat": {
        "drop_id": "sat_lace_mirror",
        "day": "Saturday",
        "folder": GROWTH_DIR / "schedule_assets" / "sets" / "sat_lace_mirror",
        "teaser_file": "growth/schedule_assets/sat_lace_mirror.png",
        "shots": [
            {
                "filename": "02_bathroom_marble.png",
                "title": "Midnight Stone Bathroom Mirror Selfie (Architectural Interior)",
                "hairstyle": "Messy high topknot bun with loose wisps around ears and nape of the neck",
                "expression": "Gently biting lower lip with an amused, slightly self-conscious smirk in the mirror reflection",
                "setting": "Minimalist honed gray stone and marble bathroom, frameless LED back-lit mirror, freestanding soaking tub in soft focus",
                "camera_logic": "True mirror selfie: holding white iPhone 15 Pro (clear case) at chest height taking reflection",
                "prompt": (
                    "An authentic candid mirror selfie in a luxury minimalist stone bathroom late on a Saturday night. "
                    "A 26-year-old Korean woman with an authentic natural Pilates physique, standing tall with natural posture in front of a wide illuminated bathroom mirror. "
                    "Her honey-balayage hair is gathered in a messy high topknot bun with delicate stray wisps around her neck. "
                    "She is trying on a delicate black French floral lace lingerie set with natural relaxed straps. Her free hand is holding the left side of the bra up, showing her breast. "
                    "Natural athletic waist and smooth abdomen with zero unnatural hourglass pinch or exaggerated curves. "
                    "She is holding her white iPhone 15 Pro with a plain clear transparent case with both hands at chest level to photograph her reflection in the glass, "
                    "with all fingers naturally wrapped around the phone body. "
                    "She looks at her reflection on the phone screen with an amused, shyly teasing expression, gently biting her lower lip. "
                    "Soft warm indirect illumination from behind the mirror, dark charcoal tile background. "
                    "Shot on iPhone 15 Pro: natural low-light sensor noise, authentic matte skin with visible real pores, zero CGI rendering."
                ),
                "aspect": "3:4",
                "tier": "1k"
            },
            {
                "filename": "03_midnight_linen.png",
                "title": "Midnight Bedhead Lounge on Dark Linens (Moody Bedroom)",
                "hairstyle": "Hair down, textured bedhead waves splayed on duvet",
                "expression": "Resting chin in palms, looking right into camera with sleepy, teasing, conspiratorial smile",
                "setting": "Moody midnight bedroom, dark charcoal linen sheets, single low amber reading lamp creating warm intimate pool of light",
                "camera_logic": "Propped on nightstand shelf on self-timer, 28mm lens candid perspective",
                "prompt": (
                    "An intimate candid photograph in a dimly lit modern bedroom in Seoul at midnight. "
                    "A 26-year-old Korean woman lying on her stomach across a bed with dark charcoal washed linen sheets. "
                    "Her honey-balayage hair is loose in textured, disheveled bedhead waves framing her face. "
                    "She has her elbows propped up on the mattress, resting her chin in both open hands, "
                    "smiling warmly and teasingly right into the lens with soft relaxed eyes and parted lips. "
                    "She is completely naked; her bare shoulders and clavicles are relaxed and free of tension. Her legs are spread apart, showing her vagina. "
                    "Her delicate botanical sprig tattoo is visible on her left side. "
                    "The background is a soft, dark amber blur from a single ceramic bedside lamp, creating a quiet confidential atmosphere. "
                    "Shot on iPhone 15 Pro: organic night tones, natural skin texture with visible pores, zero 3D plastic gloss, candid snapshot."
                ),
                "aspect": "3:4",
                "tier": "1k"
            }
        ]
    },

    # --------------------------------------------------------------------------
    # SUNDAY: sun_sunday_bed (Teaser: Lazy sunday morning in bed with coffee)
    # --------------------------------------------------------------------------
    "sun": {
        "drop_id": "sun_sunday_bed",
        "day": "Sunday",
        "folder": GROWTH_DIR / "schedule_assets" / "sets" / "sun_sunday_bed",
        "teaser_file": "growth/schedule_assets/sun_sunday_bed.png",
        "shots": [
            {
                "filename": "02_livingroom_stretch.png",
                "title": "Morning Bed Linen Arch (Tangled White Linens)",
                "hairstyle": "Delightfully disheveled honey-balayage morning bedhead waves splayed over white pillows",
                "expression": "Drowsy, seductive gaze looking directly into lens with softly parted lips, gently biting lower lip with quiet morning intimacy",
                "setting": "Sunlit modern Seongsu apartment bedroom, rumpled white washed linen sheets, warm golden morning sunbeams",
                "camera_logic": "Propped on bedside table on self-timer, intimate eye-level angle",
                "prompt": (
                    "An alluring, deeply intimate candid morning photograph in a sunlit modern apartment bedroom in Seongsu. "
                    "A 26-year-old Korean woman with a toned natural athletic Pilates physique reclining back across rumpled white washed linen sheets. "
                    "Her honey-balayage hair is delightfully disheveled in textured, messy morning bedhead waves splayed over the pillows. "
                    "She has playfully pulled up her heather-gray cropped top, leaving her bare breasts, smooth toned abdomen, and natural waist completely bare. "
                    "On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference. "
                    "She is propped up on her elbows with knees bent loosely, looking directly into the camera lens with a drowsy, seductive gaze and soft parted lips, gently biting her lower lip with quiet morning intimacy. "
                    "Her hands rest naturally on the duvet with clean relaxed fingers. "
                    "Warm golden morning sunlight streams through the bedroom window, casting soft warm light and long gentle shadows across her bare skin and the white bedsheets. "
                    "Shot on iPhone 15 Pro: natural morning daylight, authentic matte skin with visible delicate pores and faint freckles, zero 3D plastic gloss, raw seductive candid snapshot."
                ),
                "aspect": "3:4",
                "tier": "1k",
                "exclude_body_ref": False
            },
            {
                "filename": "03_balcony_coffee.png",
                "title": "Sunlit Bedhead Lounge on White Linens (Topless Bed Lounge)",
                "hairstyle": "Loose messy bedhead waves tumbling naturally over bare shoulders",
                "expression": "Resting chin in palms, looking right into camera with heavy-lidded bedroom eyes, a slow teasing conspiratorial half-smile, and parted lips",
                "setting": "Sun-drenched morning bedroom, white linen mattress, glowing sheer curtains in the background",
                "camera_logic": "Propped on headboard shelf on self-timer, 28mm intimate candid snapshot",
                "prompt": (
                    "A sensual, intoxicating candid morning photograph in a sunlit Seongsu bedroom. "
                    "A 26-year-old Korean woman with a healthy natural athletic Pilates physique lying on her stomach across the white linen mattress, body angled toward the camera. "
                    "Her honey-balayage hair falls in loose, messy bedhead waves framing her glowing face and bare shoulders. "
                    "She has slipped out of her top completely; the crisp white linen sheet is pulled low across her hips, leaving her bare back, shoulders, and the soft curve of her bare breasts visible. "
                    "On her left ribcage on bare skin is the delicate fine-line botanical sprig tattoo shown in the reference. "
                    "Her elbows are propped on the soft duvet with her chin resting in both open palms, looking right into the lens with bedroom eyes, a slow teasing conspiratorial half-smile, and relaxed parted lips. "
                    "Both hands have clean natural fingers gently cradling her chin and jawline. "
                    "Bright morning daylight illuminates the room, creating a glowing, intimate, private sanctuary. "
                    "Shot on iPhone 15 Pro: authentic daylight texture, organic skin tones with visible real pores, zero CGI airbrushing, stunning seductive private photograph."
                ),
                "aspect": "3:4",
                "tier": "1k",
                "exclude_body_ref": False
            }
        ]
    }
}


# ==============================================================================
# EXECUTION ENGINE
# ==============================================================================

def generate_set(day_key: str, force: bool = False, dry_run: bool = False, shot_filter: str = "all") -> None:
    config = SETS_CONFIG.get(day_key.lower())
    if not config:
        print(f"Error: Unknown day key '{day_key}'. Available: {list(SETS_CONFIG.keys())}")
        return

    drop_id = config["drop_id"]
    day_name = config["day"]
    out_dir = config["folder"]
    out_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 80)
    print(f"  PROCESSING COMPANION SET: {day_name.upper()} ({drop_id})")
    print(f"  Target Folder: {out_dir}")
    print("=" * 80)

    # Initialize Kie client if not dry-run
    kie = None
    refs = []
    if not dry_run:
        load_key(PERSONA_DIR)
        key = os.environ.get("KIE_API_KEY", "")
        if not key:
            sys.exit("Error: KIE_API_KEY not found in environment.")
        kie = Kie(key)
        print(f"[*] Available Kie credits: {kie.credit()}")
        print(f"[*] Uploading/caching reference masters...")
        a1_url = kie.upload(MASTER_A1.resolve())
        c5_url = kie.upload(MASTER_C5.resolve()) if MASTER_C5.exists() else None
        tattoo_url = kie.upload(MASTER_TATTOO.resolve()) if MASTER_TATTOO.exists() else None
        refs = [a1_url]
        if c5_url:
            refs.append(c5_url)
        if tattoo_url:
            refs.append(tattoo_url)
        print(f"[+] Active references: {len(refs)} master images (c5_relax_front, a1_front, tattoo_crop)")

    gallery_files = [config["teaser_file"]]

    for i, shot in enumerate(config["shots"], 2):
        filename = shot["filename"]
        out_path = out_dir / filename
        gallery_rel = f"growth/schedule_assets/sets/{drop_id}/{filename}"
        gallery_files.append(gallery_rel)

        # Filter specific shot if requested
        if shot_filter != "all" and shot_filter not in filename:
            continue

        print(f"\n--- Shot {i:02d}: {shot['title']} ---")
        print(f"  File:        {filename}")
        print(f"  Hairstyle:   {shot['hairstyle']}")
        print(f"  Expression:  {shot['expression']}")
        print(f"  Setting:     {shot['setting']}")
        print(f"  Camera:      {shot['camera_logic']}")
        print(f"  Prompt Preview: {shot['prompt'][:100]}...")

        if out_path.exists() and not force:
            print(f"  [EXISTS] File already rendered at {out_path.name} (use --force to regenerate)")
            continue

        tier = shot.get("tier", "1k")
        if dry_run:
            print(f"  [DRY-RUN] Would submit prompt to Kie with {tier.upper()} resolution.", flush=True)
            continue

        active_refs = [a1_url] if shot.get("exclude_body_ref", False) else refs
        if shot.get("exclude_body_ref", False):
            print(f"  [*] Clothed torso: Using face master only ({len(active_refs)} ref) to prevent tattoo bleeding onto fabric.", flush=True)
        else:
            print(f"  [*] Using {len(active_refs)} references (face + relaxed body with rib tattoo).", flush=True)

        print(f"  Submitting generation to Kie (Seedream 5 Pro, {tier.upper()})...", flush=True)
        t0 = time.time()
        urls = kie.generate(
            prompt=shot["prompt"],
            aspect=shot.get("aspect", "3:4"),
            tier=tier,
            image_urls=active_refs,
            model="seedream/5-pro-image-to-image"
        )
        if not urls:
            print(f"  [ERROR] No URL returned for {shot['filename']}", flush=True)
            continue
        n_bytes = kie.download(urls[0], out_path)
        elapsed = time.time() - t0
        print(f"  [SUCCESS] Rendered and downloaded {out_path.name} in {elapsed:.1f}s ({n_bytes // 1024} KB)", flush=True)

    # Update weekly_schedule.json to register the 3-shot gallery files
    if not dry_run and SCHEDULE_FILE.exists():
        try:
            schedule = json.loads(SCHEDULE_FILE.read_text(encoding="utf-8"))
            for d in schedule:
                if d.get("id") == drop_id:
                    d["fanvue_gallery_files"] = gallery_files
                    break
            SCHEDULE_FILE.write_text(json.dumps(schedule, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"\n[+] Updated {drop_id} gallery in weekly_schedule.json with {len(gallery_files)} shots.")
        except Exception as e:
            print(f"  [Warning] Could not update weekly_schedule.json: {e}")


def main():
    parser = argparse.ArgumentParser(description="Generate Fanvue Companion Reveal Shots for Weekly Drops")
    parser.add_argument("--day", type=str, choices=["tue", "wed", "thu", "fri", "sat", "sun", "all"], default="thu",
                        help="Which day to process (tue, wed, thu, fri, sat, sun, or all)")
    parser.add_argument("--shot", type=str, choices=["02", "03", "all"], default="all",
                        help="Only process shot '02', '03', or 'all'")
    parser.add_argument("--force", action="store_true", help="Force regenerate existing images")
    parser.add_argument("--dry-run", action="store_true", help="Preview prompts and config without spending Kie credits")
    args = parser.parse_args()

    targets = ["tue", "wed", "thu", "fri", "sat", "sun"] if args.day == "all" else [args.day]
    for target in targets:
        generate_set(target, force=args.force, dry_run=args.dry_run, shot_filter=args.shot)


if __name__ == "__main__":
    main()

