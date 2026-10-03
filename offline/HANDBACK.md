# HANDBACK — what needs your eyes

Written 2026-09-04 while you were out, per `offline/BRIEF.md`. Nothing was
spent, published, deleted, trained, or judged for realism — those were the
hard rules and they held. Full detail lives in `DECISIONS.md` and
`bakeoff/README.md`; this is the short version of what needs you specifically.

---

## 1. The speckle diagnosis, and the specific change to try

**Found in the workflow files, not guessed.** Three saved ComfyUI workflows
(`Krea2_turbo.json`, `Krea2_Lora_Test.json`, `image_krea2_turbo_t2i.json`)
load the Krea 2 Turbo checkpoint but decode it through
`VAELoader: Wan2_1_VAE_fp32.safetensors` — the VAE for the unrelated Wan 2.1
*video* model. Three sibling workflows use the correct
`qwen_image_vae.safetensors` instead, and that file is already on disk.

**Try this first:** `offline/bakeoff/00_fix_speckle/krea2_turbo_fixed_vae.json`
— identical graph, VAE swapped. If the speckle is gone, that was the whole
bug. This is a better-evidenced explanation than the `weight_dtype: default`
fp8 theory in `PLAN.md` — see `DECISIONS.md` section 1 for why, and don't
chase the fp8 theory further until this is ruled out.

Not run, not confirmed by a render — that's the one thing I can't do without
spending your GPU time and your judgement.

## 2. The bake-off: candidates, downloads, run order

All five candidates from your table are real, downloadable weights (nothing
was a dead end). Two are already fully on disk and runnable right now
(**FLUX.2 Klein 9B, Krea 2 Turbo**); three need exactly one file downloaded
each, everything else (text encoder, VAE) is already staged
(**FLUX.2 Klein 4B, Qwen-Image, Z-Image-Turbo**). Exact HuggingFace repo
paths, filenames, and target folders are in `bakeoff/README.md` section 2.

**Discrepancy worth your attention:** no saved workflow on this machine
actually loads `flux-2-klein-9b-fp8.safetensors`, even though `BRIEF.md`
calls it "the current workflow." Both Klein files were downloaded *today*,
which reads as: you'd started pulling FLUX.2 Klein down and hadn't wired a
workflow yet. If that's wrong, the bake-off graph I built for Klein 9B
(`bakeoff/01_flux2_klein_9b.json`) is a clean graph from confirmed filenames,
not a recovery of something that existed — check it opens and generates
before trusting it blindly.

**Run order:** speckle fix first (above), then the two free candidates,
then download and run the other three. Same prompt/seed/resolution/steps/
sampler across all five, by construction — one deliberate exception (CFG is
per-model, not locked) is explained in `bakeoff/README.md` section 3.

**You judge skin texture at 100% zoom. I did not open a single generated
image to form an opinion, because there isn't one yet — nothing was
rendered.**

## 3. Open items in `DECISIONS.md`

- Whether Klein 9B is really "current," per above.
- The `CLIPLoader` type string used for FLUX.2 Klein (`"flux2"`) is an
  inferred guess from Krea 2's own `"krea2"` convention, not confirmed —
  check it against ComfyUI's own dropdown if the graph won't load.
- Qwen-Image's real fp8 VRAM figure: two sources disagreed (16 GB vs
  ~20.5 GB) and I could not resolve which is right.
- The RunComfy guide named directly in your brief
  ("FLUX Klein LoRA Training on 16GB VRAM") would not return its article
  text when fetched — it's the single most relevant unread source for
  Task 4 and should be read before any training config is set.
- Whether FLUX.2 Klein's text encoder gets trained during LoRA training:
  genuinely not stated anywhere I found. Don't assume either way.
- A specialised tool called Fizgig claims Klein 9B LoRA training fits in
  16 GB and Krea 2 in 8 GB, which contradicts the more general ai-toolkit
  guide's own stated 24 GB floor. Worth trying if ai-toolkit OOMs, not yet
  independently verified.

## 4. Baseline scores (Task 3), recorded before any LoRA exists

From `offline/VALIDATION.md`, using the newly written `offline/score_set.py`
(imports `drift_gate.score_file()` and `bone_gate.measure()` — no scoring
logic reimplemented):

| pool | n scored | mean drift_gate cosine | mean nose_drop | mean face_len |
|---|---|---|---|---|
| `content/grid` | 28/40 (12 no face) | **0.663** | 0.5411 | 1.1643 |
| `content/week2` | 5/12 (7 no face) | **0.637** | 0.5364 | 1.1089 |

**A LoRA has to beat 0.663 mean cosine on an unseen 10-prompt test set
(Gate 2, `PLAN.md`) to be worth keeping.** Both gates were confirmed to run
cleanly and rebuild from `master/` (`canonical.npy` and `bone_stats.json`
were both regenerated as part of this check). One environment note, not a
blocker: `onnxruntime-gpu`'s CUDA provider fails to load here (missing
`cublasLt64_13.dll`) and both gates silently fall back to CPU — scoring still
works, just slower. Worth a CUDA runtime reinstall/match at some point but
did not block anything today.

## 5. What was NOT done, and why

- **No image was generated, anywhere, by anyone, for any reason** — every
  hard rule about spending held, and even the bake-off graphs (which cost
  nothing to run) were left for you to trigger, because Task 2's own rule
  ("do not judge image quality") means running one and not looking at the
  result would have been pointless, and running one and looking would have
  broken the rule.
- **No LoRA training config was finalised** — Task 4 was research only, per
  its own instruction. See `DECISIONS.md` section 3 for what's still
  unread (the RunComfy 16GB guide) and unresolved (whether 16 GB is really
  enough for Klein, at all, with any tool).
- **No weights were downloaded** — the three missing bake-off checkpoints
  (Klein 4B, Qwen-Image, Z-Image-Turbo) are named with exact HF paths in
  `bakeoff/README.md`, but pulling multi-gigabyte files onto a machine I
  can't watch, for results I'm not allowed to judge anyway, is your call
  and your bandwidth.
- **Qwen-Image and Z-Image-Turbo's LoRA training support at 16 GB was not
  researched** — only FLUX.2 Klein and Krea 2 were, because the brief named
  those two specifically. If either of the other two wins the bake-off,
  that gap needs closing before training.
