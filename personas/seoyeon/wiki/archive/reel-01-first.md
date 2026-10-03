> **ARCHIVED — 31 Aug 2026.** Superseded by reel-r1-voiceover.md. This was R1 as a Google Flow clip, before Flow refused her face.
> Kept for the reasoning, not as a plan.

# Reel 01 — the first one to publish

**Her, moving, in the studio.** Generated in Google Flow with Omni Flash, which
is free on your AI Plus. This replaces the washing-machine reel, which is not
being published.

## Why this one and not that one

At zero followers a stranger needs a reason to stop, and in this niche the
reason is HER. Relatable content — the broken machine, the coin laundry — only
works on someone who already likes you. It is the last category that starts
working, not the first, and I had it first.

This reel does three of the six things at once: it shows her, the 7am light is
genuinely beautiful, and the text carries one piece of real information. That
is why it is worth the only expensive thing we have, which is effort.

## The Flow prompt

Set **9:16**, **1080p**, **8 seconds**. Attach `master/a/a1_front.png` and
`master/a/a2_tq_left.png` as reference images.

> Vertical phone video, 9:16, filmed on an iPhone propped on a bench: flat
> contrast, low saturation, visible sensor noise, no colour grade, no cinematic
> look. It should read as a clip somebody filmed of themselves in an empty gym
> and never edited.
>
> Use Image 1 and Image 2 as a strict identity reference for her face — the
> same woman, the same features, the pale freckles across her nose and inner
> cheeks. A Korean woman in her mid twenties, black sports bra and black
> leggings, hair in a low bun coming loose. Her skin is matte from brow to jaw
> and reads slightly dry: visible pores, uneven tone, the only sheen a faint
> one along the nose.
>
> An empty pilates studio in Seongsu, Seoul, just after seven in the morning.
> Pale wood floor, reformer frames, a tall window along one side with hard low
> sun coming through it in a band across the boards. Nobody else is in the room.
>
> [0-3 seconds] She walks in from the left carrying a rolled mat, crosses
> through the band of sun, and the light goes across her face and body as she
> passes.
> [3-6 seconds] She drops the mat, sits down on it and pulls one knee in,
> looking down, breathing out.
> [6-8 seconds] She looks up toward the camera for about a second, mouth
> closed, and then away again.
>
> The camera does not move: it is propped on a bench at about knee height,
> slightly off level, and she is not centred in the frame. No pan, no zoom, no
> orbit, no gimbal.
>
> Avoid: soft dissolves, fluid morphing, limbs changing length, the face
> smoothing or brightening between frames, glossy or wet-looking skin, shallow
> depth of field, background blur, slow motion, colour grading, film grain
> overlay, lens flare, any second person, any reflection of a person in the
> mirror, black frames, and any cut. One continuous take.
>
> Audio: room tone only — distant air conditioning, one person moving on a mat.
> No music, no speech.

## The text, burned in afterwards

| | |
|---|---|
| 0.2–3.0s | **the 7am slot is the one nobody wants** |
| 3.2–6.0s | **so it is the one they give the trainee** |
| 6.2–8.0s | **i have the whole room for forty minutes** |

The third line is the turn: it stops being a complaint and becomes something
faintly enviable, which is what makes it worth watching to the end.

Save the Flow output as `content/reels/r01_seven_am.mp4`, then:

```powershell
python make_reel_text.py --video content\reels\r01_seven_am.mp4 --out clips\r01_seven_am.mp4
```

## The caption
```
the seven o'clock slot is the one nobody signs up for, so it is the one they
give you when you are still training

nobody tells you the best part is the forty minutes before anyone arrives

seongsu, tuesdays and thursdays
```
`#pilates #필라테스 #성수동 #seoul` · location **성수동**

Post as a **Trial Reel** first.

## This is also the identity test
If Flow holds her face across eight seconds of movement, every video from here
is free and the whole video problem is solved. If it does not, we know within
one free attempt and fall back to a propped-camera still sequence.

**Watch the first twelve frames at quarter speed.** Face wobble lives there or
nowhere.
