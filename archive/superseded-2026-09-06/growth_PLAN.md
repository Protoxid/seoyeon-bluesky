# GROWTH — the automation architecture
Written 5 Sep 2026. Read COMPLIANCE.md first; this document is what is left
once those rules are applied.

## 0. THE HONEST HEADLINE

You asked for everything automated: DMs, publishing, commenting, advertising.
Here is the split, and it is not the split you would expect.

| pillar | verdict |
|---|---|
| **Publishing** | fully automatable, on 6 platforms, free on 4 of them |
| **DMs** | fully automatable **on Fanvue**. On Instagram, inbound-only — cold DMs have no endpoint |
| **Commenting** | replies on our own posts: automatable. Comments on other people's posts: **no endpoint exists** |
| **Advertising** | automatable on Meta only. TikTok, X and Reddit all prohibit the destination |

The surprise is that **Fanvue is the most automatable surface in the entire
stack** and we have not touched it. It has a public API with 140+ endpoints
covering posts, chats, mass messages, media, subscribers and earnings, at 100
requests/minute. Everything we have been trying to force out of Instagram —
sending messages, reaching people, converting — is a sanctioned API call on the
platform that actually takes the money.

Instagram is not the business. Instagram is the top of a funnel that ends on
Fanvue. Once you see it that way the whole architecture falls out.

---

## 1. THE FUNNEL

```
   SFW reach layer                       conversion          money
   ─────────────────                     ──────────          ─────
   Instagram   (reels, stills, SFW) ┐
   Threads     (text + image, SFW)  │
   Bluesky     (adult ok, labelled) ├──► link in bio ──►  Fanvue
   X           (adult ok, labelled) │                     ├ subscription
   Reddit      (subreddit rules)    │                     ├ PPV messages
   YouTube     (Shorts)             ┘                     └ tips
```

Two rules fix the layout and both are quoted in COMPLIANCE.md:

**Instagram and Threads must stay SFW.** Meta removes AI-generated nudity
explicitly — "regardless of 'photorealistic' appearance". "It isn't a real body"
is not a defence there. Instagram is reach, never product.

**The link lives in the bio, on every platform.** On X this is also a money
decision: a post containing a URL costs **$0.200** against **$0.015** without
one. Thirteen times, for a link that converts worse than a bio link anyway.

---

## 2. PILLAR ONE — PUBLISHING

### What exists already
`ig_publish.py` (FTP → Meta fetch → publish, trial reels on by default),
`publish_queue.py` (the queue is the consent), `weekly_prep.py`,
`publish_prep.py`, and as of today `check_reel.py`. That is a working
single-platform publisher with a human gate. It is the right shape; it just
only speaks to one platform.

### What to build: `syndicate.py`
One queue entry fans out to every platform, each with its own body, its own
size, and its own disclosure.

**Per-platform lanes and why each is shaped that way:**

| platform | why it is in the list | constraint that shapes the code |
|---|---|---|
| **Bluesky** | free, no API key, no approval, no AI-label duty, adult content allowed with a label | ~1,666 creates/hour. Lowest friction of anything researched — build this lane first because it can be tested end to end today |
| **Threads** | free, 250 posts/day, no App Review for our own account | SFW only. Same Meta rules as Instagram |
| **Instagram** | the audience | 100 posts/24h. Trial reels are the only non-follower distribution we get for free |
| **X** | adult allowed with label, no AI-disclosure duty | pay-per-use. Link in bio only. Budget cap mandatory |
| **YouTube Shorts** | 100 uploads/day free, own quota bucket | AI disclosure required on realistic scenes |
| **Reddit** | high intent traffic | subreddit rules bind, not sitewide rules. Needs a human to pick subreddits before any automation |
| **TikTok** | parked | posts stay **private** until the API client passes audit. Not an unattended lane |

### The constraint everyone gets wrong
> "You may not post duplicative or substantially similar posts on one account or
> over multiple accounts you operate"  — X automation rules

Identical copy fanned across platforms is a violation on X **at any volume**,
and Meta's spam policy names "repetitive content" too. So `syndicate.py` does
not take one caption and broadcast it. Each platform gets its own body from a
per-platform variant in the queue entry. If a variant is missing, the lane is
**skipped**, not filled with the default — refuse rather than substitute, the
same rule as everywhere else in this codebase.

### The gate
`check_reel.py` already validates video against Meta's spec. Extend to a
`preflight()` per lane: aspect, duration, size, caption length, disclosure
present, budget available. A lane that fails preflight is skipped and reported,
never silently dropped.

