"""
model_schemas.py — per-model input shapes and quality tiers for Kie.ai.

Built from verified working examples. Two things vary between model families
and both have bitten us already:

  1. the ACCEPTED VALUES of aspect_ratio (3:4 broke Seedream and Flux)
  2. the name of the quality/resolution knob -- Seedream calls it `quality`
     with basic=1K / high=2K, while Nano Banana and Flux use `resolution`
     with "1K"/"2K"/"4K" strings.

Comparing models at different output sizes is not a fair test, so TIERS lets
the bake-off level everything at the same target and the runner ask for what
it actually wants.
"""
from __future__ import annotations

# Seedream's `nsfw_checker`. Per the published schema: setting it False
# DISABLES Kie's content filtering and returns raw model output. It arrived in
# this file from the example payload, not from a deliberate decision -- so it
# is named here rather than buried in a dict. For clinical clothed reference
# frames there is no reason to disable filtering; set True (or delete the key
# to take the service default) unless you have decided otherwise on purpose.
NSFW_CHECKER = False

# tier -> the input fragment that requests it, per model.
# {} means "this model has no knob we know of; it uses its default".
TIERS: dict[str, dict[str, dict]] = {
    "gpt-image-2-text-to-image": {
        # Undocumented in Kie's example, but --probe confirmed the API accepts
        # a `resolution` string. NOTE: accepted != honoured -- verify_sizes()
        # checks the actual pixels of what comes back.
        "1k": {"resolution": "1K"},
        "2k": {"resolution": "2K"},
        "4k": {"resolution": "4K"},
    },
    "nano-banana-pro": {
        "1k": {"resolution": "1K"},
        "2k": {"resolution": "2K"},
        "4k": {"resolution": "4K"},
    },
    "seedream/5-pro-text-to-image": {
        "1k": {"quality": "basic"},     # basic -> 1K
        "2k": {"quality": "high"},      # high  -> 2K
    },
    "qwen3/pro-text-to-image": {
        "1k": {"resolution": "1K"},
        "2k": {"resolution": "2K"},
    },
    "qwen3/pro-image-to-image": {
        "1k": {"resolution": "1K"},
        "2k": {"resolution": "2K"},
    },
    "seedream/5-pro-image-to-image": {
        "1k": {"quality": "basic"},
        "2k": {"quality": "high"},
    },
    "gpt-image-2-image-to-image": {
        "1k": {"resolution": "1K"},
        "2k": {"resolution": "2K"},
        "4k": {"resolution": "4K"},
    },
    "gpt-image-2-5-sunburst-image-to-image": {
        "1k": {"resolution": "1K"},
        "2k": {"resolution": "2K"},
        "4k": {"resolution": "4K"},
    },
    "flux-2/pro-text-to-image": {
        "1k": {"resolution": "1K"},
        "2k": {"resolution": "2K"},
    },
}

