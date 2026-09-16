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
- Captions go to `personas/seoyeon/caps/<id>.txt` (what `ig_publish.py --caption-file` expects).
- **MANDATORY HASHTAGS (CONFIRMED)**: Every caption MUST conclude with the 5 canonical hashtags appended at the very end separated by a double line break:
  ```
  <caption text>

  #seongsu #seoul #daily #filmphoto #everyday
  ```
- **Plates Directory**: Correct plates directory is `personas/seoyeon/content/plates/*.png` (`plate_room_ecc050_1.png`, `plate_studio_wide_4e68ba_1.png`, `plate_bathroom_cdd2d8_1.png`, `plate_river_fa39bf_1.png`, `plate_hallway_ac909a_1.png`, `plate_stairwell_62963d_1.png`).
- **Anatomy & Tattoo Safeguards**:
  - Legs & Limbs: Check sitting and stretching poses for clean 2-leg separation, natural knees and feet.
  - Tattoo: Fine-line sprig on her **physical LEFT ribcage** below breast line (`master/c/tattoo_crop.png`). In mirror selfies, account for horizontal reflection inversion. Omit "tattoo" and set `body=False` when clothed.

## Lived History & Anti-Repetition Registry
- **W36**: Summer fan, cold barley tea, initial studio observation, subway line 2 commute.
- **W37**: Kalguksu meal, green peaches from market, Jieun rooftop meetup, rainy studio session.
- **Rule**: Do NOT repeat these specific objects, meals, or themes in subsequent weeks. Each week moves forward along her lived timeline.

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

