# Offline pipeline — plan

Written 4 Sep 2026, after the cloud pipeline was stopped at EUR 100+ spent and
zero earned. Target hardware: **16 GB VRAM**. First priority: **identity
consistency**.

This folder is deliberately OUTSIDE `personas/seoyeon/`. The workflow is
infrastructure and could serve a second persona; only the trained weights and
the dataset are hers.

---

## 1. Why this is worth doing, in one paragraph

Not because local is better. Because **iteration stops costing money.**

The cloud pipeline discarded 82% of what it generated — 326 images, 58 kept.
At $0.09 an image and $0.56–$1.89 a clip, every rejected attempt was a real
euro, so the project could never afford to iterate, and every prompt was a
one-shot bet placed at 2am. Locally the marginal cost of a render is
electricity. **The 82% discard rate stops being an expense and becomes a
workflow**, and that is the actual fix to the economics that killed this.

Everything else in this plan is secondary to that.

---

## 2. The trap, stated first because it is counterintuitive

**A LoRA trained on gpt-image-2 output will reproduce gpt-image-2's failures.**

A LoRA distils what it is shown. The kept images carry the exact faults this
project has fought for a month: over-smooth skin, symmetrical framing,
pore-free complexion, the "glass skin" look that reads as rendered. Train on
58 of those and the result is a model that produces that look **more
reliably, faster, and for free** — a machine for manufacturing the specific
problem you were trying to solve.

There is a second, subtler version: with 18 master frames, a face LoRA may
learn *"gpt-image-2's way of drawing a face"* at least as strongly as it
learns *her* face. Identity and rendering style are entangled in the data and
nothing in the training separates them.

**Mitigations, in order of importance:**

1. **Curate against realism, not against likeness.** Include an image only if
   the SKIN and LIGHT already look photographic. A gorgeous likeness with
   plastic skin is a poisoned sample. Expect to keep far fewer than 58.
2. **Prefer variety over volume.** Angle, expression, lighting direction,
   distance, crop. Twenty varied images beat sixty similar ones, and sixty
   similar ones actively teach the model to produce one pose.
3. **Exclude the turntable.** It is one lighting setup, one backdrop, one
   expression, twelve times. As a *conditioning* reference it is excellent —
   that is proven, Seedance held her with it. As *training data* it would
   teach a grey studio backdrop.
4. Accept that the first LoRA may need throwing away. Budget for two.

---

## 3. Order of operations, and the gate that comes first

**PHASE 0 — prove the base model before training anything.**

Generate a photorealistic image of ANY woman locally, with skin that survives
a 100% zoom. No LoRA, no references, nothing persona-specific.

*Why this comes first:* a LoRA changes WHO is in the picture. It does not
change whether the picture looks like a photograph. If Flux 2 Klein at these
settings cannot produce convincing skin, a LoRA will produce unconvincing skin
that happens to look like her — and days of training will have bought nothing.
**Separate the identity problem from the realism problem, and solve realism
first, because it is the one a LoRA cannot fix.**

Known-open at the time of writing: the current workflow renders speckled,
noisy output. That is not a guidance or LoRA problem — it has the signature of
an fp8/dtype or VAE mismatch. **Phase 0 is not passed until that is gone.**

> GATE 0 — a local render whose skin holds up at 100% zoom. If this cannot be
> reached in one evening, stop: the problem is the local stack, not training.

---

## 4. Dataset (Phase 1)

**Source.** `personas/seoyeon/master/` (a: 5 face angles, b: 7 expressions,
c: 6 body) plus the best of `content/grid/` (40) and `content/week2/` (12).

**Target.** 20–40 images after curation. Not more.

**Curation rule — one line, applied ruthlessly:** *would this pass as a
photograph if it were of a stranger?* If the answer is no, it teaches the
model to fail.

**Captions.** One per image. Describe what VARIES (pose, framing, expression,
lighting, clothing) and never what is CONSTANT (her face). Captioning the
constant teaches the model to treat it as optional.

**Never in the dataset:** the turntable sheet; anything with visible AI
artefacts; near-duplicates; anything where the crop cuts the face.

