# PLATFORMS — the tier model
**Which rules apply where.** Every "can I post this / generate this / say this"
question is answered here. Read with `CANON.md`.
Quotes and source URLs for every platform rule live in `growth/COMPLIANCE.md` —
this file is the decision, that file is the evidence.
Last verified 6 Sep 2026.

---

## 1. THE ONE AXIS

Content tier decides the platform, the generator, and which agent holds the
keys. It is a single axis with three consequences, and mixing the tiers up is
the only mistake here that ends an account.

| tier | content | platforms | generator |
|---|---|---|---|
| **1 — clean** | her life. no nudity, nothing suggestive | Instagram | **gpt-image-2.5** (Kie) |
| **2 — soft** | suggestive, opaque, not explicitly posed | Bluesky, Fanvue public profile | **Seedream 5 Pro** (Kie) |
| **3 — intimate** | intimate, marked 18+ | Fanvue paywall | **Seedream 5 Pro** (Kie) |

**A tier-2 or tier-3 asset must never reach Instagram.** Meta removes
AI-generated nudity explicitly, "regardless of 'photorealistic' appearance", so
"it isn't a real body" is not a defence. This is enforced in code, not by
memory — see `PIPELINES.md` §5.

---

## 2. INSTAGRAM — `@syeon.hn` · tier 1

**Role.** She is a real person. That is the entire job of this account: an
everyday life that makes a stranger believe there is a woman behind it. It is
credibility, not conversion. Traffic leaves via the bio link (`c=fv-2`).

**Content.** Her life in Seongsu. Coffee, the studio, the flat, the walk to the
station, the fit checks. Her body is present in most frames but **incidental —
a body living a life, never posed as achievement.** See `CANON.md` §7: this is
the one place that doctrine governs, and it governs completely.

**Never here:** nudity, implied nudity, suggestive posing, held products,
legible packaging, anything that reads as sponsored.

**Duties.** Meta requires AI disclosure on photorealistic video and audio — the
in-app label, on every reel. 100 API posts / 24h.

**Status: LIVE.** Publishing confirmed working on 6 Sep 2026.

> #### Resolved incident — API access blocked, 6 Sep 2026
> `POST /{ig-id}/media` returned HTTP 400,
> `{"message":"API access blocked.","type":"OAuthException","code":200}`.
> Meta's reference: codes 200-299 mean "Permission is either not granted or has
> been removed."
>
> It cleared on its own within hours, with no change on our side. **No root
> cause was established.** The only thing that had changed was that the app had
> entered business verification, which is consistent with a temporary hold
> while a review step settles — but that is a hypothesis, not a finding.
>
> **If it recurs:** run `ig_publish.py --dry-run` first. Its free `GET` splits
> the diagnosis — a working GET with a blocked POST means the publishing
> permission specifically; both blocked means app-level enforcement. Then check
> the App Dashboard alert panel, App Review → Permissions and Features, and
> Business Settings → Security Center. Do not change code: nothing in ours
> caused it last time.

## 3. BLUESKY — `@syeonhn.bsky.social` · tier 2

**Role.** Reach. It is the only platform in the stack that is free, needs no
API key, no approval, and permits labelled adult content. Every teaser threads
a conversion reply to Fanvue (`c=fv-4`).

**Content.** Soft-NSFW teasers: suggestive, opaque, not explicitly posed. Self-
labelled `suggestive` via `com.atproto.label.defs#selfLabels`.

**Duties.** No AI-disclosure rule, but their impersonation rule requires an
account's nature to be identified **in both display name and bio** — so the
display name carries "(AI)" and the bio says it plainly. Limits are generous:
~1,666 creates/hour.

**Automation.** GitHub Actions, `.github/workflows/bluesky_scheduler.yml`,
23:30 and 11:30 UTC, credentials in GitHub Secrets.

## 4. FANVUE — `@syeon.hn` · tiers 2 and 3

**Role.** The money. $9.99/mo, bundles, PPV. This is the only platform that
earns, and the only one with a full write API.

**Two surfaces, and this is the distinction that decides whether anyone pays:**

- **Public profile** (avatar, banner, intro video, bio, Discover) is **tier 2**.
  Not "SFW" — Fanvue permits "swimwear, lingerie, or boudoir-style content in
  Public Media as long as it is opaque (not see-through), not posed explicitly."
  Banned there: nudity, implied nudity, **strategic covering**, see-through
  clothing, porn-style framing, and age-baiting language ("just turned 18",
  "barely legal", "teen"). Enforcement is graduated and does not touch revenue —
  first offence removes the profile from Discover only.
- **Paywall** is **tier 3.** "Intimate content… is permitted but must be
  clearly marked as 18+ Content." A tier-1 lifestyle photo behind the paywall
  is a refund request. Deliver what the teaser promised.

**Duties.** The AI tag in the profile bio is mandatory — Fanvue states it is a
legal requirement, and failure "may result in your content being removed
and/or your account being suspended". Automation is permitted **only** through
the API; browser automation against fanvue.com is barred outright by their AUP.
Rate limit 100 requests / 60 seconds.

---

## 5. THE FUNNEL, AND THE TWO RULES THAT HOLD IT TOGETHER

```
Instagram  (tier 1, credibility) ─┐
                                  ├──► bio link ──► Fanvue ──► paywall
Bluesky    (tier 2, reach)      ─┘   c=fv-2 / c=fv-4        (tier 3)
```

**Fanvue first.** The companion set publishes or is scheduled on Fanvue
**15 minutes before** the Bluesky teaser. `weekly_schedule.json` holds the
times.

**Never tease what is not live.** A Bluesky teaser pointing at a Fanvue post
that does not exist converts a curious visitor into someone who has learned the
account lies. This is the integrity invariant; `campaign_orchestrator.py`
verifies Fanvue existence before dispatch.

---

## 6. THE SOURCE OF TRUTH FOR *WHEN*

`growth/schedule_assets/weekly_schedule.json`. One file. Published drops carry
`"status": "published"` plus their URI, and both the Bluesky worker and the
orchestrator skip them — idempotency is a property of that file, not of anyone
remembering.

`personas/seoyeon/queue.jsonl` was retired on 6 Sep 2026 and moved to
`_trash/queue.jsonl.retired-2026-09-06`. Its Instagram entries were migrated in
(the two duplicates of the same image collapsed to one), so **all three
platforms now schedule from this one file.**

**Every entry declares `tier` and `lanes`.** That is not bookkeeping — it is the
field the tier gate needs. `PIPELINES.md` §5 records that `syndicate.py` could
not enforce `sfw_only` because no asset declared a tier; it does now, so the
gate is implementable.

| field | meaning |
|---|---|
| `tier` | the tier of the PUBLIC media (1 = Instagram, 2 = Bluesky teaser / Fanvue profile) |
| `fanvue_tier` | the tier of the paid companion set, normally 3 |
| `lanes` | which platforms this entry publishes to |
