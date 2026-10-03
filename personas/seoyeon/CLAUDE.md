# Seo-yeon — operative context

**This file is the layer that is always loaded. `wiki/domains/pipeline/playbook.md` is the reasoning
behind every line of it and is NOT loaded by default — read the one section you
need, when a rule is in question or about to be changed.**

Read a PLAYBOOK section before you: change a rule, argue with a rule, or write
a prompt in an area you have not touched this session. The index at the bottom
is the map. Section numbers below match `## ` heading order in wiki/domains/pipeline/playbook.md, so
`grep -n "^## " wiki/domains/pipeline/playbook.md` gets you there.

Every rule in the index was paid for with a failed generation. None of it is
arbitrary, and none of it is style preference. When a rule looks wrong, read
its section before overriding it — the reason is usually a specific image that
came back broken.

---

## Scope of this file — READ THIS FIRST

**This file owns the gpt-image-2 / tier-1 path and the prompt rules. It does
not own the persona, the platforms, or the Kie/Seedream stack.**

A block used to sit here declaring Seedream 5 Pro the "primary generator" —
directly above the paragraph, still below, explaining that Seedream only ever
won a bake-off because references were being sent to a field gpt-image-2 does
not read. Both statements were in the always-loaded context file and a reader
could not tell which to follow. It has been removed; the real answer is that
there are TWO stacks and they are split by content tier.

| you want | read |
|---|---|
| who she is | `/CANON.md` |
| which rules apply on which platform | `/PLATFORMS.md` |
| which generator for which job | `/PIPELINES.md` |
| the commands | `/growth/RUNBOOK.md` |
| your job's reading list | `/roles/` |

Short version: **everything runs on Kie. gpt-image-2 for tier 1 (SFW,
Instagram); Seedream 5 Pro for tiers 2 and 3 (Bluesky, Fanvue) — not because
it is better, but because gpt-image-2 refuses that content. fal.ai is
deprecated.**

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

## Verified API facts (fal.ai) — ⚠ RETIRED, KEPT FOR THE REASONING

**fal.ai is deprecated. Everything runs on Kie.** `fal_api.py` no longer
exists; `outside.py` imports `kie_api`. This table is kept because the lesson
in its reference-field row outlived the provider — see `/PIPELINES.md` §1 for
the live contract. Do not take an endpoint id or a price from here.

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

## NO MEN. Anywhere. Ever.
Not in frame, not in a caption, not named, not implied, not a hand at the edge
of a photo, not the person who took it, not a "someone". No boyfriend, no ex,
no male classmate, colleague or brother. Applies to comment replies too.
The account converts on the viewer believing there is room for him. A man
anywhere in her life closes that door, and it does not reopen once a name has
been said. Every person in the cast is a woman.

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

## HER PHONE IS A WHITE iPHONE 15 PRO (already canon, in outside.py)

It is visible in every mirror selfie, every arm's-length selfie and every flat
lay, and a phone that changes colour between posts is the same continuity
break as a flat that changes rooms.

IT IS ALREADY HANDLED. `outside.py` carries a shared `PHONE` block that every
assembled prompt picks up, and it has said "a white iPhone 15 Pro with a plain
clear case, slightly scuffed at one corner" since 30 Aug. An earlier version of
this section claimed the phone could not live in a shared block and would have
to be written into 22 shots by hand, at about $2 of re-renders. That was WRONG
and it was written without reading outside.py past the shot list.

WHAT ACTUALLY PRODUCED A BLACK PHONE on 4 Sep was publishing a STALE RENDER:
`w2_studio_mirror_4487c7` predates the current prompt, `_1b34a6` matches it.
The staleness gate in `ig_publish.py` caught it; the human recommending the
file did not. **When a render disagrees with canon, suspect the render's age
before rewriting the canon.**

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


---

# The index — 149 rules, all of them in wiki/domains/pipeline/playbook.md

