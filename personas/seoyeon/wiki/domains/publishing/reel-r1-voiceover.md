# R1 voiced — voice-over, not lip-sync

Her voice runs across the whole reel. Only clip 1 shows her, and **she is not
speaking in it**. Everything after is the studio.

This removes the hardest problem in the build. Lip-sync was the thing most
likely to scream AI, and now nothing has to sync: the mouth is never making
word shapes, so it can never make the wrong ones. It also means clips 2–4 have
no face in them at all, which means no provider can refuse them and no identity
can drift.

| clip | shows | audio |
|---|---|---|
| 1 | her, front camera, **silent** | hook |
| 2 | POV: the spring bar | tip1 |
| 3 | POV: the carriage | tip2 |
| 4 | POV: grip socks by the door | tip3 |

---

## Step 0 — the studio plate, through gpt-image-2 like everything else

**`locations/studio.png` was a domestic living room with one reformer in it.**
Rug, framed print, radiator, curtains. Every POV clip below references the
studio, so building on that file gives a reel that says "studio" over footage
of a flat. It is now parked in `locations/_superseded/` so it can no longer
shadow the real plate — `plate_path()` checks `locations/` first, so leaving it
there would have silently won.

`plate_studio` is now a real entry in `pov.PLATES` and runs the normal path:

```powershell
python outside.py --plates --only plate_studio --dry-run    # free
python outside.py --plates --only plate_studio              # $0.09
```

**1:1 at tier 2k, and the reason is not cosmetic.** The other four plates were
made on fal, where `4:3` and tier `"max"` were both legal. On Kie a plate
carries no reference images, so it routes to gpt-image-2 **text-to-image**,
whose ratio enum is only `1:1, 3:4, 2:3, 9:16` — `4:3` would have been rejected
at the API after paying for the round trip. Of those four, 1:1 is the only one
that is not portrait, so it is the widest frame available for a room that has
to be seen wide. `"max"` is a fal tier with no meaning here.

That mistake was in this file until the enum was actually checked, and it got
that far because **the audit had never looked at `pov.PLATES`** — the same hole
that let week2 go unchecked. Both are closed now, and the four already-generated
plates are marked so they are not flagged forever for having been legal
somewhere else.

The mirrored wall stays in the plate. A pilates studio has one and
`w2_class_two` already shows it; it is a constraint on the POV shots, not a
reason to build a studio without mirrors.

## Clip 1 — her, silent, ~4s

References: **Image 1** `master/a/a1_front.png`, **Image 2**
`master/a/a2_tq_left.png`. No audio reference — nothing here needs to match a
voice, because nothing here makes a sound.

### POSITIVE
```
Vertical phone video, 9:16, filmed on an iPhone front camera held at arm's
length: flat contrast, low saturation, visible sensor noise in the shadows, no
colour grade and no cinematic look.

Image 1 and Image 2 are the same woman's face from two angles — use them as a
strict identity reference for her features and the pale freckles across her
nose and inner cheeks.

A Korean woman in her mid twenties, framed from the chest up, filling most of
the frame. Black sports bra, hair in a low bun coming loose at the sides. Her
skin is matte from brow to jaw and reads slightly dry: visible pores, uneven
tone, the only sheen a faint one along the nose, and it does not smooth or
brighten at any point.

She is in a pilates studio in Seongsu, Seoul — reformer frames and a window out
of focus behind her, cool daylight, flat.

She is not speaking. Her mouth stays closed the whole time. She looks into the
lens with a small closed-mouth smile, glances off to one side and back, raises
one eyebrow very slightly, and blinks twice.

The framing does not change. There is only a small constant tremor, the kind
an outstretched arm makes.
```

### NEGATIVE
```
talking, speaking, mouth opening, mouth moving, lip movement, teeth showing,
laughing, zoom, zooming in, push in, dolly, pan, tilt, orbit, camera movement,
gimbal, slow motion, morphing, warping, limbs changing length, extra fingers,
face changing between frames, face smoothing, skin smoothing, glossy skin, wet
skin, oily skin, plastic skin, airbrushed, beauty filter, shallow depth of
field, bokeh, heavy background blur, colour grading, film grain, lens flare,
second person, another face in the mirror, cut, jump cut, black frame,
subtitles, text, watermark, logo
```

**Every word for speech is in the negative and repeated in the positive as a
statement.** A mouth that moves out of time with a voice-over is worse than no
mouth movement at all — it reads as badly dubbed, which is a louder tell than
simply not seeing her speak. A closed-mouth smile is also the safest possible
expression: no teeth, and teeth are the first thing to deform.

---

## Clips 2–4 — POV of the studio

References for all three: **Image 1** =
`content/plates/plate_studio_wide_4e68ba_1.png`.
No face anywhere, so no identity problem and no refusal risk.

