# WORK ORDER — offline pipeline, phase 0 and phase 1 prep

**For an agent with no memory of this project.** Read this whole file first.
Read `PLAN.md` next to it for the reasoning; this file is what to DO.

The operator is out for roughly two hours and cannot answer questions or look
at anything. Prepare everything; decide nothing that needs eyes.

---

## HARD RULES — these are not preferences

1. **SPEND NOTHING.** No paid API call, of any kind, for any reason. Kie has a
   zero balance and will return `402` anyway, but do not attempt it. Do not run
   `outside.py` without `--dry-run`. Do not run any `make_*.py` except with
   `--dry-run`.
2. **PUBLISH NOTHING.** Do not run `ig_publish.py` or `publish_queue.py --due`.
3. **DELETE NOTHING.** `device_bash` cannot delete anyway; move to `_trash/`
   and say so.
4. **DO NOT TRAIN ANYTHING.** The base model is not chosen yet. Training before
   the bake-off is choosing by accident.
5. **DO NOT JUDGE IMAGE QUALITY.** Realism is the operator's call, made at 100%
   zoom, on their monitor. Your job is to make the comparison possible, not to
   have an opinion about it.
6. If a step needs a decision you cannot make, **write it into
   `offline/DECISIONS.md` and move on.** Do not guess and do not stall.

---

## CONTEXT IN TEN LINES

An AI persona ("Seo-yeon Han", `@syeon.hn`) was run on cloud generators for a
month: EUR 100+ spent, 82% of generations discarded, 0 followers, project
paused. The cloud pipeline works and is documented in
`personas/seoyeon/wiki/`. The pivot is to LOCAL generation so that iterating
costs nothing, with a trained identity LoRA so that every render is reliably
her.

Two things are already solved and must not be reinvented:
* **Identity scoring.** `personas/seoyeon/drift_gate.py` (ArcFace cosine
  against `canonical.npy`, built from `master/a/`) and `bone_gate.py`
  (vertical facial proportion ratios).
* **Identity for VIDEO.** Seedance 2.5 with `master/turntable.png` as a
  reference holds her. Video stays in the cloud. Do not touch it.

Hardware: **16 GB VRAM**, ComfyUI, Windows. Paths on that machine are
`C:\AI-Project\...`; through `device_bash` the same tree is at
`$HOME/mnt/AI-Project/...`.

---

## TASK 1 — wire up the LoRA dataset pool  (no spending)

`personas/seoyeon/lora_shots.py` already exists: 30 shots, `SHOTS` list, same
dict shape as `week2_shots.py`. It is NOT yet registered anywhere.

Do:
* Register it in `console.py`'s `POOLS` dict as `"lora"` ->
  `("lora_shots", "SHOTS", ["--lora"], "content/lora")`.
* Add a `--lora` flag to `outside.py` alongside `--week2`, `--fanvue` etc.,
  routing to the same code path those use.
* Make sure `audit.py` and `weekly_prep.py` pick the pool up. Both discover
  pools dynamically — verify rather than assume, by running them.

Accept when: `python outside.py --lora --dry-run` prints 30 assembled prompts
and a total cost of about **$2.70**, and `python audit.py` includes the `lora`
pool in its output.

**Then stop. Do not generate them.**

---

## TASK 2 — the base-model bake-off rig  (no spending, no judging)

The current workflow uses `flux-2-klein-9b-fp8`. That was inherited, never
chosen. Klein is FLUX.2's *efficiency* tier — FLUX.2 [dev] is reported at
~32 GB fp8, which does not fit 16 GB. Candidates that reportedly do fit:

| candidate | reported VRAM | note |
|---|---|---|
| FLUX.2 Klein 9B | fits (currently installed) | the incumbent |
| FLUX.2 Klein 4B | ~13 GB | smaller sibling, sometimes better on 16 GB |
| Krea 2 Turbo | ~12 GB fp8 | **one source** calls it the open-weight photoreal leader, "within 0.14 points of GPT Image 2 on style fidelity", trained on real photos with no synthetic data. UNCORROBORATED — a lead, not a fact |
| Qwen-Image | ~8–12 GB | strong general, native 2K |
| Z-Image-Turbo | fits 16 GB | named by a second source |

