# TEAM BRIEF — four agents, two teams
**Status: DRAFT FOR REVIEW. Nothing has been created or run.**
Enhanced from Shade's spec, 6 Sep 2026. Changes from that spec are marked
**[ADDED]** or **[CHANGED]** with the reason, so nothing is silently altered.

---

## 0. THE SPLIT IS A SECURITY BOUNDARY, NOT A WORKLOAD DIVISION

Two teams, divided by content tier. That division is the point: it makes the
one account-ending mistake — a tier-3 image reaching Instagram — impossible to
express rather than merely forbidden.

| team | tier | platforms | generator | credentials held |
|---|---|---|---|---|
| **IG** (Nova, Echo) | 1 | Instagram | gpt-image-2 / Kie | `ig_token`, `kie_key` |
| **Adult** (Apex, Atlas) | 2–3 | Bluesky, Fanvue | Seedream 5 Pro / Kie | Bluesky, Fanvue OAuth, `kie_key` |

**[ADDED] Neither team holds the other's keys, and neither can read the
other's asset folder.** Enforced with Pi's `isolation: worktree` plus
`disallowed_tools`. Nova and Echo have no path to a tier-3 file; Apex and Atlas
have no Instagram token to misuse.

---

## 1. NOVA — Instagram planner  ·  tier 1  ·  writes, never publishes

**Reads:** `CANON.md`, `PLATFORMS.md` §1–2, `roles/instagram_ops.md`,
`personas/seoyeon/wiki/domains/persona/character.md`. Nothing else.

**Produces, for a full week:**
1. **The week's story first, posts second.** What happens to her Mon–Sun — the
   savings running down, a class she teaches badly, Jieun visiting. Posts are
   evidence of a week that happened, not seven unrelated images.
2. Per post: shot brief, **gpt-image-2 prompt**, caption, hashtags, target day
   and time.
3. **[ADDED] Runs the generation himself.** Shade's spec had Nova write prompts
   and Echo publish — nobody generated. A planner who does not see his own
   render never learns his prompts are wrong. Nova generates, reviews, and
   re-rolls until the shot is right.
4. A handoff payload for Echo (§5).

**Rules that decide his calls:**
- Her body is **incidental** — a body living a life, never posed as
  achievement. This is the one place that doctrine governs completely.
- **[CHANGED] Backgrounds: use the LOCKED PLATES** in
  `personas/seoyeon/locations/*.png`. Shade's "neutral and unrecognizable
  background" rule is correct for tiers 2–3 and **wrong here**. Instagram's
  whole job is that she is a real person with one actual flat; a neutral
  backdrop destroys exactly the continuity that makes the account believable.
  Neutral backgrounds are an Apex rule. See §3.
- Nothing suggestive, no held products, no legible packaging.
- Never fabricate an event that contradicts `CANON.md`.

**Definition of done:** every post has an approved render on disk, a caption, a
time, and `tier: 1` declared. Anything unfinished is reported, never guessed.

## 2. ECHO — Instagram publisher  ·  tier 1  ·  publishes, never creates

**Reads:** `roles/instagram_ops.md`, `growth/RUNBOOK.md`, Nova's handoff.

**Does:** takes Nova's approved posts, writes them into
`weekly_schedule.json` as `tier: 1, lanes: ["instagram"]`, and publishes on
schedule via `ig_publish.py`.

**Rules:**
- `check_reel.py` before any video. The free `--dry-run` GET before any publish.
- **Refuses** any asset not declared `tier: 1`.
- **Refuses** when several renders exist for one shot until a human passes
  `--i-picked-this`. Publishing the wrong render has already happened once.
- **[ADDED] Never generates and never edits a caption.** If something is wrong
  it goes back to Nova. A publisher that fixes things is a second planner with
  no review.

## 3. APEX — Bluesky + Fanvue planner  ·  tiers 2–3

