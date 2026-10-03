# OPERATOR BRIEF — generate the LoRA dataset, then train it

**You are the operator. You execute; you do not redesign.** The prompts, the
config and the dataset spec were written and checked already. If something
looks wrong, **stop and report it** — do not fix it yourself. A single
improvised change here costs real money or a wasted training run.

**Paste real terminal output for every verification step.** Do not summarise
and do not write "done" — the actual output is the proof. If you cannot show
the output, the step did not happen.

Machine: Windows, `C:\AI-Project\`. Everything below runs from
`C:\AI-Project\personas\seoyeon\` unless stated.

---

## RULES

1. **Never run a paid command without running its `--dry-run` first and
   pasting the result.**
2. **Never edit** `lora_shots.py`, `outside.py`, `audit.py`,
   `make_lora_dataset.py`, or `offline/train_krea2_seoyeon.yml`. They are
   checked. If one is wrong, report it.
3. **Never invent a value.** If a field needs something you do not have, stop
   and ask. An invented model path or scheduler produces a run that completes
   and is silently worthless.
4. **Do not judge whether an image looks good.** That is the human's job. You
   report counts, errors, and whether files exist.
5. If any check below fails, **stop at that step.** Do not continue "to save
   time". The later steps cost money.

---

# PART 1 — GENERATE THE DATASET  (costs ~$2.70)

### 1.0 A PREVIOUS RUN HAPPENED. READ THIS FIRST.

An earlier attempt generated **18 of the 30** shots (it did not finish) using
prompts that have since been rewritten. Those images are wrong in two ways
that cannot be seen by looking at them: they were made before clothing and
hair were controlled, and they came back in **three resolutions across two
aspect ratios**, which the research says degrades training.

They have been moved to `content/lora/_superseded_v1/`. **Do not use them, do
not move them back, and do not count them.** `content/lora/` itself must be
empty before you generate. Confirm with:

```
dir content\lora
```

It should contain only the `_superseded_v1` folder. If any `.png` sits
directly in `content\lora`, STOP and report it.

`make_lora_dataset.py` now refuses images whose prompt hash does not match the
current prompt, and refuses a set with mixed aspect ratios — so a repeat of
this cannot reach training silently. But the refusal happens AFTER the money
is spent, which is why this section exists.

### 1.1 Confirm the pool, spend nothing

```
python outside.py --lora --dry-run
```

**Must print exactly `30 shots, ~$2.70` on the last line.** Paste the last 5
lines. If the number is not 30 or the cost is not ~$2.70, STOP.

### 1.2 Confirm the audit is clean

```
python audit.py
```

Must end with `65 issue(s)`. That number is the project's known pre-existing
debt in other pools. **If it is higher than 65, something changed in the lora
pool — STOP and paste the lines containing `lx_`.**

### 1.3 Confirm there is credit

Kie had a zero balance. Generating with no credit returns HTTP 402 and costs
nothing, but wastes the run. Confirm with the human that the account is topped
up before the next step. **Do not top it up yourself.**

### 1.4 Generate

```
python outside.py --lora --all
```

This spends about **$2.70**. Run it ONCE. If it fails part-way, paste the
error and STOP — do not re-run the whole set, because the shots that already
succeeded would be paid for twice.

### 1.5 Verify what arrived

```
python make_lora_dataset.py --check
```

Expected: `found 30/30`, and `mix close 12  half 9  full 9`.
Paste the whole output. If any are missing, list which.

### 1.6 HAND BACK TO THE HUMAN — curation

**Stop here.** The human opens the 30 images and decides which to discard.
You cannot do this; you are not allowed to judge image quality.

Tell them: *the recipe wants 15–40 images and says 20 good ones are enough, so
discarding some is normal. Curate on whether the skin and light look
photographic, not on whether it looks like her.*

They give you back a list of ids to drop.

### 1.7 Build the training folder

```
python make_lora_dataset.py --build --skip <ids they gave you, comma separated>
```

Must end with `_lora_dataset/  N images, N captions` and the two numbers must
be EQUAL. It refuses below 15 images, above 40, under 3 full-body or under 5
close — those are the recipe's floors. If it refuses, paste the reason and
report it; do not force it.

Upload **only** `_lora_dataset/` to the pod. Nothing else from this machine.

---

# PART 2 — TRAIN  (costs GPU rental)

### 2.1 Pod

Rent a GPU with ai-toolkit. **Confirm the hourly rate before starting** and
report it — do not assume a figure from anywhere, including this document.

Install: `github.com/ostris/ai-toolkit`, per its own README.

### 2.2 Get Krea 2 **RAW** — not Turbo

The LoRA trains against **Krea 2 Raw**, the undistilled base. **Turbo is only
used later, to judge the result.** If you download Turbo and train on it, the
run is wasted. Confirm you have Raw by name before continuing and report the
exact filename or repo id.

### 2.3 The config — and the one thing you must check yourself

Copy `offline/train_krea2_seoyeon.yml` to the pod.

**Open ai-toolkit's own example config for Krea 2** (in
`ai-toolkit/config/examples/`) and **diff it against ours.** Four lines in ours
are marked `### CONFIRM` because they could not be verified:

