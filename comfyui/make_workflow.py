import json
import os

workflow = {
  "last_node_id": 19,
  "last_link_id": 22,
  "nodes": [
    {
      "id": 1,
      "type": "UNETLoader",
      "pos": [40, 100],
      "size": [320, 82],
      "flags": {},
      "order": 0,
      "mode": 0,
      "inputs": [],
      "outputs": [
        {"name": "MODEL", "type": "MODEL", "links": [1], "shape": 3, "slot_index": 0}
      ],
      "properties": {"Node name for S&R": "UNETLoader"},
      "widgets_values": ["flux2_klein_9b_fp8.safetensors", "default"]
    },
    {
      "id": 2,
      "type": "CLIPLoader",
      "pos": [40, 230],
      "size": [320, 82],
      "flags": {},
      "order": 1,
      "mode": 0,
      "inputs": [],
      "outputs": [
        {"name": "CLIP", "type": "CLIP", "links": [2], "shape": 3, "slot_index": 0}
      ],
      "properties": {"Node name for S&R": "CLIPLoader"},
      "widgets_values": ["mistral_3_small_flux2_fp8.safetensors", "flux2"]
    },
    {
      "id": 3,
      "type": "VAELoader",
      "pos": [40, 360],
      "size": [320, 82],
      "flags": {},
      "order": 2,
      "mode": 0,
      "inputs": [],
      "outputs": [
        {"name": "VAE", "type": "VAE", "links": [7, 8, 9], "shape": 3, "slot_index": 0}
      ],
      "properties": {"Node name for S&R": "VAELoader"},
      "widgets_values": ["flux2_vae.safetensors"]
    },
    {
      "id": 4,
      "type": "LoraLoader",
      "pos": [40, 490],
      "size": [320, 126],
      "flags": {},
      "order": 3,
      "mode": 0,
      "inputs": [
        {"name": "model", "type": "MODEL", "link": 1},
        {"name": "clip", "type": "CLIP", "link": 2}
      ],
      "outputs": [
        {"name": "MODEL", "type": "MODEL", "links": [3], "shape": 3, "slot_index": 0},
        {"name": "CLIP", "type": "CLIP", "links": [4, 5], "shape": 3, "slot_index": 1}
      ],
      "properties": {"Node name for S&R": "LoraLoader"},
      "widgets_values": ["flux2_nsfw_unlock.safetensors", 0.85, 0.85]
    },
    {
      "id": 8,
      "type": "LoadImage",
      "pos": [420, 100],
      "size": [315, 314],
      "flags": {},
      "order": 4,
      "mode": 0,
      "inputs": [],
      "outputs": [
        {"name": "IMAGE", "type": "IMAGE", "links": [10], "shape": 3, "slot_index": 0},
        {"name": "MASK", "type": "MASK", "links": None, "shape": 3, "slot_index": 1}
      ],
      "properties": {"Node name for S&R": "LoadImage"},
      "widgets_values": ["seoyeon_a1_front.png", "image"]
    },
    {
      "id": 9,
      "type": "ImageScaleToTotalPixels",
      "pos": [420, 460],
      "size": [315, 82],
      "flags": {},
      "order": 5,
      "mode": 0,
      "inputs": [
        {"name": "image", "type": "IMAGE", "link": 10}
      ],
      "outputs": [
        {"name": "IMAGE", "type": "IMAGE", "links": [11], "shape": 3, "slot_index": 0}
      ],
      "properties": {"Node name for S&R": "ImageScaleToTotalPixels"},
      "widgets_values": ["bicubic", 1.0]
    },
    {
      "id": 10,
      "type": "VAEEncode",
      "pos": [420, 590],
      "size": [315, 60],
      "flags": {},
      "order": 6,
      "mode": 0,
      "inputs": [
        {"name": "pixels", "type": "IMAGE", "link": 11},
        {"name": "vae", "type": "VAE", "link": 7}
      ],
      "outputs": [
        {"name": "LATENT", "type": "LATENT", "links": [13], "shape": 3, "slot_index": 0}
      ],
      "properties": {"Node name for S&R": "VAEEncode"},
      "widgets_values": []
    },
    {
      "id": 12,
      "type": "LoadImage",
      "pos": [780, 100],
      "size": [315, 314],
      "flags": {},
      "order": 7,
      "mode": 0,
      "inputs": [],
      "outputs": [
        {"name": "IMAGE", "type": "IMAGE", "links": [14], "shape": 3, "slot_index": 0},
        {"name": "MASK", "type": "MASK", "links": None, "shape": 3, "slot_index": 1}
      ],
      "properties": {"Node name for S&R": "LoadImage"},
      "widgets_values": ["seoyeon_c5_relax.png", "image"]
    },
    {
      "id": 13,
      "type": "ImageScaleToTotalPixels",
      "pos": [780, 460],
      "size": [315, 82],
      "flags": {},
      "order": 8,
      "mode": 0,
      "inputs": [
        {"name": "image", "type": "IMAGE", "link": 14}
      ],
      "outputs": [
        {"name": "IMAGE", "type": "IMAGE", "links": [15], "shape": 3, "slot_index": 0}
      ],
      "properties": {"Node name for S&R": "ImageScaleToTotalPixels"},
      "widgets_values": ["bicubic", 1.0]
    },
    {
      "id": 14,
      "type": "VAEEncode",
      "pos": [780, 590],
      "size": [315, 60],
      "flags": {},
      "order": 9,
      "mode": 0,
      "inputs": [
        {"name": "pixels", "type": "IMAGE", "link": 15},
        {"name": "vae", "type": "VAE", "link": 8}
      ],
      "outputs": [
        {"name": "LATENT", "type": "LATENT", "links": [17], "shape": 3, "slot_index": 0}
      ],
      "properties": {"Node name for S&R": "VAEEncode"},
      "widgets_values": []
    },
    {
      "id": 5,
      "type": "CLIPTextEncode",
      "pos": [1140, 100],
      "size": [400, 180],
      "flags": {},
      "order": 10,
      "mode": 0,
      "inputs": [
        {"name": "clip", "type": "CLIP", "link": 4}
      ],
      "outputs": [
        {"name": "CONDITIONING", "type": "CONDITIONING", "links": [6], "shape": 3, "slot_index": 0}
      ],
      "properties": {"Node name for S&R": "CLIPTextEncode"},
      "widgets_values": [
        "A raw, intimate, candid flash photograph of the Korean woman shown in the reference images (image 1 face, image 2 body). In a modern dimly lit Seongsu Seoul apartment bedroom at 1am, wearing an unbuttoned oversized white linen shirt falling off her shoulder, natural skin texture, subtle freckles and skin pores, natural parted dark hair, direct phone flash reflection in mirror, realistic iPhone 15 Pro photo aesthetics, film grain, sensual fanvue exclusive."
      ]
    },
    {
      "id": 6,
      "type": "CLIPTextEncode",
      "pos": [1140, 320],
      "size": [400, 110],
      "flags": {},
      "order": 11,
      "mode": 0,
      "inputs": [
        {"name": "clip", "type": "CLIP", "link": 5}
      ],
      "outputs": [
        {"name": "CONDITIONING", "type": "CONDITIONING", "links": [19], "shape": 3, "slot_index": 0}
      ],
      "properties": {"Node name for S&R": "CLIPTextEncode"},
      "widgets_values": [
        "cgi, 3d render, plastic skin, doll, anime, cartoon, airbrushed, bad anatomy, deformed fingers, extra limbs, oversaturated, blurry, watermark"
      ]
    },
    {
      "id": 7,
      "type": "FluxGuidance",
      "pos": [1140, 470],
      "size": [315, 60],
      "flags": {},
      "order": 12,
      "mode": 0,
      "inputs": [
        {"name": "conditioning", "type": "CONDITIONING", "link": 6}
      ],
      "outputs": [
        {"name": "CONDITIONING", "type": "CONDITIONING", "links": [12], "shape": 3, "slot_index": 0}
      ],
      "properties": {"Node name for S&R": "FluxGuidance"},
      "widgets_values": [3.5]
    },
    {
      "id": 11,
      "type": "Flux2ReferenceLatent",
      "pos": [1140, 570],
      "size": [315, 60],
      "flags": {},
      "order": 13,
      "mode": 0,
      "inputs": [
        {"name": "conditioning", "type": "CONDITIONING", "link": 12},
        {"name": "latent", "type": "LATENT", "link": 13}
      ],
      "outputs": [
        {"name": "CONDITIONING", "type": "CONDITIONING", "links": [16], "shape": 3, "slot_index": 0}
      ],
      "properties": {"Node name for S&R": "Flux2ReferenceLatent"},
      "widgets_values": []
    },
    {
      "id": 15,
      "type": "Flux2ReferenceLatent",
      "pos": [1140, 670],
      "size": [315, 60],
      "flags": {},
      "order": 14,
      "mode": 0,
      "inputs": [
        {"name": "conditioning", "type": "CONDITIONING", "link": 16},
        {"name": "latent", "type": "LATENT", "link": 17}
      ],
      "outputs": [
        {"name": "CONDITIONING", "type": "CONDITIONING", "links": [18], "shape": 3, "slot_index": 0}
      ],
      "properties": {"Node name for S&R": "Flux2ReferenceLatent"},
      "widgets_values": []
    },
    {
      "id": 16,
      "type": "EmptyLatentImage",
      "pos": [1580, 100],
      "size": [315, 106],
      "flags": {},
      "order": 15,
      "mode": 0,
      "inputs": [],
      "outputs": [
        {"name": "LATENT", "type": "LATENT", "links": [20], "shape": 3, "slot_index": 0}
      ],
      "properties": {"Node name for S&R": "EmptyLatentImage"},
      "widgets_values": [896, 1152, 1]
    },
    {
      "id": 17,
      "type": "KSampler",
      "pos": [1580, 250],
      "size": [315, 262],
      "flags": {},
      "order": 16,
      "mode": 0,
      "inputs": [
        {"name": "model", "type": "MODEL", "link": 3},
        {"name": "positive", "type": "CONDITIONING", "link": 18},
        {"name": "negative", "type": "CONDITIONING", "link": 19},
        {"name": "latent_image", "type": "LATENT", "link": 20}
      ],
      "outputs": [
        {"name": "LATENT", "type": "LATENT", "links": [21], "shape": 3, "slot_index": 0}
      ],
      "properties": {"Node name for S&R": "KSampler"},
      "widgets_values": [42, "randomize", 25, 1.0, "euler", "simple", 1.0]
    },
    {
      "id": 18,
      "type": "VAEDecode",
      "pos": [1580, 560],
      "size": [315, 60],
      "flags": {},
      "order": 17,
      "mode": 0,
      "inputs": [
        {"name": "samples", "type": "LATENT", "link": 21},
        {"name": "vae", "type": "VAE", "link": 9}
      ],
      "outputs": [
        {"name": "IMAGE", "type": "IMAGE", "links": [22], "shape": 3, "slot_index": 0}
      ],
      "properties": {"Node name for S&R": "VAEDecode"},
      "widgets_values": []
    },
    {
      "id": 19,
      "type": "SaveImage",
      "pos": [1940, 100],
      "size": [350, 450],
      "flags": {},
      "order": 18,
      "mode": 0,
      "inputs": [
        {"name": "images", "type": "IMAGE", "link": 22}
      ],
      "outputs": [],
      "properties": {"Node name for S&R": "SaveImage"},
      "widgets_values": ["Fanvue_Seoyeon_Flux2"]
    }
  ],
  "links": [
    [1, 1, 0, 4, 0, "MODEL"],
    [2, 2, 0, 4, 1, "CLIP"],
    [3, 4, 0, 17, 0, "MODEL"],
    [4, 4, 1, 5, 0, "CLIP"],
    [5, 4, 1, 6, 0, "CLIP"],
    [6, 5, 0, 7, 0, "CONDITIONING"],
    [7, 3, 0, 10, 1, "VAE"],
    [8, 3, 0, 14, 1, "VAE"],
    [9, 3, 0, 18, 1, "VAE"],
    [10, 8, 0, 9, 0, "IMAGE"],
    [11, 9, 0, 10, 0, "IMAGE"],
    [12, 7, 0, 11, 0, "CONDITIONING"],
    [13, 10, 0, 11, 1, "LATENT"],
    [14, 12, 0, 13, 0, "IMAGE"],
    [15, 13, 0, 14, 0, "IMAGE"],
    [16, 11, 0, 15, 0, "CONDITIONING"],
    [17, 14, 0, 15, 1, "LATENT"],
    [18, 15, 0, 17, 1, "CONDITIONING"],
    [19, 6, 0, 17, 2, "CONDITIONING"],
    [20, 16, 0, 17, 3, "LATENT"],
    [21, 17, 0, 18, 0, "LATENT"],
    [22, 18, 0, 19, 0, "IMAGE"]
  ],
  "groups": [
    {
      "title": "1. FLUX.2 Model & NSFW LoRA Loaders",
      "bounding": [20, 40, 360, 600],
      "color": "#3f789e",
      "font_size": 22
    },
    {
      "title": "2. Seoyeon Canonical References (Native Multi-Ref)",
      "bounding": [400, 40, 710, 650],
      "color": "#a15822",
      "font_size": 22
    },
    {
      "title": "3. Prompt Conditioning & Reference Injection Chain",
      "bounding": [1120, 40, 430, 720],
      "color": "#3b8254",
      "font_size": 22
    },
    {
      "title": "4. Generation (Euler/Simple, 896x1152) & Save",
      "bounding": [1560, 40, 750, 600],
      "color": "#783f9e",
      "font_size": 22
    }
  ],
  "config": {},
  "extra": {},
  "version": 0.4
}

out_path = r"c:\AI-Project - Copia\comfyui\flux2_seoyeon_multiref_workflow.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(workflow, f, indent=2)

print(f"Successfully generated ComfyUI workflow JSON: {out_path}")
