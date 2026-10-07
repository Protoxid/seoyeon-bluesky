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
    Synthesizes a complete, identity-locked image prompt for OpenAI GPT Image 2.5 on Kie.ai.
    Explicitly instructs the model to preserve the reference face from input_urls[0].
    Enforces authentic self-captured perspective (selfie or mirror selfie) so that Seo-yeon,
    living alone in Seoul, is naturally the one taking the photograph.
    """
    mood_str = f"Mood: {mood}. " if mood else ""

    identity_lock = (
        "CRITICAL IDENTITY REQUIREMENT: The subject MUST be the exact same individual shown in the reference image (input_urls[0]). "
        "Strictly reproduce her identical facial features, facial bone structure, almond amber-hazel irises with dark limbal rings, "
        "pronounced aegyo-sal, cheekbones, clean mandibular jawline, subtle freckles on nose bridge, and long wavy espresso-to-honey balayage hair. "
        "Do NOT invent a different face; preserve the reference face faithfully."
    )

    shot_framing = (
        "Shot Framing & Perspective: Authentic smartphone front-facing camera selfie taken by Han Seo-yeon herself at arm's length. "
        "Natural arm angle extending slightly toward the lower edge or corner holding the phone. "
        "Candid eye-level or slight high-angle front-camera framing. Natural, unposed everyday self-portrait. "
        "NOT a studio photoshoot, NO external photographer."
        if is_selfie and "mirror" not in scene_description.lower()
        else ""
    )

    prompt = (
        f"{identity_lock} "
        f"Subject: {VISUAL_CANON.subject} "
        f"{VISUAL_CANON.face_and_hair} "
        f"{shot_framing} "
        f"Scene & Setting: {scene_description}. "
        f"{mood_str}"
        f"Style: {VISUAL_CANON.photography_style} "
        f"Strict constraints: {VISUAL_CANON.negative_rules}"
    )
    return " ".join(prompt.split())
