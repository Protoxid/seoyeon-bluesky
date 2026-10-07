"""
agent/visual_identity.py — Permanent Visual Identity Specification & Prompt Synthesizer.

Defines the unchanging visual canon for Han Seo-yeon to preserve identity continuity
across all OpenAI GPT Image 2.5 generations:
  - Korean ethnicity, 26 years old in prompt prompts.
  - Heart-shaped sculpted jawline, high cheekbones, large amber-hazel irises with dark limbal rings, pronounced aegyo-sal.
  - Salon balayage: deep espresso roots graduating into warm honey-blonde waves, curtain bangs.
  - 165 cm, athletic pilates-lean frame.
  - Natural everyday photography: 35mm film / iPhone candid texture, authentic lighting, no CGI plastic skin.
  - Zero men in frame, zero commercial product logos.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class VisualCanon:
    subject: str = (
        "Adult Korean woman, 26 years old, height 165 cm. "
        "Athletic pilates-lean proportions, slender waist, graceful posture. "
        "Very fair porcelain complexion with cool-neutral undertone and soft satin finish, natural skin pores."
    )
    face_and_hair: str = (
        "Refined heart-shaped face with high prominent cheekbones and cleanly defined mandibular jawline. "
        "Large wide-set eyes with double eyelids, striking light amber-hazel irises ringed by a dark limbal circle, "
        "pronounced aegyo-sal beneath lower lash line. Light dusting of 9-12 pale taupe freckles across nose bridge. "
        "Long wavy hair falling below collarbones with curtain bangs, styled in a lived-in salon balayage: "
        "deep espresso roots melting into warm amber and honey-blonde ends. "
        "One small polished gold huggie earring in each lobe."
    )
    photography_style: str = (
        "Candid authentic photography, shot on 35mm lens or modern smartphone camera. "
        "Natural available light, realistic depth of field, authentic filmic grain and color grading. "
        "NOT an AI glamour rendering, NOT airbrushed, NO plastic waxy skin, NO CGI sheen."
    )
    negative_rules: str = (
        "NO other people or men in frame, NO visible commercial logos or brand names, "
        "NO exaggerated glamour poses, NO bikini or lingerie, NO excessive makeup."
    )


VISUAL_CANON = VisualCanon()


def build_image_prompt(
    scene_description: str,
    mood: Optional[str] = None,
    is_selfie: bool = True,
) -> str:
    """
    Synthesizes a short, punchy photographic prompt for OpenAI GPT Image 2.5 on Kie.ai.
    When is_selfie=True: Identity is anchored via reference images (a1 + c5 in input_urls).
    Photorealism embraces natural imperfections, varied hairstyles, and candid everyday framing.
    When is_selfie=False: Direct 35mm film POV environmental observation.
    """
    clean_scene = scene_description.strip().rstrip(".")
    mood_str = f", {mood}" if mood else ""

    if is_selfie:
        return (
            f"Candid everyday smartphone selfie of Seo-yeon, {clean_scene}{mood_str}. "
            "Natural unposed expression, authentic everyday phone camera quality with subtle real-life imperfections, "
            "unedited, natural lighting, no studio lighting, no CGI."
        )
    else:
        # Environmental POV
        return (
            f"35mm film photograph of {clean_scene}{mood_str}. "
            "Authentic natural lighting, candid street photography, realistic texture and film grain, no people, no CGI."
        )

