# Seo-yeon Han AI Persona — Autonomous Bluesky Operating Context & Architecture

This repository powers the autonomous presence, cognitive decision loop, and persistent personal interactions for **Seo-yeon Han (한서연)**, a 25-year-old Korean woman living alone in Seongsu-dong, Seoul (`@syeonhn.bsky.social`).

Bluesky is her exclusive window to the social world.

---

## 1. Core Operating Philosophy
- **Autonomous Human Behavior**: Seo-yeon evaluates her context (Seoul time, weather, notifications, DMs, recency, social battery) and decides whether to act.
- **Natural Restraint**: `NO_ACTION` is an explicit, common, and valid choice.
- **Organic Discussions**: She talks about normal everyday life (independent cinema, architecture, Hangul typography, translated literature, secondhand books, Line 2 observations).
- **Anti-Cliché & Anti-Bait**: Strict ≤ 10% frequency caps on recurring topics (pilates, tea). Zero marketing, zero sales pitches, zero exclamation marks (`!`), no engagement bait ("what do you think?").
- **Multimodal Realism**: 50% text reflections, 25% 35mm POV environmental captures, 15% community dialogue (quote-posts/reposts), ≤ 10% authentic handheld selfies.

---

## 2. Architecture & Modules (`agent/`)
- `agent/config.py`: Central settings, environment flags (`AUTONOMOUS_MODE`, `DRY_RUN`, `ALLOW_POSTS`, `DAILY_AI_BUDGET`).
- `agent/context_engine.py`: Real-world Seoul context (time in KST, live weather via Open-Meteo with cache, Korean holidays, activity recency).
- `agent/memory_store.py`: Persistent multi-tiered memory (`identity_memory.json`, `user_memory.json`, `opinions_memory.json`, `recent_context.json`, `episodic_memory.jsonl`).
- `agent/vault.py`: Encrypted private vault (`data/vault.enc`) securing `private_journal.jsonl` and `private_dms.jsonl` with overwrite protection and atomic backups.
- `agent/decision_engine.py`: Cognitive action evaluation (scoring `NO_ACTION`, text post, image post, reply, quote-post, repost, follow, DM response, feed like).
- `agent/generator.py`: OpenRouter LLM generation (`anthropic/claude-sonnet-5.5` primary, `deepseek-v4.1-flash` fallback) with prompt injection protection and consistent truthful AI disclosure.
- `agent/image_engine.py`: Kie.ai (`gpt-image-2-5-sunburst-image-to-image`) conditioned on dual master face references (`a1_front.png` + `c5_relax_front.png`) for authentic candid realism without AI gloss.
- `agent/visual_identity.py`: Punchy, photorealistic prompt generator emphasizing real-world imperfections, flexible hairstyles, and 35mm street photography.
- `agent/validator.py`: The Critic (verifies zero exclamation marks, anti-repetition Jaccard overlap, cliché frequency quotas, no marketing terms, prompt injection defense, temporal coherence verification, truthful AI disclosure pass-through).
- `agent/goal_manager.py`: Autonomous goal lifecycle (`PROPOSED`, `ACTIVE`, `IN_PROGRESS`, `COMPLETED`, `PAUSED`, `ABANDONED`) with anti-cliché quotas (≤10% pilates/tea) and automatic keyword activity detection.
- `agent/narrative_engine.py`: Narrative continuity engine managing open conversational loops, multi-day arcs, and temporal coherence validation.
- `agent/budget_manager.py`: Atomic budget reservations (`reserve()`, `reconcile()`, `release()`) preventing concurrent overages and double-billing. Hard daily ($2.00) / monthly ($30.00) spending caps.
- `agent/bsky_client.py`: Full AT Protocol XRPC client for posts, images, replies, quote-posts (`embed.record`), reposts, follows, facets (`#link`, `#tag`), profile updates, and direct messages (`chat.bsky.convo.*`).
- `agent/notifier.py`: Bidirectional Telegram bridge to her human creator, receiving directives and delivering daily evening check-ins.
- `agent/runner.py`: Master cognitive loop runner with DM privacy masking and safe vault load halting.

---

## 3. GitHub Actions Cloud Automation
- Workflow: `.github/workflows/bluesky_scheduler.yml`.
- Schedule: Runs every 30 minutes during Seoul waking hours (07:00–01:30 KST = 22:00–16:30 UTC).
- State Persistence: Commits updated memory files in `data/memory/`, `data/vault.enc`, and `data/logs/` automatically.
- Required GitHub Secrets:
  - `BSKY_HANDLE`
  - `BSKY_APP_PASSWORD`
  - `KIE_API_KEY`
  - `OPENROUTER_API_KEY`
  - `TELEGRAM_BOT_TOKEN`
  - `TELEGRAM_CHAT_ID`
  - `DATA_ENCRYPTION_KEY`

---

## 4. Daily Command Cheatsheet
From project root:
```powershell
# 1. Live status dashboard
python agent_runner.py --status

# 2. Run single cognitive tick in DRY_RUN mode (simulation)
python agent_runner.py --dry-run

# 3. Run live autonomous cognitive tick
python agent_runner.py --auto

# 4. Generate & deliver evening check-in to creator via Telegram
python agent_runner.py --daily-summary --dry-run
python agent_runner.py --daily-summary

# 5. Check & reply to incoming Telegram messages from creator
python agent_runner.py --check-master

# 6. Nightly memory consolidation & private journal pass
python agent_runner.py --consolidate

# 7. Force specific action in dry-run mode
python agent_runner.py --dry-run --force-action PUBLISH_TEXT_POST
python agent_runner.py --dry-run --force-action PUBLISH_IMAGE_POST
python agent_runner.py --dry-run --force-action QUOTE_POST
python agent_runner.py --dry-run --force-action NO_ACTION

# 8. Run 30-day deterministic simulation harness
python scripts/simulate_30_days.py --days 30

# 9. Run automated test suite (124 hermetic tests)
python -m unittest discover -s tests -p "test_*.py"
```
