# FLUX.2 ComfyUI Workflow for Seoyeon (Native Multi-Reference + NSFW)

This directory contains the complete ComfyUI workflow files and automation scripts to generate photorealistic, identity-consistent NSFW/suggestive images of **Seoyeon** using **FLUX.2** on an **RTX 5060 Ti (16 GB VRAM)**.

---

## 1. VRAM Reality & Model Recommendations (5060 Ti 16 GB)

> [!CAUTION]
> **Do NOT download the raw 35 GB `flux2_dev.safetensors`!**
> FLUX.2 [dev] is a massive **32-billion parameter** architecture. The raw weights (~35 GB in bf16 / ~32 GB in fp8) cannot fit into 16 GB VRAM. Attempting to load it will force ComfyUI to offload half the model into your system RAM, leading to 10+ minute generation times or outright Out-Of-Memory (OOM) crashes.

To get fast (15–30s) generation on your **RTX 5060 Ti 16 GB**, use either:
1. **FLUX.2 [klein] 9B (fp8)**: Retains FLUX.2's **native multi-reference consistency**, but distilled into a 9B architecture that fits comfortably in ~13–14 GB VRAM.
2. **FLUX.1 [dev] (fp8)**: The 12B model (`~11.9 GB`), fits natively with 4 GB of headroom for LoRAs and has the largest NSFW unlock library on Civitai.

| Component | Recommended Model File (16 GB VRAM) | Download Source | Destination in ComfyUI |
|---|---|---|---|
| **Diffusion Model (FLUX.2)** | `flux2_klein_9b_fp8.safetensors` *(or `flux2_klein_4b_fp8.safetensors`)* | HuggingFace (`black-forest-labs/FLUX.2-klein`) | `ComfyUI/models/diffusion_models/` |
| **Diffusion Model (FLUX.1 Alternative)** | `flux1-dev-fp8.safetensors` *(or GGUF `flux1-dev-Q8_0.gguf`)* | HuggingFace / Civitai | `ComfyUI/models/diffusion_models/` |
| **Text Encoder (for FLUX.2)** | `mistral_3_small_flux2_fp8.safetensors` | HuggingFace / Civitai | `ComfyUI/models/text_encoders/` |
| **Text Encoders (for FLUX.1)** | `t5xxl_fp8_e4m3fn.safetensors` + `clip_l.safetensors` | HuggingFace / ComfyUI | `ComfyUI/models/clip/` |
| **VAE** | `flux2_vae.safetensors` *(or `ae.safetensors`)* | HuggingFace | `ComfyUI/models/vae/` |
| **NSFW Unlock LoRA** | `flux2_nsfw_unlock.safetensors` *(or FLUX.1 `aidmaNSFWunlock`)* | Civitai | `ComfyUI/models/loras/` |

---

## 2. Reference Images Setup

FLUX.2 uses **native multi-reference conditioning** without needing external PuLID or IP-Adapter nodes. 

Copy Seoyeon's canonical reference shots into `ComfyUI/input/`:
* **Reference 1 (Front Face Canon)**: `personas/seoyeon/master/a/a1_front.png` → rename to `seoyeon_a1_front.png`
* **Reference 2 (Body & Physique Canon)**: `personas/seoyeon/master/c/c5_relax_front.png` → rename to `seoyeon_c5_relax.png`

*(Or simply use the Python automation script below, which uploads them automatically via API).*

---

## 3. How to Use the Workflow

### Method A: ComfyUI Web Interface (Drag & Drop)
1. Launch ComfyUI (e.g. `run_nvidia_gpu.bat`).
2. Drag and drop `flux2_seoyeon_multiref_workflow.json` directly into your ComfyUI browser window.
3. In the **LoRA Loader** node (Node #4), select your preferred FLUX.2 NSFW unlock LoRA (strength `0.80 - 0.90`).
4. In the **Reference Nodes** (Nodes #8 and #12), verify that `seoyeon_a1_front.png` and `seoyeon_c5_relax.png` are selected.
5. Click **Queue Prompt**.

### Method B: Automated CLI Runner (via Python)
You can render any shot from `exclusive_shots.py` directly from your terminal:

```bash
# List all 21 canonical exclusive shots
python personas/seoyeon/run_comfy_exclusive.py --list

# Render morning bed shirt shot
python personas/seoyeon/run_comfy_exclusive.py --shot ex_bed_shirt

# Render mirror towel shot with custom seed
python personas/seoyeon/run_comfy_exclusive.py --shot ex_towel_mirror --seed 42
```
The script will upload the reference images, inject the shot prompt, trigger ComfyUI, and automatically save the output into `personas/seoyeon/content/exclusive/`.

---

## 4. Key Node Parameters

* **Sampler**: `euler` with scheduler `simple` or `beta`
* **Steps**: `25` steps
* **CFG**: `1.0` (FluxGuidance handles prompt strength; do NOT increase CFG above 1.0)
* **Guidance**: `3.5` (Node #7)
* **Output Resolution**: `896 x 1152` (Optimal vertical 3:4 / 9:16 mobile aspect ratio for Fanvue)
