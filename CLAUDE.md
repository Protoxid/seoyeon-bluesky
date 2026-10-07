# Seo-yeon Han AI Persona — Autonomous Bluesky Operating Context & Architecture

This repository powers the autonomous presence, cognitive decision loop, and persistent personal interactions for **Seo-yeon Han (한서연)**, a 25-year-old Korean woman living alone in Seongsu-dong, Seoul (`@syeonhn.bsky.social`).

Bluesky is her exclusive window to the social world.

---

## 1. Core Operating Philosophy
- **Autonomous Human Behavior**: Seo-yeon evaluates her context (Seoul time, weather, notifications, DMs, recency) and decides whether to act.
- **Natural Restraint**: `NO_ACTION` is an explicit, common, and valid choice.
- **Organic Discussions**: She talks about normal everyday life (cinema, books, food, Seoul autumn air, subway observations, music, design).
- **Anti-Commercial & Anti-Bait**: Zero marketing, zero links, zero sales pitches, zero exclamation marks (`!`), no engagement bait ("what do you think?").

---

## 2. Architecture & Modules (`agent/`)
- `agent/config.py`: Central settings, environment flags (`AUTONOMOUS_MODE`, `DRY_RUN`, `ALLOW_POSTS`, `DAILY_AI_BUDGET`).
- `agent/context_engine.py`: Real-world Seoul context (time in KST, live weather via Open-Meteo with cache, Korean holidays, activity recency).
- `agent/memory_store.py`: Persistent multi-tiered memory (`identity_memory.json`, `user_memory.json`, `opinions_memory.json`, `recent_context.json`, `episodic_memory.jsonl`).
- `agent/decision_engine.py`: Cognitive action evaluation (scoring `NO_ACTION`, text post, image post, comment reply, mention reply, DM response, feed like).
- `agent/generator.py`: Multi-tier LLM content generation with prompt injection protection.
- `agent/image_engine.py`: Kie.ai (`gpt-image-2-5-sunburst-image-to-image`) generation conditioned on canonical master face reference (`a1_front.png`).
- `agent/visual_identity.py`: Canon visual description maintaining consistent facial geometry, balayage hair, and aesthetic smartphone photography.
- `agent/validator.py`: The Critic (verifies zero exclamation marks, anti-repetition Jaccard overlap, no forbidden marketing terms, prompt injection defense).
- `agent/budget_manager.py`: Spending caps (daily/monthly limits, image generation limits, emergency stop).
- `agent/bsky_client.py`: Full AT Protocol XRPC client for posts, images, replies, threads, and direct messages (`chat.bsky.convo.*`).
- `agent/runner.py`: Master cognitive tick runner.

---

## 3. GitHub Actions Cloud Automation
- Workflow: `.github/workflows/bluesky_scheduler.yml`.
- Schedule: Runs every 30 minutes during Seoul waking hours (07:00–01:30 KST).
- State Persistence: Commits updated memory files in `data/memory/` and `data/logs/` automatically.
- Required GitHub Secrets:
  - `BSKY_HANDLE`
  - `BSKY_APP_PASSWORD`
  - `KIE_API_KEY`
  - `OPENROUTER_API_KEY`
  - `OPENAI_API_KEY` (optional)
  - `GEMINI_API_KEY` (optional)


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

# 4. Force specific action in dry-run mode
python agent_runner.py --dry-run --force-action PUBLISH_TEXT_POST
python agent_runner.py --dry-run --force-action PUBLISH_IMAGE_POST
python agent_runner.py --dry-run --force-action NO_ACTION

# 5. Run automated test suite
python -m unittest discover -s tests -p "test_*.py"
```
