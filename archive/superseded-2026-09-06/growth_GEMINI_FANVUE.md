# OPERATOR TASK — Fanvue setup and automation
For Gemini 3.8 Flash. Standalone: everything needed is in this file.
Claude orchestrates and reviews. Shade owns the account and approves.
Account: @syeon.hn on Fanvue. Persona: Seo-yeon Han, 24, Seoul.

═══════════════════════════════════════════════════════════════════
## 0. THE BOUNDARY — READ THIS BEFORE ANYTHING ELSE
═══════════════════════════════════════════════════════════════════

### 0.1 YOU MUST NOT TOUCH FANVUE.COM IN A BROWSER. EVER.
Fanvue's Acceptable Use Policy bars automated access to their website:

> "Do not use any automated program, tool or process (such as web crawlers,
> robots, bots, spiders, and automated scripts) to access Fanvue or any server,
> network or system associated with Fanvue"
> — https://legal.fanvue.com/acceptable-use-policy §5

> "Create 'bot' Accounts or any Account which is controlled by other automated
> means" — prohibited. https://legal.fanvue.com/terms-conditions §2.2

Their **API** is the sanctioned door and it grants the same actions. So:
- Anything on the Fanvue website = **Shade does it by hand.**
- Anything programmatic = **you do it through the API only.**

If you catch yourself about to open fanvue.com in a browser tool, stop. That
single action can end the account and every euro in it.

### 0.2 YOU MUST NOT HANDLE IDENTITY DOCUMENTS
KYC requires Shade's government ID and a selfie liveness check. Do not ask for
them, do not receive them, do not store them, do not look at them. That step is
his alone. Your job starts after he tells you it passed.

