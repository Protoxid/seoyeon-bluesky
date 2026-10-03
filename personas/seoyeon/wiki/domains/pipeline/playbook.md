# Seo-yeon — the playbook

The full reasoning. `CLAUDE.md` holds the operative layer and the
index; this file holds the why, and every entry is a mistake that
cost a generation. Not loaded by default — read the section you
need.

Section order here is the numbering used by the index in
CLAUDE.md.

---

Read this before touching anything. Every rule below was learned by getting it
wrong and paying for it. They are counterintuitive: most of them say *send less*
where instinct says send more.

---

## The one rule everything else follows from

**A reference image anchors what it visibly depicts, at the angle it depicts
it. Nothing else.**

- seed06 is head-and-shoulders → it anchors her face and says nothing below the
  collarbone. Body frames generated against it alone invented a new body each
  time.
- A front-on body frame does not anchor a left-ribcage tattoo, because the
  tattoo is nearly edge-on. Anchors must show the thing, from a useful angle.
- Text is only for what no reference can show. Everything else, the photo says
  better.

## Prompting

**Short beats long when a reference is attached.** A 4,600-character identity
block plus seed06 produced a *different woman*. One sentence plus seed06
produced a flawless 12-panel turntable. The text competes with the photo; the
more you describe, the more it generates from words instead of reproducing the
image. Phase-A prompts are ~31 characters: `"Three-quarter left, 45 degrees."`

**Never negate.** "NO scars" produced scars. "No specular highlights on the
forehead" produced a forehead highlight. Mentioning a thing summons it,
whatever grammar wraps it. To not get something, never write the word.

**Never use conditionals in a shared block.** "A dimple *only when she smiles*"
put a smile on a neutral frame. Per-frame features go in per-frame shot text.
The shared block holds only what must appear in EVERY image.

**Never emphasise what the reference already shows.** "Clearly darker than the
others" rendered her nose freckle as a blot. The photo and the prompt both push;
emphasis doubles the force.

**A reference anchors WARDROBE too, not just the face.** The master stack shows
a sleeveless high-neck top. Asking for a cardigan produced a cardigan half off
one shoulder in four of six frames — the model split the difference between the
photo and the words. State the garment completely, including how it sits:
"an oversized cream cardigan, sitting properly on both shoulders with both arms
through the sleeves". This is the same failure as the tattoo, one layer out.

**A reference anchors EXPRESSION too.** a1_front is neutral, so any action that
does not state a face inherits that neutral — six different poses, one
expression, which reads as a mannequin. Every action carries its own expression.

**Vary the emotional register, not just the face.** Six contemplative actions
give six contemplative photos even with six different expressions. A real feed
has tired, amused, absorbed, startled, unaware, mid-laugh. Half the shots should
have her not looking at the camera and not knowing it is there.

**Every attached image must agree about the lens.** A 35mm room plate plus an
"iPhone 2x, 48mm" prompt gives the model two incompatible views of one room, and
the perspective goes soft. Plates are now shot on the same phone as the content.

**Never put two measurements in one sentence.** "3 cm below the earlobe,
roughly 3 mm across" produced a 3 cm mole. Numbers bind to the nearest noun.

**Never generate from a generation.** Drift compounds. `a1_front` is a byte copy
of seed06, not a regeneration of it — regenerating the anchor was measurably
worse than copying it.

## Markers

**No markers on paired features.** Models have a strong symmetry prior for eyes,
ears and cheeks. Asymmetric earring counts, uneven brows and one-sided freckle
density all collapsed to symmetric. Asymmetry only survives on unpaired
features — a nose tip, a ribcage, one ankle.

**A marker that only exists in text will drift.** The olive-sprig tattoo was
redrawn differently every call until a body frame showing it was attached. Text
can say *there is one, here*; only an image can say what it looks like.

**Good markers are discrete, countable, central and unpaired.** The freckle on
her nose tip is the best in the set: one dot, no symmetric twin, visible at
front, three-quarter and profile.

## What makes an image read as AI

Not the subject — the render.

- Creamy f/1.4 bokeh. Real phones cannot do it optically.
- Flawless composition. Real framing is a degree off level.
- Punchy contrast. A real iPhone lifts shadows and holds highlights, so contrast
  reads FLAT. Models default the other way.
- Clean shadows. Real sensors are noisiest where there is least signal.
- A room with nothing accidental in it. Generated interiors are always tidied.
- Perfect loops. Pixel-identical first/last frames read as GIF. Narrative
  continuity is fine; pixel identity is a tell.
- Smooth camera moves. See below.

`realism.py` adds shadow-weighted grain, chromatic aberration and vignette
deterministically, AFTER the drift gate. Asking the model for grain gets it
sometimes; adding it after gets it every time.

## Continuity

**Camera position is a story decision.** "Who is holding this?" has an answer in
every frame. For a woman alone the answer is almost always *nobody* — the phone
is propped. A smooth push-in casts a second person you never intended.
`video.py --camera propped|selfie|filmed`.

**Her gear: a white iPhone 16 Pro.** 2x (48mm) for portraits. Low saturation,
aggressive HDR, accurate white balance, slightly over-sharpened, modest
background separation from a 1/1.28" sensor.

**If her phone is visible, it is not the camera.** Only the mirror shot is
consistent with the phone in frame. Everywhere else it must be out of shot, or
you have implied a second device. `PHONE_VISIBLE_OK` in content.py.

---

## Verified API facts (fal.ai)

Do not infer these. Every field name inferred on the last provider was wrong at
least once, and one of them cost a whole model bake-off.

| Fact | Detail |
|---|---|
| Queue submit | `POST https://queue.fal.run/{model_id}` |
| Status | `GET https://queue.fal.run/{model_id}/requests/{id}/status` -> `IN_QUEUE` / `IN_PROGRESS` / `COMPLETED` |
| Result | `GET https://queue.fal.run/{model_id}/requests/{id}` |
| Auth | header `Authorization: Key $FAL_KEY` |
| Image endpoints | t2i `openai/gpt-image-2` · i2i `openai/gpt-image-2/edit` |
| **i2i reference field** | **`image_urls`** — on Kie the same model read `input_urls`. THE FIELD IS A PROPERTY OF THE PROVIDER, not only of the model. Re-read it on every migration. |
| Size | no `aspect_ratio` and no resolution tier. `image_size` takes an enum OR exact `{"width":W,"height":H}` |
| Size limits | **multiples of 16, max edge 3840.** We send exact pixels; `fal_api.SIZES` maps our "3:4" strings to them |
| Quality | `quality`: `auto` / `low` / `medium` / `high` — replaces the old tier knob |
| Image output | `{"images":[{"url","content_type","file_name","width","height"}]}` |
| Video endpoint | `minimax/h3-max/image-to-video` |
| Video fields | `image_url` = FIRST frame (Kie called it `first_frame_url`); `end_image_url` = last frame, **never sent** |
| **H3 resolution** | **`480P` or `768P` only. THERE IS NO 2K ON FAL.** Kie offered one; this endpoint does not. Plan around it rather than discovering it mid-batch. |
| **H3 prompt rewriting** | `prompt_expansion_mode` is **REQUIRED**, `balanced` or `quality`, and it REWRITES THE PROMPT with no documented way off. Same hazard as Qwen's `prompt_extend`. We send `balanced` and log `expanded_prompt` every call to `h3_expanded_prompts.jsonl`. |
| Video output | `{"video":{"url",...},"expanded_prompt":...}` |
| Seedance ref2v | `bytedance/seedance-2.5/reference-to-video`, refs in `image_urls` (max 30), addressed in the prompt as `@Image1`. Still the method that failed first time — it re-derives identity per frame. |
| Uploads | NOT confirmed from fal's own docs (their files page 404s). `fal_api.upload()` tries a `data:` URI first and falls back to storage. `python fal_api.py --probe` settles it. |
| **Price** | **UNPUBLISHED on the model pages, and deliberately left at 0.0.** A guessed number in a budget guard is worse than none. `outside.py` refuses to spend until `--unit-price` is given or FAMILIES is filled in. |
| Egress | `queue.fal.run` is blocked from the cloud container and device_bash, exactly as api.kie.ai was. All API calls run on the user's Windows Python. |

## Models in use

**`gpt-image-2` IS THE RENDERER.** `outside.py --model` defaults to `gpt` and
should stay there. Everything in the current grid was made with it.

| Stage | Model | Why |
|---|---|---|
| Grid / content, with references (i2i) | `gpt-image-2-image-to-image` | The best images in the project: correct skin, correct wide-lens arm distortion, real people in the background, a market stall another AI argued was a real photograph. Refs go in **`input_urls`**. |
| No-face shots, no references (t2i) | `gpt-image-2-text-to-image` | A shot with nobody in it must not carry face references — attach them to a fruit stall and she appears in the fruit stall. Same family keeps the grid looking like one camera. |
| Fallback / A-B only | `qwen3/pro-image-to-image` | Still wired. The only one with `negative_prompt` and `seed`. Renders the mirror selfie that gpt refuses. |
| Video, first-frame conditioned | `minimax-h3/image-to-video` | i2v from an accepted still. Never ref2v — see the video section. |
| Video, movement-led | `kling-3.0-omni/image-to-video` | Motion and physics; multi-shot |

**The 0.804-vs-0.496 number that used to sit in this table was deleted, and it
should never be quoted again.** It was measured while gpt-image-2's references
were being sent to `image_urls`, a field that model does not read, so gpt was
generating from text alone with no identity input at all. The test measured a
broken integration and scored a model on it. Seedream "winning" was an artefact
of my own bug, and that wrong number sat at the top of this playbook for a day
telling every future reader to pick the wrong model.

## Drift gate

Thresholds scale with face size, because ArcFace aligns to 112x112 and a small
face is upscaled into that — a full-body frame scores 0.05-0.08 below a head
shot OF THE SAME PERSON.

```
head shot >= 0.75 · half-body >= 0.72 · full-body >= 0.68 · distant >= 0.64
```

Run `--calibrate` against the master stack to set these from real data rather
than these defaults, which I invented before there was a single image.

## Files

```
identity_block.txt   full identity — SEED generation only (text-to-image)
identity_brief.txt   condensed — phase c only, where the body block needs room
body_block.txt       proportions + tattoo; the reference cannot show a body
master/a|b|c/        the reference stack. IRREPLACEABLE. Back it up.
locations/*.png      locked environment plates
canonical.npy        the drift gate's identity centroid
```

## Working style that has helped

- `pyflakes` before handing anything over. Two latent bugs shipped without it.
- Assert on every string replace. Two edits silently did nothing and reported
  success.
- Mock-test the API layer. Budget caps, resume and thresholds were all verified
  against a fake client before spending.
- One frame before a batch. `--only`, `--action`, `--dry-run` exist for this.

## Rooms: describe them, don't attach them
**A location plate attached as a reference makes the model composite.** It
keeps the plate as a background layer and places the subject in front of it —
no shared light, no contact shadow, cut-out edges. Tested: same action, same
identity refs. Plate attached = glued on. Plate removed, room described in
TEXT = totally blended in.
Room identity therefore lives in `locations.PLACES` text, imported into
`content.py`. Plates are still generated and locked — they are the visual
spec the text is written from, and `--plate` re-attaches one — but they are
off by default.
Corollary: **a reference is for things text cannot carry** (a face, a body).
Anything a sentence can specify should be a sentence.

**MODEL-SPECIFIC. Operator finding, 25 Aug: gpt-image-2 does NOT do this.**
Hand it a room image alongside the character image and it puts her IN the room,
shared light and all — not a cut-out in front of a backdrop. Everything above
was measured on Seedream, where the compositing was real and repeatable, and it
was written as though it were a fact about diffusion models. It is a fact about
one model.
This is the third time the same trap has been sprung in this file — the H3
camera-lock note already says "model-specific rules do not transfer" and cites
applying Seedream's fewer-references rule to Kling. Assume every rule here is
about the model it was learned on until it is re-tested.
The corollary above survives anyway, and is the better way to hold it: attach a
reference for what a sentence cannot carry. On gpt-image-2 a ROOM is now in
that category.

## Rooms: edit one hero, never regenerate
**Room consistency cannot be prompted.** A model asked to draw a room from a
description invents a new one every time — plate attached or not, prompt long
or short, roles indexed or not. All of that was tested and all of it failed QC.
**The fix is to stop generating the room.** Generate ONE hero photo of her in
the room (`heroes/<place>.png`), then produce every other frame in that room as
an EDIT of that file via `session.py` (`nano-banana-pro`, `image_input`).
Verified: chair, stool, mug, plant, window and her face all survive a pose
change, a wardrobe change and a time-of-day change.
Rules: always edit FROM THE HERO, never from an edit (one generation deep).
One change per edit. Never describe the room — the hero IS the room.
Strategy corollary: keep repeated interiors to a minority of the feed. Streets,
cafes, gyms and shops are expected to differ, so drift there is free.

**LIKELY SUPERSEDED, 25 Aug.** "Room consistency cannot be prompted" was true
of every model tested at the time. It is not true of gpt-image-2 with a plate
ATTACHED, which is a different claim from prompting it in text. If the operator
finding holds under a controlled test, the hero+edit chain stops being
necessary: a locked plate plus the face references gives room consistency
without the one-generation-deep rule, without editing from an edit, and without
the "a clean hero contaminates every frame edited out of it" problem further
down this file.
Do not tear out `session.py` until the test below has actually been run.

## The camera sits on furniture, not on a tripod
A propped phone rests on whatever surface the room has, at that surface's
height — stool 45 cm, bedside table 60 cm, counter 90 cm, parapet ~100 cm,
shelf 140 cm. Most of those look UP at a standing woman. "Chest height" is
where a photographer puts a tripod and it reads as one.
**Perfect framing is an AI tell.** Generated images are almost always
balanced, centred and level; real propped-phone photos are not. Every hero
states the surface AND the framing error it causes — off-centre, too much
ceiling, a low crop, a degree of roll. `content.PROP`, used by `hero.py`.
Only heroes need this: session edits inherit the camera from the hero.

