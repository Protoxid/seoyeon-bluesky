# Nova — memory index

Role: plan Seo-yeon Han's Instagram week and produce approved renders. Never
publish (Echo does). Source docs: `CANON.md`, `PLATFORMS.md` §1–2,
`roles/instagram_ops.md`, `personas/seoyeon/wiki/domains/persona/character.md`.

## Standing facts about the pipeline (verified, not assumed)
- Generation is **Kie**, `gpt-image-2-image-to-image`, $0.09/image, through
  `personas/seoyeon/kie_api.py`. fal is deprecated. The i2i reference field is
  `input_urls` — `model_schemas.build_input` sets it; never hand-build a body.
- `exclude_body_ref` does not exist in the code. The real mechanism is
  `body=True` / `limb=True` in `outside.py`: the body master
  (`master/c/c5_relax_front.png`, sports bra, visible ribcage) attaches only on
  those flags. Clothedy torso shots set neither and never say "tattoo".
- Plate ids resolve via `pov.plate_path` to `<id>_<6hex>_<n>.png`. The flat is
  `plate_room` → `plate_room_ecc050_1.png`; the studio is `plate_studio_wide` →
  `plate_studio_wide_4e68ba_1.png`. Bare `plate_studio`, `plate_kitchen`,
  `plate_window` do NOT resolve; `_superseded_rich_flat/` is a different flat.
- A no-face shot with no plate routes to `gpt-image-2-text-to-image` with zero
  references — that is correct, not a bug.
- Captions go to `personas/seoyeon/caps/<id>.txt` (what `ig_publish.py
  --caption-file` expects). Hashtags stay OUT of the body — the delivery
  mechanism is still unverified.

## Memory files
- [w37-generation-pipeline](w37-generation-pipeline.md) — how to render W37:
  `--week3` flag, `w37_shots.py`, `checkpoint.py`, plate ids, review workflow.
- [render-lessons-w37-batch1](render-lessons-w37-batch1.md) — what the first
  four images taught about curtains/light, fan motion, unbranded packaging,
  plate+face conditioning, batch checkpointing.

## Open threads
- **W37 batch 2** (Wed–Sun): `w37_studio_after`, `w37_jieun_roof`,
  `w37_market_peaches`, `w37_table_sunday`. Prompts already written and
  dry-run verified; `outside.py --week3 --only <id>` then `checkpoint.py`.
- No `console.POOLS` row for `--week3`, so `weekly_prep.py` does not audit the
  W37 pool yet.
- Two unverified docs flagged by the planning run: `PIPELINES.md` §5 (tattoo
  rendering rules) and `growth/RUNBOOK.md`. Neither was read.
