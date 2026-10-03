# THE WEEK — Mon 7 → Sun 13 Sep 2026 (ISO 2026-W37) · tier 1

Day count: **day 244 → day 250** since she resigned (day 230 = Mon 24 Aug, per
`character.md` STATUS; day 0 = 6 Jan 2026). Caption age **25** (26 in prompts
only — CANON §2).

## Season, first, because it drives everything
The heat came back after the week-2 turn. That is not a repeat of last week's
story, it is the reversal of it: the fan is on again, the window is shut at
9pm, and the thing she was enjoying is gone. A season going backwards is the
cheapest variety there is and it is honest — this is what early September in
Seoul actually does.

## What happens to her, Monday to Sunday

**MON 7 — day 244.** The 7am beginner class, and she teaches it badly. Not
catastrophically: she loses the count on the second set, says "again" when she
means "wait", and one regular corrects her in front of the other four. She is
still thinking about the count on the platform home. Heat from 8am.

**TUE 8 — day 245.** No class. Course reading at the table she cannot concentrate
on, the fan achieving nothing, and a 2,500 won gimbap for lunch because she
worked out on Monday exactly how much is left and did not enjoy it. She notices
the price of coffee again.

**WED 9 — day 246.** Second 7am class. Better — she gets the count right and
someone asks a question she can answer — and the reward for teaching it well is
the studio asking her to cover a fourth slot next month, which is money and
also more hours. She stays in the empty room afterwards.

**THU 10 — day 247.** Jieun comes up with a container of something her mother
made, which is how food travels between the three of them. They eat at the
table, move to the roof because the flat is 29 degrees, and Jieun leaves before
nine because she has work. The flat is warmer for being in it.

**FRI 11 — day 248.** She goes down to the river path at sunset, on her own,
because the roof was good on Thursday and the walk is free. This is the one
frame all week where she is not in the flat or the studio.

**SAT 12 — day 249.** Market in the morning — she still shops at a market
rather than a department store — peaches and too much for one person. Laundry.
The washing machine is still making the noise.

**SUN 13 — day 250.** The money post. She sits at the table with the laptop and
the bank app and works out the date the savings run out, which she has known
for months and has never written down in a caption. She does not post the
number. The week ends on a decision she will not say out loud: the fourth slot,
she is going to say yes.

## Thread, in one line
Two classes, one taught badly and one taught well · the fan winning · Jieun
visiting · the number she will not post. Three of seven frames show her face;
four are objects or rooms. Nothing is posed as achievement.

## The seven shots (all generated and approved — see handoff.json)

| id | day · time KST | plate | shot | caption |
|---|---|---|---|---|
| `w37_class_bad` | Mon 7 · 07:55 | `plate_studio_wide` | studio, after, sitting on the floor of the empty room, hair coming out of the bun, mouth closed and pushed to one side. selfie, face in. | "the seven o'clock. i lost the count on the second set and someone said it out loud\n\nfour people in the room and i could feel every one of them looking at the wrong thing" |
| `w37_fan` | Tue 8 · 15:10 | `plate_room` | the flat at mid-afternoon: the standing fan pointed at the bed, the window shut, the table with the laptop open and a glass of water. no face, no person. | "29 degrees in the flat and the fan has been on since this morning and it has achieved nothing\n\ni have started closing the window like it is the fan's fault" |
| `w37_gimbap` | Tue 8 · 13:20 | — (one-off, convenience store counter, not the flat) | rear-camera photo of a 2,500 won gimbap and a bottle of barley tea on the counter by the till, wrapper unbranded, everything blurred except the tray. no face. | "2,500 won for lunch and i stood there doing the division\n\ndid no reading today. the fan won" |
| `w37_studio_after` | Wed 9 · 08:05 | `plate_studio_wide` | the studio empty after the class, reformers lined up, her towel and bottle left on the near machine, morning light on the floor. no face. | "they asked me to cover a fourth slot next month\n\nthe reward for teaching it properly is more of it. i have been here for twenty minutes deciding whether that is a compliment" |
| `w37_jieun_roof` | Thu 10 · 20:40 | — (one-off, no plate — no valid empty rooftop plate exists; the roof matches the published grid shots) | friend-taken dusk roof shot, her face in, hair clipped up, oversized grey tee. the second cup nearest the lens and a food container with chopsticks imply Jieun behind the camera — Jieun is never rendered (grid-week-1 precedent). women only. | "jieun brought something her mother made and we ate it up here because the flat is warmer than outside\n\nshe left before nine. the cups stayed until i came down" |
| `w37_market_peaches` | Sat 12 · 10:15 | — (one-off, market stall) | a market stall tray of late peaches, cardboard, a plastic bag, Korean price card, taken standing in the queue, crooked, slightly blocked at one edge. no face. | "peaches are going cheap, which means they are nearly gone\n\nbought eight. i will eat four before they turn" |
| `w37_table_sunday` | Sun 13 · 21:05 | `plate_room` | night selfie at the table, her face in, lamp on. the laptop screen turned away from the lens — only its back and a thin glow in frame, the single pencil line too faint to read, no readable numerals anywhere, the fan still running in the background. | "wrote the date down. i have known it since june and it is still worse in pencil\n\nnot posting the number. yes to the fourth slot" |

**Hashtags (one set, used unchanged):** `#seongsu #seoul #daily #filmphoto #
everyday` — five, lowercase, no location tag, no niche/fitness tags. Hashtags
stay out of the caption body and are appended by `ig_publish.py`.

## Continuity notes for whoever regenerates these
- The flat is `plate_room_ecc050_1.png` (kitchenette left, table and one chair
  in the near half, bed under the window, standing fan beside the bed, grey
  curtains). Every home frame uses that plate or none — never a described room.
- `plate_studio_wide_4e68ba_1.png` is the studio (two rows of reformers, tall
  windows left, full-height mirror right, water cooler, blue mats stacked).
  `plate_studio` (bare id) does **not** resolve — only a `.url` pointer is on
  disk — so do not name it.
- `plate_rooftop` resolves to `locations/rooftop.png`; `plate_cafe`,
  `plate_hallway`, `plate_bathroom`, `plate_stairwell`, `plate_river` all
  resolve. `plate_kitchen` and `plate_window` do **not** (the only kitchen and
  window plates are under `locations/_superseded_rich_flat/` — superseded,
  a different flat; do not use).
- Clothedy torso shots: no `body=True`, no mention of the tattoo. The body
  reference (`master/c/c5_relax_front.png`, sports bra and shorts, ribcage
  visible) attaches only on `body=True`/`limb=True`, which is the mechanism
  `exclude_body_ref` refers to — that key does not exist in `outside.py`.
- No men in any frame, including backgrounds. Last week's studio selfie has a
  woman in the doorway; keep it that way.
