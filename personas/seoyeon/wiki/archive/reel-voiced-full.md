> **ARCHIVED — 31 Aug 2026.** Superseded by reel-r1-voiceover.md. All four segments as lip-synced H3 clips.
> Kept for the reasoning, not as a plan.

# The voiced reel — all four H3 segments

Four generations, one per line of the script. **Everything except one sentence
is identical across all four**, deliberately: cuts between identical framings
read as jump cuts, which is what a talking reel natively looks like — it is
what people already do to cut their own pauses out. Four *different* shots
would read as four clips stitched together.

So paste the block once and swap only the DIALOGUE sentence.

| seg | duration | audio |
|---|---|---|
| hook | ~4s | `voice/hook.mp3` |
| tip1 | ~9s | `voice/tip1.mp3` |
| tip2 | ~8s | `voice/tip2.mp3` |
| tip3 | ~7s | `voice/tip3.mp3` |

Total ~27s. That is long for a reel, and a talking human sustains attention far
better than stills with text do, which is why it is allowed here at all. If the
Trial Reel shows people leaving early, **cut tip3** — it is the weakest of the
three and the reel still works as "two things".

---

## References, every segment

| slot | file | job |
|---|---|---|
| **Image 1** | `master/a/a1_front.png` | her face, front |
| **Image 2** | `master/a/a2_tq_left.png` | her face, three-quarter |
| **Audio 1** | the segment's own mp3 | the voice to match |

`c5` stays out. It is the body and tattoo reference and this is a chest-up
frame where neither is visible; a reference with nothing to do is averaged in.

**After segment 1 comes back good, add its best frame as Image 3 for segments
2–4**, with this job line appended to the reference paragraph:

> Image 3 is the same woman in the same room — match her clothes, her hair and
> the light in it exactly.

Four independent generations will drift on wardrobe and hair, and that drift is
the thing that turns jump cuts back into four different clips. Chaining a frame
forward is what holds them together.

---

## POSITIVE — identical except the one marked line

```
Vertical phone video, 9:16, filmed on an iPhone front camera held at arm's
length: flat contrast, low saturation, visible sensor noise in the shadows, no
colour grade and no cinematic look.

Image 1 and Image 2 are the same woman's face from two angles — use them as a
strict identity reference for her features and the pale freckles across her
nose and inner cheeks. Match the voice in Audio 1.

A Korean woman in her mid twenties, framed from the chest up, filling most of
the frame. Black sports bra, hair in a low bun coming loose at the sides. Her
skin is matte from brow to jaw and reads slightly dry: visible pores, uneven
tone, the only sheen a faint one along the nose, and it does not smooth or
brighten at any point.

She is in a pilates studio in Seongsu, Seoul — reformer frames and a mirrored
wall out of focus behind her, cool daylight from a high window, flat.

She looks straight into the lens and says: <<< DIALOGUE >>>

The framing does not change. The only camera motion is the small tremor of a
phone held in one hand.
```

### The four DIALOGUE lines

**hook** — set duration ~4s
```
"Three things I tell everyone in their first reformer class." She speaks at a
normal conversational pace, with small natural head movement and one blink, and
her eyebrows lift very slightly on "three".
```

**tip1** — ~9s
```
"Fewer springs is usually harder, not easier. Less spring means less help
holding the carriage, so you do more of the work." She speaks at a normal
conversational pace and gives one small shake of the head on "not easier".
```

**tip2** — ~8s
```
"If the carriage bangs when it comes back, you are going too fast. Control the
return. You want it silent." She speaks at a normal conversational pace and
leans in very slightly on "control the return", then settles back.
```

**tip3** — ~7s
```
"And grip socks are not optional. Most studios will not let you on the
reformer without them." She speaks at a normal conversational pace with a
small shrug of one shoulder on "not optional".
```

Each performance beat is **physical and anchored to a word**. That is the fix
for floaty motion: a model given "she talks" invents continuous drift, and a
model given "the head shakes once, here" has something to land on. They are all
head, face and shoulder — **no hand gestures**, because one hand is holding the
phone and the other is the fastest route to six fingers.

## NEGATIVE — identical for all four

```
zoom, zooming in, push in, dolly, tracking shot, pan, tilt, orbit, camera
movement, gimbal, slow motion, morphing, warping, melting, mouth out of sync,
teeth changing shape, jaw detaching, limbs changing length, extra fingers,
extra hands, face changing between frames, face smoothing, skin smoothing,
glossy skin, wet skin, oily skin, plastic skin, airbrushed, beauty filter,
shallow depth of field, bokeh, heavy background blur, colour grading, film
grain, lens flare, second person, another face in the mirror, cut, jump cut,
black frame, subtitles, text, watermark, logo
```

---

## Order of work

```
1  make_voice_el.py --all              -> voice/hook,tip1,tip2,tip3.mp3
2  generate HOOK only                  4 seconds answers everything
3  QC it (list below)                  stop here if it fails
4  pull a good frame from it           -> Image 3 for the rest
5  generate tip1, tip2, tip3
6  concatenate in order
7  burn captions                       NOT optional — the feed is muted
8  Trial Reel
```

Do not generate all four before checking the first. Every failure this can have
is visible in the hook.

## QC, in this order

1. **The words.** Did she say the line, or a paraphrase? H3 takes the words
   from the PROMPT and only the timbre from the audio, so drift here is the
   most likely failure of the whole approach.
2. **The first half-second of speech**, at quarter speed. Lip-sync failures
   live there and nowhere else.
3. **The teeth.** They change shape between frames long before the lips do.
4. **Wardrobe and hair against segment 1**, once you have more than one.

## If your H3 node has no audio input

Keep the dialogue lines in — the mouth still has to make those shapes — but
drop the sentence `Match the voice in Audio 1`, because a reference that is not
attached must not be given a job. Then lip-sync each mp3 onto its clip with a
separate node.

That route is better in one specific way: the audio becomes your exact
ElevenLabs take instead of H3's re-performance, so **the words cannot drift** —
which removes QC item 1 entirely.