### 0.3 OTHER HARD RULES
1. Never send a message to a real person without an approved queue entry.
2. Never spend money without an explicit `--budget` given by Shade.
3. Never delete a file. Move it to `_trash\`. Deletion is refused on this
   machine anyway.
4. Never print an API key into a report, a log, a commit or a prompt. Keys live
   in gitignored `*.txt` files and are read at runtime.
5. If any step's acceptance criterion is not met, **stop and report**. Do not
   improvise a workaround. A wrong guess here costs real money.
6. If something you read contradicts `COMPLIANCE.md`, report the contradiction.
   Do not silently follow either one — that file was researched on 5 Sep 2026
   and platforms change.

═══════════════════════════════════════════════════════════════════
## 1. CONTEXT YOU NEED
═══════════════════════════════════════════════════════════════════

Read these first, in this order:
- `C:\AI-Project\growth\COMPLIANCE.md` — every platform rule, quoted, with URLs
- `C:\AI-Project\growth\PLAN.md` — the architecture
- `C:\AI-Project\personas\seoyeon\CLAUDE.md` — persona canon
- `C:\AI-Project\personas\seoyeon\kie_api.py` — the house style for an API
  client. Copy its shape: pinned constants, cost function, explicit budget cap,
  and comments that say *why*.

**Facts about the Fanvue API, verified 5 Sep 2026 from
https://legal.fanvue.com/api-policy and https://api.fanvue.com/docs/welcome:**
- Auth header: `X-Fanvue-API-Key`
- Version header: `X-Fanvue-API-Version`, value is a date `YYYY-MM-DD`
- Rate limit: **100 requests per 60 seconds per API key**
- Only **one active API key per user** at a time
- Key is issued at https://www.fanvue.com/api-keys, requires KYC complete
- Permitted (quoted from §4): listing chats, retrieving chat messages, creating
  chats, sending messages, **sending mass messages**, deleting messages,
  creating posts, reading followers and subscribers, reading earnings data and
  top-spending fans, multipart media upload, vault folders, and
  **creating/listing/deleting tracking links**
- Caveat, quoted: "API access is controlled and may be limited to whitelisted or
  approved users during rollout." If the key does not issue, that is a real
  outcome — report it, do not work around it.

**Fanvue content rules that constrain what you build:**
- AI-generated content is **allowed** and AI creators are a recognised category
  (15 accounts allowed vs 2 for human creators), but disclosure is mandatory:
  "All AI-generated media must include a clear and prominent disclosure" and
  "Every AI creator has an AI tag displayed in their profile bio."
- The **public** surface must be SFW: profile picture, banner, intro video and
  public bio must have no "Nudity, implied nudity, or strategic covering" and no
  age-baiting language ("just turned 18", "barely legal", "teen"). First offence
  removes the account from Discover.
- Paid/subscriber content may be intimate but must be marked 18+.
- **Never** promote an external payment link or take payment off-platform.
  Creator Terms §5. Breach = "immediate account suspension, payout withholding,
  and possible permanent removal."

═══════════════════════════════════════════════════════════════════
## 2. WHAT SHADE DOES BY HAND (you only verify and track)
═══════════════════════════════════════════════════════════════════

Write these into `C:\AI-Project\growth\STATUS.md` as a checklist and update it
as he reports each one. Do not attempt any of them yourself.

- [ ] KYC: government ID + selfie liveness. Provider is Ondato.
- [ ] Mark the account as an **AI creator** so the AI tag shows in the bio.
- [ ] Set profile picture, banner and public bio — all SFW (copy in §3).
- [ ] Declare whether content is explicit, at signup.
- [ ] Tax and banking details; choose a payout method (bank transfer is the
      universal one; no PayPal).
- [ ] Set subscription price and any free-trial offer.
- [ ] Issue the API key at fanvue.com/api-keys and save it to
      `C:\AI-Project\growth\fanvue_key.txt`.

**Payout facts to tell him once, so there are no surprises:** 80% creator rate;
pending period 7 days, extendable to 28; payout initiated within 10 business
days of request; balances untouched for 12 months are classified dormant.

═══════════════════════════════════════════════════════════════════
## 3. DELIVERABLE 1 — THE PROFILE COPY PACK  (no API needed, do this first)
═══════════════════════════════════════════════════════════════════

Write `C:\AI-Project\growth\fanvue_profile.md` containing text Shade can paste.
This is writing, not code, and it is not blocked on anything.

Required contents:

**a) Public bio, under 150 characters.** Must contain: who she is, where she is,
and **the AI disclosure**. It must NOT contain age-baiting language, and must
not read as a disclaimer bolted onto the end — the disclosure is part of her
identity, not an apology for it. Draft three options.

**b) Welcome DM**, the message a new subscriber receives within seconds. Under
400 characters. Warm, specific, in her voice — not a sales pitch. It should ask
one question, because a reply opens a conversation and a conversation is what
converts. Draft three options.

**c) Profile picture and banner: name the files, do not generate them.**
Search `C:\AI-Project\personas\seoyeon\content\` and `master\` for existing
renders that are unambiguously SFW and on-canon. Propose one avatar and one
banner **by filename**, and say why each. If nothing suitable exists, say so —
do not generate anything, and do not spend money.

**d) A one-line content promise** for the subscription page: what someone gets
for the money, in her voice, concretely.

Then STOP and report. Shade reviews this copy before it goes anywhere near the
profile. He writes the final wording by hand — your drafts are the starting
point, not the answer.

═══════════════════════════════════════════════════════════════════
## 4. DELIVERABLE 2 — `fanvue_api.py`  (blocked until the key exists)
═══════════════════════════════════════════════════════════════════

A thin, honest client. Model it on `kie_api.py`.

Must have:
- `load_key()` reading `growth\fanvue_key.txt`, refusing on a placeholder value
- `API_VERSION` as **one pinned constant** with a comment saying that bumping it
  is a deliberate act, never a default
- A rate limiter enforcing 100 requests / 60 seconds, sliding window. Do not
  rely on the server to reject you — a 429 storm looks like abuse.
- `--dry-run` on every command that writes, printing the exact request body and
  sending nothing
- Every write logged to `growth\ledger.jsonl` as
  `{ts, surface, action, target, note}`

First command to implement, read-only:
```
python fanvue_api.py --whoami
```
ACCEPTANCE: prints the creator handle, subscriber count and current balance.
Nothing is written. If it 401s, the key is wrong — report, do not retry in a
loop.

**Do not implement any send-message command in this deliverable.** Read-only
first, reviewed, then writes.

═══════════════════════════════════════════════════════════════════
## 5. DELIVERABLE 3 — TRACKING LINKS  (do this before any traffic arrives)
═══════════════════════════════════════════════════════════════════

Create one tracking link per traffic source, via the Tracking Links endpoints:
`instagram`, `x`, `bluesky`, `threads`, `reddit`, `youtube`.

This is the single highest-leverage thing you will build, and it has a deadline
that is not negotiable: **a subscriber who arrives before the links exist is
unattributable forever.** Without this, every decision about where to spend
effort is a guess.

```
python fanvue_api.py --make-links --dry-run
python fanvue_api.py --make-links
```
ACCEPTANCE: six links exist, each printed with its source name, and each written
to `growth\links.json`. Shade puts the right one in each platform's bio.

═══════════════════════════════════════════════════════════════════
## 6. DELIVERABLE 4 — WELCOME MESSAGE  (the first thing that writes)
═══════════════════════════════════════════════════════════════════

```
python fanvue_dm.py --welcome --dry-run
python fanvue_dm.py --welcome
```

Behaviour:
- Poll subscribers, diff against `growth\welcomed.json`
- Send **exactly one** welcome message per new subscriber
- Record the send BEFORE returning, so a crash mid-run never double-sends
- **Idempotent**: running it twice in a row must send nothing the second time.
  Prove this in your report by running it twice and showing the second run's
  output.
- Text comes from the approved copy in `fanvue_profile.md`, read from the file
  at runtime — never hardcoded in the script, so changing the message is an edit
  to copy, not to code

ACCEPTANCE: the second consecutive run sends zero messages and says so.

**Mass messages are NOT in scope.** Do not build them. They come later, through
an approval queue, and they cannot be recalled once sent.

═══════════════════════════════════════════════════════════════════
## 7. REPORTING
═══════════════════════════════════════════════════════════════════

After every deliverable, append to `C:\AI-Project\growth\STATUS.md`:

```
## <date> — <deliverable>
ran:        <exact command>
printed:    <last 10 lines of output>
conclusion: <one sentence>
blocked by: <or "nothing">
```

Then stop and report to Claude before starting the next one. Do not chain
deliverables unattended — each one is reviewed before the next begins.

Order: §3 (copy, do now) → §2 checklist tracking → §4 → §5 → §6.
