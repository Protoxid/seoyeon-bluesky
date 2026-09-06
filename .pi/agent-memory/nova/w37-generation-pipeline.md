---
name: w37-generation-pipeline
description: How to render W37 Instagram shots end to end (flags, files, plate ids, checkpoint script)
type: reference
---

W37 (Mon 7 – Sun 13 Sep 2026) lives in `personas/seoyeon/content/w37_2026-09-07/`.

**Pipeline (added by me 6 Sep, was the documented gap):**
- `w37_shots.py` — all seven prompts in the week2 dict shape (`id/day/tier/aspect/story/text` + `noface|selfie|plate|safe`).
- `outside.py --week3` → pool `W37_SHOTS`, destination `content/w37_2026-09-07`.
  Run one shot: `python outside.py --week3 --only w37_fan --n 1 --budget 0.30`
  (~2.5 min for 3 shots in parallel; each render 5–8 MB PNG, 3:4 at 2k.)
- `content/w37_2026-09-07/checkpoint.py <id> <file.png> "<publish_at>"` — writes
  `caps/<id>.txt` from `handoff.json["captions"][id]`, moves the entry from
  `blocked` to `entries`, prints `OK <id> <file> <n>`.
- Still missing: a `console.POOLS` row, so `weekly_prep.py` does not audit this pool.

**Plate ids that resolve** (via `pov.plate_path`, which matches `<id>_<6hex>_<n>.png`):
`plate_room` → `content/plates/plate_room_ecc050_1.png` ·
`plate_studio_wide` → `..._4e68ba_1.png` · `plate_rooftop` → `locations/rooftop.png`.
Bare `plate_studio`, `plate_kitchen`, `plate_window` do NOT resolve.

**Model routing is automatic in outside.py:** noface + plate → `gpt-image-2-image-to-image`
with the plate as Image 1; noface + no plate → `gpt-image-2-text-to-image` (no refs);
face shots → 2 face masters + optional body, plate prepended, ordinals computed by
`roles_for()` so the prompt never contradicts itself. $0.09/image either way.

**Reviewing renders:** never read the 8 MB PNGs. Make JPEG thumbs under
`_thumbs/w37b1/` (long edge ~760–900) and a labelled contact sheet
(masters + a shipped precedent + the plate + the render) — one read answers
identity, room continuity and framing at once.
