# WEEK 2 — the plan, rebuilt
**Posting Mon 31 Aug → Sun 6 Sep 2026. Her week: Mon 24 → Sun 30 Aug.**
All eleven stills are generated and approved. Followers: 0.

---

## 1. The Reels were wrong, and the diagnosis is worth keeping

A photo-dump slideshow is a **mood board**. Mood boards work for accounts that
already have an audience, because the audience supplies the interest. At zero
followers nothing supplies it, so the reel is asking a stranger to care about a
person they have never heard of, for nine seconds, in silence.

Your list is the right test, and I am adopting it as the design constraint. A
reel gets watched because it does **one** of these:

| | | can she do it? |
|---|---|---|
| **teaches / new information** | "3 things nobody tells you…" | **yes** — she is a pilates trainee. This is real, earned authority |
| **beautiful** | landscape, golden hour, a place | **yes** — Seoul, and no person in frame means no identity to hold |
| **relatable** | "this is my life too" | **yes** — cheapest thing she has |
| **funny** | a small disaster | **yes** — the washing machine died |
| **attractive person, shown off** | outfit, gym fit, transformation | **yes**, and it is the most reliable driver in this niche |
| **prank / skit** | multi-take, other people, voice | **no.** Not buildable |

The slideshow did none of them. Every reel below does exactly one, on purpose.

---

## 2. Omni Flash changes the economics completely

You have **Gemini Omni 1.1 Flash free in Google Flow** on AI Plus. That is not
a marginal saving, it reverses the whole video strategy:

- up to **40 seconds**, extended in 10s increments
- **360p / 720p / 1080p / 4K**
- **first and last frame** keyframing
- up to **3 seconds of video** as a reference
- native audio

**So: every video attempt goes to Flow first, because it costs nothing.** Paid
video is now the exception that has to justify itself, not the default.

The trade is that Flow is a UI, not an API — you generate by hand and drop the
file into `content/reels/`. At zero revenue, free-and-manual beats
paid-and-automated every time.