Each line is the rule. Read the section for why, and for the failure that
produced it. `grep -n "^## " wiki/domains/pipeline/playbook.md` to jump.

  1. The one rule everything else follows from  ·
  2. Prompting
  3. Markers
  4. What makes an image read as AI
  5. Continuity
  6. Verified API facts (fal.ai)  ·
  7. Models in use  ·
  8. Drift gate  ·
  9. Files  ·
 10. Working style that has helped
 11. Rooms: describe them, don't attach them
 12. Rooms: edit one hero, never regenerate
 13. The camera sits on furniture, not on a tripod
 14. Never name the camera device
 15. A room owns furniture, an action owns props
 16. Audit before you spend
 17. Rooms: used, not worn
 18. Roughly 1 in 4 posts has no person in it
 19. Vary per room, never with a shared extras list
 20. The character bible is a decision document, not prompt text
 21. Age is 26, fixed by the identity block
 22. A session edit needs the face reference too, not just the hero
 23. Never ask for legible text — Korean especially
 24. The face reference must match the frame's angle
 25. Two face references per edit: front plus a second angle
 26. Tool routing: EDITOR vs RENDERER, chosen per frame
 27. Outside is the majority of the feed
 28. audit.py now covers outside.py too
 29. Wardrobe: pieces that recombine, not fixed outfits
 30. Check DISTRIBUTION, not just individual prompts
 31. English only, romanised Korean nouns
 32. Faces drift on wide shots because of PIXELS, not references
 33. The arm's-length front selfie is the default outdoors
 34. Fill the walls — a place can invite text without naming it
 35. Text: name the surface, never the signage
 36. A selfie occupies one hand
 37. Three paragraphs, not eight blocks
 38. What real fitness/lifestyle grids do that we were not
 39. Positioning: not a gym influencer
 40. Vertical, warm, seasonal — and overlay text instead of generating it
 41. Write every prompt separately. Do not compose them from fields.
 42. Three failure modes from the first summer batch
 43. Naming an emotion produces a performance of it
 44. In a selfie the free hand must stay at her body
 45. Export at 3:4, not 4:5 — the grid changed
 46. "1k" is one MEGAPIXEL, not 1080 wide
 47. Video: condition on a frame, not on references
 48. One clip per call. Multi-shot is a false economy.
 49. Resolution tiers lie in video too
 50. A phrase search must never decide whether a whole instruction is sent
 51. Floaty motion is under-specified motion
 52. The camera lock must match the camera in the frame
 53. I can see the generated images now — `cat >` breaks the hardlink
 54. A clip that mirrors needs landmarks, not a prohibition
 55. Never write an anchor for a frame you have not looked at
 56. Hashtags: the quote still stands, but there is now a HARD CAP OF 5
 57. "Catalogue / studio-like" is four specific things, not a vibe
 58. A clean hero contaminates every frame edited out of it
 59. A third-person frame needs an owner, and must stay rare
 60. Every picture is a story, and everything in it is a consequence
 61. `week.md` — her life is the source, not a content calendar
 62. NO MEN. Anywhere. Ever.  ·
 63. A day has slots, not one event
 64. The premise must justify the CAMERA, not just the scene
 65. Name light that is INCONVENIENT, not merely directional
 66. Propped means POSED. Selfie means IMPULSE. (operator's rule)
 67. ALWAYS DOUBLE CHECK WHAT YOU HAVE (operator's rule, absolute)  ·
 68. Nobody photographs what they do not want seen (operator's rule)
 69. Amateur is in the CAMERA, not in the subject
 70. A selfie can only contain what fits at arm's length
 71. Do not aim limbs at a wide lens from close range
 72. BAD LIGHT + POSITIVE MOTIVE. That is the combination.
 73. Overexposure is not the glass-skin tell — do not confuse them
 74. The highlight was never the SKIN block. It was the LIGHT I kept asking for.
 75. If the HAND is in frame, the model puts a phone in it
 76. Background blur is the biggest single AI tell in a selfie
 77. SUPERSEDED — Qwen3 is NOT the renderer. See "gpt-image-2 is the renderer" below. Kept only because the reasoning error is the lesson.
 78. gpt-image-2 i2i reads `input_urls`, not `image_urls`
 79. SAY ONLY THE DELTA (the most important prompting rule in this file)  ·
 80. gpt-image-2 IS THE RENDERER. The first test that said otherwise was broken. (This supersedes the Qwen3 entry above. It is also the entry the "Models in use" table at the top now reflects.)
 81. Expressions come from TEXT, not from reference frames
 82. Read the canon before writing the prompt
 83. The tattoo anchor itself was bad, which is why it never rendered
 84. NEVER NAME THE PHOTOGRAPHER — they will appear in the frame
 85. A friend's photo is taken from a chair, not from a tripod
 86. You cannot photograph yourself doing something involuntary
 87. A no-face shot with a LIMB in it still needs a reference
 88. Five selfies in twelve is one photograph taken five times
 89. NAME THE PLACE, never the category (operator's rule)  ·
 90. "Everything sharp" is a DAYLIGHT rule. At night it manufactures a studio
 91. Never name a colour for the sky. Name the lights that are in the picture
 92. "Posed deliberately, chin lifted, small closed smile, looking straight at the camera" is a direction you give a MODEL, and you get a model
 93. A limb shot inherits the reference's WARDROBE, not just its proportions
 94. console.py — the local control panel, and the one rule that keeps it honest
 95. Room plates: gpt-image-2 CANNOT generate one at 16:9 or 21:9
 96. First frame TO LAST FRAME is interpolation, not motion
 97. A Reel does not have to be generated video
 98. ffmpeg zoompan emits `d` frames FOR EVERY INPUT FRAME
 99. Custom pixel sizes kill the 16:9 room-plate blocker
100. An unused import is still a dependency
101. A comment is legal before `from __future__`. A docstring is not.
102. A zero price does not make a run free. It disables the budget cap.
103. The "everything sharp" rule is about LIGHT, not the clock
104. A file I maintain is not evidence. The artefact the process emitted is.
105. The repost calculation inverts at zero followers
106. A rewritten prompt does not oblige a re-render, and a withdrawn judgement must not survive in a file
107. If she is not in frame, the identity problem does not exist (operator's idea)
108. A POV clip needs an owner too, and "filming her own class" has none
109. A first-person camera in a mirrored room photographs the person holding it
110. Seedance and H3 disagree on all three reference fields
111. Once the long edge is capped, a wider aspect buys nothing
112. A precondition checked during the work is not a precondition
113. A chronological photo dump is not a Reel
114. The REST contract a vendor does not publish: use their client, not a mirror
115. A plate earns its cost only if the place RECURS and a viewer would NOTICE
116. Suggested commands must be RUNNABLE, not templated
117. Cost is per PIXEL here, so one "price per image" is wrong by 6x
118. "2k is the minimum publishable tier" does not survive the provider change
119. fal vs Kie: the size choice and the provider choice are the SAME decision
120. Use the URLs the API RETURNS. Deriving them breaks on sub-path models
121. The same error string in two places is ONE bug until proven otherwise
122. A guard that refuses everything looks exactly like a guard working
123. At most ONE "meaning" reel a week. The rest is life. (operator's rule)
124. Her phone is a white iPhone 15 Pro — and the bug was that nothing said so
125. `--only a, b` in PowerShell is TWO arguments, and it used to run one shot
126. We were shipping 38 MB of references on every single image
127. The 403 was a key SCOPE, and it was also a dependency we did not need
128. Seedream is retired and a mechanical constraint is not a reason to unretire it
129. A reel is watched for ONE of six reasons. Name it before building. (operator's rule)
130. Gemini Omni 1.1 Flash is free in Google Flow, which reverses the video plan
131. The repository is an LLM Wiki, and the code is not part of it
132. ffmpeg drawtext does not wrap, and a clipped line still looks like a line
133. RELATABLE REQUIRES AN EXISTING RELATIONSHIP. Lead with the person.
134. Three providers refuse her face. One does not. That is a structural risk.
135. The unchecked category is where the errors live
136. A false positive is a bug in the CHECKER. A false negative is worse.
137. A doc that says "ready to post" about a killed idea is a stale artefact
138. An ordinal is a property of the LIST. Never write one down twice.
139. H3 speaks, and the audio slot is a TIMBRE reference, not a voice clone
140. device_bash has no network, so generations run in the operator's shell
141. Development ran on Linux; the operator runs Windows. Find externals, do not name them.
142. A mechanical edit that neuters a guard is worse than the bug it was fixing
143. An id that is a PREFIX of another id silently steals its files
144. A number in a prompt is a claim about the world, and gets checked like one
145. The camera is not an object in the scene, and a denial still names it
146. Tuning by argument is guessing. Render the grid and listen.
147. A title card is dead air, and the first payoff has to be the first thing
148. You cannot prompt naturalness by asking for imperfection
149. She can describe her life. She cannot make an offer a viewer could act on.

`·` = the full section is also kept above, in this file.


---

# When to read the long version

- **About to change a rule** — read it first, always. Twice this project has
  had a "stale" line corrected that turned out to be describing live code.
- **A prompt area you have not touched this session** — the rules interact.
  Skin, light and background blur are three sections that only make sense
  together.
- **A model behaved unexpectedly** — check whether the rule you are relying on
  was learned on a different model. It usually was. Rules do not transfer
  between models; this file has been caught by that three times.
- **Anything about video** — sections 47 to 55. Video has its own physics and
  the stills rules mostly do not apply.

# When NOT to read it

Routine work inside rules you already have in front of you. That is the entire
point of the split.