The plate is a WIDE view and the three shots below are close ones. That is
fine and intended: a reference supplies the room's content — floor, machines,
mirror, light — not the framing. The framing comes from the shot line.

Each shot illustrates the line running over it. That is the whole reason this
structure works — it is not filler behind a voice, it is the thing being
described.

### Shared POSITIVE skeleton
```
Vertical phone video, 9:16. Shot on an iPhone 15 Pro: flat contrast, low
saturation, everything sharp front to back, visible sensor noise in the
shadows, no colour grade and no cinematic look.

Image 1 is the room. Keep its floor, its light, its machines and its mirrored
wall exactly: it is the same studio, not a similar one.

An empty pilates studio in Seongsu, Seoul, early morning, before anyone else
arrives. Nobody is in the room and nobody enters it.

<<< SHOT >>>

The view is at about chest height and never settles: small constant
unevenness, a drift off level, a slight overshoot when it stops. Never smooth,
never locked off.
```

### The three SHOT lines

**Clip 2 · over tip1, "fewer springs is harder"**
```
The camera is low, close to the underside of a reformer, and moves slowly along
the spring bar so the coloured springs pass through frame one after another,
then stops on the last one.
```

**Clip 3 · over tip2, "control the return, you want it silent"**
```
The camera looks down the length of a reformer from the foot end. The carriage
rolls slowly away along its tracks, slows, and comes to rest against the stop
without bouncing. The camera stays where it is and only the carriage moves.
```

**Clip 4 · over tip3, "grip socks are not optional"**
```
The camera looks down at the low wooden bench along the wall, where a folded
pair of grip socks sits next to a rolled mat, holds on them, then tips up
slightly to take in the room beyond.
```

### NEGATIVE for all three
```
any person, person appearing, figure, hand, hands, arm, arms entering frame,
phone, smartphone, mobile phone, camera in shot, selfie stick, any
reflection of a person, reflection in a mirror, someone in the mirrored wall,
smooth gimbal motion, tripod, slow motion, zoom, push in, morphing, warping,
colour grading, film grain, lens flare, shallow depth of field, heavy
background blur, black frame, cut, jump cut, text, watermark, logo
```

**THE CAMERA IS NOT AN OBJECT IN THE SCENE.** The first version of this
skeleton opened *"filmed on an iPhone held in one hand, first-person point of
view. The person holding the phone is not visible and is never in shot"* — and
a phone appeared in frame. Three separate summons in two sentences: a hand, a
phone, and a person. The denial is the worse half, because naming a thing in
order to forbid it still names it. Naming the device as a **lens spec** has
never done this; naming how it is *held* always does. So the opening is a lens
spec, the motion is described by its shape, and `phone`, `hand`, `arm` and
`person` live only in the negative.

**The mirrored wall is the second trap.** A pilates studio has one, and a first-person
camera in a mirrored room photographs the person holding it — we have hit this
before. So the shots above all point at equipment and floor, away from the
mirror, and reflections are negated three different ways. If a person appears
in glass anywhere, that is the cause.

---

## Audio, per clip

The reverb default is fixed — the first pass used a 0.34s bright tail at wet
3.0, which is a tiled bathroom. `studio` is now the default: a 0.16s dull tail
at wet 1.0.

```
python phone_audio.py --audio voice\hook.mp3 --under clips\c1_raw.mp4 ^
                      --mux clips\c1_raw.mp4 --out clips\c1.mp4
```

* `--delay` exists but you should not need it. It was written for a lost
  pause; the real complaint was the voice sitting out of sync with the mouth,
  and **with voice-over there is no mouth to be out of sync with**. Reach for
  it only if you actively want a beat of room tone before she starts.
* `--preset dry|studio|room|hall` if `studio` is still not right. Go **down**
  before you go up.
* `--no-normalize` if the pause still fills with noise. Loudnorm gains by
  *integrated* loudness, so a take with a long pause gets more gain and the
  silence stops sounding like silence.
* On clips 2–4 you can raise `--bed-lp` to 4000 or so. That crush exists to
  stop H3's own generated speech leaking under her voice, and **these clips
  have no speech in them** — so their room tone can come through properly,
  which is the best-matching bed available.

---

## Assemble

```
concatenate c1..c4 in order
python make_reel_text.py --video <joined> --out clips\r1_voiced.mp4 --fit
```

Captions are still not optional. Most of the feed is watched muted and this
reel's entire value is the words.

## QC

1. **Clip 1: is her mouth moving?** If it is, regenerate. Everything else is
   recoverable and that is not.
2. **Clips 2–4: is anyone reflected in anything?**
3. **Does the room match across 2, 3 and 4?** If not, the plate is not holding
   and its weight needs raising.
4. **Does the voice sound like it is in that room** — not in front of it, and
   not in a bathroom.