Do:
* **Research first, and cite.** Confirm which of these actually exist as
  downloadable weights, their real VRAM at fp8, and whether ComfyUI supports
  them natively or needs custom nodes. Write findings with sources into
  `offline/DECISIONS.md`. **If you cannot verify something, say so — do not
  fill the gap.**
* Write `offline/bakeoff/` containing one ComfyUI workflow JSON per viable
  candidate, **identical in every respect except the model**: same prompt,
  same seed, same resolution (896x1152), same steps, same sampler.
* The prompt must be a HUMAN FACE with visible skin, close enough to judge
  pores. Do not use the persona; use a generic description. This tests the
  MODEL, not the character.
* Write `offline/bakeoff/README.md`: what to download, where each file goes,
  the exact run order, and what the operator is looking for (skin texture at
  100% zoom, not composition, not likeness).

Do NOT download multi-gigabyte weights unless disk space is confirmed free —
check first and record the figure.

**Known blocker to fix first:** the operator's current workflow renders
speckled, noisy output. That is not guidance or LoRA related; it has the
signature of an fp8 `weight_dtype` mismatch or a VAE that does not match the
checkpoint. `UNETLoader` is currently `weight_dtype: "default"` with an fp8
file. Investigate, write the candidate fixes into `DECISIONS.md`, and put a
corrected workflow in `offline/bakeoff/00_fix_speckle/`. **The bake-off is
meaningless until a clean render is possible.**

---

## TASK 3 — validation harness  (no spending)

Do:
* Read `drift_gate.py` and `bone_gate.py`. Confirm they run, that
  `canonical.npy` exists or can be rebuilt from `master/a/`, and record the
  exact commands in `offline/VALIDATION.md`.
* Write `offline/score_set.py`: point it at a folder of images, get back a
  table of drift_gate cosine and bone_gate ratios per file, plus a mean.
  Reuse the existing modules — **import them, do not reimplement the scoring.**
* Establish the BASELINE: score the current cloud-generated stills
  (`content/grid/`, `content/week2/`) and write the numbers into
  `VALIDATION.md`. This is the bar a LoRA has to beat, and it must be recorded
  BEFORE any LoRA exists so it cannot be rationalised afterwards.

Accept when: `python offline/score_set.py content/week2` prints per-image
scores and a mean, and the baseline is written down.

---

## TASK 4 — training config, researched not written  (no spending)

Do NOT train. Do NOT download trainers.

Research and record in `offline/DECISIONS.md`, with sources:
* Which trainer is current for the candidate models on 16 GB — ai-toolkit
  (ostris), kohya_ss / sd-scripts, OneTrainer, FluxGym.
* Whether LoRA training is supported at all for each bake-off candidate. Newer
  bases often have inference support long before training support. **This may
  eliminate a model that wins the bake-off, so find out early.**
* Real settings for 16 GB: quantisation, resolution, batch size, gradient
  checkpointing, optimiser, rank, learning rate, step count, whether the text
  encoder is trained.
* A published source specifically on FLUX.2 Klein LoRA training at 16 GB
  exists — including when the 4B variant beats the 9B. Find it and read it.

**Every number must carry a source. An unsourced number is worse than a blank,
because a blank gets checked.**

---

## WHAT NEEDS THE OPERATOR WHEN THEY RETURN

Leave `offline/HANDBACK.md` containing exactly these, filled in:

1. The speckle diagnosis, with the specific change to try.
2. The bake-off: which candidates are viable, what to download, and the run
   order. **They judge. You do not.**
3. Anything in `DECISIONS.md` that is still open.
4. The recorded baseline scores from Task 3.
5. One line: what you did NOT do, and why.

---

## ORDER

Task 1 → Task 3 → Task 2 → Task 4. Task 1 and 3 are self-contained and cannot
fail; do them first so there is something finished even if the research on 2
and 4 goes badly.

## THE POINT

The purpose of all of this is not a LoRA. It is a pipeline where **being wrong
is free**. The cloud version failed because every mistake cost a euro and every
prompt was a one-shot bet. If the end state still costs money per attempt, the
plan failed even if the LoRA is excellent.
