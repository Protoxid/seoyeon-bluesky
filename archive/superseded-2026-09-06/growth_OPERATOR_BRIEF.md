# OPERATOR BRIEF — growth automation
For Gemini 3.8 Flash, operating. Claude orchestrates. Shade approves.

## 0. HOW TO USE THIS FILE
Read `COMPLIANCE.md` first, then `PLAN.md`, then this. Work top to bottom. Do
not skip a step because a later one looks easier — the order encodes lead times
and dependencies. After each step, report back: what you ran, what it printed,
what you concluded. If a step's acceptance criterion is not met, **stop and
report** rather than improvising a workaround.

Working root: `C:\AI-Project\growth\` for new code,
`C:\AI-Project\personas\seoyeon\` for the existing pipeline.

## 1. THINGS YOU MUST NEVER DO
These are not preferences. Each one has a quoted rule behind it in
COMPLIANCE.md, and several would end the account.

1. **Never send a DM to anyone on Instagram who has not messaged first.** There
   is no endpoint. If you find code or a library claiming to do it, it is doing
   browser automation — do not run it.
2. **Never post a comment on a post we do not own**, by API or by browser.
3. **Never run browser automation against Fanvue.** Their AUP bars it outright
   while the API permits the same actions. Use the API.
4. **Never publish adult or suggestive content to Instagram or Threads.** Meta's
   policy names AI-generated nudity explicitly.
5. **Never spend money without an explicit `--budget` flag** stated by Shade.
6. **Never send a mass message or create an ad campaign without written
   approval** in the queue. Drafts are automation; sending is a human act.
7. **Never delete files.** Move them to `_trash/`. Delete permission was
   refused and `device_bash` cannot delete anyway.
8. **Never paste secrets into a report, a commit, or a prompt.** Keys live in
   gitignored files: `fanvue_key.txt`, `ig_token.txt`, `x_key.txt`, etc.
9. If any platform returns a policy rejection, **stop that lane and report**.
   Do not retry with altered wording to get past a filter.

## 2. STEP 0 — FANVUE ACCOUNT AND API KEY  (Shade does this, you verify)
Blocks everything that earns money.

Shade must: create the creator account, complete KYC (government ID + selfie —
his, not the persona's; it is not shown on the profile), mark the account as an
AI creator so the **AI tag appears in the profile bio**, set the public profile
SFW (no implied nudity in avatar, banner or bio), and issue an API key at
`https://www.fanvue.com/api-keys`.

Your job once he has: save the key to `growth\fanvue_key.txt`, add that filename
to `.gitignore`, and verify with a single read-only call.

```powershell
cd C:\AI-Project\growth
python fanvue_api.py --whoami
```

ACCEPTANCE: prints the creator handle and subscriber count. Header names are
`X-Fanvue-API-Key` and `X-Fanvue-API-Version` (pin the version date in ONE
constant, the way `kie_api.py` pins model ids). Rate limit is 100 requests per
60 seconds — build the limiter into the client now, not later.
IF THE KEY WILL NOT ISSUE: report it. The API policy says access "may be limited
to whitelisted or approved users during rollout". That is a real possibility and
it changes the plan; do not work around it.

## 3. STEP 1 — META BUSINESS VERIFICATION  (Shade does this, you track)
Start it immediately; it runs for days in the background.

Needed for **Advanced Access**, which is what unlocks private replies — the only
way Instagram lets us message someone who has not messaged us. Requires Business
Verification plus App Review for `instagram_manage_comments` + `pages_messaging`
+ the Human Agent feature.

Your job: keep a status line in `growth\STATUS.md` with the date submitted and
the current state. Nothing to build until it lands.

## 4. STEP 2 — ONE MANUAL META AD  (Shade does this, you record the result)
DO NOT BUILD `ads_meta.py` BEFORE THIS COMES BACK.

Meta permits "links to... adult subscription websites" at 18+ targeting, and
bans "logos, screenshots or video clips of known pornographic websites", and
publishes no definition of either. Whether Fanvue is the first or the second is
unanswerable from the docs. One small manual ad answers it.

Setup: clean SFW creative, **18+ targeting is mandatory**, Fanvue link as the
destination, one day, small budget.

Record in `growth\STATUS.md`: approved or rejected, and the exact rejection text
if rejected. That one line decides whether the entire paid pillar exists.

## 5. STEP 3 — `syndicate.py`  (you build)
Start with **Bluesky**, because it needs no API key, no approval and no fee.

Design, non-negotiable:
- Reads the existing `queue.jsonl` shape. Each entry carries a **per-platform
  body**. A lane with no body for it is **SKIPPED and reported**, never filled
  with a default. X prohibits "duplicative or substantially similar posts...
  over multiple accounts you operate", so identical copy across lanes is a
  violation, not a shortcut.
- `preflight()` per lane before anything is sent: aspect, duration, size,
  caption length, AI disclosure present, budget available. Reuse
  `check_reel.py`'s approach — it already validates video against Meta's spec.
- `--dry-run` prints exactly what each lane would send and spends nothing.
- Every lane writes to `ledger.py`.

Order: Bluesky → Threads (250 posts/day, free, SFW) → fold in the existing
`ig_publish.py` as the Instagram lane.

ACCEPTANCE: `python syndicate.py --dry-run --due` prints one block per lane with
the exact body, and refuses any lane missing a body or a disclosure.

## 6. STEP 4 — `fanvue_dm.py`  (you build)
Highest-value automation in the plan.

1. **Tracking links first.** One per platform, via the Tracking Links endpoints.
   Without these we cannot tell which lane produces subscribers, and every later
   decision is guesswork.
2. **Welcome message on new subscriber.** Poll subscribers, detect new, send one
   message. Idempotent — record who has been welcomed so a restart never
   double-sends.
3. Mass messages and re-engagement come later and **always** through the
   approval queue.

ACCEPTANCE: a new test subscriber receives exactly one welcome message, and
re-running the script sends nothing.

## 7. STEP 5 — `ig_engage.py`  (you build)
Poll `GET /<media-id>/comments`, draft a reply per new comment, write drafts to
an approval queue. Only approved drafts post, via `POST /<comment-id>/replies`.

ACCEPTANCE: drafts appear in the queue; nothing posts without an approve flag.

## 8. REPORTING
After every step, append to `growth\STATUS.md`:
```
## <date> — <step>
ran:        <exact command>
printed:    <the last 10 lines>
conclusion: <one sentence>
blocked by: <or "nothing">
```
Report to Claude before starting the next step. If something contradicts
COMPLIANCE.md, COMPLIANCE.md is not automatically right — it was researched on
5 Sep 2026 and platforms change. Report the contradiction; do not silently
follow either one.
