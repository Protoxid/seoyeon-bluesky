# Training — Krea 2 identity LoRA, ai-toolkit, rented GPU

Decided 4 Sep 2026. Supersedes the "16 GB local training" branch in `PLAN.md`:
training moves to a rented GPU, **inference stays local** on the 16 GB card.

**Source for everything in the settings table:** a community-calibrated Krea-2
LoRA workflow for face/character training on Ostris AI-Toolkit —
`github.com/chengyansen-ai/krea2-lora-training`. **Community, not official.**
It is specific to this model and internally coherent, which is more than any
general Flux guide offers, but nothing here is vendor-confirmed.

---

## The two things that would have wasted a run

### 1. TRAIN ON RAW. RUN ON TURBO.

Krea 2 ships as **Raw** (undistilled base) and **Turbo** (distilled, fast).
Train the LoRA against **Raw**; use **Turbo** only to judge the result. The
obvious move — train on the model you intend to generate with — is the wrong
one here.

Consequence: Raw previews *look flat and plastic during training*. The recipe
lists "plastic appearance on Raw" under **expected behaviour, not a fault**.
Given this project's history, that is the single most likely reason to abandon
a perfectly good run out of despair at 2am. Judge on Turbo or do not judge.

### 2. DO NOT IMPORT FLUX SETTINGS.

Named as the most common mistake. Krea 2 needs:

```
timestep_type:    linear
noise_scheduler:  flowmatch
```

Not sigmoid, not weighted. A default ai-toolkit config carries FLUX values and
will not warn you.

---

## Settings

| setting | value |
|---|---|
| base | **Krea 2 Raw** |
| rank / alpha | 32 / 32 (no conv rank on this model) |
| learning rate | 1e-4 to start; 5e-5 if it overfits |
| optimiser | AdamW8Bit, cosine schedule |
| steps | 2500 first run; 3000–4000 if lr dropped to 5e-5 |
| batch / grad accum | 1 / 1 (accum 2 for smoother gradients) |
| text encoder | **not trained** — Qwen3-VL-4B is too large; saves VRAM, more stable |
| quantisation | qfloat8 on transformer and text encoder |
| resolution buckets | 512 + 768 + 1024 — composition, quality, face detail |

**Verification, on Turbo:** 8 steps, CFG 0, LoRA weight 1.0, mu 1.15.

**Three prompts per checkpoint:** one in-distribution, one novel scene, and one
**without the trigger word** to confirm the base model is not contaminated.
That third test is the one people skip and it is the one that catches a LoRA
that has eaten the whole model.

---

## Dataset — what the research changed

Two sources, cross-checked against each other and against the Krea-2 recipe.

**Source A** — the Krea-2 workflow already cited above (framing mix, step
counts, schedulers).
**Source B** — Rishi Desai, *Unlocking Character LoRAs with Structured
Captions* (rishidesai.org/posts/character-lora), which is specifically about
why character LoRAs fail: *"Even with high-quality images the results were
disappointing... the issue wasn't with the images but the captions."*

### 1. UNIFORM ASPECT RATIO — the fault that was about to ship

Source B: **"inconsistent aspect ratios degrade generation quality"**, and
recommends uniform resolution, 1024x1024 or higher.

The dataset had **two** ratios — 1:1 for the twelve close shots, 3:4 for the
eighteen half and full ones. That was mine, chosen per-shot because a square
suits a portrait, and it was wrong. **All thirty are now 3:4.**

Note the tension, since it is real: ai-toolkit does aspect-ratio bucketing, and
the Krea-2 recipe's `resolution: [512, 768, 1024]` implies mixed shapes are
handled. Bucketing SUPPORTING mixed ratios is not the same as mixed ratios
being FREE. Uniformity costs nothing here, so it wins.

### 2. CAPTIONS: DESCRIBE WHAT VARIES, DELETE WHAT DOES NOT

Source B's template:

    [Trigger] [Style], [Notable Features], [Clothing], [Pose],
    [Expression], [Background], [Lighting], [Camera Angle]

with two rules that decide everything:

* **"Do not include inherent features that are constant, such as eye, hair, or
  skin color, unless it's variable to the character."** Anything captioned
  becomes editable at inference; anything left out is absorbed into the
  trigger. Caption her face and you teach the model her face is optional.
* **"If certain elements like clothes, expressions, or style are constant —
  remove it from the template."**

Applied: `style` and `notable features` are gone (constant across all thirty,
so they belong in the trigger). So are `single person` and `sharp focus`,
which were in every caption and therefore doing nothing but taking tokens.
Hair STYLE stays because it genuinely varies — sixteen shots up, fourteen down
— which is exactly the "unless it's variable" clause. Hair and skin COLOUR are
absent by design.

Final shape:

    sy3nh, [clothing], [hair], [pose], [expression], [background],
    [lighting], [camera angle]

### 3. FRAMING MIX — corroborated, not changed

Source B's own set was 18 images: 1 frontal, 5 full-body angles, 4 face
angles, 4 expressions, 4 lighting conditions — about 28% full body. Source A
asks for 30%. The dataset's 12 close / 9 half / 9 full sits between them.
Two independent sources agreeing is the only reason this number is trusted.

## Dataset — as built

`personas/seoyeon/lora_shots.py`, 30 shots, ~$2.70 on Kie, written to this
recipe: **12 close / 9 half / 9 full body (40/30/30)**, 25 distinct
backgrounds, shoes visible in every full-body shot, head never filling the
frame, captions in the recipe's own schema with the fictional trigger `sy3nh`.

Recipe says 15–40 images and that 20 good ones suffice, so **expect to discard
some after curation and still be fine.** Curate on realism, not likeness.

---

## Rented GPU

The 16 GB constraint only ever applied to *training*. Renting removes it, and
the economics are the right shape for the first time in this project:

* **one-off cost per training run**, not a cost per image forever
* inference afterwards is local and free
* a failed run costs one rental, not a growing per-image bill

Confirm the hourly rate at booking rather than trusting any figure here — GPU
rental pricing moves. Budget a small number of hours for 2500 steps at batch 1.

**Bring back:** the `.safetensors` LoRA. Nothing else needs to leave the pod.

---

## Pitfalls, from the same source

| symptom | real cause | fix |
|---|---|---|
| LoRA barely does anything | weak captions, low trigger consistency | 3000–4000 steps; rank 64 only as a last resort |
| background or composition bleeds in | repetitive dataset, vague captions | more variety; earlier checkpoint; lr 5e-5 |
| face drifts at inference | **the sampler**, not the training | Euler + simple before blaming the LoRA |
| plastic on Raw | expected | verify on Turbo |
| tattoo or fine detail missing | no close-ups, 1024 bucket unused | add close-ups, name the detail in captions |

The tattoo row matters here: canon puts a fine-line botanical tattoo on her
**left ribcage below the bra line**. If it needs to survive into the LoRA, the
dataset needs shots that show it and captions that name it — and the current
30 do neither, deliberately, because every one of them is clothed.

---

## Gate, unchanged

A LoRA is worth keeping only if it beats the recorded baseline on unseen
prompts: **0.663 mean drift_gate cosine** (`offline/VALIDATION.md`). Score it
with `offline/score_set.py`. The number was written down before any LoRA
existed, which is the only reason it can be trusted.