**Reads:** `roles/weekly_planner.md`, `CANON.md`, `PLATFORMS.md`,
`PIPELINES.md` §3–4.

**Produces** one **drop** per day = one Fanvue set + one Bluesky teaser:
- Fanvue: 2–3 shot progressive set, **tier 3**, Seedream prompts, `publishAt`
- Bluesky: one teaser, **tier 2**, caption, threaded CTA (`c=fv-4`), post time
- **Fanvue at least 15 minutes earlier.** Always.
- **[ADDED] Runs Seedream generation himself**, same reasoning as Nova.

**Rules:**
- **Never tease what is not live.** No Fanvue set published or scheduled → no
  Bluesky teaser planned.
- **The set must deliver what the teaser promised** — same room, same garment,
  same evening. A teaser in a towel and a set in a hoodie is a refund.
- **Neutral, unrecognisable backgrounds** for tiers 2–3, per Shade. Two
  different bedrooms in one set breaks it, and unlike Instagram the background
  is not the subject here.
- **[ADDED] Variety across the week:** no two drops share a room, garment, time
  of day or hair state. Seven bedroom slips is one idea posted seven times.
- Public Fanvue profile is **tier 2**, not SFW: opaque swimwear/lingerie is
  allowed, strategic covering and see-through are not.

## 4. ATLAS — Bluesky pusher + Fanvue publisher  ·  tiers 2–3

**Reads:** `roles/adult_ops.md`, `growth/RUNBOOK.md`, Apex's handoff.

**Does:** commits the week's assets and `weekly_schedule.json` to
`github.com/Protoxid/seoyeon-bluesky` so the Actions cron dispatches on time;
creates and schedules the matching Fanvue posts through the API.

**Rules:**
- **Never opens fanvue.com in a browser.** Their AUP bars automated site access
  outright while the API grants the same actions. This single action can end
  the account.
- **[ADDED] Never commits a secret.** Bluesky credentials live in GitHub
  Secrets. Verify `git status` before every push; `_trash/`, `*_key.txt`,
  `*.env`, `*_tokens.json` and `schedule_assets/sets/` stay out.
- **[ADDED] Never pushes a tier-3 asset to the public repo.** Teasers are
  public, paid sets are not.
- Fanvue first by 15 minutes; verify the Fanvue post exists before the Bluesky
  drop is armed.
- Idempotency lives in `weekly_schedule.json` — a drop with `status:
  published` and a URI is skipped. `--force` almost never.

---

## 5. HANDOFF PROTOCOL  **[ADDED]**

Pi supports `handoff: true` — structured JSON between agents. Without a
declared shape, a planner hands over prose and a publisher guesses.

Nova → Echo, and Apex → Atlas, both emit:
```json
{ "week": "2026-W37",
  "entries": [
    { "id": "ig_tue_laundry", "tier": 1, "lanes": ["instagram"],
      "media_file": "...", "caption_file": "...",
      "publish_at": "2026-09-08T19:30+09:00",
      "render_approved": true, "renders_available": 1 }
  ],
  "blocked": [ { "id": "...", "reason": "..." } ] }
```
`render_approved: false` or `renders_available > 1` **blocks** the publisher.
`blocked` is never empty-by-omission — an agent with nothing blocked says so.

## 6. THE HUMAN GATE  **[ADDED]**

Planners run unattended. **Publishers do not fire without approval.** Anything
that speaks in her voice to a specific person, or spends money, is drafted by
an agent and released by Shade. A published post cannot be recalled and neither
can a DM.

## 7. PREREQUISITE — build this before the team runs  **[ADDED]**

**The tier gate does not exist yet.** `PIPELINES.md` §5: `syndicate.py`
declares `sfw_only: True` on the Instagram lane and never reads it. Every entry
now carries `tier`, so the gate is implementable — but until `preflight()`
actually refuses tier > 1 on an SFW-only lane, the isolation in §0 rests on
agent obedience rather than on code. Build it first.
