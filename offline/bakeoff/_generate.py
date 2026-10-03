#!/usr/bin/env python3
"""
_generate.py — builds the bake-off workflow JSONs from one shared template.

Not part of the pipeline; a build script. Run it again if PROMPT, SEED,
RESOLUTION or a candidate's filenames change, so the "identical in every
respect except the model" guarantee is enforced by construction rather than
by someone hand-editing five JSON files and hoping they stayed in sync — the
exact failure mode CLAUDE.md's "ALWAYS DOUBLE CHECK WHAT YOU HAVE" section
warns about (a print of intent is not evidence of a match).

Output format: ComfyUI's API/prompt graph (node id -> {class_type, inputs}).
Import it either by dragging the .json onto the ComfyUI canvas, or via
Workflow -> Open in a build that added API-format import; both are covered
in README.md, including what to do if neither works.
"""
import json
import pathlib

HERE = pathlib.Path(__file__).parent

# ---- locked identical across every candidate, per BRIEF.md Task 2 ----------
PROMPT = ("Close-up photograph of a woman's face, straight-on, filling most "
          "of the frame from the top of her forehead to her collarbone. "
          "Mid-30s, visible skin texture and pores, faint under-eye lines, "
          "a few stray hairs escaping a loose ponytail. Indoors near a "
          "window on an overcast afternoon, soft diffuse light from one "
          "side. Neutral expression, looking directly at the camera. "
          "Shot on a full-frame camera with a sharp prime lens, natural "
          "unretouched skin, no makeup filter, no smoothing.")
NEGATIVE = ""
SEED = 20260904
WIDTH, HEIGHT = 896, 1152
STEPS = 20
SAMPLER = "euler"
SCHEDULER = "simple"


def build(unet_name, clip_name, clip_type, vae_name, cfg, prefix,
          weight_dtype="default"):
    return {
        "1": {"class_type": "UNETLoader",
              "inputs": {"unet_name": unet_name, "weight_dtype": weight_dtype}},
        "2": {"class_type": "CLIPLoader",
              "inputs": {"clip_name": clip_name, "type": clip_type,
                         "device": "default"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": vae_name}},
        "4": {"class_type": "CLIPTextEncode",
              "inputs": {"text": PROMPT, "clip": ["2", 0]}},
        "5": {"class_type": "CLIPTextEncode",
              "inputs": {"text": NEGATIVE, "clip": ["2", 0]}},
        "6": {"class_type": "EmptyLatentImage",
              "inputs": {"width": WIDTH, "height": HEIGHT, "batch_size": 1}},
        "7": {"class_type": "KSampler",
              "inputs": {"seed": SEED, "steps": STEPS, "cfg": cfg,
                         "sampler_name": SAMPLER, "scheduler": SCHEDULER,
                         "denoise": 1.0, "model": ["1", 0],
                         "positive": ["4", 0], "negative": ["5", 0],
                         "latent_image": ["6", 0]}},
        "8": {"class_type": "VAEDecode",
              "inputs": {"samples": ["7", 0], "vae": ["3", 0]}},
        "9": {"class_type": "SaveImage",
              "inputs": {"images": ["8", 0], "filename_prefix": prefix}},
    }


CANDIDATES = {
    # id: file, present-on-disk, clip file, clip type, vae file, cfg, prefix
    "01_flux2_klein_9b.json": dict(
        unet_name="flux-2-klein-9b-fp8.safetensors",
        clip_name="qwen_3_8b_fp8mixed.safetensors", clip_type="flux2",
        vae_name="flux2-vae.safetensors", cfg=1.0,
        prefix="bakeoff_klein9b"),
    "02_krea2_turbo.json": dict(
        unet_name="krea2_turbo_fp8_scaled.safetensors",
        clip_name="qwen3vl_4b_fp8_scaled.safetensors", clip_type="krea2",
        vae_name="qwen_image_vae.safetensors", cfg=1.0,
        prefix="bakeoff_krea2turbo"),
    "03_flux2_klein_4b.json": dict(
        unet_name="flux-2-klein-4b-fp8.safetensors",
        clip_name="qwen_3_8b_fp8mixed.safetensors", clip_type="flux2",
        vae_name="flux2-vae.safetensors", cfg=1.0,
        prefix="bakeoff_klein4b"),
    "04_qwen_image.json": dict(
        unet_name="qwen_image_fp8_e4m3fn.safetensors",
        clip_name="qwen_2.5_vl_7b_fp8_scaled.safetensors",
        clip_type="qwen_image",
        vae_name="qwen_image_vae.safetensors", cfg=4.0,
        prefix="bakeoff_qwenimage"),
    "05_z_image_turbo.json": dict(
        unet_name="z_image_turbo_bf16.safetensors",
        clip_name="qwen_3_4b.safetensors", clip_type="z_image",
        vae_name="ae.safetensors", cfg=1.0,
        prefix="bakeoff_zimageturbo"),
}

FIX_SPECKLE = dict(
    unet_name="krea2_turbo_fp8_scaled.safetensors",
    clip_name="qwen3vl_4b_fp8_scaled.safetensors", clip_type="krea2",
    vae_name="qwen_image_vae.safetensors",  # was Wan2_1_VAE_fp32.safetensors
    cfg=1.0, prefix="fix_speckle_test")


def main():
    for fname, cfg in CANDIDATES.items():
        graph = build(**cfg)
        (HERE / fname).write_text(json.dumps(graph, indent=2), encoding="utf-8")
        print(f"  wrote {fname}")

    fixed = build(**FIX_SPECKLE)
    (HERE / "00_fix_speckle" / "krea2_turbo_fixed_vae.json").write_text(
        json.dumps(fixed, indent=2), encoding="utf-8")
    print("  wrote 00_fix_speckle/krea2_turbo_fixed_vae.json")


if __name__ == "__main__":
    main()