*Sources: [Google — build with Gemini Omni 1.1 Flash](https://blog.google/innovation-and-ai/technology/developers-tools/build-with-gemini-omni-1-1-flash/) · [DeepMind model card](https://deepmind.google/models/model-cards/gemini-omni-flash/)*

**What we do not yet know:** whether Omni Flash will hold her face from
reference images the way H3 does. That is the one thing worth testing first,
because if it does, the entire video problem is solved for free. Test order is
in §6.

---

## 3. The four Reels

### R1 · TEACHES · "3 things before your first reformer class" · **UNSCHEDULED**

**NOT DATED, DELIBERATELY.** It was set for Mon 31 and pulled the night before
because the voice did not pass. Putting it straight onto another date would be
the same bet again — the reel is blocked on one input, and a date does not
unblock it. It goes back on the calendar when there is a voice take that
passes, and not before.

Everything else is done: the four clips, the assembly (`build_r1.py`, verified
28.0s of picture), the captions, the caption copy and the first comment.

**Two open items, both unrelated to the voice:**
* The closing line "seven in the morning, Tuesdays and Thursdays, Seongsu" is
  an invitation to a class that does not exist, and it appears in FOUR places.
  Awaiting a decision — the proposed replacement is "honestly, you'll be fine".
* `clips/r1_five_things.mp4`, the slideshow version, is still sitting next to
  the real files with a confusingly similar name. It is the format that was
  rejected at the start of this project and should not be reachable by
  accident.

**THE FIRST VERSION WAS SCRAPPED, AND THIS IS THE IMPORTANT PART.** It was
three anatomy claims and I had written all three from my own head:

| claim | what checking it found |
|---|---|
| "your hip flexors are not tight, they are short from sitting" | **Unsupported.** Repeated everywhere, cited nowhere. The one study that looks like support is cross-sectional and measures limited hip *extension* — a range of motion, not a muscle length, and an association, not a cause. |
| "stop tucking your pelvis, neutral is not flat" | **Contested.** Imprint vs neutral is a live disagreement *between Pilates schools*; STOTT teaches both placements as valid. Picking a side from a zero-follower account picks a fight with half the profession. |
| "you will not feel it in your abs for about three weeks" | **I made the number up.** |

A teaching reel puts claims in her mouth **as a professional**, in a niche full
of real instructors. One wrong claim in the comments costs more than the reel
earns. So the content moved from PHYSIOLOGY — which cannot be verified to the
standard this account needs — to PROCEDURE. Every line is now attributable, and
the authority comes from insider knowledge instead of anatomical assertion.

| | tip | source |
|---|---|---|
| 1 | fewer springs is often *harder* — less spring means less help controlling the carriage | bodymindlife |
| 2 | grip socks are required at most studios | FORM · Club Pilates |
| 3 | come ten minutes early; that is when you are shown the machine | FORM |
| — | *unused, sourced: where the soreness lands; it is more mental than physical* | FORM |

**Three tips, not five.** Nineteen seconds of stills-with-text is a long hold
for someone who has never heard of her, and completion is the lever on a Trial
Reel. The original plan was right about the length and wrong about the content.
The two spare tips are the next teaching reel, also free.

**It opens on her face.** An empty room gives nobody a reason to stop
scrolling. Segment three returns to the same frame pushed tighter so the offer
reads as a bookend, not a third unrelated picture.

```
python make_reel_r1.py --check      verifies the beats, builds nothing
python make_reel_r1.py              $0
```
Caption: `things i wish someone had told me before my first reformer class` ·
`#pilates #reformerpilates #seoul #성수동` · location **none** · **Trial Reel**.

> **A live fault this uncovered.** `locations/studio.png` — the canonical
> studio plate — is a **domestic living room with one reformer in it**: rug,
> framed print, radiator, curtains. It was segment one until the QC frames were
> actually opened. The studio in the *stills* (reformers, mirrored wall,
> another woman by the door, in `w2_class_two`) is a different room entirely.
> `pov.pov_studio_open` resolves `plate_studio` to that living room, so **R3's
> free POV clip would render a flat, not a studio.** Fix the plate before
> building any studio POV.

### ~~R2 · FUNNY · "the washing machine"~~ · **KILLED**
Built, watched, rejected before publication. *"Nobody cares of the washing
machine."* No reason to press like — the hook was mundane relatability, and
relatable needs an existing relationship that a zero-follower account does not
have. The file is in `_to_delete/`. The Mon 31 reel slot is now empty; **R1 is
the candidate to move up**, since it is free and needs no face.

### R3 · BEAUTIFUL · "the Han at seven" · $0.56 · **THU 3, moved from Fri 4**

**Why it moved.** Friday already carries `w2_river_steps` in the feed — her on
the steps by the Han, same hour, same water. The river twice in one day is the
`w1_desk` mistake with a day's warning instead of after the fact. Thursday had
no reel and `week-structure.md` calls Thursday evening *"Han river path,
walking"*, which is the shot. The clip's own story line already said THU 19:00.

**Free was an assumption about Flow, and Flow refuses her.** It does not apply
here anyway — nobody's face is in this clip — but the supplier is Kie, and Kie
charges. 7s at 768P is $0.56.

**No plate.** A plate keeps a place the SAME place; the Han path is forty
kilometres long and she walks a different stretch each time. The price of
dropping it is that the prompt carries the river in full, which is why it runs
to 2,337 characters. `pov.pov_river_walk` holds it; `audit_video.py` checks it.

**Her shadow and her feet are in it.** A walking POV where the walker never
appears is drone stock. A long low-sun shadow up the path and trainers entering
the bottom of frame cost nothing, cannot fail a likeness check, and are the
difference between *a river* and *someone walking by the river*. R1's numbers
are the argument: the reel with almost no person in it got 118 views and
nothing after them.

One card, on the front, no text after it:
**"seoul does this every evening and i still stop"**

```
python make_river_clip.py --dry-run                              free
python make_river_clip.py                                        $0.56
python make_reel_text.py --video clips/r3_river_raw.mp4 --out clips/r3_river.mp4 --set river
```
NOT `--fit` — one card on a 7s clip would be stretched across the whole reel.

### R4 · SHOWN OFF · **the fit check** · $0.61 · THE ONE WE ARE MAKING FIRST
The category you named, and the most reliable engagement driver in this niche.
It is also the only one of the six reasons that needs **no existing
relationship with the viewer** — relatable needs one, funny needs context,
teaching needs authority. A good-looking person and a good outfit need nothing.
The payoff is a PROFILE VISIT, which is the metric that compounds from zero.

This slot was written as "free if Flow holds her face". **Flow does not** —
Omni Flash refuses her as a real person, and so do two other providers. The
slot never needed a new concept, it needed a supplier.

| | |
|---|---|
| still | `w2r_fit_door` — full-length mirror by the front door, `plate_hallway`, 9:16 · **$0.09** |
| clip | `make_fit_clip.py` — H3 **image-to-video**, 6s at 768P · **$0.52** |
| text | `make_reel_text.py` — three burned-in beats · **$0** |

**Why image-to-video and not reference-to-video.** ref2v is $0.76 and asks the
model to invent the outfit, the room, the light and the face from three
head-and-shoulders stills. Here all four are already correct in one approved
frame, so the only thing generated is movement — a weight shift, a tug at the
hem, a half turn, chin up. Cheaper *and* stronger, which is SAY ONLY THE DELTA
applied to video: the frame carries more than the prompt can.

**Why the mirror is not the usual problem.** The playbook warns that a
first-person camera in a mirrored room photographs the person holding it — but
that is about a room where she is not meant to be visible. Here the reflection
IS the subject and the phone in frame is the format. The remaining risk is the
model rendering her twice, once as a body and once as a reflection, and the
avoid list names that directly.

```
python outside.py --week2 --w2reel --all      $0.09   LOOK AT IT before the next line
python make_fit_clip.py                       $0.52
python make_reel_text.py --video clips/r4_fit_door_raw.mp4 --out clips/r4_fit_door.mp4
```
Text beats: *"seoul in august is not a joke"* → *"this is the third fit and i am
already late"* → *"we are going with it"*.
Caption: `changed three times for a dinner that lasted forty minutes` ·
`#seoul #ootd #성수동` · location **none** · post as a **Trial Reel**.

---

## 3b. STATUS, 31 Aug evening

**R1 went out and the result is a completion failure, not a content failure.**
118 views, **6s average watch on 23.5s** (26% retention), 0 likes, saves,
shares and profile visits. The first caption ran 0.3s→6.5s, so the average
viewer left exactly as the first tip was about to land. Almost nobody reached
the tips, so **zero saves says nothing about whether they are good.**
`fix_r1_timing.py` re-cuts it — first tip at 0.2s, the count folded into the
cards, reel trimmed to ~19s. **Not reposted:** recycled content is down-ranked
and a re-run could not be attributed to the fix.

**R4 IS NOT BUILT AND IT IS SCHEDULED SATURDAY.** The only fit-check file on
disk is `clips/r4_fit_door_raw.mp4`, which is the *bad* Kie image-to-video
version — the good ComfyUI render is not in the project folder. To finish:

```powershell
python make_reel_text.py --video <the good ComfyUI render> --out clips\r4_fit_door.mp4 --fit
```

Its caption beats are already written and width-checked, and its timing is
clean against the R1 lesson: first card at 0.2s, three cards of about 2s.

**Open, not blocking Saturday:** the voice (failed QC, see
`../pipeline/handoff.md` §6); the "seven in the morning, Tuesdays and
Thursdays, Seongsu" line still in four files; and
`clips/r1_five_things.mp4`, the rejected slideshow, still sitting beside the
real files.

## 4. The eleven posts, with captions

Voice: lowercase, no terminal full stop, keywords in the caption body. Crop
**Original**. Hashtags capped at 5. Alt text on every one.

---
**MON 31 · R1 the reel** — post first, 07:30
```
three things i tell everyone before their first reformer class

the springs one gets people every time. fewer springs is harder, not easier —
less spring means less help holding the carriage, so you are doing more of the
work

save this for your first class
```
`#reformerpilates #pilatesforbeginners #pilates #seoul #성수동` ·
location **성수동** · **Trial Reel** · cover: the frame where she looks at the lens

*first comment, posted immediately:* `two more that did not fit — you will be
sore in the inner thighs and between the shoulder blades for a day or two, and
it is more mental than physical at the start. most people settle by class four`

*alt: A woman in a black sports bra looks into a phone camera in a pilates
studio, then close shots of a reformer's springs, its carriage rolling to a
stop, and a folded pair of grip socks on a bench.*

---
**MON 31 · `w2_subway_am`** — Seongsu platform, 07:35
```
the seven o'clock slot means the platform is empty and the light does that
thing for about four minutes

first morning in five weeks i wasn't already sweating
```
`#성수동 #seoul #pilates` · location **성수동**
*alt: An empty subway platform at Seongsu station early in the morning, glass screen doors along the edge, tiled wall, empty metal seats, Korean signage and a lit route map.*

---
**TUE 1 · `w2_broken_machine`** — 09:15
```
it has been making the noise since july and i have been pretending not to hear it

nine in the morning. there is a towel involved
```
`#seoul #자취 #wfh` · location **none**
*alt: A small washing machine in the corner of a one-room flat, door open with wet washing inside, a puddle across the floor, a towel thrown down at the edge of it and a bottle of detergent knocked over.*

---
**TUE 1 · `w2_rain_awning`** — 15:20
```
first rain since june

went down for milk, came back wet. stood under the awning for five minutes
pretending i was deciding
```
`#seoul #자취 #비` · location **none**
*alt: A woman takes a front-camera selfie under the awning outside a convenience store on a residential street in Seoul during heavy rain. Her hair is damp and stuck to her forehead, her t-shirt is wet at the shoulders, and she is laughing. Behind her the rain falls on a wet road, parked scooters and a low building with Korean signage.*

---
**WED 2 · `w2_class_two`** — 14:40
```
second class

nobody tells you the second one is worse in a different way — the first one you
survive, the second one you have to actually be good at
it was fine. someone asked a question i could answer
```
`#pilates #필라테스 #성수동 #seoul` · location **성수동**
*alt: A woman sits on the floor of a pilates studio after teaching, taking a selfie at arm's length. Black sports bra and leggings, hair coming loose, flushed. Reformer frames and another woman putting her shoes on behind her.*

---
**WED 2 · `w2_laundromat`** — 21:30
```
half nine at night in the coin laundry because of this morning

forty minutes of doing nothing, which i have not done in a while. i am not
going to pretend i hated it
```
`#seoul #빨래방 #자취` · location **none**
*alt: The inside of a small coin laundry late at night. A row of washing machines, one running, a plastic basket on a folding counter with a paperback on top, a detergent vending machine, Korean signs on the wall.*

---
**THU 3 · `w2_bakery`** — 17:10
```
jieun's birthday is tomorrow and i stood in front of this tray for genuinely
four minutes

got the 6,000 won one. obviously
```
`#seoul #빵 #bakery` · location **none**
*alt: The counter of a small neighbourhood bakery in the late afternoon. Trays of bread and pastries under warm light, metal tongs resting on a tray, handwritten Korean price cards, a glass case at the till.*

---
**THU 3 · `w2_bad_coffee`** — 12:40
```
6,000 won and it tastes like a rumour of coffee

posting this so i remember not to go back
```
`#seoul #카페 #coffee` · location **none**
*alt: An iced americano in a tall plastic cup on a small marble table outside a cafe, ice melted to a pale layer at the top, a paper straw going soft, a phone face down and keys beside it. A narrow street behind.*

---
**FRI 4 · `w2_studio_mirror`** — 08:50
```
checking whether the leggings have gone see-through at the back, which is the
actual reason anyone takes this photo

they had not. this time
```
`#pilates #필라테스 #ootd #seoul` · location **성수동**
*alt: A mirror selfie in the small changing room of a pilates studio. A woman in black leggings and a sports bra holds her phone at chest height, a zip-up over one arm. Lockers, a bench with a bag, a folded towel behind her.*
**Crop anchor 0.35** — a mirror selfie sits high and the default 0.70 takes the top of her head off.

---
**FRI 4 · `w2_river_steps`** — 19:40
```
jieun turned 27 and instead of a restaurant we bought beer at the gs25 and sat
on the steps like students

best thing i have done all month and it cost four thousand won
```
`#한강 #hanriver #seoul` · location **뚝섬한강공원**
*alt: A woman sits on the wide concrete steps beside the Han river in the evening, turned to talk with one hand mid-gesture, looking past the camera. A can and an open bag of snacks beside her, the river and a lit bridge behind.*

---
**SAT 5 · `w2_daiso_haul`** — 16:20
```
went in for freezer bags

the sponge is a strawberry. i do not want to talk about it
```
`#다이소 #daiso #seoul #자취` · location **none**
*alt: A flat lay on a pale wood floor of things bought at a Daiso: grey grip socks still on their tag, two black hair claws, three stacked plastic containers, a roll of freezer bags, a kitchen sponge shaped like a strawberry, and a curled receipt.*

---
**SUN 6 · `w2_kitchen_sun`** — 11:00
```
no course this weekend so sunday is laundry, something on the hob, and writing
down the week

the flat is a normal temperature for the first time since june and i am
weirdly happy about it
```
`#seoul #자취 #sunday` · location **none**
*alt: A woman takes a selfie at arm's length in the small kitchen area of a one-room flat late on a Sunday morning. Hair unbrushed, an oversized washed-out t-shirt, no makeup, mouth open mid-sentence. A pot on the hob, a drying rack, a laundry rack through the doorway.*

---

## 5. The calendar

| day | feed | reel |
|---|---|---|
| **Mon 31** | `w2_subway_am` ✅ | **R1 text version** ✅ *(118 views · 6s watch · 0 else)* |
| **Tue 1** | `w2_broken_machine`, `w2_rain_awning` | — |
| **Wed 2** | `w2_class_two`, `w2_laundromat` | — |
| **Thu 3** | `w2_bakery`, `w2_bad_coffee` | **R3 — the Han at seven** *(built, $0.56)* |
| **Fri 4** | `w2_studio_mirror` ✅ *(posted via API; first render was the stale `4487c7`, archived; reposted `1b34a6` at anchor 0.35)*, `w2_river_steps` | — |
| **Sat 5** | `w2_daiso_haul` | **R4 — the fit check** ⚠️ *NOT BUILT — see below* |
| **Sun 6** | `w2_kitchen_sun` | — |

Every reel goes out as a **Trial Reel** first — shown only to non-followers, so
it is a free reach test that never touches the grid.

R2 leads because it is funny and needs nothing from anyone. R1 mid-week because
that is when saves happen. Do not open with the teaching one: an account with
no posts telling you about your hip flexors is a brand.

---

## 6. Tests, in order, cheapest first

**1 · Omni Flash identity — free.** In Flow, feed `master/a/a1_front.png` and
`master/a/a2_tq_left.png` and ask for four seconds of her lowering a phone.
Does the face hold? If yes, all video is free from here and R4 is on.

**2 · Seedance and the turntable — the one you asked for.** Seedance refused
real-person references before. `master/turntable.png` is a contact sheet of
angles rather than a portrait, which may or may not read differently to the
filter. Worth one call to know:

```powershell
python -c "import kie_api, pathlib; k=kie_api.Kie(__import__('os').environ['KIE_API_KEY']); print(k.upload(pathlib.Path('master/turntable.png')))"
```
then run it through `seedance_video()` with a single reference. **My honest
expectation is that it still refuses** — the filter is looking at whether the
image depicts a real identifiable person, and a turntable is more evidence of
one, not less. Worth the one call to be sure rather than assume.

**3 · Paid video only if both fail.** H3 on Kie, $0.08/s at 768P.

---

## 7. Money

| | |
|---|---|
| week 2 stills | **done** |
| four plates | **done** |
| R1–R4 in Flow | **$0** |
| paid video | only if the free path fails |

**The week costs nothing from here.**
