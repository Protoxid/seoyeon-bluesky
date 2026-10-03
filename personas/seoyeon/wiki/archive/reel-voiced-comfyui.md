> **ARCHIVED — 31 Aug 2026.** Superseded by reel-r1-voiceover.md. The lip-sync build, before the structure moved to voice-over.
> Kept for the reasoning, not as a plan.

# The voiced clip — H3 ref2v in ComfyUI

## Test with the hook. It is 3.8 seconds and it answers everything.

The hook is the right test precisely because it is short: it is one sentence,
so if the mouth is wrong you see it immediately, and if the voice is wrong you
hear it in four seconds instead of thirty.

```
1  python make_voice_el.py --dry-run --all        free, check the script
2  python make_voice_el.py --only hook            -> voice/hook.mp3, ~4s
3  LISTEN. Judge the accent before anything else.
4  H3 ref2v in ComfyUI, prompts below             -> a ~5s talking clip
5  Watch the mouth at QUARTER SPEED.
```

Both key files are already in place — `elevenlabs_key.txt` and `voice_id.txt`
are exactly the names the script looks for, so no flags are needed.

**No new still is required.** ref2v conditions on references, not on a first
frame, so her face masters carry identity and the framing is described in
words. That removes a whole step from the earlier plan.

---

## References

| slot | file | job |
|---|---|---|
| **Image 1** | `master/a/a1_front.png` | her face, front |
| **Image 2** | `master/a/a2_tq_left.png` | her face, three-quarter |
| **Audio 1** | `voice/hook.mp3` | the voice to match |

`c5` is deliberately absent. It is the body and tattoo reference, and this is a
chest-up frame where neither is visible — an attached reference with nothing to
do is paid for and averaged in.

---

## POSITIVE

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

She looks straight into the lens and says: "Three things I tell everyone in
their first reformer class." She speaks at a normal conversational pace, with
small natural head movement and one blink, and her eyebrows lift very slightly
on "three".

The framing does not change. The only camera motion is the small tremor of a
phone held in one hand.
```

## NEGATIVE

```
zoom, zooming in, push in, dolly, tracking shot, pan, tilt, orbit, camera
movement, gimbal, slow motion, morphing, warping, melting, mouth out of sync,
teeth changing shape, jaw detaching, limbs changing length, extra fingers, face
changing between frames, face smoothing, skin smoothing, glossy skin, wet skin,
oily skin, plastic skin, airbrushed, beauty filter, shallow depth of field,
bokeh, heavy background blur, colour grading, film grain, lens flare, second
person, another face in the mirror, cut, jump cut, black frame, subtitles,
text, watermark, logo
```

---

## What is doing what, and why

**`Match the voice in Audio 1` is the documented convention** — the H3 guide's
own phrasing. Give every reference a stated job or it gets averaged in.

**The line is embedded, not tagged.** H3 has no dialogue block. Its guide puts
speech inside the description: *"The character says: '...'"*. So the sentence
sits in the prose exactly as written above.

**The words come from the PROMPT, not from the mp3.** The audio slot supplies
timbre only. If the returned clip says something other than the line above,
that is the model paraphrasing, and it is the single most likely failure —
check the words before you check the mouth.

**Camera words live only in NEGATIVE.** In a positive prompt, naming a thing
summons it: "no zoom" is how the Kie i2v attempt ended up zooming. If the
workflow exposes a motion or CFG-motion control, lower it as well.

**One deliberate exception to a standing rule.** Everywhere else we forbid
background blur, because bokeh is the loudest AI tell. Here the background is
*out of focus behind her* on purpose — a front camera at arm's length genuinely
does that, and a chest-up frame with a razor-sharp studio behind it looks
composited. `heavy background blur` stays in the negative to keep it honest.

---

## If your H3 node has no audio input

Plenty of ComfyUI wrappers expose only the video path. Then:

1. Run the same POSITIVE with the dialogue line **kept in** — the mouth still
   needs to be making those shapes — and no Audio 1 reference. Drop the
   `Match the voice in Audio 1` sentence, since a reference that is not
   attached must not be given a job.
2. Lip-sync `voice/hook.mp3` onto the result with a separate node.

That route is strictly better in one way: the audio becomes your exact
ElevenLabs take rather than H3's re-performance, so the words cannot drift.

---

## What to check on the returned clip, in this order

1. **The words.** Did she say the line, or a paraphrase of it?
2. **The first half-second of speech**, at quarter speed. Every lip-sync
   failure lives there.
3. **The teeth.** They are the tell — they change shape between frames long
   before the lips do.
4. **The accent**, if H3 generated the audio rather than you supplying it.
