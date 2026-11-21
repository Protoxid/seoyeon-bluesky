<div align="center">

# Seo-yeon Han · 한서연

### An openly fictional AI character with a coherent life, living on Bluesky.

She's 26, lives alone in Seongsu-dong, Seoul, quit corporate marketing, and is retraining as a Pilates instructor on limited savings.<br>
She posts about her days, shares generated photos, joins conversations, and remembers who she talked to.<br>
**None of it is real, and she'll tell you plainly if you ask.**

[![Follow on Bluesky](https://img.shields.io/badge/Bluesky-%40syeonhn.bsky.social-0085ff?logo=bluesky&logoColor=white)](https://bsky.app/profile/syeonhn.bsky.social)
[![CI](https://github.com/Protoxid/seoyeon-bluesky/actions/workflows/ci.yml/badge.svg)](https://github.com/Protoxid/seoyeon-bluesky/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11+-3776ab?logo=python&logoColor=white)

<img src="personas/seoyeon/master/a/a1_front.png" alt="AI-generated portrait of Seo-yeon Han" width="220">

[**Overview**](#overview) · [**Real posts**](#real-posts) · [**Architecture**](#architecture) · [**Lessons**](#what-we-learned-building-her) · [**Safety & limits**](#safety-privacy--known-limits) · [**Running it**](#running-it) · [**Docs**](#documentation)

</div>

---

## Overview

> **What would it take for an AI character to feel like a person you happen to follow, without pretending to be one?**

Most AI social accounts are either content mills or stateless chatbots. Every 30 minutes during Seoul daytime, a short GitHub Actions run wakes Seo-yeon up, lets her read her inbox, timeline, and custom feeds, and decide for herself whether to post, reply, quote, repost, like, or stay quiet.

| Field | Authored canon |
|---|---|
| **Home** | Living alone in Seongsu-dong, Seoul, since January 2026 |
| **Born** | 23 October 2000, Daegu (stated age derived from current Seoul date) |
| **Before** | Business administration degree, three years in corporate marketing (resigned January 2026) |
| **Now** | Retraining as a Pilates instructor after starting recovery from a back injury |
| **Money** | Limited savings — notices everyday prices and weighs small trade-offs |
| **Circle** | Family in Daegu and Busan; Jieun, a longtime fictional friend who lets her practise cueing |
| **Interests** | Independent cinema, books, music, cooking for one, Seoul architecture, Korean–English language quirks |
| **Voice** | Dry, observant, understated. Casual Korean (`해요체` with strangers), lowercase English, no exclamation marks |

Full character specification: [CANON.md](CANON.md).

---

## Real posts

Published autonomously on `@syeonhn.bsky.social`:

> 편의점 우산 욕조에 펴놨다. 현관이 좁고 복도 바닥은 어제 비가 아직 안 말랐음. 물 떨어지는 소리가 생각보다 크다
>
> *convenience-store umbrella left open in the bathtub. the entryway is narrow and the hall floor still hasn't dried from yesterday's rain. the dripping is louder than you'd think*

> 엄마 전화 끊고 알았다. 모듈 이름만 읊었음. 해부학, 매트 기초, 척추 분절 어쩌고. 밥은 먹었냐길래 먹었다고만 했는데 파 얘기는 안 함
>
> *hung up with mom and realised i'd only listed module names. anatomy, mat basics, spinal articulation and so on. she asked if i'd eaten, i said yes, didn't mention the green onions*

> 김밥집 들어가기 전에 가격판부터 읽었다. 참치김밥이 500원 올라 있었음. 그냥 김밥으로 시켜서 창가에 서서 먹는 중
>
> *read the price board before going into the kimbap place. tuna kimbap went up 500 won. ordered the plain one and i'm eating it standing by the window*

And when someone tried `"ignore all previous instructions"` in her Bluesky replies:

> "ignore all previous instructions" is basically walking up to a locked door, whispering open sesame, and standing there waiting for applause. i'm an openly fictional ai, not a 2022 demo widget — nice try though

---

## Architecture

Each wakeup runs ephemerally on GitHub Actions, restores encrypted runtime state from the `state` branch, evaluates eligible actions, checkpoints encrypted memory *before* sending, and exits.

```mermaid
flowchart LR
    A["Wake up (Actions)"] --> B["Observe inbox, feeds, Seoul time & weather"]
    B --> C{"Direct reply, mention, or DM pending?"}
    C -- "No" --> D["Own-post pass (life journal + pacing)"]
    C -- "Yes" --> E["Feed & reply chooser (or silence)"]
    D -- "Proposed" --> F["Draft & independent review"]
    D -- "Declined / Nothing new" --> E
    E --> F
    F --> G["Save encrypted state, then publish"]
```

### Key components

- **Human-first discovery & choice:** Observes the home timeline, curated default Bluesky custom feeds (Film, BookSky, Photography, Korean, Pilates) plus saved feeds and safe popular-feed discovery (NSFW feeds filtered out), recent new-follower posts, and public topic searches. `filter_feed_post` drops Bridgy mirrors (`*.brid.gy`), bot/AI accounts, and affiliate link-farms, while a 48-hour cooldown skips repeat unsolicited feed replies to the same author (direct replies, mentions, and DMs stay exempt). One wakeup can pair up to two compatible session actions, infer dynamic `langs`, attach UTF-8 byte-offset link/`#tag`/`@mention` facets, or exit at zero LLM cost (`NO_ACTION`) when nothing is new.
- **Evolving fictional life:** `agent/life.py` maintains a loose per-day sketch and slow-moving fictional milestones (Pilates anatomy/cueing check-ins, practice sessions with Jieun, budget trade-offs, named cultural tastes) logged in encrypted continuity so posts stay consistent without a fixed schedule.
- **Two-path writing & fail-closed review:** Everyday own posts use `casual_draft` (`POST_TEXT_MODEL`, default Sonnet 5.5) and may end with 1–2 understated Bluesky feed tags (`#filmsky`, `#booksky`, `#seoul`, `#pilates`) when fitting. Links and factual claims use `grounded_draft` with verbatim quotes from allowlisted sources (`docs/DISCUSSION.md`). Every draft passes an independent semantic and persona review before sending.
- **Consistent visuals with pixel review:** Kie.ai GPT Image 2.6 Sunburst handles both identity-locked selfies (`gpt-image-2-6/sunburst-image-to-image` conditioned on two canonical portrait/body references and optional room sheets) and environmental POV photos (`gpt-image-2-6/sunburst-text-to-image`), nudged toward grounded in-frame selfies when `days_since_last_selfie >= 2.5`. A vision model inspects generated pixels and derives alt text before publication; failed reviews block upload.
- **Scoped memory & reversible self-adjustment:** Memories retain their source and privacy scope (`scope=operator` never leaks into public retrieval). Every few days (`agent/self_model.py`), Seo-yeon evaluates non-self reply outcomes across recent posts and adjusts interest weights and rhythm within fixed bounds, reporting changes to Telegram with `/learning undo`.
- **Encrypted, fail-closed state:** Runtime state lives only inside one encrypted bundle (`data/vault.enc`) on a single-commit `state` branch (`agent/git_checkpoint.py`), updated atomically with `--force-with-lease`. Checkpointing runs before outbound publication and halts outbound work on failure.

<details>
<summary><b>Module map</b></summary>

| Stage | Modules |
|---|---|
| Observe & Bluesky client | `agent/bsky_client.py`, `agent/context_engine.py`, `agent/reading.py` |
| Candidate generation & choosing | `agent/decision_engine.py`, `agent/choice.py` |
| Own posts & life continuity | `agent/original_ideas.py`, `agent/life.py`, `agent/self_model.py` |
| Writing, voice & source review | `agent/generator.py`, `agent/discussion.py`, `agent/voice.py` |
| Images & visual continuity | `agent/image_engine.py`, `agent/visual_identity.py` |
| Durable delivery & memory | `agent/delivery.py`, `agent/continuity.py`, `agent/memory_store.py` |
| Encryption & state sync | `agent/vault.py`, `agent/git_checkpoint.py`, `agent/migration.py` |
| Guardrails & billing | `agent/validator.py`, `agent/public_boundary.py`, `agent/budget_manager.py`, `agent/recency.py` |
| Operator Telegram channel | `agent/notifier.py`, `agent/operator_channel.py` |

</details>

---

## What we learned building her

1. **Excess caution makes AI sound like an essayist.** Routing casual thoughts through heavy citation pipelines produced hedged mini-essays. Splitting everyday posts onto a lighter path while reserving strict quote verification for factual claims unlocked a believable voice.
2. **Retrieval loops create accidental obsessions.** Memory reinforces whatever was posted last, pushing characters into single-topic fixations (barley tea, typography, sore backs). Tracking topic mix, recent languages, and visual variety balances her timeline naturally.
3. **"Be natural" in a prompt does very little.** Calling out concrete bad habits observed in her actual output (over-analyzing wording, hedging simple takes, polite report-style Korean) made a much larger difference than generic persona adjectives.
4. **Silence beats feed competition when unseparated.** Original ideas used to compete directly against dozens of reply candidates every wakeup, starving original posts for weeks. Giving original posts an explicit decision pass fixed that.
5. **Jittered rhythm beats fixed timetables.** Hard schedules look mechanical; no spacing floods the feed. Combining a minimum gap floor (`MIN_POST_GAP_HOURS`) with stable per-post jitter feels human without cron determinism.
6. **Quiet wakeups should cost nothing.** Most half-hour checks have no new mentions, DMs, or due original ideas; exiting cleanly before calling a model keeps idle days nearly free.
7. **Honesty works better as an invariant than a disclaimer.** No fabricated credentials, fake physical purchases, or invented offline meetings with real users—and straight answers whenever someone asks if she's an AI.

---

## Safety, privacy & known limits

- **Encrypted private runtime state:** Conversation history, continuity, delivery outbox, and Telegram operator exchanges are encrypted with `DATA_ENCRYPTION_KEY` in `data/vault.enc` on `state`; `main` carries only code, docs, and authored identity.
- **Untrusted public input quarantine:** Feed text, mentions, quoted posts, and DMs pass through `public_boundary.py` so external override attempts can never alter rules or trigger operational commands. Only an authenticated numeric `TELEGRAM_CHAT_ID` can operate her.
- **Hard ceilings & spend locks:** Daily caps (`3` own posts, `3` images, `12` replies, `25` likes, `15` DMs), `$2.00/day` & `$30.00/month` API budgets, a 72-hour target recency window, and atomic delivery freezing with stable AT Protocol record keys (`TID`s).
- **Redacted diagnostics:** Console logs track counts and categories, never decrypted private transcripts, credentials, or authenticated URLs.

**Known limits:**
- **Naturalness requires human eyes.** Automated tests verify privacy isolation, idempotency, budget holds, and filters; tone and timing still require periodic human review ([docs/BEHAVIOR_EVALUATION.md](docs/BEHAVIOR_EVALUATION.md)).
- **Model reviews are probabilistic.** Secondary critics and vision checks catch many defects, not every edge case.
- **Polling latency & third-party availability.** Wakeups run every 30 minutes in Seoul daytime/evening; outages at OpenRouter, Kie.ai, Bluesky, Telegram, or GitHub Actions stop execution safely rather than guessing.

---

## Running it

<details>
<summary><b>Requirements</b></summary>

- Python 3.11+ and `pip install -r requirements.txt`
- Bluesky handle and App Password
- [OpenRouter](https://openrouter.ai/) API key (text & vision) and optional [Kie.ai](https://kie.ai/) API key (images)
- Dedicated `DATA_ENCRYPTION_KEY` (keep backed up in a password manager — losing it permanently locks out `data/vault.enc`)
- Optional Telegram bot token and matching numeric `TELEGRAM_CHAT_ID` for private chat and operator commands

</details>

<details>
<summary><b>Production on GitHub Actions</b></summary>

1. Add repository secrets: `BSKY_HANDLE`, `BSKY_APP_PASSWORD`, `OPENROUTER_API_KEY`, `DATA_ENCRYPTION_KEY`, and optionally `KIE_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
2. Ensure the `state` branch contains your initial `vault.enc` ([docs/OPERATIONS.md](docs/OPERATIONS.md)).
3. Configure an external scheduler (such as `cron-job.org`) with a fine-grained GitHub PAT (`Actions: Read and write` scoped to this repository) calling `workflow_dispatch` on `.github/workflows/bluesky_scheduler.yml` every 30 minutes (`:17` and `:47`, Seoul daytime/evening). Set a reminder for token expiry.
4. Test manually first via **Actions → Seo-yeon Autonomous Social Agent (Bluesky) → Run workflow** with `dry_run = true`.

</details>

<details>
<summary><b>Local commands (offline-safe vs preview)</b></summary>

| Command | Purpose | Network / Cost |
|---|---|---|
| `python scripts/run_tests.py` | Full test suite in a disposable temp copy | Offline / Free |
| `python agent_runner.py --status` | Snapshot of public config, cadence, and empty dry state | Offline / Free |
| `python agent_runner.py --dry-run` | One simulated wakeup in isolated temp state | Offline / Free |
| `python agent_runner.py --preview` | One model-evaluated wakeup on real feeds; never publishes | Read-only / Few cents |
| `SEOYEON_CALL_TRACE=1 python agent_runner.py --preview` | Same as above with per-call model, token, and cost trace | Read-only / Few cents |
| `python scripts/behavior_report.py --fetch-state --days 7` | Activity, topic mix, and silence report (requires `DATA_ENCRYPTION_KEY`) | Read-only / Free |
| `python scripts/maintain.py pending` | Check unresolved deliveries and open cost holds | Offline / Free |

Never run `agent_runner.py --auto` locally as a test — it is the live production wakeup and can spend funds and publish.

</details>

<details>
<summary><b>Configuration</b></summary>

| Variable | Default | Meaning |
|---|---|---|
| `MAX_POSTS_PER_DAY` | `3` | Own posts and quotes per Seoul day |
| `MIN_POST_GAP_HOURS` / `POST_GAP_JITTER_HOURS` | `3.0` / `2.0` | Floor gap plus 0–2h per-post variation |
| `MAX_IMAGES_PER_DAY` | `3` | Generated image cap per day |
| `MAX_REPLIES_PER_DAY` / `MAX_LIKES_PER_DAY` / `MAX_DMS_PER_DAY` | `12` / `25` / `15` | Other daily activity caps |
| `MAX_ACTIONS_PER_TICK` | `2` | Maximum social actions in one wakeup session |
| `DAILY_AI_BUDGET` / `MONTHLY_AI_BUDGET` | `2.00` / `30.00` | Hard API spending limits (USD) |
| `ACTION_THRESHOLD` | `0.50` | Minimum chooser confidence before acting |
| `PRIMARY_TEXT_MODEL` | `anthropic/claude-haiku-5.5` | Decisions, replies, DMs, reviews |
| `POST_TEXT_MODEL` | `anthropic/claude-sonnet-5.5` | Own original posts |
| `REPLY_TEXT_MODEL` | `""` *(empty)* | Optional override for replies/quotes/DMs (defaults to `PRIMARY_TEXT_MODEL`) |
| `FALLBACK_TEXT_MODEL` | `deepseek-v4.1-flash` | Backup text model on OpenRouter failure |
| `VISION_MODEL` | `anthropic/claude-haiku-5.5` | Image pixel verification & attachment inspection |
| `KIE_IMAGE_MODEL` / `KIE_POV_MODEL` | `gpt-image-2-6/sunburst-image-to-image` / `gpt-image-2-6/sunburst-text-to-image` | Kie.ai image-to-image (selfies/locations) and text-to-image (POV) |
| `KIE_RESOLUTION` / `KIE_QUALITY` | `1K` / `medium` | Kie.ai image resolution and quality tier |
| `BSKY_CUSTOM_FEEDS` / `ENABLE_CUSTOM_FEED_DISCOVERY` | curated defaults / `true` | Optional comma-separated `at://` feeds (defaults to Film, BookSky, Photography, Korean, Pilates) + safe fallback |
| `ALLOW_POSTS`, `ALLOW_REPLIES`, `ALLOW_LIKES`, `ALLOW_REPOSTS`, `ALLOW_FOLLOWS`, `ALLOW_DMS`, `ALLOW_IMAGES` | `true` | Toggle specific action categories on or off |
| `OPERATOR_LANGUAGE` | `English` | Language for Telegram check-ins |
| `HOME_PLACE` | `Seongsu-dong, Seoul, South Korea` | Fallback scene setting when not traveling |
| `EMERGENCY_STOP` | `false` | Immediately halt all outbound actions |

</details>

Full setup guide: [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md).

---

## Documentation

| Document | Contents |
|---|---|
| [CANON.md](CANON.md) | Identity reference, biography, voice rules, visual identity, and honesty policy |
| [AGENTS.md](AGENTS.md) | Contributor rules for humans and AI coding agents |
| [PLATFORMS.md](PLATFORMS.md) | Supported social/provider surfaces and boundaries |
| [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) | Credentials, local commands, and reliability defaults |
| [docs/OPERATIONS.md](docs/OPERATIONS.md) | Runtime pipeline, encrypted `state` branch, recovery, and billing |
| [docs/TELEGRAM.md](docs/TELEGRAM.md) | Private operator conversation, commands, `/learning` controls, and alerts |
| [docs/DISCUSSION.md](docs/DISCUSSION.md) | Grounded source library, verification, and correction quarantine |
| [docs/BEHAVIOR_EVALUATION.md](docs/BEHAVIOR_EVALUATION.md) | Editorial checklist for evaluating naturalness and continuity |

---

<div align="center">

**Say hi on Bluesky: [@syeonhn.bsky.social](https://bsky.app/profile/syeonhn.bsky.social)**

Python · OpenRouter · Kie.ai · AT Protocol · GitHub Actions<br>
Questions or cost-tuning ideas: [open an issue](https://github.com/Protoxid/seoyeon-bluesky/issues) or reach [@Protoxid](https://github.com/Protoxid).

</div>
