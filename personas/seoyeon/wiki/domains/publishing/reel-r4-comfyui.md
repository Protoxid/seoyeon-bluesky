# R4 · fit check · ref2v prompts for ComfyUI

## References — wire both, in this order

| slot | file | job |
|---|---|---|
| **Image 1** | `content/week2_reel/w2r_fit_door_36013e_1.png` | the shot itself: framing, outfit, room, mirror, light |
| **Image 2** | `master/c/c5_relax_front.png` | her build, proportions, and her skin as it appears there |

**The tattoo is not described anywhere below, deliberately.** Text competes with
pixels, and a written tattoo comes back different from the master every time —
canon already says a picture holds it and a sentence never has. It has to ride
in on c5. Note the generated still **lost it**: her midriff is bare there, so
Image 1 alone cannot reintroduce it and Image 2 is doing real work, not
decoration.

---

## POSITIVE

```
Image 1 is this exact shot. Keep her face, her clothes, the room, the mirror
and the framing exactly as they are in it. Image 2 is the same woman full
length — use it for her build, her proportions, and her skin exactly as it
appears there.

A woman filming herself in a full-length mirror on her phone. Vertical 9:16,
handheld, flat contrast, low saturation, visible sensor noise in the shadows.
Her skin stays matte and slightly dry throughout: visible pores, uneven tone,
no gloss, and it does not smooth or brighten at any point.

She shifts her weight off one foot onto the other. Her free hand takes the hem
of the open shirt, pulls it straight, and drops back to her side. She turns her
upper body a few degrees, looks down at the shorts in the mirror, then
straightens and lifts her chin to look at herself.

The framing is locked. The mirror edges, the doorway, the coat hook and the
shoe rack sit in exactly the same place in the last frame as in the first.
Only her body moves. The only camera motion is the small tremor of a phone
held in one hand.
```

## NEGATIVE

```
zoom, zooming in, push in, dolly, tracking shot, pan, tilt, orbit, crane,
camera movement, gimbal, slow motion, morphing, warping, melting, limbs
changing length, extra limbs, extra fingers, face changing between frames,
face smoothing, skin smoothing, glossy skin, wet skin, oily skin, plastic
skin, airbrushed, beauty filter, shallow depth of field, bokeh, background
blur, colour grading, film grain, lens flare, second person, another person
reflected, second phone, clothes changing, cut, jump cut, black frame, text,
watermark, logo
```

---

## What each of the three failures needed

**The slow zoom.** Every camera word was sitting in the *positive* prompt as
"no pan, no zoom, no push in" — and in a positive prompt naming a thing is how
you summon it. The API had no separate negative field so there was nowhere else
to put them; ComfyUI does, so they move wholesale into NEGATIVE and the
positive says only what the camera *is* — locked, with named fixed landmarks so
"locked" is checkable rather than adjectival. If the workflow exposes a motion
or CFG-motion control, drop it as well: i2v priors drift toward a push-in on
their own, without being asked.

**The missing tattoo.** Not a prompt problem — a reference problem. Neither the
still nor the face frames carry it. c5 does.

**Floaty movement.** Three actions with contact points instead of a smooth
continuous drift: weight transfers onto a foot, a hand grips a hem and
releases, the torso rotates and stops. Floatiness is what a model produces when
nothing in the description has to touch anything.

---

## Two things that depend on your model, which I have not tested

Model-specific rules do not transfer — that has caught us four times, so treat
both as adjustable rather than settled:

1. **Timecodes.** H3 acts on `[0-2 seconds]` beats; most ComfyUI video models
   ignore them and prefer one flowing sentence. The positive above is written
   flat for that reason. If you are running H3 weights locally, split the third
   paragraph into `[0-2s] [2-4s] [4-6s]`.
2. **Reference count.** Some ref2v workflows weight the first reference far
   more heavily than the rest. If the tattoo still does not land, raise Image
   2's weight before touching a word of the prompt.

**Local runs are free.** That is the important consequence: iterate on this
rather than reasoning about it, and the per-second cost question that was
blocking the voiced version stops mattering for anything you generate locally.
