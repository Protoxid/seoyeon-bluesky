# Playground run sheet — Seo-yeon

## The rule that governs all of this

**When a reference image is attached, keep the prompt SHORT.** A long
description competes with the photo — the model starts generating from your
words instead of reproducing the image. Your 12-panel turntable came from one
sentence. That is not a fluke, it is the mechanism.

Corollaries, each learned the hard way this session:

- **Never use negations.** "No scars" produces scars. "No specular highlights
  on the forehead" produces a forehead highlight. Describe only what you want.
- **Never use conditionals.** "A dimple *only when she smiles*" put a smile on a
  neutral frame. If a feature belongs to one panel, say it in that panel only.
- **Never emphasise.** "Clearly darker than the others" rendered the nose
  freckle as a blot. Anything already visible in the reference needs no words.
- **Text is only for what the reference cannot show.** A head-and-shoulders
  photo says nothing about her body — that is the one place description earns
  its length.

---

## Settings (every sheet)

| Setting | Value |
|---|---|
| Model | GPT Image 2 |
| Reference | `seed_gpt-image-2/seed06.png` — attach as File 1 |
| Aspect | 3:4 for head sheets · 2:3 or 3:4 for body |
| Resolution | Highest available |
| References | One. seed06 only. Do not attach generated frames. |

---

## Panel count vs detail

A 4K canvas split twelve ways gives ~768x1365 per panel — far below seed06's
2016x2688. **Four panels per sheet (2x2) gives ~1536x2048**, close to native and
still one coherent generation. So: more sheets, fewer panels each.

Every sheet references seed06, so they stay consistent with each other.

---

## SHEET A1 — Core angles (the ones you will actually use)

Attach seed06 as File 1. Aspect 3:4, highest resolution.

```
Generate a turntable of the subject in File 1.

Four panels in a 2x2 grid, each labelled underneath. The same woman in every
panel — same face, same hair, same wardrobe, same seamless grey studio
backdrop, same soft even lighting. Head and shoulders, neutral expression with
the mouth closed.

1. Front, eyes to camera
2. Three-quarter left
3. Three-quarter right
4. Front, chin tipped slightly down
```

## SHEET A2 — Profiles and back

```
Generate a turntable of the subject in File 1.

Four panels in a 2x2 grid, each labelled underneath. The same woman in every
panel — same face, same hair, same wardrobe, same seamless grey studio
backdrop, same soft even lighting. Head and shoulders, neutral expression with
the mouth closed.

1. Left profile, 90 degrees
2. Right profile, 90 degrees
3. Back of head
4. Back three-quarter, over her shoulder
```

## SHEET A3 — Overhead (optional)

```
Generate a turntable of the subject in File 1.

Four panels in a 2x2 grid, each labelled underneath. Same woman, same face,
hair, wardrobe, grey backdrop and lighting throughout. Head and shoulders,
neutral expression.

1. Seen from above, head tipped forward, looking down
2. From above, three-quarter left
3. From above, three-quarter right
4. Chin lifted, looking slightly up at camera
```

---

## SHEET B1 — Warm expressions

```
Generate an expression sheet of the subject in File 1.

Four panels in a 2x2 grid, each labelled underneath. Same woman, same face,
hair, wardrobe, grey backdrop and lighting throughout. Head and shoulders,
facing camera.

1. Soft closed-lip smile
2. Open smile showing teeth
3. Laughing, head tilted slightly back
4. Warm knowing look straight to camera
```

## SHEET B2 — Quiet expressions

```
Generate an expression sheet of the subject in File 1.

Four panels in a 2x2 grid, each labelled underneath. Same woman, same face,
hair, wardrobe, grey backdrop and lighting throughout. Head and shoulders.

1. Eyes closed, calm
2. Looking away to her left, thoughtful
3. Serious and composed, eyes to camera
4. Soft smile, looking down
```

**Check every sheet:** same woman throughout · nose-tip freckle wherever the
nose shows · one gold huggie per lobe · espresso roots melting to honey ends.

---

## SHEET C — Body

Attach seed06 as File 1. **This is the one long prompt** — the reference is a
head shot, so her body has to come from text.

```
Generate a full-body turntable of the subject in File 1.

Her face, hair and colouring exactly as the reference photograph.

Her body: 165 cm, athletic hourglass. Pilates-lean through the waist and
limbs, full natural bust (C to D cup on her frame, natural teardrop shape, set
high), softly rounded hips, waist-to-hip ratio 0.68. Long torso, high waist,
legs a little over half her total height. Visible deltoid separation, long lean
quadriceps, flat abdomen with defined obliques. Long narrow fingers, short
unpolished nails. A mature adult woman in her mid-twenties.

One fine-line botanical tattoo on her LEFT ribcage: a single olive sprig with
nine leaves in soft black linework, about 7 cm tall, running vertically with
the stem pointing down, starting just below the bra line. It is her only
tattoo. A thin plain gold anklet on her LEFT ankle.

Wardrobe: a matte bone-white fitted athletic set — supportive scoop-neck sports
bra and high-waisted mid-thigh shorts, plain, no logos. Barefoot. Hair tied
back in a low smooth bun so her shoulders and back are clear. Her skin is the
same very fair porcelain from head to toe, even, with no tan lines.

Four panels in a 2x2 grid, each labelled underneath, full body in every panel,
standing on a seamless grey backdrop with soft even studio lighting:
front, three-quarter left, left profile, back.

(Then run it a second time with panels: three-quarter right, right profile,
arms raised overhead, ribcage tattoo close-up.)
```

**Check when it lands:** proportions identical across panels · tattoo on the
same side, same size, never duplicated · face still hers · five fingers and
five toes.

---

## After each sheet

```
python split_sheet.py <sheet>.png --cols 4 --rows 3 --preview
python split_sheet.py <sheet>.png --cols 4 --rows 3 --out master/<name>
python drift_gate.py --in master/<name>
```

The drift gate is the objective check — it scores each panel against your
canonical and tells you whether the model held her or quietly substituted
someone else.

---

## If a sheet comes back wrong

Change **one thing** and regenerate. Do not add a sentence explaining what you
did not want — that is what produced every artifact we chased today.

| Symptom | Fix |
|---|---|
| Different woman | Reference not applied. Re-attach, shorten the prompt further. |
| Feature over-rendered | Delete the words describing it. The photo already has it. |
| Unwanted feature | Delete any mention of it, including negations. |
| Wrong expression on a panel | That panel's line only. Leave the others alone. |
| Face fine, body wrong | Body text is the only lever — the reference cannot help. |

---

## Local upscale — use the 5060 Ti

A 1536x2048 panel upscales cleanly to 4K on your card, and that is what the GPU
is for. In ComfyUI: load the panel, `4x-UltraSharp`, tiled at 512, ~10s each.
It will not invent markers that are not there, but it does recover a lot of
apparent detail in skin and hair.

Do this AFTER the drift gate, on accepted panels only. Never upscale something
you have not verified is her.
