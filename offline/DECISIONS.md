# DECISIONS — research findings and open questions

Written 2026-09-04 while the operator was away, per `BRIEF.md`. Every number
below carries a source or is explicitly marked unsourced. Where two sources
disagreed and I could not resolve it, both are given rather than picking one
silently.

---

## 1. The speckle bug — Task 2's blocker, diagnosed from local files

**This is not a hypothesis, it is read directly off the ComfyUI workflow
JSON on this machine**
(`%LOCALAPPDATA%\Comfy-Desktop\ComfyUI-Installs\girl-insta\ComfyUI\user\default\workflows\`):

`Krea2_turbo.json`, `Krea2_Lora_Test.json` and `image_krea2_turbo_t2i.json`
all load `krea2_turbo_fp8_scaled.safetensors` (a Qwen-Image-architecture
checkpoint — confirmed by its own paired `CLIPLoader` using
`qwen3vl_4b_fp8_scaled.safetensors` with `type: krea2`) but decode through
**`VAELoader: Wan2_1_VAE_fp32.safetensors`** — the VAE that belongs to the
Wan 2.1 *video* model, an unrelated architecture. Three sibling workflows
(`krea2_edit.json`, `Krea2_turbo_v2.json`, `NaBi_Carousel_Consistency.json`)
load the identical checkpoint but correctly decode through
`qwen_image_vae.safetensors`, which is already present on disk at
`ComfyUI-Shared/models/vae/qwen_image_vae.safetensors`.

Decoding a latent with the wrong model family's VAE is a well-known cause of
exactly the "speckled, noisy" symptom `BRIEF.md` describes — the two latent
spaces do not agree on what a channel encodes, so the decoder reconstructs
static rather than an image.

**This is a better-evidenced explanation than the `weight_dtype: "default"`
fp8 theory** `BRIEF.md`/`PLAN.md` proposed, for two reasons:
1. `weight_dtype: "default"` on an already-`_fp8_scaled`-suffixed checkpoint
   is the setting ComfyUI/Comfy-Org's own convention expects — a "_scaled"
   file carries its own per-tensor scale metadata, and `"default"` reads it.
   Forcing an explicit `fp8_e4m3fn` on top of an already-scaled file is more
   likely to be wrong than the observed "default" setting. **Unverified
   against Comfy-Org's own documentation for `krea2_turbo_fp8_scaled`
   specifically — I did not find a primary source confirming this
   convention for this exact file, only inferring it from the naming
   pattern used across Comfy-Org's other "_scaled" releases (e.g.
   Qwen-Image's own fp8_scaled text encoders).**
2. The VAE mismatch is directly visible in the JSON, not inferred from a
   symptom.

**Not corroborated by an actual render** — no generation was run (see hard
rule 1; every candidate here still costs GPU time even at zero dollars, and
running the fix is the operator's confirmation to make, not mine to claim).
`offline/bakeoff/00_fix_speckle/krea2_turbo_fixed_vae.json` is the same graph
with the VAE swapped; see `bakeoff/README.md` section 0.

**Open, needs the operator's eyes:** whether `flux-2-klein-9b-fp8.safetensors`
(downloaded today, 2026-09-04, not wired into any saved workflow yet) is
actually "the current workflow" `BRIEF.md` describes, given no saved
workflow on this machine loads it. See `bakeoff/README.md` section 1 for the
timeline evidence. I did not build a workflow around unverified assumptions
about what node graph the operator intended for it — `01_flux2_klein_9b.json`
in the bake-off is a clean graph built from confirmed file names, not a
recovery of an existing (nonexistent) one.

---

## 2. Bake-off candidates

### What exists as downloadable weights

| candidate | exists? | source |
|---|---|---|
| FLUX.2 Klein 9B (distilled + base) | yes, both on disk already | local file check, `ComfyUI-Shared/models/diffusion_models/` |
| FLUX.2 Klein 4B (distilled + base) | yes | [black-forest-labs/FLUX.2-klein-4b-fp8](https://huggingface.co/black-forest-labs/FLUX.2-klein-4b-fp8), [black-forest-labs/FLUX.2-klein-base-4b-fp8](https://huggingface.co/black-forest-labs/FLUX.2-klein-base-4b-fp8), [Comfy-Org/flux2-klein-4B](https://huggingface.co/Comfy-Org/flux2-klein-4B) |
| Krea 2 Turbo + Krea 2 Raw | yes, both on disk already | local file check |
| Qwen-Image | yes | [Comfy-Org/Qwen-Image_ComfyUI](https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/tree/main/split_files/diffusion_models) |
| Z-Image-Turbo | yes | [Comfy-Org/z_image_turbo](https://huggingface.co/Comfy-Org/z_image_turbo) |

All five are real, current, downloadable open-weight releases as of this
research (2026-09-04). None of the operator's table entries were dead ends.

### VRAM at fp8, sourced

| candidate | reported VRAM | source |
|---|---|---|
| FLUX.2 Klein 9B | ~29 GB fp16, **~15 GB fp8** | [Will It Run AI — Klein 9B VRAM](https://willitrunai.com/blog/flux-2-klein-9b-vram-requirements) |
| FLUX.2 Klein 4B | "genuinely a 12 GB-class model"; ComfyUI's own template reports ~8.4 GB with offload on a 5090 | [blog.comfy.org — Klein 4B](https://blog.comfy.org/p/flux2-klein-4b-fast-local-image-editing) |
| Krea 2 Turbo | BF16 24.76 GiB -> **fp8 12.01 GiB** (community quant); "approximately 10 to 12 GB" fp8 elsewhere | [InstaSD — Krea 2 Turbo checkpoint formats](https://www.instasd.com/post/krea-2-turbo-checkpoint-formats-vram-guide), [Will It Run AI — Krea 2](https://willitrunai.com/image-models/krea-2) |
| Qwen-Image | fp8 called "the sweet spot" at 16 GB by one source; ~20.5 GB fp8 framed against a 24 GB card by another | **DISAGREE, unresolved** — both from search-result summaries, neither independently verified against Comfy-Org's own hardware notes. Treat as "test carefully," not "confirmed to fit." |
| Z-Image-Turbo | BF16 ~14–16 GB, fp8 build reported ~8 GB, GGUF ~6 GB | [WillItRunAI — Z-Image Turbo](https://willitrunai.com/image-models/z-image-turbo) — **the fp8/GGUF filenames themselves were not found on Comfy-Org's repo in this research; only `z_image_turbo_bf16.safetensors` was confirmed to exist there.** Do not assume an fp8 path exists until you see the file.

### ComfyUI native support

All five load with the standard `UNETLoader` + `CLIPLoader` + `VAELoader`
node trio — no custom nodes needed for base inference, per
[docs.comfy.org's own per-model tutorials](https://docs.comfy.org/tutorials/flux/flux-2-klein)
for Klein, [ComfyUI Qwen-Image example](https://docs.comfy.org/tutorials/image/qwen/qwen-image)
and [Z-Image-Turbo example](https://docs.comfy.org/tutorials/image/z-image/z-image-turbo).
Krea 2's own node type strings (`krea2` on `CLIPLoader`) are confirmed
directly from a workflow already saved on this machine.

**FLUX.2 Klein's `CLIPLoader` type string is written as `"flux2"` in the
generated bake-off graphs — this is an INFERENCE from the pattern
(`"krea2"` for Krea 2, so `"flux2"` for FLUX.2), not a confirmed literal
string from documentation.** If loading `01_flux2_klein_9b.json` or
`03_flux2_klein_4b.json` fails with an unrecognised `type` value, check
ComfyUI's `CLIPLoader` node's dropdown for the actual string and fix it —
this is exactly the kind of gap the brief says not to silently fill, so it
is flagged rather than asserted.

**Text encoder / VAE reuse, confirmed:**
- FLUX.2 Klein (9B and 4B) uses `qwen_3_8b_fp8mixed.safetensors` as its text
  encoder (not Mistral, despite FLUX.2 [dev] using Mistral) — [search
  result summary citing ComfyUI Klein workflow node names]; the file is
  already on disk.
- Z-Image-Turbo reuses the **FLUX.1 VAE** (`ae.safetensors`) rather than a
  Tongyi-trained one — [WillItRunAI — Z-Image Turbo](https://willitrunai.com/image-models/z-image-turbo).
  Already on disk.
- Qwen-Image's text encoder (`qwen_2.5_vl_7b_fp8_scaled.safetensors`) and
  VAE (`qwen_image_vae.safetensors`) are both already on disk.

### The Krea 2 claim from `PLAN.md`, checked

`PLAN.md`'s table called Krea 2 Turbo's "within 0.14 points of GPT Image 2 on
style fidelity" claim **"UNCORROBORATED — a lead, not a fact."** It is now
corroborated by two independent sources repeating the same figure:
[Medium — Krea 2: Open-Weights Image Model That Caught the Frontier](https://medium.com/@computeleap/krea-2-open-weights-image-model-that-caught-the-frontier-73d102dab053)
and the search summary of
[ComputeLeap's own blog](https://www.computeleap.com/blog/krea-2-open-weights-image-model-frontier-2026/),
both citing Artificial Analysis's benchmark. **Still not independently
verified against Artificial Analysis's own published numbers — both sources
found here look like they may share a common origin, so this should be read
as "two outlets repeating the same claim," not "two independent
measurements."**

---

## 3. Training research (Task 4) — NOT a decision to train, research only

**No training was run. No trainer was downloaded.** This is what to read
before choosing, per the brief.

### Trainer landscape

- **OneTrainer** supports FLUX.2 Dev and FLUX.2 Klein directly, per its own
  GitHub repo description ([Nerogar/OneTrainer](https://github.com/nerogar/OneTrainer)).
  Not tested here; listed as a real alternative to ai-toolkit, not verified
  at 16 GB specifically.
- **FluxGym** is built for **FLUX.1**, not FLUX.2 — its low-VRAM presets
  (12/16/20 GB) do not carry over to Klein or any FLUX.2 variant on the
  evidence found. **Rule it out for this project** unless a FLUX.2-specific
  fork turns up later.
- **A specialised third-party tool, Fizgig**
  ([shootthesound/Fizgig](https://github.com/shootthesound/Fizgig), billed
  as a "LoKR Studio" for Krea 2, MiniMax and Klein 9B specifically) claims
  a full Klein 9B LoRA trains on 16 GB and a Krea 2 (12.9B) LoRA on 8 GB.
  **This directly contradicts the 24 GB floor the BFL/HF blog states for
  ai-toolkit below — read as "a specialised tool may get further than the
  general-purpose one," not as confirmation that ai-toolkit itself will fit
  in 16 GB.** Not independently verified beyond the repo's own description;
  worth trying if ai-toolkit OOMs at 16 GB before concluding Klein is out.
- **ai-toolkit (ostris)** has day-zero support for FLUX.2 Klein LoRA
  training, both 4B and 9B, base variant — confirmed directly by the
  maintainer:
  ["AI Toolkit now fully supports training LoRAs for FLUX.2 Klein 9B and 4B
  base models"](https://x.com/ostrisai/status/2012689973892571639) (Ostris,
  X/Twitter). Official write-up:
  [Fine-tune FLUX.2 \[klein\] with a LoRA under 60 minutes](https://huggingface.co/blog/black-forest-labs/flux-2-klein-lora)
  (Black Forest Labs' own blog — this is almost certainly the "published
  source specifically on FLUX.2 Klein LoRA training" `BRIEF.md` asked me to
  find).
- **Krea 2** is supported by ai-toolkit, Hugging Face Diffusers, fal, and
  Kohya — the official Krea 2 repo names all four. Training is done on
  **Krea 2 Raw** (the base checkpoint, already on disk as `raw.safetensors`),
  never on Turbo, then the resulting LoRA is loaded onto Turbo for
  inference. Kohya's path specifically is via **musubi-tuner**, reported
  running on a local 12 GB card. Source:
  [InstaSD — Krea 2 LoRA training LoKr guide](https://www.instasd.com/post/krea-2-lora-training-lokr-guide),
  [note.com — Krea2 character LoRA on 12GB VRAM with musubi-tuner](https://note.com/sepiablue/n/nbc355cc7e114?hl=en).
- **Qwen-Image and Z-Image-Turbo training support at 16 GB was not
  separately researched in this pass** — time was spent on the two
  candidates the brief specifically flagged (FLUX.2 Klein's 4B-vs-9B
  question, and Krea 2 since it is already on disk). If either wins the
  bake-off, check their training support before assuming it exists —
  "inference support arrives long before training support" per the
  brief's own warning, and this was not checked for these two.

### The 4B-vs-9B question, and whether 16 GB is actually enough

This is the least settled part of the research, and it should be read
carefully rather than summarised optimistically:

- The Black Forest Labs / Hugging Face blog on FLUX.2 Klein LoRA training
  states training is done on the **base** checkpoint (not the distilled
  4-step one), in **bf16**, and that "a LoRA run lands under 24 GB for the
  base model, so a 4090 or an L4 is enough" — **this states 24 GB, not
  16 GB**, as the guide's own practical floor.
- A dedicated RunComfy guide is titled "FLUX Klein LoRA Training on 16GB
  VRAM: What Works, What OOMs, and When to Use 4B" — its existence confirms
  16 GB training is attempted and documented somewhere, but its content
  could not be retrieved in this pass (the page returned only navigation,
  not article text, when fetched). **This is the single most important
  unread source for Task 4 — read it before setting any training config.**
  URL: https://www.runcomfy.com/trainer/ai-toolkit/flux-2-klein-16gb-vram-training
- General ai-toolkit low-VRAM technique (confirmed, not Klein-specific):
  combine `low_vram: true`, float8 quantisation of the frozen base, layer
  offloading, latent caching, and gradient checkpointing to fit a LoRA under
  16 GB. Rank 16 was reported as producing poor results; rank 32 was
  preferred. Source: [DeepWiki — ai-toolkit VRAM optimisation guide](https://deepwiki.com/ostris/ai-toolkit/19.1-vram-optimization-guide)
  and search-result summary of the toolkit's own UI defaults.
- Learning rate for FLUX.2 Klein LoRA per the BFL/HF blog: **`1e-4`**, and a
  typical visual peak around **step 750–1500**, with a full 1800-step run
  taking under an hour on a 4090.
- **Whether the text encoder (`qwen_3_8b_fp8mixed` / `qwen_3_8b` for Klein)
  is trained: not stated in any source found.** Flag as genuinely unknown,
  not assumed off. Most FLUX-family LoRA workflows leave the text encoder
  frozen by convention, but that is a convention, not confirmation for this
  specific model.

**Bottom line for the operator:** the published guide most directly on point
(BFL's own blog) implies **24 GB, not 16 GB**, is the tested floor for
FLUX.2 Klein 4B LoRA training in bf16. Getting under 16 GB is plausible with
ai-toolkit's standard low-VRAM stack (quantisation + offload + gradient
checkpointing) but this specific combination was not found confirmed for
Klein specifically — only asserted generically for the FLUX architecture
family. **This may be the fact that eliminates Klein 4B/9B from training
consideration even if it wins the bake-off on image quality**, exactly the
scenario `BRIEF.md` warned about ("this may eliminate a model that wins the
bake-off"). Read the RunComfy 16GB-specific guide before deciding.

---

## 4. Open items — need the operator, not a guess

1. **Is `flux-2-klein-9b-fp8.safetensors` actually wired into a workflow
   anywhere, or was it downloaded today and never used?** See section 1.
   Affects whether "the current workflow" in `BRIEF.md` refers to something
   that exists, or something the operator was mid-way through building.
2. **The `CLIPLoader` type string for FLUX.2 Klein (`"flux2"` in the
   generated graphs) is inferred, not confirmed.** Check it against the
   node's own dropdown in ComfyUI before trusting a load failure to mean
   the checkpoint is bad.
3. **Qwen-Image's real fp8 VRAM figure is contested between two sources**
   (16 GB "sweet spot" vs ~20.5 GB in a 24 GB context) and was not resolved.
4. **The RunComfy 16GB Klein training guide could not be read in this
   pass** (page returned navigation only) — it is named directly in the
   brief's own hoped-for source and should be read before any training
   config is finalised.
5. **Qwen-Image and Z-Image-Turbo LoRA training support at 16 GB was not
   researched** in this pass — only FLUX.2 Klein and Krea 2 were covered in
   depth, because those are the two the brief specifically named. If either
   of the other two wins the bake-off, this gap needs closing before
   training.
6. **CFG was deliberately left un-locked across the bake-off candidates**
   (see `bakeoff/README.md` section 3) — a mechanical judgement call, not a
   quality opinion, but worth the operator's confirmation that this was the
   right read of "same sampler" not implying "same CFG."
