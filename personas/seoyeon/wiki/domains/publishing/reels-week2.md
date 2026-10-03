# The Reels — week 2

## The rule this is built on

**At most ONE "meaning" reel a week. The rest is life.**

The first version of this file had three reels and all three were pilates and
money running out. That is one note played three times, and it fails twice
over: it is not what anyone sends to a friend, and an account that only posts
its Big Life Theme reads as a brand rather than a person — which is the
realism problem, not just an engagement one.

A send says *"this is you"* or *"this is us."* Nobody sends a friend a reel
about someone's savings running out. Everybody sends one about being destroyed
at seven in the morning.

The career change is the account's spine and it belongs — once. Around it goes
what a 25-year-old actually posts: something she bought, something that went
wrong, something that is funny because it is true.

**Comedy is in the structure and the text, not the picture.** Contrast, lists,
escalation. That is why the funniest reels here are also the cheapest — two
images and an overlay beats anything generated.

---

## REEL A · "7am me vs 11pm me" · **$0** · post this first

Two images that already exist. The whole joke is the cut between them.

| | |
|---|---|
| **0–3s** | `n_studio_taught` — flushed, wrecked, blank.<br>Text: **"7am me, who signed up for this"** |
| **3–6s** | `n_conv_yawn` — deadpan under the convenience-store strip light.<br>Text: **"11pm me, who is now buying two dinners"** |

Zero cost, zero generation, and it is the most sendable thing on the account —
the format is universally understood and the punchline is a real convenience
store at 23:10. Post it before anything else.

```powershell
python reel_build.py content/grid/n_studio_taught_5e9f18_1.png content/grid/n_conv_yawn_b3fa75_1.png --dur 3.0 --out clips/rA_7am_11pm.mp4
```

---

## REEL B · the Daiso haul · **one image** · light, Korean, extremely relatable

A haul is the most ordinary thing a person posts and we have nothing like it.
Daiso is specific, cheap, and instantly legible to a Korean audience.

**One flat-lay image, four beats.** `reel_build.py` pushes in and the crops do
the rest, so a five-item haul costs one generation rather than five.

| | |
|---|---|
| **0–2s** | the whole flat-lay. Text: **"₩12,000 at daiso, no regrets"** |
| then | in on each thing: the grip socks, the hair claws, the tiny tupperware, the sponge shaped like a strawberry |

The strawberry sponge is the last beat because it is the joke, and the joke is
why anyone reaches the end. See `w2_daiso_haul` in `week2_shots.py`.

---

## REEL C · "POV: you have the key" · **one Seedance clip** · the capability test

| | |
|---|---|
| **0–1s** | Text: **"pov: you have the key to the class nobody wants"** |
| **0–7s** | `pov_studio_open` — the camera lifts, pans the empty room, stops on the window |

Quiet, close to ASMR, and it earns a rewatch because nothing happens in it.
This is the one that tells us whether POV video works for us at all.

---

## REEL D · "month eight" · **$0** · the one heavy one

The account's spine, said once and not again this week.

| | |
|---|---|
| **0–2.5s** | `n_studio_dawn`. Text: **"i quit my job in january to teach pilates"** |
| **2.5–4s** | `n_desk_late` |
| **4–5.5s** | `n_market` |
| **5.5–8s** | `n_studio_taught`. Text: **"month eight. i taught my first class last week."** |

The payoff is a blank face rather than a triumphant one, which is what makes
the claim believable instead of promotional.

```powershell
python reel_build.py content/grid/n_studio_dawn_6df563_1.png content/grid/n_desk_late_933157_1.png content/grid/n_market_peaches_ace1f9_1.png content/grid/n_studio_taught_5e9f18_1.png --dur 2.0 --out clips/rD_month_eight.mp4
```

---

## Order

| | | |
|---|---|---|
| **Mon** | A — 7am vs 11pm | $0 |
| **Wed** | B — the Daiso haul | one image |
| **Fri** | D — month eight | $0 |
| **Sat** | C — the POV test | one clip |

Light first. The heavy one lands in the middle of the week, by which point
whoever is watching has already seen her be funny — which is what makes the
serious one land rather than read as a pitch.

---

## Rules that apply to all four

1. **On-screen text in the first frame, always.** Reels autoplay silent. Text
   is the hook and it is the only thing working in second one.
2. **7–12 seconds.** Completion is the metric at zero followers.
3. **One idea per reel.**
4. **Trial Reel first, every time** — shown only to non-followers, so it is a
   free reach test that never touches the grid.
5. **Music in Instagram, never in the file.** A Creator account keeps the full
   catalogue and in-app audio is a discovery signal an embedded track is not.

## What to read afterwards

Views from non-followers, then completion, then **sends**. Ignore likes. The
specific thing to watch this week: **whether A and B outperform C and D.** If
the funny ones win — and they should — the ratio next week goes further that
way, and the account stops being about a career change and starts being about
a person who happens to be changing careers.