---

## 3. PILLAR TWO — COMMENTING

### What cannot be done
Commenting on other accounts' posts. There is no endpoint. This is settled and
COMPLIANCE.md §1.2 carries the reasoning. Any tool that offers it is doing
browser automation, which is the behaviour the devpolicy bot clause covers and
carries "with or without notice" termination.

### What can be done: `ig_engage.py`
1. Poll `GET /<media-id>/comments` across recent media.
2. Draft a reply per comment.
3. **Write drafts to an approval queue.** A human reads them and marks approve.
4. Post approved replies via `POST /<comment-id>/replies`.

Same consent shape as `publish_queue.py`: the queue is the consent, the schedule
only decides when. This matters more for replies than for posts, because a reply
lands under someone's name and there is no undo that they will not have already
seen.

### The high-value piece: private replies
One DM to a person who commented, within 7 days, one per comment. This is the
**only** way to reach somebody who has not messaged first, and it converts far
better than a public reply because it lands in their inbox.

It requires **Advanced Access** — Business Verification plus App Review. That is
the longest lead time in this whole plan, which is why it is step 1 of the build
order below, ahead of things that feel more urgent.

---

## 4. PILLAR THREE — DMs

Two systems with completely different rules. Do not build them as one.

### 4a. Instagram — inbound only, `ig_dm.py`
- 24h window to respond to any inbound message.
- Human agent tag extends to 7 days.
- Bridge: a private reply opens a conversation; once they answer, the normal
  24h window applies and the funnel can continue.
- Auto-respond only with a first reply that is honest and useful. Anything
  further goes through the approval queue.
- There is no cold DM. Do not let anyone sell you a tool that claims otherwise.

### 4b. Fanvue — the real system, `fanvue_dm.py`
This is where the money is and it is fully sanctioned. From the API policy:
creating chats, sending messages, **sending mass messages**, plus tracking links
for attribution.

Build, in order of value:
1. **Welcome message on new subscriber.** Fires within seconds of a
   subscription. This is the single highest-converting automation on any
   subscription platform and it is one API call on a webhook or a poll.
2. **Tracking links per traffic source** — create one per platform so we can
   finally see which of the six lanes actually produces subscribers. Without
   this, everything else is guesswork.
3. **Segmented mass messages** — using `Insights` (top-spending fans,
   subscriber counts) to segment rather than blasting everyone.
4. **Re-engagement** for lapsed subscribers.

**Rate limit 100 requests / 60 seconds.** One API key per user, header
`X-Fanvue-API-Key`, and a pinned `X-Fanvue-API-Version` — pin it in one place
the way `kie_api.py` pins model ids, so a version bump is a deliberate edit and
never a surprise.

### The disclosure, which is settled and is good news
Fanvue recognises AI creators as a category, allows **15** accounts against 2 for
human creators, and requires an AI tag in the profile bio. Being an AI persona
is not something to hide there — it is a supported product category with its own
tooling. The tag goes in the bio, once, and then the automation is unremarkable.

---

## 5. PILLAR FOUR — ADVERTISING

### One platform, and one written allowance
Meta is the only one of four that permits it, and the permission is explicit:
"When targeting people aged 18 or older, advertisers can run ads that... Contain
content that contains usernames, links to or logos of adult subscription
websites". TikTok, X and Reddit all prohibit the destination outright — see
COMPLIANCE.md §6 for the quotes.

So the paid lane is Meta or nothing.

### Do this before writing any code
**Run one ad by hand in Ads Manager.** Clean creative, 18+ targeting, Fanvue
link. Small budget, one day.

The reason is that Meta permits "links to adult subscription websites" and bans
"logos, screenshots or video clips of known pornographic websites", publishes no
definition of either term, and no list of which sites are which. Whether Fanvue
counts as the first or the second is **not answerable from the documentation**.
One manual test answers it for a few euro. Building `ads_meta.py` first and
discovering the answer afterwards would be spending code and money on a lane
that may not exist.

If it is approved, then build. If it is rejected, the entire paid-advertising
pillar closes and we have lost one day and one small budget instead of a week.

### If it passes: `ads_meta.py`
- `ads_management` at **standard access** is sufficient for our own ad account —
  no App Review needed for this path.
- Hard `--budget` on every call, same as every spending script here.
- **Campaign creation always requires human approval.** Never auto-scale spend
  on performance signals. A runaway loop here spends real money.
- Log every euro to a ledger. See §7.

---

## 6. ORCHESTRATION