* `model.name_or_path` — the Krea 2 Raw path. **It is a placeholder. It will
  not run until you fill it in.**
* `model.arch`
* `model.quantize_te`
* `sample.sampler`

Where the repo's example disagrees with ours on a **key name**, the repo wins —
it is the code that parses the file. **Where it disagrees on a VALUE, stop and
report it**, because our values are from the Krea-2 recipe and the repo's
examples are often generic FLUX defaults.

**Two values in particular must survive whatever you do:**

```
noise_scheduler: "flowmatch"
timestep_type:   "linear"
```

The recipe names importing FLUX settings as the single most common mistake.
If either of these ends up as `sigmoid` or `weighted`, the run finishes and
the LoRA is quietly bad. Paste these two lines back after editing.

Also confirm `train_text_encoder: false` survived.

### 2.4 Point it at the dataset

`datasets[0].folder_path` must be the uploaded `_lora_dataset` folder. The
folder is flat: `lx_c01.png` beside `lx_c01.txt`, and so on. Confirm with a
directory listing that images and `.txt` files are equal in number.

### 2.5 Run

Report: the step count reached, the wall-clock time, and the checkpoint
filenames written. Save checkpoints every 250 steps — **the best LoRA is often
not the last one.**

**Expect the training samples to look flat and plastic.** They render on Raw,
and the recipe lists that as expected behaviour, not a fault. **Do not report
it as a problem and do not stop the run over it.**

### 2.6 Bring back

Only the `.safetensors` LoRA files. Nothing else needs to leave the pod.
Report their names and sizes.

---

# PART 3 — HAND BACK

Write `offline/RUN_REPORT.md` with:

1. Dataset: how many generated, how many the human kept, final counts by
   framing, total spent.
2. Any prompt that failed or produced an error.
3. Pod: GPU model, hourly rate, total hours, total cost.
4. Every `### CONFIRM` line: what you set it to, and what the repo's example
   said.
5. Checkpoint filenames and step counts.
6. **Anything you were unsure about and did anyway** — this section matters
   more than the others. If it is empty, say so explicitly.

## WHAT YOU DO NOT DO

* Do not judge image or LoRA quality.
* Do not train on Turbo.
* Do not regenerate images the human discarded.
* Do not change rank, learning rate, steps, or schedulers "to improve results".
* Do not auto-caption. Captions come from `lora_shots.py` and are already
  written to the recipe's schema, with the trigger `sy3nh`.

## THE GATE, FOR AFTERWARDS

A LoRA is worth keeping only if it beats **0.663 mean drift_gate cosine** on
prompts it never saw. Score with `offline/score_set.py`. That number was
recorded before any LoRA existed, which is the only reason it can be trusted.
