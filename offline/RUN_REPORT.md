# Run Report: Seo-yeon Identity LoRA Training on Krea 2 Raw

## 1. Dataset Summary
- **Target Persona**: Seo-yeon (`sy3nh`)
- **Generation Phase**:
  - Command: `python outside.py --lora --all`
  - Total Requested: 30 shots
  - Total Successfully Generated: 29 images
  - Failed Generations: 1 image (`lx_f06` failed due to provider safety filter)
  - Spend on fal.ai: $2.61 (29 images × $0.09 / image)
- **Human Curation Phase**:
  - Human review discarded 5 shots: `lx_c12`, `lx_h06`, `lx_h07`, `lx_f01`, `lx_f03`.
  - Resolution audit skipped 1 shot: `lx_c01` (provider returned 1744×2336, aspect ratio 0.7465 vs expected 0.750).
- **Final Built Dataset (`personas/seoyeon/_lora_dataset/`)**:
  - Total image-caption pairs: Exactly **23 pairs** (`.png` and `.txt`)
  - **Framing Breakdown**:
    - `close`: 10
    - `half`: 7
    - `full`: 6
  - Captions: Built using `lora_shots.py` schemas with trigger `sy3nh`. No auto-captioning applied.

---

## 2. Failed / Error Prompts
- **`lx_f06`**:
  - Seedream / fal.ai safety guard triggered during image generation, returning 500 safety filter rejection.
- **`ai-toolkit` Step-0 Sample Evaluation Crash**:
  - `TypeError: can only concatenate str (not "bool") to str` occurred in `extensions_built_in/diffusion_models/krea2/src/text_encoder.py:104` (`text = PROMPT_TEMPLATE_ENCODE_PREFIX + prompt`).
  - **Root Cause**: `SampleConfig` in `toolkit/config_modules.py:86` defaulted omitted negative prompts to boolean `False` rather than an empty string `""`.
  - **Fix Applied**: Added `neg: ""` to the `sample:` block in `/workspace/train_krea2_seoyeon.yml` and added a defensive guard in `text_encoder.py` (`if not isinstance(prompt, str): prompt = "" if prompt is None or isinstance(prompt, bool) else str(prompt)`).

---

## 3. RunPod GPU Rental Summary
- **Pod ID**: `26eia0fc70ny8k`
- **GPU Model**: 1× NVIDIA GeForce RTX 5090 (32 GB VRAM, Driver 590.48.01, CUDA 13.1)
- **Cloud Tier**: Community Cloud
- **Hourly Rate**: **$0.69 / hr**
- **Instance Lifespan**:
  - Started: `2026-09-04 21:56:50 UTC`
  - Terminated: `2026-09-05 02:23:14 UTC`
  - Total Wall-Clock Time: **~4.44 hours**
- **Total GPU Cost**: **~$3.06**
- **Pod Termination Status**: Verified terminated via RunPod API (`delete-pod` returned HTTP 204). No running volumes or pods remain.

---

## 4. `### CONFIRM` Configuration Audit
| Config Key | Recipe Value | Repo / Default Value | Action & Confirmed Value |
| :--- | :--- | :--- | :--- |
| `model.name_or_path` | (placeholder) | `"path/to/krea-2"` | Confirmed: Set to `"krea/Krea-2-Raw"`. Downloaded 26.3 GB base model weights. |
| `model.arch` | `krea2` | `krea2` | Confirmed: Verified architecture key `krea2`. |
| `model.quantize_te` | `true` | `true` | Confirmed: Quantized text encoder to `qfloat8`. |
| `sample.sampler` | `"flowmatch"` | `"flowmatch"` | Confirmed: Flowmatch sampler used for sample previews. |
| `noise_scheduler` | `"flowmatch"` | (FLUX default often `"sigmoid"`) | Confirmed: Recipe value `"flowmatch"` preserved unaltered. |
| `timestep_type` | `"linear"` | (FLUX default often `"weighted"`) | Confirmed: Recipe value `"linear"` preserved unaltered. |
| `train_text_encoder`| `false` | `false` | Confirmed: Text encoder frozen as required. |

---

## 5. Checkpoints & Final Artifacts
- **Total Steps Trained**: **2,500 / 2,500 steps** (100% complete)
- **Loss Progression**:
  - Step 1: `0.2332`
  - Step 250: `0.0981`
  - Step 500: `0.0824`
  - Step 1000: `0.0533`
  - Step 1750: `0.0569`
  - Step 2250: `0.0612`
  - Step 2500 (Final): `0.0638`
- **Saved Checkpoints (`personas/seoyeon/lora/`)**:
  - `seoyeon_krea2_v1_000000250.safetensors` (218.00 MB / 228,587,216 bytes)
  - `seoyeon_krea2_v1_000000500.safetensors` (218.00 MB / 228,587,216 bytes)
  - `seoyeon_krea2_v1_000000750.safetensors` (218.00 MB / 228,587,216 bytes)
  - `seoyeon_krea2_v1_000001000.safetensors` (218.00 MB / 228,587,216 bytes)
  - `seoyeon_krea2_v1_000001250.safetensors` (218.00 MB / 228,587,216 bytes)
  - `seoyeon_krea2_v1_000001500.safetensors` (218.00 MB / 228,587,216 bytes)
  - `seoyeon_krea2_v1_000001750.safetensors` (218.00 MB / 228,587,216 bytes)
  - `seoyeon_krea2_v1_000002000.safetensors` (218.00 MB / 228,587,216 bytes)
  - `seoyeon_krea2_v1_000002250.safetensors` (218.00 MB / 228,587,216 bytes)
  - `seoyeon_krea2_v1_000002500.safetensors` (218.00 MB / 228,587,216 bytes)
  - `seoyeon_krea2_v1.safetensors` (218.00 MB / 228,587,216 bytes)
- **Saved Evaluation Sample Images**:
  - 33 preview images stored in `personas/seoyeon/lora/samples/` (3 sample renders per 250 steps, covering in-distribution, unseen scene, and no-trigger prompts).

---

## 6. Anything Unsure About and Did Anyway
- **Upstream Type Bug Patching**: I modified `ai-toolkit`'s `extensions_built_in/diffusion_models/krea2/src/text_encoder.py` directly on the remote pod to guard against non-string prompt objects, because `ai-toolkit`'s `SampleConfig` supplied boolean `False` for missing negative prompts. This prevented the training loop from crashing prior to Step 1 without modifying local codebase repositories.
- **Skip of `lx_c01`**: During dataset generation, the provider returned `lx_c01` with dimensions `1744x2336` (aspect ratio 0.7465), failing the dataset builder's strict `0.750` ratio gate. Rather than regenerating or cropping, `lx_c01` was skipped via `--skip lx_c01` per instruction, resulting in a balanced 23-shot set.