---

## 5. Training (Phase 2) — VERIFY BEFORE COMMITTING

**Everything in this section is unverified and must be checked against current
documentation before a single training run.** The tooling for FLUX.2 moves
fast and this plan was written without access to the current numbers. Do not
treat the following as settings; treat it as a list of decisions to make.

**Tooling candidates:** ai-toolkit (ostris), kohya_ss / sd-scripts, OneTrainer,
FluxGym. ai-toolkit is the most commonly used for Flux character LoRAs.

**The 16 GB question.** Published guidance exists specifically on FLUX.2 Klein
LoRA training at 16 GB — including when the smaller **4B** variant is the
better choice than the **9B** currently loaded in the workflow. Read it before
choosing. Expect to need quantisation, gradient checkpointing, batch size 1,
reduced resolution, and a memory-efficient optimiser.

**Decisions to make and record:** base variant (9B vs 4B) · quantisation ·
resolution · rank · learning rate · step count · whether the text encoder is
trained at all.

**Fallback if training will not fit:** SDXL. Older, lower ceiling, but LoRA
training on 16 GB is well-trodden and the identity problem may be solved there
at a fraction of the effort. A working SDXL LoRA beats a Flux LoRA that OOMs.

> GATE 1 — one training run completes without OOM and produces a loadable
> LoRA. Nothing about quality yet, just that the pipeline runs end to end.

---

## 6. Validation (Phase 3) — the half already built

**Do not judge the LoRA by eye.** The project already has the instruments:

* **`drift_gate.py`** — ArcFace embedding, averaged across `master/a/` into
  `canonical.npy`, then cosine similarity for any new image. Its own docstring
  says it exists *because* there was no LoRA. It now becomes the LoRA's exam.
* **`bone_gate.py`** — vertical facial proportion ratios. Identity by bone
  structure rather than expression, which is what drift_gate's number moves
  around on.

**Write the pass mark down BEFORE training.** Pick a target cosine score and a
bone-ratio tolerance in advance, or the numbers will be rationalised after the
fact — the same failure as judging a render at 2am, with extra steps.

**Test set:** 10 prompts the LoRA has never seen, spanning angles and lighting
that are NOT in the training data. A LoRA that only holds up on poses it was
trained on has memorised, not learned.

> GATE 2 — the LoRA beats the current no-LoRA reference-conditioning approach
> on drift_gate, measured on the unseen test set. **If it does not beat what
> already works, it is not worth keeping**, however much effort it cost.

---

## 7. Integration (Phase 4)

Local generation replaces gpt-image-2 for stills. Everything downstream is
unchanged and already works: `publish_prep.py`, `audit.py`, `audit_video.py`,
`weekly_prep.py`, `ig_publish.py`, `publish_queue.py`.

**Video stays in the cloud.** Local video at 16 GB is a different and much
harder problem, and the identity question for video is already answered —
Seedance 2.5 with the turntable as a reference held her when four other
engines failed. Do not re-litigate a solved problem to save a dollar.

---

## 8. Kill gates, because the last attempt did not have any

| gate | pass condition | if it fails |
|---|---|---|
| 0 | a local render with photographic skin at 100% zoom | stop — the stack is broken, training cannot help |
| 1 | a training run completes and loads | try the 4B variant, then SDXL, then stop |
| 2 | beats reference-conditioning on drift_gate, unseen prompts | keep the reference workflow, discard the LoRA |
| 3 | a full post produced locally, start to finish, at zero marginal cost | the economics have not changed; reconsider |

**Gate 3 is the one that matters.** The purpose of this plan is not a LoRA. It
is a pipeline where being wrong is free. If the end state still costs money per
attempt, the plan failed even if the LoRA is excellent.

---

## 9. What this plan does NOT solve

It does not solve the thing that actually stopped the project. **Nine people
visited the profile in the best week and none of them followed.** That is a
content and positioning problem, and a perfect local pipeline generating the
same posts more cheaply will produce the same zero.

Worth doing anyway — cheap iteration is what makes finding the answer
affordable — but it should be built knowing it buys the ability to search, not
the answer.
