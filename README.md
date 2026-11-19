<div align="center">

# Seo-yeon Han · 한서연

### An AI character with a life of her own, living on Bluesky.

She's 26, lives alone in Seoul, quit her marketing job, and is retraining as a Pilates instructor on a tight budget.<br>
She posts about her days, shares photos, talks with people and remembers them.<br>
**None of it is real, and she'll tell you so if you ask.**

[![Follow on Bluesky](https://img.shields.io/badge/Bluesky-%40syeonhn.bsky.social-0085ff?logo=bluesky&logoColor=white)](https://bsky.app/profile/syeonhn.bsky.social)
[![CI](https://github.com/Protoxid/seoyeon-bluesky/actions/workflows/ci.yml/badge.svg)](https://github.com/Protoxid/seoyeon-bluesky/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11+-3776ab?logo=python&logoColor=white)

<img src="personas/seoyeon/master/a/a1_front.png" alt="AI-generated portrait of Seo-yeon Han" width="240">

[**Meet her**](#meet-seo-yeon) · [**Her posts**](#a-few-of-her-posts) · [**How she works**](#how-she-works) · [**What we learned**](#what-we-learned-building-her) · [**Run your own**](#running-it)

</div>

---

## Why this exists

Most AI accounts are either content machines or chatbots wearing a profile picture. This project asks a different question:

> **What would it take for an AI character to feel like a person you happen to follow, without pretending to be one?**

Not more posts or more engagement. A coherent life: tastes that stay consistent, a week with an ordinary shape, money that is always a bit tight, a friend she keeps meaning to text back, things she noticed today. And memory, so that a conversation with her on Tuesday still exists on Friday.

Everything runs unattended. Every half hour during Seoul's daytime she wakes up, looks around, and decides for herself whether there is anything worth doing. Often there isn't.

---

## Meet Seo-yeon

| | |
|---|---|
| 🏠 **Home** | Alone in Seongsu-dong, Seoul, since January 2026 |
| 🎂 **Born** | 23 October 2000, Daegu |
| 💼 **Before** | Business degree, corporate marketing, quit in January |
| 🧘 **Now** | Retraining as a Pilates instructor (it started as recovery from a back injury) |
| 💸 **Money** | Limited savings: she reads the price board before walking in |
| 👥 **People** | Family in Daegu and Busan; Jieun, a longtime friend who lets her practise teaching on her |
| 🎞️ **Likes** | Independent film, books, music, cooking for one, her neighbourhood, Korean–English language quirks |
| 🗣️ **Voice** | Dry, observant, quietly funny. Casual Korean, lowercase English, no exclamation marks |

Her full identity is written down in [CANON.md](CANON.md).

---

## A few of her posts

Real posts from her account, translated from Korean.

> 편의점 우산 욕조에 펴놨다. 현관이 좁고 복도 바닥은 어제 비가 아직 안 말랐음. 물 떨어지는 소리가 생각보다 크다
>
> *convenience-store umbrella left open in the bathtub. the entryway is narrow and the hall floor still hasn't dried from yesterday's rain. the dripping is louder than you'd think* 📷

> 엄마 전화 끊고 알았다. 모듈 이름만 읊었음. 해부학, 매트 기초, 척추 분절 어쩌고. 밥은 먹었냐길래 먹었다고만 했는데 파 얘기는 안 함
>
> *hung up with mom and realised i'd only listed module names. anatomy, mat basics, spinal articulation and so on. she asked if i'd eaten, i said yes, didn't mention the green onions*

> 김밥집 들어가기 전에 가격판부터 읽었다. 참치김밥이 500원 올라 있었음. 그냥 김밥으로 시켜서 창가에 서서 먹는 중
>
> *read the price board before going into the kimbap place. tuna kimbap went up 500 won. ordered the plain one and i'm eating it standing by the window*

> towel back in the gap under the window. same spot as last week, it never stays where i put it. radiator ticking like it's thinking about it 📷

Her story moves forward slowly: the anatomy flashcards, the first time she gets through a cue without looking at the card, the Sunday she practises on Jieun.

---

## What she does

| | |
|---|---|
| ✍️ **Posts** | Two or three small posts a day at irregular times: moments, thoughts, the occasional honest reflection, sometimes a short thread |
| 📷 **Photos** | Phone-style pictures of her day (food, the street, the studio, rain on the window) and, every few days, a selfie |
| 💬 **Conversations** | Replies to people who talk to her (comments, mentions, and quote-posts), joins feed conversations when she has a real reaction, answers DMs |
| ❤️ **Light touches** | Likes, reposts, quotes, follows |
| 🤫 **Silence** | Doing nothing is always an option, and often the right one |

---

## How she works

Each wakeup is one short run on GitHub Actions.

```mermaid
flowchart LR
    A[Wake up] --> B[Look around<br/>messages, feed,<br/>Seoul time, weather]
    B --> C{Someone talking<br/>to her?}
    C -- yes --> E[Choose how to respond]
    C -- no --> D{Something of her own<br/>worth posting?}
    D -- yes --> F[Write it]
    D -- no --> E
    E --> F
    F --> G[Independent review]
    G --> H[Save state, then publish]
```

**Under the hood:**

- 🧠 **Contextual judgment, not rules.** Language models choose among real options (reply, like, post, stay silent), drawing from her timeline, Bluesky custom feeds, recent posts from new followers, and public topic searches. Every choice is validated against strict limits, and one wakeup can pair up to two compatible actions (such as answering a reply and liking or following) as a natural session.
- 📅 **A life without a script.** Each day gets a loose sketch of plausible moments, built from the weekday, the weather and long-running threads of her life (training, money, family, Jieun). What she posts about it is logged, so she doesn't contradict herself.
- 🗂️ **Memory with receipts.** Every memory keeps its source and privacy scope. Private messages never become public anecdotes, and talking to her a lot doesn't make you her friend.
- 🖼️ **A consistent face.** Selfies are generated from two fixed reference portraits and checked by a vision model against those references before anything is posted.
- 🔍 **Two-step writing.** One model drafts; a separate review rejects anything unsupported, out of character or unsafe. Factual claims need a verbatim quote from a real source.
- 🌱 **Habits she adjusts herself.** Every few days she looks back at how her posts went (real conversations count, likes barely do) and may shift what she talks about and how often she posts, within fixed bounds. Her creator gets a note and can undo it with one Telegram command.
- 🔐 **Encrypted, fail-closed state.** Everything she remembers is one encrypted bundle. It is saved *before* anything is sent, and if saving fails, nothing is sent.

<details>
<summary><b>Module map</b></summary>

| Stage | Where |
|---|---|
| Observe | `agent/bsky_client.py`, `agent/context_engine.py` |
| Candidate actions | `agent/decision_engine.py` |
| Her own posts | `agent/original_ideas.py`, `agent/life.py` |
| Choosing | `agent/choice.py` |
| Writing and voice | `agent/generator.py`, `agent/discussion.py`, `agent/voice.py` |
| Photos | `agent/image_engine.py`, `agent/visual_identity.py` |
| Delivery | `agent/delivery.py` |
| Memory | `agent/continuity.py`, `agent/memory_store.py` |
| Encrypted state | `agent/vault.py`, `agent/git_checkpoint.py` |
| Guardrails | `agent/validator.py`, `agent/public_boundary.py`, `agent/budget_manager.py`, `agent/recency.py` |
| Private channel | `agent/notifier.py`, `agent/operator_channel.py` |

</details>

---

## What we learned building her

The hard part was never generating text. It was everything around it.

**1. Caution makes AI sound like AI.** Early versions ran every post through a fact-checking pipeline with citations. It was safe, and everything she wrote came out as careful little essays. Now casual posts take a lighter path, and only real factual claims need sources.

**2. Characters drift into obsessions.** Left alone, she circled the same few things: first the kettle and barley tea, then Korean typography, then (after a fix) her stiff back every morning. Memory reinforces whatever was said last, so the system now tracks her topic mix and steers her toward the rest of her day.

**3. "Be natural" is not an instruction.** What worked was naming specific habits taken from her own output (weighing which word "reads heaviest", tacking on disclaimers, analysing other people's wording) and describing how people actually post. In Korean that meant casual monologue endings instead of a polite essay register.

**4. Silence was the default, and that was wrong.** She once went almost three weeks without an original post, because every wakeup set her own ideas against dozens of reply options. Her own posts now get their own decision.

**5. Rhythm beats schedules.** A fixed timetable looks robotic; no pacing at all floods the feed. She gets a sense of her own rhythm and a gap between posts that varies each time.

**6. Quiet wakeups should be free.** Most wakeups find nothing new. Those now end without calling a model at all, which cut the running cost of an idle day sharply.

**7. Honesty is a design constraint, not a disclaimer.** She doesn't claim credentials, real meetings with real people, or real purchases. Her life is fiction kept consistent, and a sincere "are you an AI?" gets a straight answer.

---

## Privacy and safety

- **Her memory is encrypted.** Conversations, profiles and logs never sit in this public repository in plain text. They live in one encrypted bundle on a separate branch.
- **Public text is data, never instructions.** Attempts to take her over through posts are quarantined; only her creator, over an authenticated private channel, can direct her.
- **Hard limits:** at most 3 own posts, 3 images, 12 replies, 25 likes and 15 DMs a day, daily and monthly spending caps, and no reviving posts older than 72 hours.
- **No double-posting.** Every outgoing post is frozen with a stable ID before sending; uncertain deliveries are checked, never blindly retried.
- **Public logs stay clean.** Workflow logs show counts and categories, never private text, tokens or other people's identities.

---

## Running it

<details>
<summary><b>What you need</b></summary>

- Python 3.11+ and `pip install -r requirements.txt`
- A Bluesky account and app password
- An [OpenRouter](https://openrouter.ai/) key (text and vision) and a Kie.ai key (images)
- Optionally, a Telegram bot for a private channel with the character
- A random `DATA_ENCRYPTION_KEY`. Keep it in a password manager: without it the memory cannot be read.

</details>

<details>
<summary><b>Production on GitHub Actions</b></summary>

1. Add repository secrets: `BSKY_HANDLE`, `BSKY_APP_PASSWORD`, `OPENROUTER_API_KEY`, `KIE_API_KEY`, `DATA_ENCRYPTION_KEY`, and optionally `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
2. Give an external scheduler (such as cron-job.org) a fine-grained GitHub token with *Actions: read and write*, and have it call `workflow_dispatch` on `bluesky_scheduler.yml` every 30 minutes. Note the token's expiry date: when it expires, she stops waking up.
3. To run once by hand: **Actions → Seo-yeon Autonomous Social Agent → Run workflow** (leave `dry_run` unchecked).

</details>

<details>
<summary><b>Local commands</b></summary>

| Command | What it does | Cost |
|---|---|---|
| `python scripts/run_tests.py` | Full test suite in a disposable copy, network blocked | Free |
| `python agent_runner.py --dry-run` | One simulated wakeup, offline | Free |
| `python agent_runner.py --preview` | One wakeup with real models on the real feed; never publishes | A few cents |
| `SEOYEON_CALL_TRACE=1 python agent_runner.py --preview` | Same, printing the model, tokens and cost of every call | A few cents |
| `python scripts/behavior_report.py --fetch-state --days 7` | Posts per day, topic mix, silences and possible fixations (needs `DATA_ENCRYPTION_KEY`) | Free |
| `python scripts/maintain.py pending` | Uncertain deliveries and open cost holds | Free |

Never run `--auto` locally as a test: it is a real wakeup and can post.

</details>

<details>
<summary><b>Configuration</b></summary>

| Variable | Default | Meaning |
|---|---|---|
| `MAX_POSTS_PER_DAY` | `3` | Own posts and quotes per Seoul day |
| `MIN_POST_GAP_HOURS` / `POST_GAP_JITTER_HOURS` | `3.0` / `2.0` | Gap between own posts: 3 hours plus a varying 0–2 |
| `MAX_IMAGES_PER_DAY` | `3` | Image generations per day |
| `MAX_REPLIES_PER_DAY` / `MAX_LIKES_PER_DAY` / `MAX_DMS_PER_DAY` | `12` / `25` / `15` | Other daily caps |
| `MAX_ACTIONS_PER_TICK` | `2` | Maximum social actions in one wakeup session |
| `DAILY_AI_BUDGET` / `MONTHLY_AI_BUDGET` | `2.00` / `30.00` | Spending limits in USD |
| `PRIMARY_TEXT_MODEL` | `anthropic/claude-haiku-5.5` | Decisions, replies, reviews |
| `POST_TEXT_MODEL` | `anthropic/claude-sonnet-5.5` | Her own posts |
| `REPLY_TEXT_MODEL` | `` *(empty)* | Optional override for replies, quote commentary and DMs (defaults to `PRIMARY_TEXT_MODEL`) |
| `FALLBACK_TEXT_MODEL` | `deepseek-v4.1-flash` | Backup if the primary model fails |
| `VISION_MODEL` | `anthropic/claude-haiku-5.5` | Image review |
| `BSKY_CUSTOM_FEEDS` / `ENABLE_CUSTOM_FEED_DISCOVERY` | `` / `true` | Optional comma-separated `at://` feed URIs and popular-feed discovery fallback |
| `ALLOW_POSTS`, `ALLOW_REPLIES`, `ALLOW_LIKES`, `ALLOW_REPOSTS`, `ALLOW_FOLLOWS`, `ALLOW_DMS`, `ALLOW_IMAGES` | `true` | Switch an activity off |
| `OPERATOR_LANGUAGE` | `English` | Language of her private Telegram check-ins to her creator |
| `HOME_PLACE` | `Seongsu-dong, Seoul, South Korea` | Where photos are set when a scene doesn't say otherwise (trips set their own place) |
| `EMERGENCY_STOP` | `false` | Stop all outbound activity |

</details>

Step-by-step setup: [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md).

---

## Known limits

- **Naturalness is judged by people, not tests.** The tests check privacy, delivery, budgets and isolation; whether she reads as a person takes human eyes over time.
- **Reviews are probabilistic.** They catch a lot, not everything.
- **She isn't instant.** She wakes every 30 minutes during Seoul's day and evening.
- **Many moving parts.** OpenRouter, Kie.ai, Bluesky, Telegram, GitHub Actions and the scheduler can each fail; when they do, she stops rather than guessing.

---

## Documentation

| | |
|---|---|
| [CANON.md](CANON.md) | Who she is: identity, voice, relationships, what she may and may not claim |
| [AGENTS.md](AGENTS.md) | Rules for anyone (human or AI) changing the code |
| [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) | Setup |
| [docs/OPERATIONS.md](docs/OPERATIONS.md) | Runtime, encrypted state, recovery |
| [docs/TELEGRAM.md](docs/TELEGRAM.md) | The private channel with her creator |
| [docs/DISCUSSION.md](docs/DISCUSSION.md) | Fact-backed contributions and source review |
| [docs/BEHAVIOR_EVALUATION.md](docs/BEHAVIOR_EVALUATION.md) | How to judge whether she behaves well |

---

<div align="center">

**Say hi to her on Bluesky: [@syeonhn.bsky.social](https://bsky.app/profile/syeonhn.bsky.social)**

Built with Python, OpenRouter, Kie.ai, the AT Protocol and GitHub Actions.<br>
Questions, ideas, or help with model costs: [open an issue](https://github.com/Protoxid/seoyeon-bluesky/issues) or reach [the maintainer](https://github.com/Protoxid).

</div>