Claude orchestrates: writes the scripts, sets the gates, reviews outputs,
researches rules. Gemini operates: runs the commands, reports back. That split
already works for the LoRA pipeline and there is no reason to change it.

**Daily, unattended:**
- `syndicate.py --due` — publish whatever the queue says is due, per lane
- `ig_engage.py --poll` — pull new comments, draft replies into the queue
- `fanvue_dm.py --welcome` — welcome any new subscriber
- `ledger.py --tick` — record spend and revenue

**Daily, needs a human (2 minutes):**
- approve or reject the drafted replies and DMs
- approve tomorrow's posts

**Weekly:**
- `weekly_prep.py` — already exists, extend to cover the new lanes
- attribution report from Fanvue tracking links: which platform produced
  subscribers, not followers

**The rule that does not bend:** anything that speaks in her voice to a specific
person, and anything that spends money, is drafted by automation and released by
a human. Everything else runs unattended. That is not caution — a mass message
to your subscriber list cannot be recalled, and neither can an ad budget.

---

## 7. MONEY

You have spent €100+ and earned nothing, and that is the actual problem this
plan has to solve. So the plan carries a ledger from day one, not after it
starts working.

`ledger.py` — one JSONL, append only, every row is `{date, platform, kind,
eur, note}`. Spend rows from every script that costs money. Revenue rows from
Fanvue Insights (earnings data is an API read). The weekly report is
revenue-minus-spend per platform, with subscribers attributed by tracking link.

**Running costs of this architecture, at one post a day per lane:**
- Bluesky, Threads, Instagram, YouTube, Reddit: **€0**
- X: ~$0.45/month with the link in bio (~$6 if you put it in the post)
- Fanvue API: no fee found
- Meta ads: whatever you set, and only after the manual test passes

The free lanes cover five of six platforms. There is no reason not to run them.

---

## 8. BUILD ORDER

Ordered by lead time and by what unblocks what — not by what is most fun.

**0. Fanvue creator account, KYC, AI tag in bio, API key.**
Blocks every monetising thing in this document. KYC is on you, not the persona:
government ID plus a selfie, and it is not published on the profile. One active
API key per user, issued at fanvue.com/api-keys. Confirm the key actually issues
before anything is built against it — the API policy says access "may be limited
to whitelisted or approved users during rollout".

**1. Start Meta Business Verification and App Review for Advanced Access.**
Longest lead time in the plan, and it is what unlocks private replies — the only
outbound contact channel Instagram has. Start it now so it runs in the
background while everything else is built.

**2. One manual Meta ad test.**
Answers the biggest open question in the plan for a few euro. Do not build
`ads_meta.py` until this comes back approved.

**3. `syndicate.py`, Bluesky lane first, then Threads.**
Both free, neither needs approval, and Bluesky needs no API key at all. This is
the fastest path from here to content going out on more than one platform. Add
Instagram by folding in the existing `ig_publish.py`.

**4. `fanvue_dm.py` — welcome message and tracking links.**
The highest-value automation in the document. Tracking links first, so that from
the first subscriber we know which lane produced them.

**5. `ig_engage.py` — comment replies with an approval queue.**

**6. Private replies — the moment Advanced Access lands.**

**7. `ads_meta.py` — only if step 2 was approved.**

**8. X, Reddit, YouTube lanes.** X needs a budget cap; Reddit needs you to pick
subreddits by hand first and read their individual rules, because sitewide rules
are not what bind there.

TikTok stays parked until someone decides the audit is worth doing.

---

## 9. WHAT THIS PLAN DELIBERATELY DOES NOT INCLUDE

So that nobody adds it later thinking it was an oversight:

- **Cold DMs on Instagram.** No endpoint. Not a risk call.
- **Commenting on other people's posts, by API or by browser.** No endpoint, and
  the browser route is the behaviour the devpolicy bot clause covers.
- **Follow/unfollow, like-bots, engagement pods.** "Don't participate in any
  program that promotes or facilitates the purchase, sale, or exchange of
  'Likes', 'Shares', 'Followers', 'Comments'..." — Meta Developer Policy.
- **Browser automation against Fanvue.** Explicitly barred by their AUP §5 while
  the API grants the same actions. There is a sanctioned door; use it.
- **Adult content on Instagram or Threads.** Platform rule, names AI-generated
  nudity specifically.
- **Auto-scaling ad spend.** Money that moves without a human is how €100
  becomes €1,000.

Everything the original request asked for is in here except cold DMs and
third-party commenting, and those two are absent because the endpoints do not
exist — not because they were judged too risky.
