# WEEK 1 — Sat 5 Sep → Sun 13 Sep 2026
Owners: **S** = Shade (human only), **G** = Gemini (operator), **C** = Claude
(orchestrator, writes the code and reviews).

## THE SHAPE OF THIS WEEK
Two things have multi-day lead times and nothing can compress them: **Fanvue
KYC** and **Meta Business Verification**. Both start today. Everything else in
the week is arranged to fill that wait with work that is free and unblocked, so
that on the day the verifications land we are ready to use them rather than
starting then.

The second principle: **nothing new gets built until today's content is out.**
The reel and the feed post have been ready for days. A growth plan layered on
top of a stalled publishing habit is decoration.

---

## SATURDAY 5 SEP — TODAY

| # | who | task | why today |
|---|---|---|---|
| 1 | S | **Start Fanvue KYC** — ID + selfie liveness | longest lead time; blocks every euro |
| 2 | S | **Start Meta Business Verification** + App Review for Advanced Access | days of waiting; unlocks private replies |
| 3 | S | Finish the R4 caption by hand, re-burn the cards, publish the reel | ready since this morning |
| 4 | S | Publish `w2_daiso_haul` feed post | gate is clean, caption written |
| 5 | S | **Set up X** — profile, settings, bio (see the separate walkthrough) | free, 20 minutes, unblocks a whole lane |
| 6 | S | Create the **Bluesky** account | free, no approval, no API key — the lowest-friction lane in the plan |
| 7 | G | Write `fanvue_profile.md` — bio options, welcome DM options, avatar/banner filenames | needs nothing; ready the moment KYC lands |
| 8 | C | Write `syndicate.py` skeleton + Bluesky lane | free to test end to end today |

**Today's definition of done:** two pieces of content published, three accounts
existing, two verifications in flight, and one new script that can post to
Bluesky.

---

## SUNDAY 6 SEP

| who | task |
|---|---|
| S | Approve Gemini's Fanvue copy; write the final bio and welcome DM by hand |
| S | Top up Kie (~$5 covers the LoRA dataset at $2.70 with headroom) |
| C | `weekly_prep.py` run — the existing Sunday ritual, extended to name the new lanes |
| C | Finish the Bluesky lane; first test post from `syndicate.py --dry-run` |
| G | Regenerate the 30 LoRA dataset shots once Kie is funded — **$2.70, hard cap** |

Sunday is the prep day the pipeline already assumes. Keep it.

---

## MONDAY 7 SEP

| who | task |
|---|---|
| S | If KYC passed: set the AI creator tag, profile assets, subscription price, issue the API key |
| G | `fanvue_api.py` — read-only client, `--whoami`. Acceptance: prints handle, subscriber count, balance |
| C | Instagram lane folded into `syndicate.py` |
| S | First X post — SFW, no link in the body (the link lives in the bio) |

---

## TUESDAY 8 SEP

| who | task |
|---|---|
| G | **Tracking links** — one per platform, written to `links.json` |
| S | Put the right tracking link in each platform's bio |
| C | Threads lane in `syndicate.py` |
| S | **The manual Meta ad test** — clean creative, 18+ targeting, Fanvue link, small budget, one day |

The ad test is the highest-information action of the week. Meta permits "links
to… adult subscription websites" at 18+ and bans "logos, screenshots or video
clips of known pornographic websites", and defines neither term. This settles it
for a few euro, before any ad code exists.

---

## WEDNESDAY 9 SEP

| who | task |
|---|---|
| S | Record the ad verdict in `STATUS.md` — approved or the exact rejection text |
| G | `fanvue_dm.py --welcome`, idempotent. Acceptance: second consecutive run sends nothing |
| C | Review the welcome flow end to end before it is allowed to touch a real subscriber |
| S | Daily: publish, and answer anything in the IG inbox by hand |

---

## THURSDAY 10 SEP

| who | task |
|---|---|
| C | `ig_engage.py` — poll comments, draft replies into the approval queue |
| G | Run it; drafts appear, nothing posts |
| S | Approve or reject the drafts. Two minutes |
| S | LoRA training run on RunPod if the dataset passed QC on Sunday |

---

## FRIDAY 11 SEP

| who | task |
|---|---|
| C | `ledger.py` — spend and revenue in one JSONL, per platform |
| G | Backfill every euro spent so far, from this session's records |
| S | Check the Meta verification status |

---

## WEEKEND 12–13 SEP — THE FIRST REAL REVIEW

The week ends with numbers, not opinions:

- **Subscribers by tracking link** — which of the lanes actually produced one
- **Spend per platform** against revenue, from the ledger
- **Reach**: trial reel views vs. grid post views
- **What is still blocked** and by whom

Then the week 2 plan is written from that, not from guesses.

---

## WHAT IS DELIBERATELY NOT IN THIS WEEK

- **Mass messages on Fanvue.** Not until there is a list worth messaging and an
  approval queue to release them through. A mass message cannot be recalled.
- **`ads_meta.py`.** Not until Tuesday's manual test comes back approved.
- **Reddit and TikTok lanes.** Reddit needs subreddits chosen by hand and their
  individual rules read; TikTok needs an API audit before posts are public.
- **Private replies.** Blocked on Advanced Access, which will not land this week.

---

## THE HONEST RISK
Three of the four highest-value items — Fanvue KYC, Meta verification, the ad
verdict — are outside our control and could each slip. If all three slip, the
week still ends with: content published daily, three new platforms live, a
working multi-platform publisher, and a funded LoRA dataset. That is the floor,
and it is deliberately set so the week cannot be a write-off.
