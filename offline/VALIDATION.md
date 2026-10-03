# VALIDATION — identity gates, and the pre-LoRA baseline

Written 2026-09-04, before any LoRA exists, so these numbers cannot be
rationalised after the fact once one does. This is Task 3 of `BRIEF.md`.

---

## 1. The two gates, confirmed running

Both `drift_gate.py` and `bone_gate.py` live in `personas/seoyeon/` and both
run from there (they resolve `canonical.npy` / `bone_stats.json` and
`master/` relative to their own file, not the CWD).

```
cd personas/seoyeon
python drift_gate.py --calibrate
python bone_gate.py --calibrate
```

**drift_gate.py --calibrate** rebuilds `canonical.npy` from
`master/a/{a1_front,a2_tq_left,a3_tq_right}.png` (the two profiles,
`a4`/`a5`, are deliberately excluded — see the comment in the file). Ran
clean on 2026-09-04:

```
a1_front.png   0.911
a2_tq_left.png 0.904
a3_tq_right.png 0.909
stack agreement: mean 0.737  worst pair 0.728  (3 frames)
```

`canonical.npy` existed already and was rebuilt as part of this check — the
rebuild is deterministic from the same three master frames, so this did not
change what the gate measures, only confirmed it can be regenerated.

**bone_gate.py --calibrate** rebuilds `bone_stats.json` from
`master/a`, `master/b`, `master/c` (17 frames, 5 excluded for yaw >= 0.35 —
profiles cannot be measured by a frontal instrument). Ran clean on
2026-09-04:

```
nose_drop   mean 0.5532  sd 0.0421  n=12
face_len    mean 1.0343  sd 0.0661  n=8
```

Both scripts need `insightface`, `onnxruntime` (or `onnxruntime-gpu`),
`opencv-python`, `numpy` — all present in this environment
(`python -c "import insightface, onnxruntime, cv2, numpy"` succeeds).

**Environment note, not a blocker:** `onnxruntime-gpu`'s CUDA execution
provider fails to load here (`onnxruntime_providers_cuda.dll` depends on
`cublasLt64_13.dll`, which is missing) and both gates fall back to CPU
automatically, printing `device: CPU`. Scoring still completes; it is just
slower than it would be on GPU. This is a CUDA-runtime-version mismatch, not
a code problem — see `HANDBACK.md`.

---

## 2. `offline/score_set.py`

Written for this task. Imports `drift_gate.score_file()` (cosine + face
pixel width) and `bone_gate.measure()` (raw `nose_drop`/`face_len` ratios)
directly — it does not reimplement either measurement. Run from
`personas/seoyeon/`:

```
python ../../offline/score_set.py content/week2
python ../../offline/score_set.py content/grid
```

(It also resolves paths relative to the project root or the CWD, so
`python offline/score_set.py personas/seoyeon/content/week2` works too.)

Add `--json out.json` to also write the per-file rows plus the three means.

---

## 3. BASELINE — recorded BEFORE any LoRA exists

This is the bar a trained LoRA has to beat on Gate 2 of `PLAN.md`. Both
folders are cloud-generated (`gpt-image-2`) stills from before this pivot.

### `content/grid` (40 files, 28 with a detectable face)

| metric | mean |
|---|---|
| drift_gate cosine | **0.663** |
| bone_gate nose_drop | 0.5411 |
| bone_gate face_len | 1.1643 |

Per-file range: cosine 0.068 (`n_studio_dawn_6df563_1.png` — face only 54px
wide, an extreme case that should probably be excluded from any comparison
set rather than treated as a real low score) up to 0.820
(`n_cafe_jieun_b3c66f_1.png`). Excluding that one outlier the low end is
0.470.

12 files had no face detected at all by drift_gate (no-face shots, distant
figures, or back-turned frames) and are not in the mean.

### `content/week2` (12 files, 5 with a detectable face)

| metric | mean |
|---|---|
| drift_gate cosine | **0.637** |
| bone_gate nose_drop | 0.5364 |
| bone_gate face_len | 1.1089 |

7 of 12 had no detectable face (this pool leans heavily no-face/object shots
per its shot list).

### Reading these numbers

- Both means sit **below** the head-shot PASS bar of 0.75 in `drift_gate.py`,
  because most of these frames are half-body/full-body/distant, which score
  lower by geometry alone (see `thresholds()` in `drift_gate.py`) — this is
  not itself evidence of drift.
- The full per-file breakdown is saved in [`offline/baseline_grid.json`](baseline_grid.json)
  and [`offline/baseline_week2.json`](baseline_week2.json), produced by
  `score_set.py --json` on 2026-09-04. These are a dated snapshot, not a
  living doc — if the master stack or the pools change, re-run `score_set.py`
  rather than editing these files by hand.
- **A LoRA's test set (Gate 2, per PLAN.md) must be scored the same way, on
  10 unseen prompts, and beat 0.663 mean cosine to be worth keeping** — that
  is the number from the stronger of the two baselines (`content/grid`,
  larger n). Do not compare against a cherry-picked subset.

---

## 4. What this does NOT establish

- No bone_gate STRUCTURE verdicts (z-scores) are reported here — the brief
  asked for cosine and bone ratios, not a pass/fail per file. The raw ratios
  are what `bone_gate.py`'s own `score()` would compare to `bone_stats.json`;
  computing STRUCTURE flags for these two folders is a five-minute follow-up
  if the operator wants it (`python bone_gate.py --in content/grid`), left
  undone here because judging what counts as a flag-worthy deviation is a
  threshold decision, not a data-gathering one.