## Never name the camera device
`PROP` originally said "the phone is propped on the low wooden stool". Every
hero came back with a phone in frame — one of them in a tripod mount. Same
mechanism as `NO scars` producing scars: **naming a thing summons it**, whatever
the grammar around it. Describe only the VIEWPOINT and the framing error it
causes ("seen from about 45 cm off the floor, looking up at her, off to one
side"). The camera stays invisible. `IPHONE_LEAN` naming the phone as a lens
spec is fine — it never summoned one; it is the placement sentence that does.

## A room owns furniture, an action owns props
`locations.PLACES` for the window said "a mug on a low wooden stool" while
action 0 says "holding a ceramic mug" — every hero came back with **two mugs**.
The room description holds furniture and fixtures only. Anything she picks up,
holds, drinks from or carries belongs to the ACTION, never to both.
Check every room line against its action list before generating heroes.
`hero.py --repair <scene> "<instruction>"` fixes a defect in an already-locked
hero with one nano-banana edit, backing up the original as `<scene>.orig.png`.

## Audit before you spend
`audit.py` reads every prompt the pipeline can build and flags nine known
failure modes for free: duplicate props between room and action, wardrobe named
in a room line, negations, conditionals, two measurements in one sentence,
depth-of-field conflicts with the lens line, the camera device being named,
missing room/camera/role definitions, and session frames whose KEEP clause
contradicts the frame. Run it before any batch. `ALLOW` holds reviewed false
positives — do not add to it to silence a real collision.

## Rooms: used, not worn
Two overcorrections, both costly. The first room bible was a styled interiors
shoot — "bone, oat and warm sand palette with sage accents". Too tasteful reads
as AI, because real flats are not colour-coordinated. The correction went too
far the other way: scorch marks, grout going grey, limescale, rust, cracked
concrete. That is a *neglected* flat, and it contradicts the persona — she
lives in Seoul and earns well — and undercuts the aspiration the funnel runs on.
**The realness comes from USE, not from damage.** A cushion still dented, an
object set down mid-task and left there, curtains drawn by hand rather than
evenly, a hair tie next to the lamp, a tea towel hung slightly crooked. Warm
pale wood, white walls, clean lines, a few good pieces. Nothing broken, nothing
stained, nothing neglected.
**State it positively.** "A curtain that does not quite meet" is a negation and
renders a well-met curtain — write "a curtain with a gap down the middle".
Do not name a device or anything charging: it puts a phone in the frame.


## Roughly 1 in 4 posts has no person in it
A feed of nothing but self-portraits reads as a model's portfolio, not a
person's account. `around.py` covers the rest: food, street, interior details,
her hands, flatlays, sky. Text-to-image only — **no identity references, no
drift gate, no repair** — so they cost $0.07 and carry no risk. They also give
the grid rhythm, which makes the face posts land harder, and they are trivially
photorealistic: nobody scrutinises a bowl of noodles the way they scrutinise a
face. Hands shots state fair cool-toned skin, short unpainted nails and one
thin gold ring so they match her without a reference.
Seoul has to be legible in the street and food shots or the persona is
placeless — name real districts and real dishes.

## Vary per room, never with a shared extras list
A single shared list of extra frames appended to every room put her in the same
grey top in all seven rooms and gave the rooftop "long shadows across the wall"
when it has no wall — 14 of 45 frames from two prompts. Extras are written
**per room**: a second outfit that suits that room, a light state that actually
exists there, and a change of DISTANCE. That last one matters most — the base
actions all sit at the scene's framing, so without an explicit closer/wider
frame the whole bank reads at three crops.
Check any new batch for repeated sentences across rooms before running it.

## The character bible is a decision document, not prompt text
`character.md` holds her life, class background, money situation, flaws, voice
and what she never posts. **It never goes into a prompt** — short prompts are
load-bearing. It tells you which mug, which expression, which caption, which
shot to cut. A generic mug is a stock photo; the chipped one she has had since
university is a photograph. That difference IS photorealism.
Premise: **"Day N of quitting my job to retrain as a pilates instructor."** The
day count drives return visits, the retraining gives the account a subject and
a paid ladder, and the arc renews at certification rather than ending.
Consequences already encoded: small expressions not wide grins, a long spine in
every seated frame (the disc injury), a flat nicer than her current income,
company implied by two cups rather than shown, mostly early light.

## Age is 26, fixed by the identity block
`identity_block.txt` says 26 and every generated image descends from it, so the
biography has to fit that, not the other way round. Timeline: Seoul at 19,
graduated at 23, three years in marketing, herniated disc at 24, promoted at 25,
quit at 26 after saving for ten months. Any biographical detail that implies a
different age is a continuity error in a file that cannot be regenerated.

## A session edit needs the face reference too, not just the hero
Running `session.py` on the hero alone lost identity on the full-body reformer
frames and dropped the freckles elsewhere. The hero carries the room perfectly,
but on a wide shot there is almost no face in it to work from, and fine detail
degrades every time the model re-renders her.
Every edit now sends two references with explicit roles:
  Image 1 = the hero — the photograph being edited: room, furniture, light,
            framing and wardrobe all come from here
  Image 2 = `master/a/a1_front.png` — her face ONLY: features, skin, and the
            small pale freckles across the nose and inner cheeks
Order matters. The hero is Image 1 because it is the photograph, not a source
of ideas. The "face only" clause is what stops Image 2 leaking room or wardrobe.
Freckles need naming: they are the first thing to disappear and the last thing
a viewer consciously notices, which is exactly why losing them reads as "off".

## Never ask for legible text — Korean especially
A food shot came back with a perfect 차림표 header and a perfect 감사합니다
footer, correct prices, and **twelve dish names that were not words** — repeated
pseudo-syllables in hangul shapes. That is worse than obvious nonsense: the
correct text around it draws a Korean reader's eye straight to the broken part.
A poster also read 팔콩국수 where the real dish is 콩국수.
The prompt caused it — `around.py` said "one shop sign in Hangul lit from
inside". Removed, along with the handwritten-notebook flatlay.
Every `around.py` shot now carries `NO_TEXT`: signage, menus and packaging are
small, distant, steeply angled or out of focus, never sharp and never the
subject. That is also how text looks in a real snapshot.
`audit.py` flags any room, camera or action line containing sign / signage /
menu / hangul / handwriting / lettering / label / poster / logo / newspaper.
Everything else in that image was flawless. Text is the single failure mode —
treat it as a hard exclusion, not a quality problem to iterate on.

## The face reference must match the frame's angle
First fix sent `a1_front` with every session edit. Better than the hero alone,
but still wrong: **a reference anchors what it depicts AT THE ANGLE it depicts
it.** On a profile frame `a1_front` does not merely fail to help, it fights the
pose; on a from-behind frame it is pure noise.
`session.face_ref_for()` picks one reference per frame from the frame text:
  from behind / face not visible  -> none, and ROLES drops the face clause
  in profile / seen from the side -> a4_prof_left
  turning / glancing / mid-turn   -> a2_tq_left
  everything else                 -> a1_front
Still ONE face reference, never the whole set — more references caused the
averaging and compositing problems, and the model guidance says use the fewest
that communicate the requirement. The fix is the RIGHT one, not MORE of them.

## Two face references per edit: front plus a second angle
Superseding the one-reference rule above. One reference anchors only the angle
it depicts, which left the profile and three-quarter frames unsupported and lost
identity on the full-body reformer set.
Every session edit sends three images:
  Image 1  the hero — the photograph being edited (room, light, framing, wardrobe)
  Image 2  `a1_front` — always
  Image 3  `a2_tq_left`, or `a4_prof_left` when the frame is side-on
Three is the ceiling. Beyond that the averaging and compositing problems return.
From-behind frames still send no face references by default — they invite the
model to turn her round to satisfy them — and `--faces-everywhere` overrides
that when a back frame comes out wrong.

## Tool routing: EDITOR vs RENDERER, chosen per frame
Applies to the `session.py` / `content.py` room pipeline, which the grid no
longer uses — `outside.py` builds everything now. The editor-vs-renderer
reasoning is the part that generalises, so it stays.
Nano Banana is an EDITOR: it preserves, which is why the room holds and also
why a light-change frame came back as the same photograph with a colour shift.
An edit cannot move far from its source, so a bank built entirely from edits
reads as one photo repeated.
`session.mode_for()` routes per frame:
  **render** (`gpt-image-2-image-to-image`, via `kie_api.MODEL_I2I`) — any
  frame containing an action verb, i.e. the composition changes. Gets
  `RENDER_ROLES`, which claims the room from Image 1 explicitly, because a
  renderer generates rather than edits and will invent a room if not told.
  **edit** (`nano-banana-pro`) — a pure light or wardrobe delta with no action.
`--model edit|render` forces one for the whole run.

CORRECTED 25 Aug, and this one was a LIVE TRAP, not a stale line in a document.
Both this section and `kie_api.py` still said `seedream/5-pro-image-to-image`
long after gpt-image-2 became the renderer, and `kie_api.MODEL_I2I` is the
project-wide default: `generate()` falls back to it whenever a caller does not
name a model. So `content.py`, `hero.py` and `session.py` would all have gone
to a DIFFERENT renderer than the grid, silently, and the only symptom would
have been a bank that quietly stopped looking like one camera.
Worse, the reason the line gave for itself had already been disproved — it
said gpt-image-2's reference field was "inferred and may never have been read
at all", which was true only while it was being sent to `image_urls`. The fix
was `input_urls`, days earlier.
THE LESSON: a superseded decision is not corrected by writing SUPERSEDED above
it. It is corrected by changing the value. A banner over a wrong model id still
leaves the wrong model id in the file, and files get read by scripts, not just
by people. Grep the CODE for the old name, not only the prose.
Second half of the fix: **a pure delta can only ever be the same photo again.**
The extras were written as "she is wearing X instead" with no pose, so even a
perfect edit was a duplicate. Every extra now carries a new pose alongside its
change — "Crouching to reach a low cupboard, wearing an oversized grey
sweatshirt instead."

## Outside is the majority of the feed
Rooms were the hard problem and they are now the *small* part of the grid.
`outside.py` covers parks, restaurants, gyms, streets, cafes, markets and the
river — places a viewer has no memory of, so coherence costs nothing and we can
re-render freely instead of editing. That buys the pose, framing and distance
variety edits could not give. Home stays on hero+edit (`session.py`) and we
already have enough of it.
CORRECTED, TWICE. This paragraph originally said Seedream; the renderer is
**gpt-image-2**.
And it originally said **"1K, not 2K"** on the reasoning that a feed image is
viewed at 1080px so the extra $0.03 is waste. That is wrong and it cost a whole
batch. 1K does not mean "the same picture, smaller" — the model spends less on
it, and the things it stops spending on are exactly the things that make a
photo look real: skin texture, background detail, small type on signage. Every
grid shot is `tier="2k"`. See "Resolution tiers lie" below.
**Hair varies per shot.** She has a default — down, centre-parted, curtain
bangs — and changes it: low bun, claw clip, high ponytail, tucked behind ears,
through a cap. Stated per shot, because the reference holds the default forever
otherwise. Colour never changes; the balayage is the signature.
**Who holds the camera changes outdoors.** "Propped on the furniture" stops
working, so every shot picks one of four: a friend walking with her, a stranger
she asked (further back, more of the place in frame), a selfie at arm's length,
or set down on something nearby and left running.

## audit.py now covers outside.py too
Outdoor shots have a different failure surface: a camera mode and a hairstyle
per shot, either of which can contradict the action. What it caught on the
first pass, all of which would have shipped:
  - "not looking at the camera" / "without looking" / "face not visible" —
    negations, which is how we got scars. Rewritten positively: "eyes on the
    jug", "eyes still on the person opposite", "the back of her head and
    shoulders filling the frame".
  - "wiping her face with the hem of her shirt" in the gym, whose wardrobe is a
    cropped long-sleeve top and leggings. No shirt existed.
  - a "stranger she asked" shooting her walking away small in the frame — not a
    photograph a stranger takes. Switched to the friend camera.
New checks: selfie vs actions a selfie cannot see, the alone-camera against
actions that imply a companion, a stranger against from-behind and distant
shots, a friend against "unaware of the camera", cap-vs-loose-hair, retying
hair that is already up, garments named in an action but absent from the
wardrobe, and duplicate action text across scenes.
Verified by deliberately breaking a shot and confirming all four fire.

## Wardrobe: pieces that recombine, not fixed outfits
Wardrobe was set per SCENE, so all five park shots were one afternoon and the
charcoal coat carried 10 of 29 shots. Now it is per SHOT, drawn from
`outside.WARDROBE` — ten combinations built from a small set of pieces.
Garments repeating is CORRECT: `character.md` says she took a pay cut and
rotates six things with one good coat, and the coat still appears most often,
as it would. What was wrong was whole outfits repeating.
All seven places now show at least two outfits, so each place reads as several
visits rather than one day. Shot tuples are `(action, hair, camera, outfit)`.

## Check DISTRIBUTION, not just individual prompts
Two of the three worst defects were distribution problems — invisible in any
one prompt, obvious in a table: six outfits with ten shots in the same coat,
and two extra frames repeated across all seven rooms. A per-prompt checker can
never see those, so `audit.py` now reports distributions and **treats imbalance
as an issue**, with caps: wardrobe no single outfit over 25%, hair over 45%,
camera over 55%, and at least 8 outfits / 4 hairstyles / 3 camera modes.
It also flags any place whose shots all share a wardrobe (reads as one day)
and any session frame text repeated across rooms.
First run caught 17 of 29 shots on the "a friend took it" camera — meaning she
is almost never alone, which contradicts `character.md` (two close friends, no
wide circle, company implied rather than shown). Rebalanced to alone 14,
friend 10, selfie 3, stranger 2.
**Rule for me: never hand over a prompt set without running the distribution
report and reading every prompt end to end first.** Errors found after
generation cost real money; errors found in a table cost nothing.

## English only, romanised Korean nouns
She is Korean and lives in Seoul; she writes in English. The paying audience is
English-speaking and the DM ladder is where revenue happens, so a Korean-
language following would structurally fail to convert. The operator does not
read Korean, and Korean that is slightly wrong is a bigger tell than none —
the same failure as the generated menu board. Korean creators aiming at
international audiences write English routinely, so it reads as a choice.
Romanised nouns are good: kalguksu, Seongsu-dong, the Han, Chuseok. Never a
full Hangul sentence, in a caption or in an image.

## Faces drift on wide shots because of PIXELS, not references
A full-body frame gives the face a fraction of the frame, so fine detail
degrades however good the references are. Two fixes:
**Preventive** — `outside.WIDE` names the twelve full-body/distant shots and
runs them at 2k while everything else stays at 1k. Explicit list, not keyword
guessing. Cost goes $1.16 -> $1.52 for the outdoor bank.
**Corrective** — `fix_face.py` repairs a frame that is well composed but failed
the gate, instead of discarding a good photograph. Nano Banana is an editor, so
"correct only her face, change nothing else" is exactly what it is good at.
Backs up as `<name>.orig.png` and **refuses to repair a repair** — one hop from
the original, the same rule the hero flow follows.
    python fix_face.py content/outside --below 0.70 --budget 0.5

## The arm's-length front selfie is the default outdoors
First outdoor pass had 3 selfies in 29 shots. Backwards: a woman out on her own
photographs herself at arm's length, and that format defines the medium.
Now 16/29 (55%) across `selfie`, `selfie_away` (looking past the lens) and
`mirror`. `alone` — a phone set down outdoors — is rare in life and capped at
20%. `audit.py` treats TOO FEW selfies as an issue, not just too many.
**The front camera is a different lens.** ~23mm equivalent, 12MP, softer and
noisier than the rear, with real perspective stretch at arm's length and her
upper arm cutting into a corner. A selfie rendered like the rear camera reads
wrong without anyone being able to say why, so selfie shots take `CAM.FRONT`
for geometry plus `LENS_FRONT` for processing, never the rear `LENS`.
Splitting geometry from processing also stopped the two overlapping, which is
what pushed four prompts over the 1200-char cap.

## Fill the walls — a place can invite text without naming it
The restaurant prompt never said "menu", but a small noodle restaurant HAS one,
so the model put one on the wall and rendered it as pseudo-hangul. `NO_TEXT`
governs how text is drawn, not whether the scene calls for it.
**Saying "no menu" summons a menu** — the scars rule. So every signage-prone
place now states what IS on the walls, leaving no blank surface: the restaurant
has tiled walls, steel shelving and a wall fan; the street has roller shutters
down on the units; the cafe has shelves of crockery and trailing plants; the
market has stacked crates and hanging bulbs with the stalls out of focus; the
gym has racks and plain painted walls.
`NO_TEXT` also names the surfaces positively — "plain: tile, painted wall, bare
wood, steel, brick" — instead of describing what is absent.
`audit.py` flags any restaurant / cafe / market / shop / gym / station / street
place whose description says nothing about walls, shelving, shutters or racks.
Verified by stripping the restaurant walls and confirming it fires.

## Text: name the surface, never the signage
Gibberish writing survived the first NO_TEXT clause because that clause said
"any signage in frame is small, distant, angled" — which still tells the model
there IS signage. Exactly the mechanism that put a phone in every hero when the
prompt named one. It now states only what IS there:
    "Every surface in frame is plain: bare tile, brick, painted wall, wood,
     fabric, glass, foliage, skin."
Second half: **some objects carry print by their nature even when text is never
mentioned.** Shelving gets labelled boxes, crates get stamped, packaging gets
branding. The restaurant said "tiled walls with steel shelving" and came back
with a menu board. Replaced with "a plain white-tiled wall directly behind her
with a wall fan above it"; market crates became loose produce in shallow
baskets; cafe shelves of crockery became trailing plants on a painted wall.
`audit.py` now flags shelving / shelves / crate / packaging / box / can /
magazine / bookshelf / noticeboard / whiteboard / receipt / ticket / carton,
and flags any signage-prone place whose walls are not explicitly described —
an unstated wall is one the model will fill with a menu board.

## A selfie occupies one hand
Two restaurant frames failed on the same collision. "Leaning back, **arms
folded**" plus the selfie camera produced folded arms AND an arm reaching out
of frame — three arms. "**Holding the phone** up over the table, **chopsticks
in her other hand**" produced two phones and no free hand, and broke the iPhone
continuity rule (a visible phone is not the camera).
Rules for any selfie / mirror action:
  * never occupy both hands — no "arms folded", "both hands", "hands in her
    pockets", "in her other hand"
  * never name a phone: the extended arm is already holding it
`CAM.FRONT` now states it once — "her extended arm cuts into a corner and is
holding the only phone in the picture; her other hand is free" — and
`audit.py` flags the whole family.
What worked in the same batch: the plain white-tiled wall produced **no text at
all**, and identity held with the freckles visible. Those two fixes are sound.

## Three paragraphs, not eight blocks
Prompts were eight blocks separated by blank lines — action, place, wardrobe,
hair, camera, roles, no-text, lens. Two costs: independent blocks are weighted
independently, so boilerplate competes with the subject; and fields that never
touch each other can contradict, which is how "the hem of her shirt" reached a
scene with no shirt and "arms folded" reached a selfie.
Now grouped as **her** (action + wardrobe + hair, one paragraph), **there**
(the place), **how** (camera + lens), then the model instructions last. The
fields stay separate in code — that is what gives 10 outfits x 6 hairstyles x
6 cameras from a small set, and what makes the audit possible — only the
joining changed. 862-1191 chars, mean 1028.
Also caught here: `NO_TEXT` still read "plain and **unprinted**". The word
print was in the prompt. Now "plain: bare tile, brick, painted wall, wood,
fabric, glass, foliage, skin."

## What real fitness/lifestyle grids do that we were not
Studied three real Korean/Korean-American accounts. Taken:
  * **full body dominates.** A fitness feed shows the BODY. We had 6/29 wide;
    now 13/36. This also matters commercially — it is what converts later.
  * **backgrounds are far plainer than I was writing.** A bare white wall and a
    wooden floor is the actual format, and it is also the lowest-risk backdrop
    for text and artefacts. Added `room_full`, `room_flex`, `gym_full`.
  * **walking away and from-behind read as unposed** and are common. Added
    running away on a park path and climbing river steps.
  * **athleisure is the default**, not the exception, for this persona.
  * **expressions are much bigger than our register.** Ours were all "quietly
    amused" and "flat and content". Real grids have mouth-open laughing,
    deliberately stupid flexing, mock outrage. Added three.
  * **the grade is consistent across the whole grid** — muted greens and
    neutrals, soft filmic contrast. `realism.py` should carry one LUT.
Deliberately NOT taken: retouched beauty-editorial close-ups (that smooth-skin
register is exactly what reads as AI), sponsored product shots (legible
packaging is our worst failure mode), and group shots (a second consistent
identity is a whole separate problem we have not solved).

## Positioning: not a gym influencer
The objective is subscriber conversions (Plan B: native Instagram Subscriptions
and SFW supporter tiers like Patreon, pivoted from Fanvue because SFW/suggestive
moments cause severe churn on adult-dominated platforms). The fitness format
monetises differently — sponsorships, coaching, supplements — recruiting an
audience that wants workout content and never pays for access to a person.
Reference grids in this look all pull toward it. Resist.
**She is a woman living alone in Seoul.** Pilates explains her body; the
retraining explains her free days and tight money; neither is the subject.
Conversion runs on parasocial intimacy, so: body present but incidental, never
posed as achievement; no equipment as subject, no form demos, no progress
framing; direct eye contact in roughly half the frames; no-person posts down
from 1-in-4 to about 1-in-8; nothing that reads as sponsored.
Cut for this reason: `gym_cable` (instructional), `room_flex` (fitness comedy),
`market_pay` (transactional), `rest_reach` (fourth food shot), `park_lace`
(no face, no pull). Added `rooftop_night`, `stairwell_late`, `beach_walk` —
frames that carry pull rather than information.
The day-count serial survives as a CAPTION device only. An account whose
subject is a career change grows followers who want a career change.

## Vertical, warm, seasonal — and overlay text instead of generating it
From real Seoul lifestyle accounts, three gaps:
**Vertical.** Everything was 3:4. Stories and Reel covers are 9:16, and that is
where profile visits and link taps come from — the feed builds the impression,
Stories do the converting. `aspect` is now per shot; five 9:16 frames added.
**Warmth converts; cool does not.** Our whole register was "flat and content",
"quietly amused". People subscribe to someone who seems glad to see them. This
is not a break from "dry, not bubbly": she is **reserved in public and warm when
she is looking straight down the lens**, and that asymmetry IS the parasocial
mechanism the funnel runs on. Direct-to-camera frames get the warmth.
**The season is a reason to post.** First snow, winter light, shearling and
knitted hats — timely, very Korea, high appeal, and covered up while still
attractive, which suits Instagram.
**Overlay text, never generate it.** "first snow in seoul" is typed in the
editor afterwards: free, perfectly legible, and the opposite of the gibberish
the models produce. No prompt ever asks for words.

## Write every prompt separately. Do not compose them from fields.
**VERIFIED IN PRODUCTION — the outdoor batch came out clean.**
The pipeline assembled prompts from fields: action + wardrobe + hair + camera +
place + lens, joined with blank lines. It was efficient — 10 outfits x 6
hairstyles x 6 cameras from a small table — and it produced a long tail of
defects that no amount of checking fully closed:
  * "the hem of her shirt" in a scene whose wardrobe had no shirt
  * "arms folded" in a selfie, giving her a third arm
  * "holding the phone" in a selfie, giving her two phones
  * the same grey top in seven different rooms
  * a lens line describing "the room" in an outdoor shot
Each was a pair of fields that never met until generation time.
`outside_shots.py` holds 39 individually authored descriptions instead. One
thought each, ~500-850 chars, everything woven — what she is doing, wearing,
how her hair is, where she is, who is holding the camera, what lens. Nothing
can contradict anything else **by construction**, and the results were the best
of the project.
The cost is real: no recombination, and variety has to be written rather than
generated. Pay it. A field table optimises for the number of prompts; authored
prose optimises for the number of USABLE images, which is the only count that
matters.
`audit.py` still runs, but on the finished text: negations, text bait,
print-bearing objects, selfie hand conflicts, missing camera/lens/hair/wardrobe,
plus a distribution report. It cannot check field consistency because there are
no fields left — which is the point.

## Three failure modes from the first summer batch
**Back-of-head shots do not render.** Hair seen from directly behind comes back
as mush. `s_park_green` and `market_aisle` both rewritten so she is half turned
toward the lens instead. `audit.py` flags "seen from directly behind" and
"the back of her head". A from-behind shot can still work if her head is
turned — it is specifically the back of the hair that fails.
**"Forearms on the parapet" is both arms.** Plus the extended selfie arm makes
three. The hand check now catches `forearms`, `both arms` and `elbows on` as
well as `both hands`.
**Head-to-body proportion breaks on wide frames.** Both face references are
head shots, so on a full-length frame the model scales the head up to honour
them. Fix: `master/c/c5_relax_front.png` — the full-body reference the stack
already had and `outside.py` was not using — attached as Image 3 on wide shots,
with its own role clause ("use it only for her build and the proportion of her
head to her body"). Shots opt in with `body=True`; 18 wide frames now carry it.
This is the same lesson as the face reference: **a reference anchors what it
depicts.** Two head shots cannot anchor a body.

## Naming an emotion produces a performance of it
`s_seongsu_iced` said "squinting hard and **laughing at how hot it is**" and
came back as an obvious posed laugh. Same mechanism as naming the phone: the
model renders the named thing as the subject rather than as a consequence.
Two rules:
**Describe the physical cause, let the expression follow.** Squinting into the
sun, blowing hair off her face, mid-word, wincing at the heat, mid-bite. The
face is a byproduct. "Visibly done with the heat" beats "laughing".
**The cause must be plausible.** Nobody laughs at 34 degrees — they get
exasperated. A named emotion with an implausible trigger is the worst case,
because the model has nothing to render but the pose.
Where a smile IS the point (profile picture, the warm direct-to-camera frames),
still give it a trigger — "something just said off camera" — and describe the
mechanics rather than the mood: teeth showing, cheeks pushed up, eyes narrowed
to creases.

## In a selfie the free hand must stay at her body
`s_rooftop_dusk` had "one arm resting on the parapet" plus the extended camera
arm, and the model merged them into a single limb reaching from the parapet to
the lens. Nothing said they were on opposite sides.
**The free hand goes to her hair, her face, her chain, a cup held close — never
resting on a rail, wall, counter, table or sill.** That is where the camera arm
already is, and the two fuse. `audit.py` flags it.

## Export at 3:4, not 4:5 — the grid changed
I specified 1080x1350 (4:5) from a stale source. **Instagram moved the profile
grid to 3:4 in January 2025 and added native 3:4 photo support in May 2025.**
The feed accepts 1.91:1 through 3:4; the grid crops everything to 3:4.
Since the whole bank is generated at 3:4:
  * **3:4 uploaded** — zero crop in the feed, zero crop in the grid, and taller
    on screen than 4:5, so it takes more attention
  * **4:5 uploaded** — loses thin strips from both sides in the grid, having
    already thrown away 6% of the height to get there
`publish_prep.py --kind feed` now targets **1080x1440**. `realism.py --feed` is
deprecated and documented as such; it crops to 4:5 and should not be used.
On the phone, choose **"Original"** in the crop step, not 4:5.
Other verified upload facts: sRGB (Instagram ignores embedded profiles), JPEG,
under 3.6 MB, quality 85-95, 4:4:4 chroma. There is no quality toggle —
Instagram re-compresses everything, so the only lever is giving it less to do.

## "1k" is one MEGAPIXEL, not 1080 wide
The tier was set to 1k on the reasoning that a feed image is viewed at 1080px.
Wrong: at 3:4 the 1k tier returns **896x1184**, at 9:16 **768x1376**. Both are
under Instagram's 1080-wide floor, so **31 of 63 outdoor images uploaded soft**
and `publish_prep` was silently upscaling them, which is worse than nothing.
**2k is the minimum publishable tier.** `outside.TIER` and every shot are now
2k, and `publish_prep.py` refuses any file below the target width and names it
rather than resizing up. The saving was $0.03 an image and it cost the batch.
Home sessions were never affected — `session.py` defaults to 2k, and those come
back 1792x2400.
Check pixel dimensions of a new source before trusting a tier label. Measure,
do not read the name.

## Video: condition on a frame, not on references
Two Reel takes went `reference-to-video` — Kling with six references from the
master stack. Both came back reading as AI. The diagnostic detail was the
**ribcage tattoo appearing on the wrong side**: reference-to-video re-derives
her face and body from scratch every frame, so it also re-derived the tattoo
and mirrored it. Same cause as shot 5 not being her, and as the glass skin.
**Nothing the stills pipeline learned survives that route**, because none of it
is in the pixels the video model starts from.
`image-to-video` from a first frame keeps all of it. Frame 1 IS a still we
generated, looked at and accepted; the model only has to move it. And the
photorealism verdict happens on a **$0.07 still** instead of after a video
generation.
Corollary: **a first frame decides the output aspect** — there is no
`aspect_ratio` field on `minimax-h3/image-to-video`. The 3:4 bank cannot seed a
9:16 Reel. Reel frames are authored at 9:16 in `reel_frames.py` and run through
the normal stills pipeline with `outside.py --reel-frames`.
Keep the motion small. Drift is proportional to how much the model has to
invent, so one honest movement over four seconds beats choreography.

## One clip per call. Multi-shot is a false economy.
Kling's `multi_prompt` gave six cuts for one price and looked like the cost
lever. It is the opposite: **one bad cut means re-buying all six.** Per-shot
generation costs about the same per finished second and makes a failure cost
one shot. `make_clip.py` sends one frame per call and names each clip after its
shot, so a reroll is targeted.

## Resolution tiers lie in video too
`768P` is 768 on the SHORT edge — 768x1365 at 9:16, under Instagram's 1080
floor. It is a **draft tier only**. Finals go at `2K` (1440 short edge) and come
down to 1080x1920 in `publish_prep`. Exactly the same trap as "1k" meaning one
megapixel. On H3 the draft-then-promote path costs the same as shooting 2K
directly ($0.08 + $0.05 = $0.13/s), so drafting is free optionality.
H3 also generates native stereo audio with no switch to disable it. Strip it in
the editor — the Reel carries trending audio and typed overlays.

## A phrase search must never decide whether a whole instruction is sent
`outside.build()` decided a shot was a selfie by testing for `"arm's length"`
anywhere in the text. `rf_bed` used that phrase to say where the **camera** was
resting, and so a woman lying asleep with both arms under her pillow was about
to be told she has "the one extended toward the camera, and one other" — the
exact extra-limb failure the block exists to prevent.
Caught in a dry run, before it cost anything. Two fixes: the sentence was
rephrased, and shots can now state `selfie=False` outright, with the phrase
demoted to a default. **Any heuristic that gates a paragraph should be
overridable by the thing it is guessing about.**

## Floaty motion is under-specified motion
Take 3 held her face at 768P but drifted. Three causes, all in the prompt:
1. **No camera lock.** The still's prompt said where the camera SAT; nothing
   said whether it MOVED. These models fill that silence with a slow drift.
   The lock goes at the END of the prompt, per H3's published structure.
2. **Diminutives are the float.** "blinks slowly", "very slightly", "a little
   further", "the smallest amount" — "keep the motion small" written as
   adverbs. Diffusion video defaults to sluggish pacing because slow motion is
   the easiest thing to keep temporally consistent, so a hedged verb reads as
   permission to pick the slowest interpretation. Use discrete actions that
   start and finish, and ask for ordinary speed positively.
3. **Four seconds is the duration FLOOR.** A movement too small to fill four
   seconds gets the remainder filled with drift. Two timestamped beats
   ("0-2s: ... 2-4s: ...") fill it definitively. H3 accepts timestamped ranges;
   the published guidance is one scene, one action, one camera move.
Note we deliberately break the never-negate rule in the camera lock, because
that rule was learned on Seedream and H3 has a designated elements-to-avoid
section. **Model-specific rules do not transfer** — the same trap as applying
Seedream's "fewer references" to Kling.

## The camera lock must match the camera in the frame
The first fix gave every clip "the camera is locked off on a surface." One of
the four is a handheld selfie with her arm visibly in shot, so that line argued
with its own first frame. Propped shots and held shots need different locks,
resolved from the same `selfie` flag `outside.build()` uses. **A video prompt
inherits the frame's camera; it cannot contradict it.**

## I can see the generated images now — `cat >` breaks the hardlink
File staging off this machine failed all project with "file is hardlinked
(nlink > 1)". `cp` does not help: it preserves the link. **`cat source > dest`
writes new bytes and produces a file with one link, which stages fine.**
    cat content/outside/shot_abc123_1.png > _view/shot.png
Then read it. This matters more than a plumbing note: rule number one is
photorealism, and until now every judgement about an image was made from its
prompt rather than from the picture. Look at the frame before writing anything
that describes it.

## A clip that mirrors needs landmarks, not a prohibition
`rf_window` flipped to its mirror partway through. These models are stateless —
each frame is guided by the previous one with no 3D model of the scene — so
nothing structurally prevents a composition resolving to its mirror, and
horizontal flip is a standard training augmentation, which makes it a cheap
move in latent space. A near-symmetric frame invites it.
"Never mirrored or reversed" alone gives the model nothing to hold. **Name
fixed landmarks on named sides** so a flip contradicts the prompt: window left,
curtain right, plant bottom left, chair bottom right. Per-shot `ANCHOR` in
`reel_frames.py`.
Two contributing errors in the motion line: "the curtain moves once BESIDE
HER" named no side, and "still facing the window" re-asserted an orientation
the model then had to re-derive.

## Never write an anchor for a frame you have not looked at
The first fix for the mirror said "her back staying to the camera". She stands
in PROFILE with her face fully visible. I had described a frame I had never
seen, from memory of the prompt that made it — and a prompt that contradicts
its own first frame is worse than one that under-specifies. Caught only by
staging the image and looking. **An anchor is a description of a picture, so it
requires the picture.**

## Hashtags: the quote still stands, but there is now a HARD CAP OF 5
Mosseri's position is unchanged and current as of a July 2026 Q&A: "Hashtags
work, but they've never been a good way to actually increase your reach."
What changed is the mechanics around it, and both changes postdate the source
this playbook originally cited:
  * **13 Dec 2024** — the ability to FOLLOW a hashtag was removed, quietly, no
    announcement. Stated reason: spam. A hashtag is no longer a feed surface.
  * **19 Dec 2025** — the limit dropped from 30 to **5 per post and per Reel**.
    Reported as a hard cap: tags beyond the fifth are ignored.
So hashtags are now a **search and classification signal, not a reach lever**.
The things doing the work for discoverability are the CAPTION KEYWORDS, the alt
text, and audio attribution — which means the caption should contain the words
someone would actually search ("seoul", "pilates"), not only mood.
Existing grid captions use 1-2 tags each and are unaffected.
NOTE ON SOURCING: the cap is corroborated by BusinessToday (19 Dec 2025) and
Later's hashtag guide, but the primary Instagram announcement was not read
directly — treat the "tags beyond five are ignored" mechanism as reported
rather than verified from source.

## "Catalogue / studio-like" is four specific things, not a vibe
`morning_window` reached the grid and read as AI. Not the rendering — the
production value. It looks lit and styled by a crew. Concretely:
  1. **Monochrome palette.** White chair, white cardigan, cream curtain, pale
     wall. Nothing clashes. Real rooms always have something that clashes.
  2. **One-of-each styling.** One plant, one mug, one side table. Objects
     PLACED rather than left.
  3. **Even wraparound light, no dominant source.** Nothing underexposed,
     nothing blown, no hard edge anywhere.
  4. **Nothing mid-use.** The room reads as tidied FOR the photograph.
Prevention, per prompt: name at least two things out of place or half-finished
(yesterday's mug, a jumper over the chair arm, a charger cable), name ONE hard
light source with a direction and let something fall dark, and let one object
break the colour harmony.
This is the third recorded swing on rooms — catalogue-styled, then neglected,
now catalogue again. The stable target is USED.

## A clean hero contaminates every frame edited out of it
`morning_window` is a HERO. hero+edit inherits the room from the hero, so its
showroom cleanliness is not a property of one image — it is baked into every
frame that room will ever produce. **Mess has to exist at hero time.** Check a
hero for the four tells above BEFORE locking it, because after that the only
fix is re-shooting the hero.

## A third-person frame needs an owner, and must stay rare
I called both `morning_window` and `s_park_green` failures for having no
photographer. Wrong on the park one: a friend walking with her is a real way
that photo exists, the `friend` camera exists in CAMERAS for exactly that, and
ONE such frame in thirteen does not establish a pattern. The rule is not "never
third-person" — it is **"attributable, and not the norm."** The selfie family
cap in `audit.py` already enforces the second half.

## Every picture is a story, and everything in it is a consequence
The operator's rule, and it supersedes the way these prompts were being
written. Before any prompt, answer four questions:
  * **where** she went
  * **who** she was with
  * **what mood** she was in
  * **why this photo exists** — why she took it, and why she would post it
Camera angle, wardrobe, expression and framing are CONSEQUENCES of those
answers, not independent choices. His examples:
  "she went to the park and asked her friend to take a picture, she was
   excited" -> a friend camera, a step or two back, a real smile
  "i dressed up and felt cute so i decided to post a picture, so the phone is
   held up and angled down for a cuter shot" -> the HIGH ANGLE IS CAUSED BY THE
   INTENT. It is not a style choice.
This is why a shot can be plausible in every individual part and still read as
fake: the parts do not descend from a common cause. Dressed for a night out,
in gym light, with a neutral expression, from a propped phone — four defensible
choices that no real situation produces at once.
THE PREMISE IS NOT SENT TO THE MODEL. Naming an emotion produces a performance
of it (see the rule above). The premise exists to generate the physical
details; only those go in `text`.
Shot dicts carry it as `story="..."`. `audit.py` reports coverage per pool.
Bonus: the caption falls out of the premise for free. We have been writing
captions as a separate act, which is why some of them read like they were
attached to the picture rather than produced by the same moment.


## `week.md` — her life is the source, not a content calendar
Every `story=` premise picks a real slot from `week.md`. If a premise cannot be
placed in that week, either the week is wrong or the shot is. It exists to make
the account accumulate: the same studio corner in March and October, the same
friend's name, a countdown that was running before the viewer arrived.
TWO CLOCKS drive it, both already on camera: savings running out (four months
as of day 214) and the certification exam in autumn. They surface roughly once
a fortnight, which is how people mention the thing they think about daily.
HARD CONSTRAINT ON PEOPLE. She has friends; we cannot render them. Holding ONE
identity took the whole project and a second stable face would need its own
master stack and would drift. **People appear as EVIDENCE, never as a face** —
a second cup, a forearm at the frame edge, a bag on the opposite chair, a name
in the caption, a reply in the comments, or a photo they took of her. That last
one is what the `friend` camera in CAMERAS is for.
Do not name a real pilates academy. Use the FORMAT — three-day weekend modules
against logged observation, practice and teaching hours, ending in a practical
exam — which is how comprehensive training in Seoul actually runs. Naming a
real school implies an affiliation that does not exist.


## NO MEN. Anywhere. Ever.
Not in frame, not in a caption, not named, not implied, not a hand at the edge
of a photo, not the person who took it, not a "someone". No boyfriend, no ex,
no male classmate, colleague or brother. Applies to comment replies too.
The account converts on the viewer believing there is room for him. A man
anywhere in her life closes that door, and it does not reopen once a name has
been said. Every person in the cast is a woman.

## A day has slots, not one event
The first `week.md` gave each day a single anchor, which would produce a grid
where every twenty-four hours contains exactly one thing. Real days do not work
that way: she trains in the morning AND is out in the evening. `week.md` is now
a morning/afternoon/evening grid, and a `story=` premise names the slot, not
just the day.

## The premise must justify the CAMERA, not just the scene
`w_studio_early` and `w_desk_afternoon` both said "the camera is propped" in
the text and both came back looking like somebody else took them. The text was
not the problem. The PREMISE was.
  * studio: "she photographs it because the empty room with the sun across the
    floor is the only good thing about a seven a.m. slot" — that is a reason to
    photograph THE ROOM. It is not a reason to produce a composed portrait of
    herself sitting in it.
  * desk: "taking a picture is a way of not working for thirty seconds" — that
    is a selfie. Nobody sets up a propped shot to procrastinate for half a
    minute.
**Propping a phone is deliberate effort and needs a reason in the premise**:
she wanted her whole body in frame, she wanted the room in it, she was filming
something and kept a still. Absent such a reason, the honest camera is her arm.
And ask the second question too: does the stated reason justify photographing
HER, or the place? If it is the place, she is small in it or absent from it.
This is the same test as "the camera lock must match the camera in the frame",
one layer earlier. I wrote that rule and then failed to run it between the
premise and the camera.

## Name light that is INCONVENIENT, not merely directional
The desk shot came back magazine-ready. The prompt asked for "low late sun
through a window to one side" — directional, which the rules demanded, but also
beautiful, which they did not forbid. Sun through a window BEHIND her produces
rim-light on the hair, and rim-light is glamour: it is what a photographer buys
a scrim to get.
Real phone photographs at four in the afternoon have a window blown to white, a
face gone muddy in the middle, and contrast nobody would choose. Name that.
SECOND LEVER ON THE SHEEN. A single source directly overhead physically makes
highlights on the forehead and cheekbone — `w_mon_late` glowed partly because
the ceiling light put it there. Skin wording and light direction are two
different controls on the same artifact, and both have to be set.


## Propped means POSED. Selfie means IMPULSE. (operator's rule)
"If someone props his phone it is because he wants to pose and needs his whole
body, so he cannot hold it. If I want a picture because the light is good, I
take my phone out of my pocket and use the front camera."
This settles the camera question properly:
  * **propped** = she wanted to POSE and needed her whole body in frame, which
    is the only reason worth the effort of setting the phone down, walking into
    shot and coming back. Full length. Deliberate.
  * **selfie** = everything else. Good light, a mood, something funny, wanting
    to complain to someone. Phone out of the pocket, front camera, arm's
    length. THIS IS THE DEFAULT and should be the large majority.
The correction it forces, which I had exactly backwards: **a propped shot
should LOOK posed.** I had been writing propped shots as candid, which is the
worst combination of all —
  posed + third person   -> she set it up. Fine.
  candid + selfie        -> impulse. Fine.
  posed + selfie         -> a selfie she thought about. Fine.
  candid + third person  -> A PHOTOGRAPHER WHO IS NOT THERE. The tell.
The only exception is a friend-taken frame, where a photographer genuinely
exists — attributable, and rare.
The imperfection in a propped shot is not in the POSE, it is in the FRAMING:
she set the phone down and walked away without being able to check it.

## ALWAYS DOUBLE CHECK WHAT YOU HAVE (operator's rule, absolute)
Do not report a thing as done because the code that was supposed to do it ran
without raising. Verify against the artefact.
It was given after this exact failure: a script rewrote four prompts, printed
"4 rewritten", and changed nothing. The shots are `dict(...)` CALLS, so walking
the AST for `ast.Dict` found zero nodes, every replacement was skipped, and the
file was written back byte-identical. The success message printed the keys I
INTENDED to change, never what actually changed.
The rules that follow from it:
  * **a print statement is not evidence.** Print what changed, not what was
    planned. Compare a hash before and against after, and assert it moved.
  * **assert the match count**, not just that the code ran. `assert
    len(spans) == len(new)` would have caught this instantly.
  * **verify against the VALUE, not the source.** Prompts are implicitly
    concatenated string literals, so any phrase can be split across a line
    break — `grep "out of focus"` returns nothing on a file that contains it.
    Import the module and check the assembled strings.
  * **check the numbers moved.** Four rewritten prompts with byte-identical
    character counts is not a coincidence, it is the tell.
  * partial failure is worse than total failure: the first attempt applied one
    replacement, then threw on the second, and never wrote — so a "1 of 4"
    result looked like "0 of 4". Write only after every edit is validated.

## Nobody photographs what they do not want seen (operator's rule)
`w_mon_late` was written on the premise "she looks completely destroyed and
finds that funny, and the account is not only the good days." That is not a
motive a person has. It is an influencer-strategy rationalisation.
Real reasons a photo of yourself exists, and there are only three:
  1. she looks photographable and wants that recorded
  2. she wants to SHOW or DOCUMENT something — a place, a meal, a milestone,
     something she is pleased with or finds remarkable
  3. **somebody else took it** — and in this account there is nobody else
     except Jieun, who is rare by design
Nobody photographs their dirty kitchen. Nobody frames a used pan on the floor.
**Mess is never the SUBJECT.** It can sit in the frame incidentally and it can
live in the CAPTION — "this is dinner, do not look at the sink" works as words
over a picture she was happy to take. It does not work as the composition.
THE TEST, before writing any premise: **would she actually press post?**

## Amateur is in the CAMERA, not in the subject
The mistake underneath the one above: I had been treating "not editorial" as
"unpleasant". They are different axes.
Realism comes from the bad light, the crooked frame, the cheap front lens, the
unwashed face, the moment slightly early or late. It does NOT come from the
subject being grim. **She can look good in a badly taken photograph** — that is
the single most common photograph on Instagram.
So: keep the amateur camera, keep the ugly light, keep no makeup and real skin.
Drop the squalor.

## A selfie can only contain what fits at arm's length
`w_desk_afternoon` came back in third person — a woman holding a phone, seen
from across the room — despite an explicit front-camera line.
Cause: the prompt listed a laptop, a mug, a notebook, a charger cable, a fan, a
sofa and a window. None of that fits in a 23mm frame at arm's length, so the
model stepped back to fit the scene in, and resolved the contradiction the only
way it could — by depicting SOMEONE TAKING A SELFIE instead of producing one.
**The amount of scene you describe sets the camera distance, whatever the
camera line says.** In a selfie name two or three things at most, all of them
close to her. Everything else is out of frame, which is what out of frame is
for. If the scene needs to be seen, it is not a selfie.

## Do not aim limbs at a wide lens from close range
`w_mon_late` sat her on the floor with her knees toward a 23mm lens held low.
The nearest limbs ballooned and the proportions broke. A wide lens exaggerates
whatever is closest to it, and at floor level that is a knee. Keep the nearest
thing to the lens her face.

## BAD LIGHT + POSITIVE MOTIVE. That is the combination.
The pairing I kept getting wrong. I had been putting bad light with a negative
motive — tired, defeated, documenting the grim bits — and producing pictures
nobody would take. The operator's reference accounts are the opposite:
  "those girls felt cute and decided to take a picture of themselves, or they
   saw a nice illuminated monument and decided to take a selfie"
The MOTIVE is positive every time. She feels good, or something in front of her
is worth having. That is the whole reason the shutter goes.
The LIGHT is free to be terrible, and usually is:
  * sun straight into her eyes so she is squinting and half the frame is blown
  * backlit into flare, her face gone dark, the phone lifting it unevenly
  * a night shot the phone cannot expose, noisy and smeared
  * a single shop sign or streetlight doing all the work, colour cast and all
  * a monument or a sign lit at night and the exposure metering for THAT, so
    she is underexposed in front of it
So: keep the camera cheap and the light wrong. Make the reason to take it good.

## Overexposure is not the glass-skin tell — do not confuse them
Two different bright things, and `SKIN` only governs one.
  * **specular sheen** — wet-looking highlights on cheekbone and brow with
    correct exposure elsewhere. A beauty-light artefact. THE TELL. `SKIN`
    exists to bound it.
  * **global overexposure** — the whole frame blown because she is facing the
    sun and the phone metered for her face. Skin bright, detail gone, squinting.
    COMPLETELY REAL, and one of the most common photographs there is.
Do not let the matte-skin wording suppress the second. When a shot is written
into hard sun, say the frame is overexposed and let her skin go bright with it.

## The highlight was never the SKIN block. It was the LIGHT I kept asking for.
Measured, after three failed rewrites of the wording. Percentage of skin-toned
pixels above luminance 215:
    references (master/a)        1.07%   <- clean. Not the source.
    g_seongsu_walk              18.05%   hard overhead sun
    g_street_heat               12.56%   hard overhead sun
    g_convenience_night         11.09%   strip lighting directly overhead
    g_dressed_up                 3.93%   one warm bulb overhead
    g_studio_after               0.22%   flat overcast from a window
    g_cafe_jieun                 0.24%   overhead spots, counter brighter than her
The correlation is total. **A hard point source directly above a head puts a
hotspot on the forehead, nose and cheekbones. That is physics, and the model is
right to render it.** I had written this exact sentence into this file the same
morning, then specified overhead-hard light in four more shots, because I was
chasing "unflattering" and overhead-hard is the most obviously unflattering
thing to write.
It is also the one that produces the artefact we have spent the project
fighting. Get "unflattering" from somewhere else:
  * OPEN SHADE with the sunlit street behind her burnt out — what people
    actually do at thirty-four degrees, and there is no highlight to make
  * light from BEHIND the camera, so she squints and nothing is modelled
  * a broad source — a ceiling panel, strip lights running a whole ceiling,
    overcast through a window — where the light arrives from everywhere and
    nothing on her face is sculpted
  * bounced light only, the source out of frame behind her
NEVER a bare bulb, a spot, or the sun directly above her head.
An overhead point source is still fine where there is no skin in the frame —
g_late_noodles keeps its ceiling light.

## If the HAND is in frame, the model puts a phone in it
`g_studio_after` and `g_dressed_up` came back with a phone held up in shot.
They were the only two shots with the camera ABOVE her eyeline and "her arm
into the TOP corner". Every other selfie says the arm cuts into the BOTTOM
corner — where the forearm is visible and the hand is past the edge.
A raised arm reaching into the top of a frame brings the HAND with it, and a
hand at that angle is holding a phone in every photograph ever taken. The model
completes the gesture. This is not the old "never name the device" rule; the
device was never named. **It is anatomy: show the hand, get the object.**
Write the arm so the hand leaves the frame:
  bottom corner -> "her arm cutting into the bottom corner"   (forearm only)
  above eyeline -> "her upper arm running up and out of the top of the frame
                    with her hand beyond the edge"
The high angled-down selfie is worth keeping — it is what someone does when
they want a good one — but it has to be framed so the hand is outside it.

## Background blur is the biggest single AI tell in a selfie
`g_convenience_night` "screamed AI" and the cause was one clause I wrote:
"the shelves behind her going out of focus with nothing legible on them."
I wrote it to dodge gibberish packaging text. What it produced was creamy
portrait-mode bokeh down a whole aisle — and **a 23mm front camera at arm's
length has DEEP focus. That blur is physically impossible.** It is a DSLR or
portrait-mode look, and the eye reads it instantly even when it cannot name it.
I traded a small tell for a much larger one.
Avoid unreadable text by NOT INVITING PACKAGING, not by blurring it. Name the
surface — "the aisle and the shelves running away behind her" — and say sharp:
"deep focus with the whole aisle sharp".
Also removed from the shared FRONT constant: "the background falls away behind
her". It meant perspective, but it reads as focus, and it was going into every
selfie in the project.
**In a phone selfie, everything is sharp. Always.**

## SUPERSEDED — Qwen3 is NOT the renderer. See "gpt-image-2 is the renderer" below. Kept only because the reasoning error is the lesson.
### (original heading: Qwen3 is the renderer, decided by a three-way test)
Same three prompts through seedream, gpt-image-2 and qwen3/pro-image-to-image.
Qwen returned sweat on the hairline, visible freckles, a blank stare, a near
forearm properly stretched across the bottom third, and other people in the
room. The other two returned polished editorial from identical text — the
thing we had spent the entire project trying to prompt our way out of.
Identity held on all three Qwen frames, which also confirms `image_urls` is
its correct reference field.
TWO CAPABILITIES NOTHING ELSE HAS:
  * `negative_prompt` — negations can finally live outside the positive text
    instead of summoning what they name.
  * `seed` — real A/B tests. Change one clause, hold everything else, see what
    actually moved. Every comparison before this was confounded.
ALSO SET: `prompt_extend` must stay FALSE. It defaults TRUE and rewrites the
prompt before the model sees it, which would discard every rule in this file.
And its ratio field is `image_size`, not `aspect_ratio`.

## gpt-image-2 i2i reads `input_urls`, not `image_urls`
Its reference field was INFERRED from the text-to-image endpoint and the
comment in the schema said so plainly — "verified by the first call" — and that
verification never happened. So every reference went under a key the model does
not read, and it built a plausible woman from the text alone. Realistic, and
not her. **Never ship an inferred field name. Print the payload and read it
against the published schema first.**

## SAY ONLY THE DELTA (the most important prompting rule in this file)
The operator's entire prompt for master frame a2 was:
    "THREE-QUARTER LEFT 45 degrees."
Seven words, and it produced the best frame in the stack.
It works because a1 already carries the background, the light, the styling, the
skin and the hair. The prompt only had to say what the reference could not
show. **Every sentence describing something a reference already depicts is a
second, weaker source of truth competing with the pixels — and the pixels
should win.** That is the mechanism behind most of this file's failures: the
armchair, the editorial lighting, the perfect skin were all text fighting a
photograph.
    angle change  -> just the angle
    body frame    -> the body, because a face frame does not contain one
Before sending any prompt, delete every clause the attached reference already
answers. This is not token economy. It is removing competing instructions.

## gpt-image-2 IS THE RENDERER. The first test that said otherwise was broken. (This supersedes the Qwen3 entry above. It is also the entry the "Models in use" table at the top now reflects.)
Qwen won the three-way test — but that test ran while gpt-image-2's references
were going to `image_urls`, a field it does not read, so it was generating from
text alone. It lost on identity for a reason that had nothing to do with the
model. With `input_urls` correct it produced the best images of the project:
a market stall another AI insisted was a real photograph, and a studio selfie
with correct skin, correct near-arm distortion and real people in the room.
**A benchmark run on a broken integration measures the integration.** Fix the
plumbing before you rank the models.
Qwen stays wired and is still the only one with `negative_prompt` and `seed`.
KNOWN ISSUE: gpt-image-2 refuses the mirror-selfie prompt. Cause unconfirmed —
suspect a filter on phone-in-mirror framing. Qwen renders it fine.

## Expressions come from TEXT, not from reference frames
master/b holds an expression set. It is NOT attached. Operator's call and the
evidence supports it: gpt-image-2 produced a genuinely blank stare from words,
and Qwen produced a real yawn. Every extra reference is another thing that can
fight the prompt, so the face frames stay NEUTRAL.
BUT: she had exactly two faces for most of this project — neutral, or a soft
smile. **Every shot must name a DIFFERENT expression, described physically.**
The twelve in grid_stories.md are all distinct: mid-word, blank and flushed, a
real yawn, mouth flat with eyebrows up, eyes shut against sun, appraising,
a small deliberate closed smile, a full open laugh.

## Read the canon before writing the prompt
`masters.py` asked for "plain black" athletic wear for two master frames. The
canonical wardrobe was already written in `body_block.txt` line 30 — "a matte
bone-white fitted athletic set: a supportive scoop-neck sports bra and
high-waisted mid-thigh shorts, no logos, no patterns, no contrast seams" — and
had been the whole time. It was invented instead of looked up, and it would
have split the master stack into two wardrobes.
CORRECTION TO AN EARLIER VERSION OF THIS ENTRY: I claimed gpt-image-2 had
produced the bone-white set anyway and "outvoted" the text. It had not. The
image I read that from was the OLD c5, which masters.py had not yet replaced —
I mistook the operator's reference for a generation and wrote a conclusion
about model behaviour that never occurred. **Never describe what a model did
until you have confirmed which file you are looking at.**
Before writing any prompt touching wardrobe, build, face or the tattoo, open
identity_block.txt and body_block.txt. They are the canon. Do not reconstruct
from memory of the conversation.

## The tattoo anchor itself was bad, which is why it never rendered
The OLD c5 — the body reference every wide shot has been attaching this whole
project — carries a tattoo that is tiny, faint, and sitting on the oblique
rather than on the ribs. It is on her LEFT, which agrees with canon, so the
side was never the real problem.
**Everything downstream inherited a bad anchor.** A reference cannot pass on
detail it does not clearly contain, and "as shown in the reference" in
body_block.txt was pointing at something barely legible.
Now specified as a single upright sprig **as long as her hand**, starting just
below the bra line and **running down along the ribs**, in clean confident
single-weight linework with every leaf separated. Size, orientation, start
point, and line quality. "Small" is not a specification.

## NEVER NAME THE PHOTOGRAPHER — they will appear in the frame
`n_cafe_jieun` said "looking just past the lens at the woman sitting opposite
her". Jieun IS the camera; her position in the scene is the lens. Naming her as
a person made her a SUBJECT, and gpt-image-2 put a second woman at the near
edge of the frame — someone who cannot exist, because she is holding the phone.
Identical mechanism to "never name the device": say phone, get a phone in shot.
Say the photographer, get the photographer in shot.
Write the CAMERA POSITION instead, never the person occupying it:
  wrong -> "taken by the woman walking with her"
  wrong -> "looking at the woman opposite her"
  right -> "taken from half a step behind and to one side"
  right -> "looking just past the lens"
Who is holding it belongs in the `story=` premise, which is never sent.

## A friend's photo is taken from a chair, not from a tripod
The same shot also came back editorial: a pendant lamp haloing her, styled
balayage waves at nine in the evening, centred, balanced, magazine-grade.
A person across a small cafe table is about a METRE away with the phone at
chest height, so the frame is cramped and angled slightly UP, the table edge
looms in the near foreground, and the subject sits off-centre and gets cut by
the edge. Say all four of those, or "taken from across the table" is read as
"photographed by someone competent".
Also: hair at 21:15 has been on her head since morning. Say so.

## You cannot photograph yourself doing something involuntary
`n_conv_yawn` was written as a yawn: eyes shut, jaw wide, "she keeps that one
because it is funnier than the one where she looked fine."
Nobody photographs themselves yawning. **You cannot see yourself yawn.** It is
involuntary, it happens AFTER the button is pressed, and the frame gets
deleted. Same for a sneeze, a blink, a stumble, a mouth full of food.
This is the "she looks destroyed and finds it funny" rationalisation in a
different costume — and it was written AFTER that rule was already in this
file. **Writing a rule down is not the same as applying it.** Before any
premise: could she have DECIDED to take this, and would she press post?
The corrected frame keeps the hour and the exhaustion but gives her a motive
that exists: she catches herself in the freezer glass, decides she looks fine
anyway, and takes one deadpan.

## A no-face shot with a LIMB in it still needs a reference
`n_desk_late` is a table with a bare knee and foot at the frame edge. It ran as
noface, so NO reference was attached and no person was described — and the
model had nothing to say whose leg it was. **It rendered a man's leg.**
The operator patched it in the file to "a bare woman knee", which was the right
instinct and the wrong tool: a bare gender word invites a whole person into a
shot meant to have none, and the audit then flagged the fix as the fault.
Words cannot settle whose body this is. A picture can.
`limb=True` now attaches the BODY frame to a noface shot and says what it is
for: "the arm or leg visible at the edge of this frame is hers, nobody else is
in the picture." The audit exempts declared-limb shots from the person check.
A shot with NO body part at all — the market, the studio floor — still gets no
reference and still routes to text-to-image.

## Five selfies in twelve is one photograph taken five times
Not because the number is wrong, but because arm's-length selfies share a
COMPOSITION: forearm large across the bottom, face upper-middle, same crop,
same distance. Different places and expressions do not break that signature.
`n_river_sun` became a no-face picture of the sunset, which is what the premise
argued for anyway — "the light was unbelievable" is honestly a picture OF the
light. Final mix: 5 no-face, 4 selfie, 1 mirror, 1 friend-taken, 1 propped.
Seven of twelve still show her face.
Watch this ratio on every future batch. The constraint that pushes toward
selfies is real — no men, friends only as evidence — so the counterweight has
to be deliberate: things she saw, places, food, and the occasional frame where
she is small in a big one.

## NAME THE PLACE, never the category (operator's rule)
"A fruit stall in a market" gets the model's global default, which is Western.
"A fruit stall in a SEOUL market" got Korean shop signage with a phone number,
handwritten won price cards, polystyrene crates, wet ground and shoppers
walking away down the aisle — the frame another AI argued was a real photo.
The rule generalises: an unqualified noun renders as the training set's
average, and the average is not Seoul.
Audit of the first twelve grid prompts: only FIVE named a place. The five that
did are the five that came back best. The other seven said "a small cafe
table", "an empty pilates studio floor", "a narrow residential street" — all of
which could be anywhere, and would therefore be rendered as nowhere.
Every shot now names one: Seoul, and the neighbourhood where week.md
establishes one — Seongsu for the studio, Euljiro for the cafe with Jieun,
Seoul Forest for the park, the Han river for the river.
NEIGHBOURHOODS ONLY, NEVER A REAL BUSINESS. A district is a place; a named shop
implies an affiliation that does not exist.
`audit.py` now fails any shot with no location in it.

## "Everything sharp" is a DAYLIGHT rule. At night it manufactures a studio
It went into every prompt to kill portrait-mode bokeh, which is the loudest AI
tell in a selfie. That is correct at arm's length in daylight, where a 23mm
front camera really does hold everything. Carried into `n_roof_posed` — a woman
full length on a roof at midnight — it produced a frame with no grain, no
softness and perfectly even light on her: a fashion editorial, the single most
artificial image in the grid.
A real midnight phone photo of a person three metres away is DARK, NOISY and a
little soft on the subject. Keep the anti-bokeh intent without the daylight
claim: say "the clutter and the buildings behind are as much in focus as she
is", then say dark, underexposed, heavy noise in the shadows.
Deep focus is the point. Impossible clarity is not.

## Never name a colour for the sky. Name the lights that are in the picture
"Magenta dusk cast" did not tint the frame. It painted a flat magenta backdrop
behind her, like a studio seamless, and then the model lit her to match it.
Same failure family as the overhead bulb: I described the PHOTONS instead of
the PLACE, and got a lighting setup.
At midnight the honest sources are objects: an open lit stairwell doorway, the
windows of the buildings below the parapet, a security light. Name those, let
the sky be dark, and the light arrives from where those things are.

## "Posed deliberately, chin lifted, small closed smile, looking straight at the camera" is a direction you give a MODEL, and you get a model
The premise was right — she propped the phone because she wanted the whole
outfit in it, and that IS the one deliberate frame in the set. But the premise
does not survive being written as stage directions. Four consecutive posing
instructions produce a runway walk with softbox light.
What actually happens on a ten-second timer is that you walk into place and
stand there waiting for the shutter, arms hanging, mouth closed, weight even.
Write THAT. Standing still for a timer is not the same thing as posing, and the
difference is the whole difference between a photograph and a campaign.

## A limb shot inherits the reference's WARDROBE, not just its proportions
`limb=True` attaches the full-length body frame so the model knows whose knee
is in the corner — that is why it exists, and it did stop the man's leg. But
the reference also carries CLOTHES. `n_noodles` came back with her sitting in a
late-night noodle shop in the reference's bone-white crop top and shorts,
because the prompt described a bowl and a hand and said nothing about what she
was wearing, so the only wardrobe in the context won.
Two fixes, and the second is better:
1. State the clothing in the prompt, so the text outranks the reference.
2. Keep her body OUT of the frame. A forearm, and the rest of her past the
   edge. You cannot leak an outfit that is not in the picture — and a photo of
   your own dinner shows the bowl, not your thigh.

## console.py — the local control panel, and the one rule that keeps it honest
`python console.py` in this folder, then http://127.0.0.1:8765. Stdlib only,
no pip install, bound to loopback so nothing off this machine can reach it.
Two screens and deliberately only two: GENERATE (pick shots, see the cost, cap
it, run it, watch it, keep a real spend total) and PUBLISH (caption, tags with
the 5-cap enforced, location, alt text, export, mark posted).

THE RULE: **the console never reimplements generation or export.** It shells
out to `outside.py` and `publish_prep.py`. The prompt it shows you is obtained
by running `--dry-run` and reading what the CLI prints; the price is the number
the CLI prints divided by the images it was going to make. There is no second
prompt builder and no second price table anywhere in it.
That is not tidiness. Every lesson in this file lives in those scripts. A
console with its own copy of the prompt assembly would drift within a week, and
then the playbook would be true of only one of them, and the one it was true of
would not be the one being used.

Stale detection: it hashes each assembled prompt and compares against the
filenames on disk, which encode the hash of the prompt that made them. A shot
whose prompt changed since its last render is flagged STALE. The cache is keyed
on the shots file AND `outside.py`, because SKIN / ARMS / ROLES / SAFE live in
outside.py and changing one of those changes every prompt in every pool.
First run of it flagged exactly `n_noodles` and `n_roof_posed` and nothing
else, which is correct — those are the two rewritten on 25 Aug.

`posts.json` is the publish desk's store. `spend.jsonl` is the ledger, and it
records the cost the SCRIPT reported, never the console's estimate, because
outside.py refunds a failed image and the estimate does not know that.

## Room plates: gpt-image-2 CANNOT generate one at 16:9 or 21:9
The plan is right — a wider plate carries more of the room, and the room is
what the reference is for. But the two halves of gpt-image-2 do not accept the
same aspect ratios, and an empty room has nobody in it, so it is a TEXT-to-image
job:

    gpt-image-2-text-to-image     1:1  3:4  2:3  9:16          <- no wide
    gpt-image-2-image-to-image    1:1  3:4  2:3  9:16  4:3  3:2  16:9  21:9
    seedream/5-pro-text-to-image  1:1  3:4  2:3  9:16  4:3  3:2  16:9  21:9

So a 16:9 or 21:9 plate cannot come from gpt-image-2 text-to-image. Three ways
round it, in order of preference:
1. **i2i from a frame that already exists in that room.** Feed an existing
   photo of the room and ask for the room empty, at 16:9. Stays in the family,
   and the plate inherits a room that has already been accepted.
2. **Seedream text-to-image at 16:9 or 21:9.** The plate is a spec, not a
   published frame, so it does not have to come from the renderer. What matters
   is that the FINAL image is gpt-image-2.
3. **9:16 or 3:4 on gpt t2i** — available immediately, but it is the wrong
   direction: it carries less of the room, which is the whole point of a plate.

WIDER IS NOT AUTOMATICALLY BETTER, and I have not measured this. At a fixed 2K
tier a 21:9 plate has far fewer vertical pixels than a 3:4 one, so width is
bought with height, and a 3:4 output only ever uses a vertical band of it. It
is also unknown whether gpt-image-2 downsamples references to a fixed budget
before reading them, which would make aspect matter much less than framing.
Measure before committing: one room, plate at 16:9 and at 21:9, same shot
prompt through both, and compare the placed frames. Four images, about $0.36.

THE TEST THAT SETTLES THE COMPOSITING QUESTION, and it is cheap: one room, one
action, one identity reference stack, two runs — plate attached, and the same
room described in text with no plate. Look for the three compositing tells that
were used to write the original rule: no contact shadow under her feet, light
on her that disagrees with the light in the room, and a hard cut-out edge at
her shoulders. Two images, about $0.18. Do that before rebuilding anything.

## First frame TO LAST FRAME is interpolation, not motion
The published Reel read as AI and the mechanism is not a bad roll. Two fixed
endpoints do not describe movement — they force the model to find a path
between them and land exactly on the second, so it eases in and eases out, and
THAT EASING IS THE FLOATINESS. It is the same shape every time because it is
the same constraint every time.
One frame plus described motion leaves the model free to produce plausible
physics instead of a required landing. If a last frame is ever used again it
has to be a frame the motion would genuinely arrive at, not a second pose.
Second mechanism, separate and additive: **a video model re-renders skin on
every frame**, so its own prior reasserts and the matte skin of the source
still does not survive. That is why it came back glossy despite starting from
an accepted frame. The skin instruction is NOT inherited from the still — it
has to be in the video prompt too. Same failure family as the facial highlight
in the stills, which took four rounds to find.

## A Reel does not have to be generated video
`reel_build.py` cuts stills that have already passed QC into a 1080x1920 photo
dump with ffmpeg. No generation, so no AI-motion tells, and it costs nothing.
Real accounts post this format constantly. Until there is income this is the
DEFAULT and generated video is the exception that has to justify itself.
Decisions in it, with reasons: the still is fitted by WIDTH over a blurred
darkened copy of itself, because cropping 3:4 to 9:16 throws away a quarter of
the width and the width is where the room is. Push-in is 4% and optional —
more reads as a slideshow template. ~1.1s a still, because photo dumps are
fast. A silent audio track is muxed in because Instagram is inconsistent with
an audio-less file, and the music goes on IN THE APP: a Creator account keeps
the full catalogue and in-app audio is a discovery signal an embedded mp3 is
not.

## ffmpeg zoompan emits `d` frames FOR EVERY INPUT FRAME
The first build asked for 8.8 seconds and wrote a 246-second file. `-loop 1 -t
1.1` feeds zoompan 33 identical frames and zoompan emits `d` for each of them,
so 33 x 33. It played correctly at the start, which is exactly why nobody would
have noticed until Instagram rejected it or the whole thing looped for four
minutes.
The fix: the zoom path takes ONE input frame and generates the duration itself
(`-frames:v`), and only the static path uses `-loop`. `reel_build.py` now
ffprobes every clip it writes and raises if the duration is more than 0.35s
from what was asked for.
GENERALISES: verify what was WRITTEN, not what was requested. A file that opens
is not a file that is correct.

## Custom pixel sizes kill the 16:9 room-plate blocker
"gpt-image-2 CANNOT generate a plate at 16:9 or 21:9" was true of the ENUM and
only of the enum. fal's `image_size` also takes exact `{"width","height"}`, any
multiple of 16 up to a 3840 edge, on the TEXT-to-image endpoint as well. So
2048x1152 and 2352x1008 are both available and the plate plan is unblocked.
The earlier rule was not wrong about what it checked. It was wrong about what
it concluded, because it read the enum and stopped. WHEN A CONSTRAINT LOOKS
ABSURD, CHECK WHETHER YOU READ THE WHOLE FIELD.

## An unused import is still a dependency
`outside.py` had `from content import IPHONE_LEAN  # noqa: F401 (kept for
reference)`. IPHONE_LEAN was never used — the import line was its only
occurrence in the file. Retiring content.py therefore took the entire grid down
with it, because content.py imports the old client. A line that does nothing
still binds you to everything the module it names depends on.
Delete unused imports. "Kept for reference" is what comments are for.

## A comment is legal before `from __future__`. A docstring is not.
The retirement banner was written as a docstring and prepended to seven files,
every one of which starts with `from __future__ import annotations`. That is a
SyntaxError, and it broke all seven at once — including one the live path
imported. Banners go in as `#` comments, or after the future import.

## A zero price does not make a run free. It disables the budget cap.
fal does not publish per-image price, so the migration left `FAMILIES` at 0.0.
Every estimate then computes $0.00, and `if cost > budget` can never fire — the
guard is still there, still passing, and guarding nothing. That is worse than
no guard, because it looks like one.
`outside.py` now refuses to spend while the unit price is unknown and demands
`--unit-price`. GENERALISES: a safety check whose input is unknown must FAIL,
never default to zero.

## The "everything sharp" rule is about LIGHT, not the clock
Refining rule 90, which said "everything sharp is a daylight rule; at night it
manufactures a studio". True as far as it went, and stated too broadly: it was
learned on `n_roof_posed`, a full-length subject three metres away on a roof at
midnight, where the only light is city glow. It is NOT true of the convenience
store at 23:10, which used "Everything sharp" and came back as one of the best
frames in the grid, or of a coin laundry at 21:30.
The variable is AVAILABLE LIGHT, not the hour. A fluorescent-lit interior at
night is a daylight-equivalent exposure — a phone holds everything, and the
hard flat overhead light is itself the realism. An outdoor night scene at any
distance is not.
So: INTERIOR, ARTIFICIALLY LIT, SUBJECT CLOSE -> "everything sharp" stays.
OUTDOOR AT NIGHT, or subject metres away in low light -> dark, underexposed,
heavy noise in the shadows, a little soft on the subject; keep deep focus by
saying the background is as much in focus as she is.
A rule that names a proxy (the clock) instead of the cause (the light) will
misfire on the first honest exception. `audit.py` flags the pairing so it gets
thought about rather than applied.

## A file I maintain is not evidence. The artefact the process emitted is.
The operator said "I finished posting this week's posts" and then, later, "if I
say I posted the whole week, it means I posted the whole week." In between I
read `posts.json` — a file I write and update myself — saw six of twelve marked
posted, and planned three days of a week around six posts that did not need
posting. Two of the twelve I described as "needs generating" were already live.
`publish/feed` had the answer the whole time: an export sitting there for every
one of the twelve, timestamped, ending Sat 29 Aug. That directory is written by
the pipeline as a side effect of doing the work. It cannot be stale, because
nothing updates it except the act itself.
THE RULE: when checking state, prefer the artefact the process PRODUCED over
any record kept ABOUT the process. Files of the second kind go stale the moment
someone acts outside the tool, and the person acting outside the tool is
usually the operator, who is also the one telling you what happened.
AND THE OTHER HALF: the operator's plain statement outranks my bookkeeping. I
did not weigh it against the file and pick wrong — I did not weigh it at all.

## The repost calculation inverts at zero followers
A week ago I argued against archiving and reposting a weak image, because
archiving forfeits the engagement a post has already earned. That is sound
reasoning about an account with an audience. At ZERO followers there is no
engagement to forfeit, so the only remaining term is that the grid is the
surface that converts a profile visit into a follow — and a weak frame on it
costs more than a repost does.
Same decision, opposite answer, because one input changed. Rules that trade
things off need their inputs re-read, not their conclusions remembered.

## A rewritten prompt does not oblige a re-render, and a judgement I no longer hold must not survive in a file something else reads
I called `n_noodles` and `n_roof_posed` failures and rewrote both prompts. The
operator looked at the published frames and passed them. That read was mine,
made from downscaled copies, by someone who is not the one who knows the
audience or carries the risk. Overruled, and correctly.
The part worth keeping is not the disagreement. It is that THREE separate
places were carrying an instruction to change those images — a note in
posts.json, a line in the week plan, and the console's "stale prompt" badge —
and any one of them could have driven a later session to regenerate and repost
a frame that was fine. An opinion written into a data file outlives the opinion.
So: `locked=True` on the shot, `locked` in posts.json, and the console shows
"QC passed" instead of "stale" and excludes locked shots from "select stale".
The rewritten prompts stay, because they are better prompts and the reasoning
in them holds for FUTURE shots — a prompt is a recipe for the next image, not a
verdict on the last one.
GENERALISES: when a judgement is withdrawn, grep for every file that encoded
it. Retracting it in conversation changes nothing that a script reads.

## If she is not in frame, the identity problem does not exist (operator's idea)
Seedance refuses real-person identity references, which read as a wall. It is
not one. A FIRST-PERSON clip has no person in it, so there is nothing to
identify and nothing to refuse — and at the same time the hardest thing in
generated video to get past a viewer, a human face in motion, is simply absent.
No drift, no mirroring, no glossy skin, no gate to pass, no master stack to
upload. It is the cheapest believable video this account can make, and the
restriction that looked like a blocker selected the format for us.
`pov.py` holds the plates and the clips. Everything below is what the idea
needs in order to survive contact.

## A POV clip needs an owner too, and "filming her own class" has none
She is TEACHING the class. You cannot cue a room and hold a phone. It is the
same rule as the stills — a frame needs somebody whose hand the camera is in,
with a free hand and a reason.
What works, all already established in week.md: the empty studio BEFORE anyone
arrives (she has a key and nothing else to do — people have already seen the
photograph of exactly this); the walk in from the street; packing up after; her
own class as a PARTICIPANT rather than the teacher; or not the studio at all —
the river path, the market aisle, the subway.

## A first-person camera in a mirrored room photographs the person holding it
A pilates studio is full of mirrors. This is the video form of NEVER NAME THE
PHOTOGRAPHER — the mechanism is identical and so is the outcome. Frame away
from the mirrored wall, keep it out of the plate, and negate reflections
explicitly. The plates in `pov.py` say "no mirrored wall in view" for this
reason and not as decoration.
Same for HANDS: the moment one enters frame it is an unreferenced limb, and an
unreferenced limb came back as a man's leg in `n_desk_late`. Keep them out —
a POV clip does not need them.

## Seedance and H3 disagree on all three reference fields
Every one fails quietly rather than erroring, which is why this is a table.

    | thing              | H3 ref2v              | Seedance 2.5 ref2v |
    | references         | reference_image_urls  | image_urls         |
    | resolution casing  | 480P 768P 2K 4K       | 480p 720p 1080p    |
    | prompt reference   | "Image 1"             | "@Image1"          |

`seedance_video()` refuses a prompt with no `@Image` token in it, because a
plate that is attached but never addressed is paid for and ignored.
`generate_audio` defaults TRUE upstream and costs the same either way; we send
FALSE, because generated ambience is a tell and the music goes on in Instagram.

## Once the long edge is capped, a wider aspect buys nothing
fal caps any edge at 3840. Pin the long edge there and every wide ratio is the
SAME WIDTH:
    21:9   3840 x 1648    6.3 MP
    16:9   3840 x 2160    8.3 MP
     4:3   3840 x 2880   11.1 MP
21:9 is not wider than 4:3. It is 4:3 with the top and bottom thrown away. So a
plate — whose entire job is to contain the room — is 4:3 at 3840x2880, which is
maximum possible width AND the most vertical information, 11.1 MP against the
2.4 MP a 16:9 plate at the old "2k" tier would have been.
The general error: treating aspect ratio as if it controlled field of view. It
controls SHAPE. Under a fixed long edge it only ever trades one axis for the
other, and the wider ratio is always the one giving something up.

## A precondition checked during the work is not a precondition
`plate=` validation lived inside the generation worker, so a missing plate
killed a run halfway through — after paying for whatever sorted first. Moved to
before the cost line, over the whole batch. Anything that can refuse a run must
refuse it before the first call, not on the call that happens to hit it.
And it REFUSES rather than falling back to a described room. A silent fallback
would reintroduce the exact fault plates exist to fix, invisibly, at full price.

## A chronological photo dump is not a Reel
At zero followers only two signals decide whether a stranger sees anything:
COMPLETION and SENDS. A pretty sequence earns neither — no hook, so nothing
happens in the first three seconds; no question, so no reason to reach the end;
and nothing about the VIEWER, so no reason to send it to anyone.
What earns them: on-screen text in the first frame (Reels autoplay silent, so
text is the only thing working in second one); 7-12 seconds, because completion
is the metric; one idea per reel; a countable list when you want completion,
because people wait for the last item; and a claim with stakes when you want
sends, because a send is someone giving it to one specific person.
"i quit my job in january" is sendable. "here is my week" is not.


## The REST contract a vendor does not publish: use their client, not a mirror
fal's own docs page for file uploads 404s. I reconstructed the contract from a
third-party OpenAPI mirror, wrote "NOT VERIFIED FROM FAL'S OWN DOCS" in the
header, and shipped it as the fallback anyway. It returned
`404 Application "upload" not found` on every call, and because uploads gate
every image-to-image request, the entire pipeline was dead — masters, grid,
week two — while text-to-image kept working, so auth and the queue both looked
fine.
LABELLING A GUESS DOES NOT STOP IT BEING LOAD-BEARING. If the only honest note
you can write next to a piece of code is that you could not verify it, that is
not a caveat, it is a defect.
`fal_client.SyncClient(key).upload_file(path) -> str` is first-party and
documented. `pip install fal-client` is the correct trade: stdlib-only is a
rule for console.py, a server that must start on a machine I cannot inspect. It
was never a reason to reimplement a vendor's upload protocol from a stranger's
Postman collection.

## A plate earns its cost only if the place RECURS and a viewer would NOTICE
I put the Han river in the plate set. It does not belong there and the test was
already written down two rules above it: "outside is the majority of the feed —
places a viewer has no memory of, so coherence costs nothing and we can
re-render freely". The Han path is forty kilometres long and looks different
along all of it. A river plate buys consistency nobody could notice was
missing, at 11.1 megapixels a go.
The precedent is the worse half: plate the river and the same logic demands the
market, the street, the bakery and the subway, and the outside-is-free rule is
gone.
THE TWO CONDITIONS, both required:
  1. the place RECURS across many frames, and
  2. a viewer would NOTICE it changing.
Her flat passes both — people build a mental model of somebody's home, and a
home that rearranges itself is uncanny in a way nobody can name. So do the
hallway and the building. The studio passes on frequency and because it is HER
workplace. The river, the market, a bakery, a street: neither condition. Those
stay text.


## Suggested commands must be RUNNABLE, not templated
`--unit-price <p> --budget <5p>` pasted into PowerShell is not a wrong value,
it is a PARSE ERROR: `<` is a reserved redirection operator, so the shell
rejects the line before python ever sees it. The operator is on Windows
PowerShell and every command in this project will be pasted there.
Rules: concrete numbers in every example, never angle brackets. Line
continuation in PowerShell is a BACKTICK, not `^` (that is cmd) — so put long
commands on ONE line, which cannot be got wrong in either shell. Quote any path
that might contain a space.
This applied to the docs AND to outside.py's own error message, which helpfully
told the operator to run a command that could not parse.

## Cost is per PIXEL here, so one "price per image" is wrong by 6x
Measured: plate_room, 3840x2880 = 11.06 MP, quality high, $0.5304. gpt-image-2
bills OUTPUT TOKENS and they scale with area, so there is no per-image price —
there is a per-pixel one. 4.796e-8 USD/px, from that single charge.
    3840x2880  plate      11.06 MP   $0.5304  (measured)
    1728x2304  feed        3.98 MP   $0.1909
    1152x1536  feed alt    1.77 MP   $0.0849
A flat `--unit-price` is therefore wrong the moment a batch mixes sizes, and a
plate and a feed frame differ by six times. outside.py now prices every shot by
its own pixel count and only uses a flat figure if one is passed explicitly.
ONE DATA POINT. Linearity is assumed, not measured. `record_measurement()`
prints the constant any new real charge implies, so correcting it stays a
one-line job.

## "2k is the minimum publishable tier" does not survive the provider change
The old rule — 1k is one megapixel, not 1080 wide, and the $0.03 saving cost a
whole batch — was learned where ONE knob set resolution AND how hard the model
worked. fal separates them: `image_size` is pixels, `quality` is effort. So
"high quality at fewer pixels" is now possible and it was not before.
publish_prep exports 1080x1440. Generating at 1728 wide means paying for 1728
and discarding 60% of it. 1152x1536 is exactly 3:4, both edges multiples of 16,
still above 1080 so the export still downscales — and half the price, $0.0849
against $0.1909, every feed image forever.
NOT ADOPTED ON THIS REASONING. Tier "feed" exists and is not the default until
one shot has been generated both ways and looked at, because the rule this
overturns exists precisely because an obvious-sounding per-image saving cost a
batch. The reasoning explains why it MIGHT be safe now. Only the comparison can
say that it is.

## fal vs Kie: the size choice and the provider choice are the SAME decision
Operator's instinct was right on the headline. Kie charged a FLAT $0.09 an
image at any size; fal charges per pixel.
    plate 3840x2880   fal $0.5304   kie $0.09    Kie, 6x
    feed  1728x2304   fal $0.1909   kie $0.09    Kie, 2.1x
    feed  1152x1536   fal $0.0849   kie $0.09    fal
    6s clip, 3 refs   fal $0.36     kie $0.60    fal, 40%
A steady week — 8 stills and one clip, plates already made:
    fal at 1728x2304  $1.89        kie $1.32     Kie
    fal at 1152x1536  $1.04        kie $1.32     fal
So fal is only dearer because we ask for pixels Instagram discards. Kie's flat
rate SOUNDS cheaper but it came with fixed 1K/2K/4K tiers: you paid $0.09 for
4.07 MP whether you needed it or not and could not buy 1.77 MP for less. Per-
pixel billing is irritating exactly because it is paired with the thing that
makes it cheap — asking for what you actually need.
THE CONSEQUENCE: the 1152x1536 comparison is not a small saving to get round
to. It DECIDES THE PROVIDER. Hold it before any migration conversation.
UNVERIFIED: Kie's flat $0.09 was recorded but never tested at 4K. If Kie also
scaled with size, its plate column collapses and the comparison changes again.
Also not free to move: custom pixel sizes, H3 reference-to-video with 9 refs at
2K, and Seedance for POV clips are all things Kie did not expose, and the
current plan is built on them.

## Use the URLs the API RETURNS. Deriving them breaks on sub-path models
Submitting to `openai/gpt-image-2/edit` returns `status_url`, `response_url`
and `cancel_url`. I ignored them and built `.../{model}/requests/{id}/status`
myself. For a SUB-PATH model that address is wrong, and — worse than wrong — it
answers with an EMPTY BODY rather than an error, so the failure surfaced as
"unexpected status '': {}" with no clue in it.
The tell was in the first real run and I should have read it there:
`plate_room` succeeded, every week-two shot failed. Plates are text-to-image on
`openai/gpt-image-2` (no sub-path). The week is image-to-image on `/edit`.
ONLY THE SUB-PATH MODELS FAILED. When one class of call works and another does
not, the difference between them is the bug.

## The same error string in two places is ONE bug until proven otherwise
The probe's data-URI test failed with this identical message and I concluded
"fal rejects data URIs", moved uploads to fal_client, and wrote a playbook
entry about vendor SDKs. That test also ran against `/edit`. It was the status
URL the whole time, and the data-URI path may have been fine.
The fal_client change stands — it is first-party and the REST upload contract
genuinely is unpublished — but THE REASON I GAVE WAS NOT THE REASON IT BROKE,
and a fix that works for the wrong reason will mislead the next person to read
it. Two failures with one error string get one diagnosis, not two.

## A guard that refuses everything looks exactly like a guard working
`--budget` defaulted to 0.5. A batch quoted at $2.12 skipped all four shots and
printed "skip budget cap" for each, which reads as correct behaviour. Nothing
was wrong with the cap; the DEFAULT was unrelated to the work.
It also charged every shot the batch AVERAGE, so on a mixed batch a cheap shot
subsidised an expensive one against the cap and the arithmetic was simply
wrong. Now each job is priced by its own pixels, and --budget defaults to the
cost just printed — it still stops a typo or a runaway, but it cannot silently
refuse a run the operator has already been quoted.
A default that is not derived from the work is a guess with authority.

## At most ONE "meaning" reel a week. The rest is life. (operator's rule)
I planned three Reels and all three were pilates and money running out. That is
one note played three times and it fails BOTH rules at once.
Engagement: a send says "this is you" or "this is us". Nobody sends a friend a
reel about someone's savings running out. Everybody sends one about being
destroyed at seven in the morning.
Realism, which matters more: AN ACCOUNT THAT ONLY POSTS ITS BIG THEME READS AS
A BRAND. Real people post a thing they bought, a thing that broke, a thing that
is funny because it is true. Building her as a thesis rather than a person is
the same failure as a too-perfect photograph, one level up — every individual
frame passes and the ACCOUNT does not.
The career change is the spine and it belongs, once. Around it: a Daiso haul, a
washing machine that finally died, a ₩6,000 iced americano that tasted of
nothing.
COMEDY IS IN THE STRUCTURE AND THE TEXT, NOT THE PICTURE. Contrast, lists,
escalation. Which is why the funniest reel of the four is also the cheapest:
"7am me / 11pm me" is two stills we already own and an overlay.
Order matters too — light first, the heavy one mid-week, so that by the time
anyone sees the serious one they have already seen her be funny. That is what
makes it land instead of reading as a pitch.

## Her phone is a white iPhone 15 Pro — and the bug was that nothing said so
Two week-two shots came back with different handsets. The cause was not model
drift: `character.md`, `profile.md` and `week.md` did not mention the phone
ANYWHERE. The only hit in the whole canon was "the phone was on a stool".
A DETAIL THAT LIVES ONLY IN THE OPERATOR'S HEAD IS NOT CANON. It is a
preference nothing downstream can act on — not the model, not the audit, not a
future session — so it renders differently every time and the fault presents as
drift when it is a missing line in a document.
Two corrections that pull opposite ways, and they must not be merged:
  * AS THE CAMERA the phone is INVISIBLE and must never be described or
    placed. Naming the placement summons it into frame — that is why every
    early hero came back with a phone in it, one in a tripod mount. Unchanged.
  * AS A PROP it is VISIBLE and must be identical every time: a mirror selfie,
    or lying face down on a cafe table. A room owns furniture, an action owns
    props, and she owns ONE phone. `phone=True` appends outside.PHONE.
Also: the LENS blocks said iPhone 16 Pro. The playbook permits naming the
device as a lens spec — "it never summoned one; it is the placement sentence
that does" — so it stays, it just has to be the RIGHT phone. Now 15 Pro.
THE FLAG GATES THE SEND; THE PHRASE SEARCH ONLY NAGS. audit.py warns when a
phone is described in frame without phone=True, but never decides what is sent
— a phrase search must not do that. First run of the check found two more in
the fanvue set that nobody had noticed.

## `--only a, b` in PowerShell is TWO arguments, and it used to run one shot
A space after the comma means `--only` receives "a," and "b" lands on the
positional `scene`. The old code split on commas, matched one id, found a
non-empty list, and generated a single image reporting success. THE OPERATOR
ASKED FOR TWO AND PAID FOR ONE, and nothing said so.
Two fixes, and the second matters more than the first:
  1. --only now splits on commas AND whitespace, and folds a stray positional
     in with a note rather than swallowing it.
  2. EVERY ID MUST EXIST OR NOTHING RUNS. `--only real,typo` previously ran
     the real one and silently dropped the typo. A partial run that looks like
     a whole one is the same failure family as a budget cap that skips
     everything: the tool is confident and wrong.
GENERALISES: when input is ambiguous, refuse. Never take the interpretation
that happens to parse — a request that half-worked is worse than one that
failed, because nobody goes looking for the missing half.

## We were shipping 38 MB of references on every single image
The masters are 5-7 MB each and three or four are attached to every call:
a1 5.3 · a2 7.4 · a3 7.5 · c5 6.3 MB. As base64 that is ~52 MB in the body of
every request. Nobody noticed because it "worked" — it was only slow.
At 2048px on the long edge as JPEG q92 the same frames are 2.7 MB total, ten
times smaller. gpt-image-2 resizes internally regardless, and what a PLATE was
generated at 3840 for is FRAMING — the field of view that contains the room —
which survives a resize completely. Pixel density was never the point.
REASONED, NOT MEASURED. Identity loss is exactly what `drift_gate.py` exists to
catch: run it on the first batch and compare with the 0.911 / 0.904 / 0.909 the
full-size references produced. If it drops, raise REF_MAX_EDGE. Do not assume
it held because the argument was good.

## The 403 was a key SCOPE, and it was also a dependency we did not need
`fal_client` asks rest.fal.ai for a CDN token and got 403 Forbidden — with the
same key that had just generated an image. Valid for inference, not for
storage: a scope on the key.
The fix was not to fight the scope. A `data:` URI carries the bytes inline —
no upload, no auth token, no CDN, no expiry, nothing that can 403. That was the
original design and I removed it because a probe "proved" data URIs were
rejected. THAT PROBE FAILED ON THE STATUS-URL BUG, against `/edit`, and the
conclusion was wrong; removing the simple path was the actual mistake, and the
403 is what a needless dependency costs when it finally fails.
`FAL_FORCE_STORAGE=1` still routes through fal_client for anyone whose key has
the scope. Nothing needs it.

## Seedream is retired and a mechanical constraint is not a reason to unretire it
Reverting to Kie, I put seedream back into FAMILIES and routed the plates
through it, because Kie's gpt TEXT-to-image enum lacks 4:3. The argument was
purely mechanical and I never checked WHY the model was dropped. HANDOFF.md
says it in four words: "pulls editorial" — the exact failure this project
exists to avoid — and the bake-off it supposedly won was scored while
gpt-image-2's references were going to a field it does not read.
AND THE CONSTRAINT DID NOT EVEN APPLY. All four plates were already generated
and on disk, and gpt IMAGE-to-image takes 4:3, 16:9 and 21:9 anyway, so a wide
plate can be seeded from an existing frame of the room. I reached for a retired
tool to solve a problem that did not exist.
Same failure as writing a prompt without reading the canon, one level up: the
retirement WAS the canon and it took four words to check.
`--model seedream` is now not a valid choice, and `MODEL_T2I_SD` — a seedream
fallback for no-face shots — is gone too. No back doors: the no-face path uses
gpt text-to-image so the grid stays one camera.

## A reel is watched for ONE of six reasons. Name it before building. (operator's rule)
The photo-dump slideshow was a MOOD BOARD. Mood boards work for accounts that
already have an audience, because the audience supplies the interest. At zero
followers nothing supplies it — the reel is asking a stranger to care about
someone they have never heard of, for nine seconds, in silence.
The operator's taxonomy, adopted as the design constraint. A reel earns a watch
because it:
    TEACHES / gives new information    "3 things nobody tells you..."
    IS BEAUTIFUL                       a place, golden hour, landscape
    IS RELATABLE                       "this is my life too"
    IS FUNNY                           a small disaster
    SHOWS OFF AN ATTRACTIVE PERSON     outfit, gym fit, transformation
    IS A PRANK OR SKIT                 not buildable here: multi-take, voice
Every reel must do exactly ONE, deliberately, and you have to be able to say
which before it is built. "Here is my week" is none of them.
The teaching one is the most valuable because it gets SAVED, which is the
strongest signal available, and because it makes her an authority rather than
someone you look at. Do not open with it though: an account with no posts
telling you about your hip flexors is a brand.

## Gemini Omni 1.1 Flash is free in Google Flow, which reverses the video plan
Google AI Plus includes it: up to 40 seconds in 10s extensions, 360p/720p/
1080p/4K, first AND last frame keyframing, up to 3 seconds of video as a
reference, native audio.
So EVERY VIDEO ATTEMPT GOES TO FLOW FIRST, because it costs nothing, and paid
video is now the exception that has to justify itself. The trade is that Flow
is a UI, not an API — generate by hand, drop the file into content/reels/. At
zero revenue, free-and-manual beats paid-and-automated every time.
UNTESTED: whether it holds her face from reference images the way H3 does. That
is the single highest-value test available and it costs nothing. If it holds,
the whole video problem is solved for free.

## The repository is an LLM Wiki, and the code is not part of it
Documents live in `wiki/domains/{persona,pipeline,publishing}`, superseded ones
in `wiki/archive/`, decisions append to `wiki/log.md`, `wiki/index.md` is the
catalog, `AGENTS.md` is the entry point. Kebab-case names, relative cross-links.
THE CODE STAYED AT THE ROOT and that is deliberate. Fifty-eight modules import
each other by bare name and every documented command says `python outside.py`.
Moving them into `code/` breaks every import and every instruction the operator
has, to satisfy a convention written for a notes repository. Apply a structure
where it fits and refuse it where it does not.
`CLAUDE.md` also stays at the root because the tooling auto-loads it from there;
`AGENTS.md` is a ten-line POINTER to it, not a second copy.

## ffmpeg drawtext does not wrap, and a clipped line still looks like a line
The first build of R2 drew "it has been making the noise since july" — 38
characters at fontsize 54 on a 1080 frame — straight off the right-hand edge,
losing "...since july". It was visible in the check sheet and I nearly missed
it, because a truncated line reads as a line.
Two fixes. Text is PRE-WRAPPED in the beat list with a hard `MAX_LINE = 30`
check that RAISES rather than warns, so an over-long line cannot be rendered at
all. And drawtext reads from `textfile=` instead of `text=`, so colons,
apostrophes and newlines never have to survive two layers of escaping.
And the check sheet itself was wrong: it sorted extracted frames by a broken
slice, so they were displayed out of order. A VERIFICATION TOOL THAT IS WRONG IS
WORSE THAN NO VERIFICATION TOOL — it produces confidence. Frames are now named
with a zero-padded index so sorting cannot be clever and wrong.

## RELATABLE REQUIRES AN EXISTING RELATIONSHIP. Lead with the person.
I built the washing-machine reel first and the operator's verdict was that
nobody would care and everybody would skip it. Correct, and the reason
generalises further than one reel.
"This is my life too" only lands on somebody who ALREADY LIKES YOU. A stranger
has no reason to care that an appliance broke: there is no joke, nothing
happens, and — the part I missed entirely — SHE IS NOT EVEN IN IT. Relatable is
the LAST category that starts working, not the first.
At zero followers the order is:
    1. HER. In this niche a woman moving in a studio, well lit, is the scarce
       thing a stranger stops for. This is the "shown off" category.
    2. BEAUTIFUL. A place doing something genuinely worth looking at.
    3. TEACHES. Converts a stop into a follow, and gets saved.
    4. relatable / funny — once there is an audience to relate.
And the deeper error, which is the one to watch for: I BUILT THE REEL OUT OF
WHAT I ALREADY HAD RATHER THAN WHAT WOULD WORK. Two stills existed, so the reel
was made of two stills. Assets are not a brief. Decide what should exist, then
find out what it costs.

## Three providers refuse her face. One does not. That is a structural risk.
    Seedance 2.5 reference-to-video   REFUSES  real-person identity references
    Gemini Omni Flash (Google Flow)   REFUSES  "sees her as a real person"
    MiniMax H3 image-to-video         WORKS    conditions on a first frame
The irony is exact: THE THING THAT MAKES THIS PROJECT WORK IS THE THING THAT
TRIPS THE FILTERS. A likeness filter is asking "does this reference depict a
real identifiable person", and the whole point of the master stack is that the
honest answer looks like yes. Better references will make this worse, not
better.
WHAT STILL WORKS, and the split is clean:
  * HER FACE IN MOTION -> H3, first-frame conditioned, on Kie. $0.08/s at 768P,
    so roughly $0.68 for eight seconds. It is the only route.
  * EVERYTHING WITHOUT HER FACE -> Google Flow, free. POV, a place, the studio
    empty, the river, hands out of frame. No person, nothing to identify,
    nothing to refuse. The free tier is not lost, it is scoped.
THE RISK, said once and plainly: providers are tightening likeness policy, not
loosening it. H3 works today and may not in six months, and when it stops there
is no obvious replacement. Anything that depends on generated video OF HER is
built on one supplier with no second source. Video of PLACES has many.
Plan accordingly: keep the account's core value in stills and in places, and
treat her-in-motion as an enhancement rather than a foundation.

## The unchecked category is where the errors live

`audit.py` has run the realism rules over the still pools since early on. It
has never once looked at a video prompt. The video prompts were written by
hand, read by eye, and declared ready — and when a checker was finally pointed
at them it found two violations of rules THE PLAYBOOK ALREADY CONTAINED:
"propped on a bench" (a camera-placement sentence, the thing that put a phone
in frame in every early hero) and "the light goes across her face" (the exact
mechanism behind the glass-skin highlight that took four rounds to find).
Neither was a new mistake. Both were old mistakes made again in a place where
nothing was watching.
The rule is not "write better prompts". It is: WHEN A CLASS OF ARTEFACT HAS NO
MECHANICAL CHECK, ASSUME IT VIOLATES THE RULES, because there is no evidence it
does not. Reading it over is not evidence — I had read this prompt several
times and written that it was ready.

THE SAME HOLE WAS OPEN ON THE STILLS, and I had assumed it was not.
`check_all_pools()` in `audit.py` walked a HARDCODED list of pools, and
`week2_shots` had never been added to it. The eleven shots that were actually
generated, approved and queued to publish were the one pool nothing checked —
which is precisely the "newest prompts are the least examined" failure that
function's own docstring was written to fix, recurring one pool later. It came
up clean when finally run, but that was luck, not process.
A REGISTRY YOU HAVE TO REMEMBER TO UPDATE IS A REGISTRY THAT GOES STALE. The
list is now discovered by globbing `*_shots.py`, so the next pool is audited
because it exists rather than because someone remembered. Any check that needs
a human to enrol its subjects will eventually be checking only the old ones.
The standing debt this exposed, recorded rather than bulk-fixed because a bad
place qualifier is worse than none: 65 prompts predate the NAME THE PLACE rule
— outside 37/54, fanvue 21/21, week 5/6, reel_frames 2/4. Everything ever
GENERATED is clean (grid 0/12, week2 0/11). Fanvue must be fixed before a
single image in that pool is paid for.

## A false positive is a bug in the CHECKER. A false negative is worse.

The first run of `audit_video.py` reported eight issues. Six were the checker's
fault:
  * A 60-CHARACTER LOOKBACK CANNOT FIND "Avoid:". Every prompt here ends with
    one long "Avoid: a, b, c, ..." sentence, and "shallow depth of field" sits
    180 characters into it. The negation test has to scope over the SENTENCE,
    because the sentence is what the negation scopes over.
  * A BARE NEWLINE IS NOT A SENTENCE BREAK. The docs hard-wrap, so "Avoid:" can
    sit two lines above the term it negates. Only whitespace preceded by
    sentence punctuation ends a sentence.
  * NO PERSON IN FRAME MEANS NO SKIN RULES. A POV clip has no face in it.
    Demanding a skin block there is demanding text that competes with pixels.
  * NEVER INVENT THE PARAMETERS. It assumed every prompt found in a doc had two
    references attached, then flagged it for not saying what Image 1 was for.
    A reference count is not knowable from a blockquote, so the rule does not
    run there.
None of those is a reason to edit a prompt, and this is the third time that has
had to be said (hair claws, a phone face down, now these).
THE WORSE HALF: the same run MISSED the light-on-the-face violation, which I
already knew was in there before I wrote a line of the checker. The regex
demanded a hardness adjective in the same sentence as the face, because that is
how the example in my head was worded. The hardness was declared one sentence
earlier, on the room. I wrote the check to match the EXAMPLE rather than the
RULE, and a checker that returns green on a bug you already know about is worse
than no checker, because now the green is evidence.
Every rule in a checker gets a probe with a known answer before the checker is
trusted. `audit_video.py` has eight; they cost nothing and they caught this.

## A doc that says "ready to post" about a killed idea is a stale artefact

`reel-r2-washing-machine.md` was still headed "ready to post" after the concept
was rejected and the mp4 moved to `_to_delete/`. Same failure as reading
`posts.json` instead of `publish/feed`: a file I maintain, asserting a state
the process contradicts. When a thing is killed, the header changes in the same
breath. It is now headed RETIRED, and `audit_video.py` skips retired docs so a
dead prompt cannot become permanent noise that trains me to ignore the report.

## An ordinal is a property of the LIST. Never write one down twice.

`ROLE_PLATE` said "Image 1 is the room". `ROLES_BODY` said "Images 1 and 2 are
her face, Image 3 is her full length". Both were constants. At send time the
plate is PREPENDED to the reference list, so the real order is plate, face,
face, body — and every plated shot therefore shipped a prompt in which Image 1
was the room and her face in the same breath, with the body reference pointed
one slot short. `ROLE_LIMB` had the same fault.
It hit w2_desk_rain, w2_kitchen_sun and w2_broken_machine. They were generated,
they passed QC, and they are NOT being regenerated — they passed, and a
withdrawn judgement must not survive in a file. The model evidently recovered
from the contradiction. That is luck and it is not a reason to keep sending it.
The ordinals are now computed from whether a plate is attached, in one function
next to the code that builds the list. THE GENERAL FORM: the moment a number
describing a list is typed into a string, it is a copy of state that the list
can change without telling you. Derive it or do not write it.
It surfaced only because the fit check was the first shot to want a plate AND a
body reference at once. Two features that each work alone are not a tested
combination.

## H3 speaks, and the audio slot is a TIMBRE reference, not a voice clone

Confirmed against MiniMax's own model card and platform docs, because three
third-party blogs said three different things:
  * H3 outputs NATIVE STEREO AUDIO, 32 kHz, and it LIP-SYNCS. The model card's
    own example: the subject "physically speaks, his mouth movements naturally
    syncing to the new dialogue".
  * `reference_audio_urls`: up to 3 clips, 2-15s each, 15s combined, MPEG/WAV,
    <=15 MB on Kie, addressed in the prompt as "Audio 1" like the images.
  * IT CANNOT BE SENT ALONE. At least one image or video reference must go
    with it.
  * What it does: "Voice timbre follows reference audio 1". TIMBRE MATCHING,
    and the card is explicit it is not strict voice cloning. So it steers a
    voice, it does not reproduce one — which is the right shape anyway, because
    WE CLONE NOBODY. The voice is designed from a text description with no
    source recording (MiniMax Voice Design does this natively; on Kie the same
    job goes to ElevenLabs, which is in the market where Voice Design is not).

FIFTEEN SECONDS IS A HARD CEILING PER GENERATION, and that is the fact that
reshapes any talking reel. Three tips spoken naturally is 25-35s, so a voiced
reel is two or three stitched calls, not one. Jump cuts are native to the
format, but the cost multiplies with them.

THE PER-SECOND PRICE IS NOT CONFIRMED AND MUST NOT BE ASSERTED. `kie_api` says
$0.08/s at 768P plus $0.04 per input image; the H3 documentation the operator
quoted says $0.06/s with the first five references free. Those disagree by a
third on the rate and completely on references. Nobody has run an H3 job yet,
so the honest number is a range until a dashboard deduction settles it — the
same method that fixed the fal model after it was 60% low for a fortnight.
Read the deduction after the FIRST job and write the real figure in.

## device_bash has no network, so generations run in the operator's shell

`outside.py` failed from the device shell with four upload endpoints all
reporting "Max retries exceeded". That looks exactly like a wrong API path and
it is not one: a connectivity probe showed DNS failing and a 403 tunnel refusal
for google.com as well, so it is the sandbox's egress policy blocking
everything. NOTHING IN `kie_upload.py` IS BROKEN and its CANDIDATES list must
not be "fixed".
The general form, and it is the same shape as the audit false positives: WHEN A
FAILURE COULD BE OURS OR THE ENVIRONMENT'S, PROBE THE ENVIRONMENT FIRST. One
call to a known-good host separates the two, and editing working code to chase
an environment fault leaves a real bug behind where a fake one was.

## Development ran on Linux; the operator runs Windows. Externals must be found, not named.

`phone_audio.py` died in PowerShell with a bare `FileNotFoundError: [WinError
2]` out of `subprocess`. The traceback names no file and reads like a bug in
the script. It is not one: Windows could not find `ffprobe`.
EVERY ffmpeg SCRIPT IN THIS PROJECT HAD THE SAME FAULT — eight of them — and
none had shown it, because every one had only ever been run through the device
shell, which is Linux and has both binaries on PATH. A whole class of scripts
was untested on the only machine that actually runs them.
`ffbin.py` now resolves both once: PATH, then winget, scoop, chocolatey, a
hand-unzipped C:\ffmpeg, and the copy inside `imageio-ffmpeg`, which a ComfyUI
install very often already has. A missing binary produces an instruction rather
than a traceback.
AND IT SURVIVES A MISSING ffprobe SPECIFICALLY. ffprobe is the one people end
up without, and every use of it here asks one question — how long is this file
— which `ffmpeg -i` also answers on stderr. So `duration()` falls back to
parsing that, and the dependency disappears rather than being documented.

## A mechanical edit that neuters a guard is worse than the bug it was fixing

Rerouting those eight files, I ran a regex that replaced each longhand ffprobe
call with `None` and each `float(q.stdout.strip() or 0)` with `0.0`. Everything
still imported. Everything still ran. Every duration check now compared against
zero and passed — including the ones that exist to catch a filter graph writing
a 246-second file when 8 was asked for, which is a fault this project has
actually shipped once.
A GUARD THAT ALWAYS PASSES IS INVISIBLE. A crash announces itself; a disabled
check announces nothing and quietly returns the codebase to the state it was in
before the check was written. The repair was nine explicit anchors, one per
site, each with the variable it was actually measuring — which is what should
have been done first, because the pattern was the thing that broke them.
The check that caught it: after any sweep, grep for the REPLACEMENT text and
read every hit. `got = 0.0` is not a plausible line to have written on purpose.

## An id that is a PREFIX of another id silently steals its files

`plate_path()` resolved a generated plate with `glob("<pid>_*_*.png")`. Add a
plate called `plate_studio_wide` next to `plate_studio` and that glob matches
`plate_studio_wide_4e68ba_1.png` for BOTH ids. So `plate_studio` and
`plate_studio_wide` returned the same picture, and re-rendering the wide plate
would have fed it ITSELF as its reference — a room slowly converging on a copy
of a copy, with nothing anywhere reporting an error.
Generated names are always `<id>_<six hex>_<n>.png`, so the hash segment is the
thing that separates them: it is now matched exactly instead of with a
wildcard. THE GENERAL FORM: a wildcard between two known-shaped fields will
eventually swallow a longer sibling. Anchor on the shape you know.

## A number in a prompt is a claim about the world, and gets checked like one

The studio plate said "three reformers" because I typed three. It rendered
three, in a line, in a narrow room, and it read as somebody's spare room rather
than a business. A typical group class is 8-12 people and a mid-size studio
runs 10-12 machines, so three was not a stylistic choice, it was wrong — and it
quietly contradicted the reel's own closing line, "7am tue + thu, seongsu",
which only works if the room can hold a class.
Two other numbers in that same prompt did damage too: "a SMALL pilates studio"
and "seen wide FROM THE DOORWAY". The model obeyed both exactly — door jambs in
each edge, machines nose-to-tail. Every quantity and every viewpoint in a
prompt is an instruction that WILL be followed, so each one is either checked
against how the real thing works or it is a guess being rendered at full
confidence.

## The camera is not an object in the scene, and a denial still names it

The POV skeleton opened: "filmed on an iPhone held in one hand, first-person
point of view. The person holding the phone is not visible and is never in
shot." A phone appeared in frame.
THREE SUMMONS IN TWO SENTENCES — a hand, a phone, a person — and the second
sentence is the worse half, because naming a thing in order to forbid it still
puts the noun in the prompt. That is the same mistake as every negation we have
been caught by, wearing the costume of a safety instruction.
The distinction was ALREADY IN THIS PLAYBOOK and I broke it anyway: naming the
device as a LENS SPEC ("Shot on an iPhone 15 Pro: flat contrast, low
saturation...") has never summoned one, because it describes the picture.
Naming how the device is HELD describes an object in the room.
The rule, stated so it survives paraphrase: DESCRIBE THE VIEWPOINT AND THE
FRAMING ERRORS IT CAUSES, NEVER THE THING CAUSING THEM. "The view never
settles: small constant unevenness, a drift off level, a slight overshoot when
it stops." No hand, no phone, no person, and the same picture.
"handheld" counts. It is a hand named as a noun.
THE ONE EXEMPTION: a mirror shot, where the phone in frame is the format rather
than the failure. `audit_video.py` now has a CAMERA HELD rule with exactly that
exemption, probed against the broken line, the denial, the word "handheld", a
clean lens spec, and an exempt mirror shot.

## Tuning by argument is guessing. Render the grid and listen.

Her voice took three rounds to get right and every round was one exchange
long: the brief said "unhurried, calm, breathy, vocal fry, understated" and it
came back ASLEEP; the fix said "Persona: pilates instructor. Emotion:
energetic. Crisp consonants. Each sentence landing firmly on its last word"
and it came back a YOUTUBE PRESENTER; the fix for that came back ROBOTIC.
Three changes, three failures, three round trips — because each one was a
single number or adjective altered on a hunch and then handed over to be
judged.
`voice_matrix.py` rendered the same sentence NINE WAYS for about 666
characters, a fraction of a cent, and the answer was stability 0.40 — the
middle of the range, which is the one place I had never tried. Sweeping one
axis at a time is what makes the result readable: change two things, get an
improvement, and you have learned nothing about either.
THE TEST FOR WHETHER TO BUILD A GRID: if the next step is "try X and tell me",
and X is one value out of a continuous range, and generating is cheap, then
the grid is cheaper than the conversation. It is cheaper on the FIRST round,
not the third.
And the thing I was most confident about was the thing I did not know:
ElevenLabs documents low stability as expressive and high as consistent, but
never says which end sounds ROBOTIC — and both ends plausibly do, flat at one
end and artefact-ridden at the other. I asserted a direction from half a fact,
three times.
The chosen row is now canon in `make_voice_el.py`, alongside the voice_id: a
setting that changes between reels changes her voice between reels.

## A title card is dead air, and the first payoff has to be the first thing

R1 went out as a silent reel: 118 views, **6 seconds average watch on 23.5s**,
26% retention, and zero on everything else. Caption one ran 0.3s to 6.5s. The
average viewer left at the exact moment the first tip was about to appear —
they waited six seconds and got a title.
The card said "3 things before your first reformer class", which is a CATEGORY
LABEL. The thing that stops a scroll is the counterintuitive CLAIM: "fewer
springs is harder, not easier". The hook is the payoff, not the promise of one.
WHY IT PASSED REVIEW: on the VOICED cut the hook is spoken while the picture
moves, so the title costs nothing. Stripping the voice out turned a free
opening into six seconds of silence, and `silent()` spread the captions "by
reading time", which handed the longest slot to the shortest, least informative
card in the reel. A layout that is correct with audio is not correct without
it.
The list promise is still worth having — it tells a viewer there are two more
and roughly when they end — so the count now lives INSIDE the first tip card
("1 of 3") and costs nothing.
AND THE RESULT SAYS NOTHING ABOUT THE CONTENT. At 26% retention almost nobody
reached the tips, so zero saves is not evidence the tips are bad. A metric can
only judge what was actually seen.

## You cannot prompt naturalness by asking for imperfection

The voice brief said "relaxed and slightly uneven — some words run together,
some trail off, small pauses in the middle of sentences." It came back
ROBOTIC, along with an accent that was not Korean.
A TTS told to be uneven produces ARTEFACTS, and artefacts are exactly what
robotic sounds like. Imperfection in a rendered voice is not the same substance
as imperfection in a human one: a person's unevenness is the residue of
thinking, and a model's is a defect. Naturalness comes from a good base voice
at moderate settings, and the unevenness has to live in the WRITING — "okay",
"so", "oh, and", contractions, short sentences — where it is a property of the
script rather than a request to the renderer.
THE SAME SHAPE AS THE SKIN RULE. "Do not make it glossy" is a losing sentence;
"visible pores, uneven tone" is a winning one. Describe the thing you want to
exist, never the quality you want it to have.
And the bigger correction underneath it: a DESIGNED voice is synthesised from a
description, a LIBRARY voice is a real human recording. For accent authenticity
that is not a close call, and "unique" was the wrong thing to optimise — a
voice nobody else has that does not sound like a person is worth less than a
shared one that does.

## She can describe her life. She cannot make an offer a viewer could act on.

The reel closed on "seven in the morning, Tuesdays and Thursdays, Seongsu" and
I had written it three times without noticing what it was: an invitation to a
class that does not exist, from a person who does not exist, to a real place.
It reached FOUR files before the operator asked what it was.
The line between the account working and the account writing cheques it cannot
cash: "the 7am slot is the one nobody wants" is a story about her. "7am
Tuesdays and Thursdays, Seongsu" is an APPOINTMENT. The first is the whole
point of the persona; the second creates a commitment that gets harder to dodge
as the account grows, and the first DM asking "which studio?" leaves only bad
answers.
IT IS A TEACHING-REEL TEMPTATION SPECIFICALLY, because the natural ending for
real instructor content is come to my class, and that ending is not available
here. The replacement is warmth, not an offer: "honestly, you'll be fine".
Applies to everything downstream — no bookings, no discount codes, no meet-ups,
no address, no class times, and nothing on Fanvue that promises a real-world
interaction.
