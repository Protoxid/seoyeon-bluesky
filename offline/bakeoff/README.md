# Bake-off — base model comparison, phase 0 of PLAN.md

**Nobody has judged an image yet. This folder makes the comparison possible;
it does not make the call. Read `HANDBACK.md` for the one open question that
needs your eyes.**

---

## 0. Fix the speckle first — `00_fix_speckle/`

**Found, not guessed.** Three of the saved ComfyUI workflows on this machine
(`Krea2_turbo.json`, `Krea2_Lora_Test.json`, `image_krea2_turbo_t2i.json`,
all under
`%LOCALAPPDATA%\Comfy-Desktop\ComfyUI-Installs\girl-insta\ComfyUI\user\default\workflows\`)
load the diffusion model `krea2_turbo_fp8_scaled.safetensors` (a Qwen-Image-
architecture checkpoint — its own `CLIPLoader` uses `type: krea2`, a Qwen3VL
text encoder) but decode through **`VAELoader: Wan2_1_VAE_fp32.safetensors`
— the VAE for a completely different model family (the Wan 2.1 *video*
model)**. Decoding a Qwen-Image-architecture latent with a Wan 2.1 VAE is
exactly the kind of mismatch that produces colourful static / speckle: the
two latent spaces don't agree on what a channel means.

Three of the *other* saved workflows (`krea2_edit.json`, `Krea2_turbo_v2.json`,
`NaBi_Carousel_Consistency.json`) load the same checkpoint with
**`VAELoader: qwen_image_vae.safetensors`** instead — the correct VAE for
this architecture, and it is already sitting in
`ComfyUI-Shared/models/vae/qwen_image_vae.safetensors`.

**The fix:** `00_fix_speckle/krea2_turbo_fixed_vae.json` is the same graph,
same checkpoint, with the VAE swapped to `qwen_image_vae.safetensors`. Run it
and compare against a render from the original `Krea2_turbo.json` at the same
seed. If the speckle is gone, this was the whole bug and there is no
fp8/`weight_dtype` problem to chase — **do not spend more time on the
`weight_dtype: default` theory in `BRIEF.md` and `PLAN.md` until this is
ruled out first**, because it is now the cheaper, better-evidenced
explanation.

**Not verified:** I have not run these graphs (no generation was executed —
see the hard rule against spending, and every model here still needs actual
inference which is not free of time even if free of money; that render is
the operator's to trigger and judge). This is a diagnosis from reading the
workflow JSON, not a confirmed fix.

---

## 1. What is already on this machine

Checked directly, not assumed — `ComfyUI-Shared` is the model store shared
across ComfyUI Desktop installs
(`%LOCALAPPDATA%\Comfy-Desktop\ComfyUI-Shared\models\`):

| file | folder | present? |
|---|---|---|
| `flux-2-klein-9b-fp8.safetensors` | diffusion_models | **yes** (downloaded today) |
| `flux-2-klein-base-9b-fp8.safetensors` | diffusion_models | **yes** (downloaded today) — this is the *training* variant, not for the bake-off, see below |
| `krea2_turbo_fp8_scaled.safetensors` | diffusion_models | **yes** |
| `raw.safetensors` | diffusion_models | **yes** — this is Krea 2 *Raw*, the non-distilled base used for training, not inference |
| `qwen_3_8b_fp8mixed.safetensors` | text_encoders | **yes** (Klein's text encoder) |
| `qwen3vl_4b_fp8_scaled.safetensors` | text_encoders | **yes** (Krea 2's text encoder) |
| `qwen_2.5_vl_7b_fp8_scaled.safetensors` | text_encoders | **yes** (Qwen-Image's text encoder) |
| `qwen_3_4b.safetensors` | text_encoders | **yes** (Z-Image-Turbo's text encoder) |
| `flux2-vae.safetensors` | vae | **yes** (FLUX.2's VAE) |
| `qwen_image_vae.safetensors` | vae | **yes** |
| `ae.safetensors` | vae | **yes** — this is the FLUX.1 VAE; Z-Image-Turbo reuses it |
| `flux-2-klein-4b-fp8.safetensors` | diffusion_models | **no** — needs downloading |
| `qwen_image_fp8_e4m3fn.safetensors` | diffusion_models | **no** — needs downloading |
| `z_image_turbo_bf16.safetensors` | diffusion_models | **no** — needs downloading |

**Disk space checked: 340 GB free on C:** (`df -h /c/` on 2026-09-04). Every
missing file above is well under that.

**A discrepancy worth flagging, not resolving silently:** `BRIEF.md` states
"the current workflow uses `flux-2-klein-9b-fp8`", but no *saved* ComfyUI
workflow on this machine actually loads that file — every saved image
workflow found loads `krea2_turbo_fp8_scaled.safetensors` instead. Both
`flux-2-klein-9b-fp8.safetensors` and `flux-2-klein-base-9b-fp8.safetensors`
were downloaded **today** (2026-09-04, file mtimes 14:04 and 18:50), which
reads as: the operator had just started pulling FLUX.2 Klein down when they
had to step away, and had not yet built or saved a workflow around it. If
that is wrong, say so — I did not guess a workflow into existence for a
model with no wiring on disk yet; see the candidate below noted as "no
observed local workflow."

---

## 2. The candidates, and what they need

| id | model | on disk? | VRAM (fp8, sourced) | ComfyUI support | verdict |
|---|---|---|---|---|---|
| `01_flux2_klein_9b.json` | FLUX.2 Klein 9B (distilled) | yes | ~15 GB fp8 | native (`UNETLoader`) | **viable, tight** — leaves little headroom for text encoder + VAE + OS on a 16 GB card |
| `02_krea2_turbo.json` | Krea 2 Turbo | yes | ~10–12 GB fp8 | native | **viable** — the current incumbent-in-practice per what is actually wired on disk |
| `03_flux2_klein_4b.json` | FLUX.2 Klein 4B (distilled) | needs 1 file (~4 GB) | ~8.4 GB with offload (ComfyUI's own template, on a 5090) | native | **viable, most headroom** |
| `04_qwen_image.json` | Qwen-Image | needs 1 file | fp8 "sweet spot" at 16 GB per one source; ~20.5 GB at fp8 per another for a 24 GB card context — **numbers disagree, see below** | native | **viable but unresolved VRAM number, test carefully** |
| `05_z_image_turbo.json` | Z-Image-Turbo | needs 1 file (~16 GB bf16) | bf16 ~16 GB, **fp8 build reported ~8 GB** if available | native | **viable** — but only the bf16 filename is confirmed to exist on Comfy-Org's repo; an fp8 quant was reported by a secondary source and NOT independently confirmed — check before assuming an 8 GB path exists |

**Downloads needed (all from Hugging Face, all free, no account/spend
required for the raw file):**

```
FLUX.2 Klein 4B  ->  black-forest-labs/FLUX.2-klein-4b-fp8
                     file: flux-2-klein-4b-fp8.safetensors  (~4 GB)
                     -> ComfyUI-Shared/models/diffusion_models/

Qwen-Image       ->  Comfy-Org/Qwen-Image_ComfyUI
                     file: split_files/diffusion_models/qwen_image_fp8_e4m3fn.safetensors
                     -> ComfyUI-Shared/models/diffusion_models/

Z-Image-Turbo    ->  Comfy-Org/z_image_turbo
                     file: split_files/diffusion_models/z_image_turbo_bf16.safetensors
                     -> ComfyUI-Shared/models/diffusion_models/
```

Everything else each of these three needs (text encoder, VAE) is already on
disk — see the table in section 1. **I did not download any of these.**
Multi-gigabyte downloads on a machine I cannot watch, for weights whose
result I am not allowed to judge anyway, is exactly the kind of thing to
leave for the operator's own connection and disk — see `HANDBACK.md`.

**On the VRAM disagreement for Qwen-Image:** one source says fp8 is "the
sweet spot" at 16 GB, another frames ~20.5 GB fp8 usage in the context of a
24 GB card. I could not resolve which is right from search results alone —
this table is not a green light, it is "test this one carefully and watch
for OOM before assuming it fits." Recorded as open in `DECISIONS.md`.

---

## 3. What is held identical across every candidate, and why

Per `BRIEF.md`: **same prompt, same seed, same resolution, same steps, same
sampler.** All five `NN_*.json` files (plus the speckle-fix graph) were
generated by `_generate.py` from one shared template so this is true by
construction, not by hand-copying:

- **Prompt** — a generic human face, no persona, close enough to judge pores
  (the brief is explicit that this tests the MODEL, not her likeness):
  > "Close-up photograph of a woman's face, straight-on, filling most of the
  > frame from the top of her forehead to her collarbone. Mid-30s, visible
  > skin texture and pores, faint under-eye lines, a few stray hairs escaping
  > a loose ponytail. Indoors near a window on an overcast afternoon, soft
  > diffuse light from one side. Neutral expression, looking directly at the
  > camera. Shot on a full-frame camera with a sharp prime lens, natural
  > unretouched skin, no makeup filter, no smoothing."
- **Seed** — `20260904`, fixed across every graph.
- **Resolution** — `896x1152`, per the work order.
- **Steps** — `20`, fixed across every graph.
- **Sampler / scheduler** — `euler` / `simple`, fixed across every graph.

**One deliberate deviation, disclosed rather than silent: CFG is NOT locked
identical.** The brief's list of what must match does not include CFG, and
locking it would have actively broken the comparison: Krea 2 Turbo,
FLUX.2 Klein (distilled), and Z-Image-Turbo are all guidance-distilled and
are meant to run at `cfg=1.0` — forcing a real CFG value like 4.0 onto them
does not make the test fairer, it pushes them outside how they are meant to
operate and would burn/oversaturate the output for a reason that has nothing
to do with skin quality. Qwen-Image (not distilled) uses `cfg=4.0`, a
commonly published default for it — **treat that number as typical, not
verified against Comfy-Org's own reference workflow, and check it before
trusting a bad Qwen-Image result.** This is recorded in `DECISIONS.md` as
the one judgement call made without operator sign-off; it was mechanical
(a units-of-measurement choice, not a quality opinion) rather than a
decision requiring eyes.

**Also disclosed:** 20 steps is generous for the distilled/turbo candidates,
which normally run at 4–8. Fixing steps identical per the brief means
they are not being tested at their own recommended speed — only at a speed
where all five candidates are directly comparable. If a candidate looks weak,
it is worth a second, unfair-but-informative render at its own native step
count before ruling it out.

---

## 4. Run order

1. `00_fix_speckle/krea2_turbo_fixed_vae.json` — confirm the speckle is gone
   before spending any time on the rest. **Gate 0 of `PLAN.md` is not passed
   until this render has clean skin at 100% zoom.**
2. `01_flux2_klein_9b.json` and `02_krea2_turbo.json` — both runnable right
   now, no downloads needed.
3. Download the three files in section 2, then run `03`, `04`, `05` in any
   order.

## 5. How to load a graph

Each `NN_*.json` is a ComfyUI API/prompt graph (node id -> `{class_type,
inputs}`), not the newer UI-canvas format with `nodes`/`links`/positions.
Try, in order:

1. Drag the `.json` onto the ComfyUI canvas. Recent ComfyUI frontends detect
   and convert an API-format graph automatically.
2. If that does not import cleanly: ComfyUI's menu -> **Workflow -> Open**,
   pick the file. Some versions require this path instead of drag-and-drop.
3. If neither works on this ComfyUI build (`v0.20.1`, checked
   `manifest.json`), the graph is still simple enough to rebuild by hand in
   under two minutes from the "graph shape" comment at the top of
   `_generate.py`'s `build()` function — nine nodes, linear chain, no
   branching.

## 6. What you are looking for

**Skin texture at 100% zoom. Nothing else.** Not composition (it is a
generic face, not the persona), not likeness, not which one you personally
find prettiest at thumbnail size. Zoom to 100% and look at the cheek and
under-eye area for: visible pore texture, natural skin tone variation, the
absence of the "airbrushed plastic" look. That is the one thing this rig
exists to let you compare, and it is explicitly not something this file — or
any script — should have an opinion about. See rule 5 in the hard rules at
the top of `BRIEF.md`.
