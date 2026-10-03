> **ARCHIVED — 31 Aug 2026.** Superseded by reel-r1-voiceover.md. The route comparison that chose local lip-sync, before voice-over removed the need for any.
> Kept for the reasoning, not as a plan.

# The voiced reel — pipeline from "we have the hook"

## First, the thing that changes the whole shape

**H3's audio slot will not make her say your file.** It is a TIMBRE reference:
MiniMax's own wording is "voice timbre follows reference audio 1", and the
model card's example reads "references the calm male voice timbre of <Audio 2>
for <Subject 1>'s spoken lines". The *lines* come from the prompt. The mp3
supplies only the character of the voice.

So H3 would re-perform the script in a voice **like** hers, with delivery it
chooses, and we would be paying per attempt to find out how close it gets.
A local lip-sync pass instead drives the mouth from the **exact** ElevenLabs
take — the one you already approved by ear.

That points at Route B, and it is also the free one.

| | Route A · H3 speaks | Route B · ComfyUI lip-sync |
|---|---|---|
| words | H3 re-performs from the prompt | your exact mp3, verbatim |
| delivery | H3 decides | you already heard it |
| length cap | **15s per generation**, hard | your workflow's, not H3's |
| cost | per second, rate still unconfirmed | free |
| iterate | costs money each time | costs time |

**Route B.** Route A only becomes interesting if the local lip-sync nodes turn
out mushy and you would rather pay than fight them.

---

## The asset we do not have

**None of the existing stills can carry a lip-sync.** The fit check is
full-length in a hallway — her face is maybe 4% of the frame, and a lip-sync
model needs the mouth at real resolution. `w2_class_two` is closer but it is
3:4 and she is mid-torso.

So step one is a new frame, and it has four requirements that are easy to get
wrong:

1. **9:16, face large** — roughly upper chest to just above the head.
2. **MOUTH CLOSED, neutral.** A lip-sync model repaints the mouth region; a
   starting frame that is already smiling or open fights it the whole way and
   the seam shows.
3. **Eyes to camera**, front camera at arm's length. This is the one shot where
   looking down the lens is right — she is talking to the viewer.
4. **The studio behind her**, written in text. Do NOT reach for `plate_studio`:
   that file is the domestic living room, and a teaching reel shot in a flat
   throws away the authority the reel exists to build.

$0.09 on Kie, or free locally now that ComfyUI is doing the work.

---

## The pipeline

```
1  VOICE          make_voice_el.py --only hook          judge the ACCENT first
                  then --all                            -> voice/*.mp3
2  TALKING FRAME  one 9:16 front-camera still, mouth closed
3  LIP-SYNC       ComfyUI, still + mp3 -> clip          one per segment
4  ASSEMBLE       4 segments, same framing = jump cuts, the native look
5  CAPTIONS       burned in, NOT optional
6  QC             mouth at quarter speed, face drift, sync at the cuts
7  PUBLISH        Trial Reel
```

**Step 3, the choice inside it.** Animate the still directly from audio
(Sonic, LatentSync) or generate a silent ref2v clip first and lip-sync onto
that. Start with the still: fewer moving parts, and a talking head needs almost
no body motion. Add the ref2v pass only if it reads too static.

**Step 4.** Reusing the same still for all four segments is a feature. Cuts
between identical framings read as jump cuts, which is exactly what a talking
reel looks like natively — it is what people already do to cut their own
pauses out.

**Step 5 is not decoration.** Most of the feed is watched muted, and this is a
teaching reel whose entire value is the words. No captions means the tips do
not land at all for most viewers. The script is already known, so the captions
can be cut to the real segment durations rather than transcribed.

---

## Where it lands in the calendar

It does not make this week, and it should not be rushed to.

* **Mon 31 — R1, the text version, $0, already built.** It is the safety net.
* **Sat 5 — R4, the fit check.** Finish it with the text burn.
* **Voiced R1 — week 3.** It is the same three tips, so it is a straight
  upgrade of a reel that will already have a Trial Reel number against it —
  which means you get a real comparison instead of a guess about whether the
  voice was worth it.

---

## Three things I would check before spending anything

1. **The accent, on the hook alone.** A Seoul instructor with a flat American
   voice reads as dubbed. Different tell, same failure.
2. **Whether the 15s ceiling even applies locally.** It is an H3 API limit. Your
   workflow may have a different one, set by VRAM rather than by contract. It
   decides whether this is four clips or one.
3. **The mouth at quarter speed, on ONE segment**, before generating four. Every
   lip-sync failure lives in the first half-second of speech.