SCHEMAS: dict[str, dict] = {
    "gpt-image-2-text-to-image": {
        "extras": {"output_format": "png"},
        "ref_key": "image_urls",          # unverified — probe before relying on it
        "ratios": ["1:1", "3:4", "2:3", "9:16"],
        "notes": "highest documented ceiling (max edge 3840)",
    },
    "nano-banana-pro": {
        "extras": {"output_format": "png"},
        "ref_key": "image_input",         # VERIFIED: an array, not image_urls
        "ratios": ["1:1", "3:4", "9:16"],
        "notes": "4K reachable via Kie without the Google Pro subscription",
    },
    "seedream/5-pro-text-to-image": {
        "extras": {"output_format": "png", "nsfw_checker": NSFW_CHECKER},
        "ref_key": None,
        # 3:4 confirmed working in production. The earlier ["1:1"] was an
        # artifact of the probe testing the preferred ratio first and stopping.
        "ratios": ["3:4", "1:1", "2:3", "3:2", "4:3", "16:9", "9:16", "21:9"],
        "notes": "quality REQUIRED: basic=1K, high=2K; prompt max 5000 chars",
    },
    "flux-2/pro-text-to-image": {
        "extras": {"nsfw_checker": NSFW_CHECKER},
        "ref_key": None,
        "ratios": ["1:1"],
        "notes": "no output_format in the documented example",
    },
    "gpt-image-2-image-to-image": {
        "extras": {"output_format": "png"},
        # WAS "image_urls", INFERRED AND WRONG. The documented field is
        # `input_urls`. Every reference we sent went under a key the model does
        # not read, so it generated a plausible woman from the text alone —
        # realistic, and not her. Verified against Kie's published schema.
        "ref_key": "input_urls",
        "ratios": ["3:4", "1:1", "2:3", "9:16", "4:3", "3:2", "16:9", "21:9"],
        "notes": "input_urls (NOT image_urls); prompt max 20000",
    },
    "gpt-image-2-5-sunburst-image-to-image": {
        "extras": {"background": "auto"},
        "ref_key": "input_urls",
        "ratios": ["auto", "1:1", "16:27", "16:9", "21:9", "2:3", "27:16", "3:2", "3:4", "4:3", "8:9", "9:16", "9:8"],
        "notes": "gpt-image-2.5 Sunburst i2i. input_urls; prompt max 20000; 1K/2K/4K resolution",
    },
    # The reference-conditioned sibling of the bake-off winner. This is what
    # phases a/b/c run on: up to 10 reference images via image_urls.
    "qwen3/pro-text-to-image": {
        # Sibling of the i2i endpoint. Its field names are ASSUMED to match
        # (image_size, resolution, prompt_extend) because they belong to the
        # same family — NOT read from a published schema. gpt-image-2 was
        # assumed the same way and it cost a whole batch: its i2i field is
        # input_urls, not image_urls. Print the payload and check it before
        # spending. No ref_key: text-to-image takes no references.
        "extras": {"output_format": "png", "prompt_extend": False,
                   "nsfw_checker": NSFW_CHECKER},
        "ref_key": None,
        "ratio_key": "image_size",
        "ratios": ["1:1", "16:9", "21:9", "2:3", "3:2", "3:4", "4:3", "9:16"],
        "notes": "UNVERIFIED field names — mirrored from the i2i sibling",
    },
    "qwen3/pro-image-to-image": {
        # prompt_extend DEFAULTS TO TRUE and rewrites the prompt before the
        # model sees it. Every rule in this project lives in exact wording, so
        # leaving it on discards all of it. Off, always.
        # negative_prompt is a real field here — negations can finally live
        # somewhere other than the positive text.
        "extras": {"output_format": "png", "prompt_extend": False,
                   "nsfw_checker": NSFW_CHECKER},
        "ref_key": "image_urls",        # up to 3, 10 MB each
        "ratio_key": "image_size",      # NOT aspect_ratio
        "ratios": ["1:1", "16:9", "21:9", "2:3", "3:2", "3:4", "4:3", "9:16"],
        "notes": "i2i only, no t2i sibling; seed available for reproducible A/B",
    },
    "seedream/5-pro-image-to-image": {
        "extras": {"output_format": "png", "nsfw_checker": NSFW_CHECKER},
        "ref_key": "image_urls",
        "ratios": ["3:4", "1:1", "2:3", "3:2", "4:3", "16:9", "9:16", "21:9"],
        "notes": "image_urls required; 30 MB each; jpeg/png/webp; prompt max 5000",
    },
}

# Seedream's full documented enum. Note 4:5 is NOT in it — an earlier guess.
RATIO_FALLBACKS = ["1:1", "3:4", "2:3", "3:2", "4:3", "16:9", "9:16", "21:9"]

# Rough per-image USD for the budget guard only. Never sent upstream.
TIER_PRICE = {"1k": 0.04, "2k": 0.08, "4k": 0.16}


def tier_fragment(model: str, tier: str) -> dict:
    """The input fragment requesting `tier` from `model`. Falls back to the
    highest tier the model supports rather than silently asking for one it
    does not have."""
    t = TIERS.get(model, {})
    if tier in t:
        return dict(t[tier])
    for lower in ("4k", "2k", "1k"):
        if lower in t:
            return dict(t[lower])
    return {}


def supported_tier(model: str, tier: str) -> str:
    t = TIERS.get(model, {})
    if tier in t:
        return tier
    for lower in ("4k", "2k", "1k"):
        if lower in t:
            return lower
    return tier


def build_input(model: str, prompt: str, ratio: str = "1:1",
                tier: str = "2k", refs: list[str] | None = None,
                overrides: dict | None = None) -> dict:
    """Assemble the `input` object for one model at a target quality tier."""
    s = SCHEMAS.get(model, {"extras": {}, "ref_key": None})
    # Qwen calls this field `image_size`. A hardcoded key silently drops
    # the ratio and returns whatever the model defaults to.
    inp: dict = {"prompt": prompt, s.get("ratio_key", "aspect_ratio"): ratio}
    inp.update(s.get("extras", {}))
    inp.update(tier_fragment(model, tier))
    if refs:
        key = s.get("ref_key")
        if not key:
            raise ValueError(
                f"{model} has no known reference-image field -- "
                f"use a model with one, or probe for it")
        inp[key] = list(refs)
    if overrides:
        inp.update(overrides)
    return inp
