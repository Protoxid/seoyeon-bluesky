# PIPELINES — how an image gets made
**Two generation stacks run in parallel. That is deliberate.** Nearly every
contradiction in this repo came from a document asserting one "primary
generator" as if there were only one.
Last verified 6 Sep 2026.

---

## 1. WHICH MODEL, AND WHY

**Everything runs on Kie. fal.ai is deprecated** — `fal_api.py` no longer
exists and `outside.py` imports `kie_api`. Any document or comment still
naming fal is stale; correct it rather than working around it.

| tier | model | entry point | $/image |
|---|---|---|---|
| **1 — SFW** | `gpt-image-2-5-sunburst-image-to-image` / `-text-to-image` | `personas/seoyeon/outside.py --model gpt` | 0.09 |
| **2 and 3** | `seedream/5-pro-image-to-image` | `growth/generate_weekly_companion_sets.py` | 0.07 |

**Seedream is not chosen because it is better. It is chosen because
gpt refuses this content.** The standing warning in
`wiki/domains/pipeline/playbook.md` — that Seedream once "won" a bake-off only
because references were going to a field gpt does not read — is still
correct about SFW quality and must not be deleted. It simply does not apply
where gpt is not an option.

### ⚠ THE REFERENCE FIELD IS NOT THE SAME FOR ALL THREE

The usual rule is that a field belongs to the provider. **Here it varies
between models on the SAME provider**, which is worse, because a wrong field is
ignored rather than rejected — you get a plausible image generated from the
prompt alone with no identity input, and no error anywhere.

| model | reference field |
|---|---|
| `gpt-image-2-5-sunburst-image-to-image` | **`input_urls`** |
| `gpt-image-2-image-to-image` | **`input_urls`** |
| `gpt-image-2-text-to-image` | `image_urls` |
| `seedream/5-pro-image-to-image` | `image_urls` |
| `kling-3.0/video` | `image_urls` (first + last frame) |
| `bytedance/seedance-2-5` | `reference_image_urls` (max 2) |

This exact mistake invalidated a whole model bake-off once: gpt was
scored with no identity input at all, Seedream "won", and that wrong number sat
at the top of the playbook for a day telling every reader to pick the wrong
model. `kie_api.py` routes this correctly — do not bypass it with a hand-built
request body.

## 2. RESOLUTION

- **Seedream (tiers 2–3): `"tier": "1k"`** — 1024×1365 for 3:4. 2K costs ~4x
  and 1K keeps the filmic sensor grain. Enforce it.
- **gpt-image-2.5 (tier 1): `"tier": "1k"`** — accepts `resolution`: `"1K"`, `"2K"`, `"4K"`. Enforce 1K to conserve credits and preserve sensor grain.

## 3. THE TATTOO — a rendering problem, not a canon one

Canon says one thing (`CANON.md` §5): a fine-line two-branch botanical sprig,
left ribcage, below the breast line. Reference crop at
`personas/seoyeon/master/c/tattoo_crop.png`.

Getting it on screen is where the rules live, and they are opposite depending
on whether the ribcage is visible:

**Zero-Tattoo in Prompts.** Do NOT mention the word "tattoo" anywhere in the
prompts (clothed or bare). Prompting the word "tattoo" causes diffusion models to
hallucinate random ink, bleed ink onto fabrics, or mirror placement to the wrong
side. The visual master references (`c5_relax_front.png`, `tattoo_crop.png`) anchor
the tattoo directly to HER anatomical left ribcage without text interference.

**Clothed torso — SUPPRESS BODY REFS.** Set `"exclude_body_ref": True` so only
`a1_front.png` goes, and omit body references so tattoos never bleed onto fabric.

**Bare ribcage — ANCHOR VIA REFERENCES.** Condition on
`[a1_front, c5_relax_front, tattoo_crop]` without the word "tattoo" in the prompt.
The reference image physically has the sprig on her anatomical left ribcage.

**Why a reference alone is not enough.** The one rule everything follows from:
*a reference anchors what it visibly depicts, at the angle it depicts it.* A
front-on body frame does not anchor a left-ribcage tattoo, because the tattoo
is nearly edge-on. That is why `tattoo_crop.png` exists.

## 4. OTHER STANDING PROMPT RULES

- **Zero body prompting.** Never write "tiny waist" or "hourglass" — it renders
  a CGI wasp-waist. Her proportions come from the references.
- **Single strap.** Slips and camisoles must explicitly ask for one clean
  spaghetti strap per shoulder, or you get duplicates.
- **The phone.** White iPhone 15 Pro, plain clear case. Visible only in mirror
  selfies or propped on a table.
- **Mirror shots.** In a mirror selfie the phone in the reflection *is* the
  camera. "The camera is still" and "her arm moves" are two instructions about
  one object; give them opposite values and the phone slides inside a locked
  frame. State the eyeline **on the glass**, never in the room.
- **Plateless default (avoid plates).** Use plates as little as possible: at most a couple (~2) per week, restricted strictly to recurring indoor anchor locations (flat, studio). Attaching plates to outdoor scenes, streets, cafes, rivers, or parks causes glued-on composite artifacts. Rely on natural prompt descriptions and identity face references.
- **Video.** First-frame conditioning for anything without her face in it;
  reference conditioning when she is on camera. Kling holds motion but not
  identity; Seedance 2.5 with the turntable holds identity.

## 5. THE TIER GATE — the one piece of code that must not be decorative

`growth/syndicate.py` declares `sfw_only: True` on the Instagram and Threads
lanes. **As of 6 Sep that key is never read** — it appears four times in a
config dict and nowhere else in 693 lines, and no asset declares a tier. It is
a comment wearing a boolean's clothes.

Required: every asset carries `tier: 1|2|3`, and `preflight()` **refuses** a
lane whose `sfw_only` is true when the tier is above 1. Refuse, never downgrade,
never substitute. Until that exists, nothing structurally prevents a tier-3
image reaching Instagram.

## 6. VERIFIED API FACTS

Do not infer these. Every field name inferred on a previous provider was wrong
at least once.

**fal.ai** — full table in `personas/seoyeon/CLAUDE.md`. The load-bearing one:
the i2i reference field is **`image_urls`** on fal and was **`input_urls`** on
Kie for the same model. **The field belongs to the provider, not the model.**
Re-read it on every migration.

**Kie** — `seedream/5-pro-image-to-image`, `$0.07`/image (`kie_api.py PRICE`).

**Egress** — both `queue.fal.run` and `api.kie.ai` are blocked from the cloud
container and from `device_bash`. **Every generation call runs on the Windows
box.** This is not negotiable infrastructure; plan around it.

## 7. COST DISCIPLINE

Every script that spends takes an explicit `--budget` and refuses without one.
A guessed unit price in a budget guard is worse than no guard — `outside.py`
refuses to spend until `--unit-price` is given, because fal does not publish
per-image prices. Spend rows go to `growth/ledger.jsonl`.
