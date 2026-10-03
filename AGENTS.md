# Seo-yeon Han AI Persona — Autonomous Bluesky Operating Context & Architecture

This repository powers the fully autonomous presence, natural social interactions, and persistent cognitive life of **Seo-yeon Han (한서연)**, a 25-year-old Korean woman living alone in Seongsu-dong, Seoul (`@syeonhn.bsky.social`).

All Instagram and Fanvue integrations have been permanently removed. The project focuses exclusively on Seo-yeon's Bluesky account as her sole window to the social world.

---

## 1. Operating Objective: An Autonomous Person, Not a Bot
Seo-yeon operates her account independently without rigid schedules or predictable cron events:
- **No fixed schedules**: No "08:00 coffee", "13:00 lunch", or "20:00 pilates" clockwork.
- **Cognitive Decision Loop**: Each cycle evaluates the current Seoul environment (time, weather, season), inbound notifications, unread DMs, recent actions, and her memory store before deciding what to do.
- **Natural Restraint (`NO_ACTION`)**: "Doing nothing" is a common, valid, and prominent outcome. If she has no organic reason to act, she stays quietly offline.
- **Ordinary Topics**: Her thoughts cover everyday life (cinema, books, food, Korean autumn air, quiet evenings, subway observations, music, design). Pilates and coffee are part of her life, not constant catchphrases.

---

## 2. The Cognitive Loop Architecture
The system runs via `agent_runner.py` following this high-level loop:

```text
       OBSERVE
          │  (Sensory inputs: Seoul time & weather, notifications, DMs, feed)
          ▼
    BUILD CONTEXT
          │  (Temporal phase, weather, holidays, recency of actions)
          ▼
   RECALL MEMORY
          │  (Identity facts, user profile, established opinions, recent posts)
          ▼
EVALUATE CANDIDATES
          │  (Scores possible actions: NO_ACTION, post, reply, DM, like)
          ▼
        DECIDE
          │  (Selects highest-scoring organic action)
          ▼
   GENERATE CONTENT
          │  (Multi-tier LLM generation grounded in her dry, lowercase voice)
          ▼
 CRITIC / VALIDATOR
          │  (Enforces zero '!', no marketing, anti-repetition, anti-injection)
          ▼
       EXECUTE
          │  (Publishes to Bluesky via AT Protocol XRPC)
          ▼
    STORE IN MEMORY
             (Updates user memory, episodic memory, recent context, budget)
```

---

## 3. Persistent Memory System (`data/memory/`)
1. **Identity Memory (`identity_memory.json`)**:
   - Canonical facts from `CANON.md`: 25 years old (turns 26 on 23 Oct), lives in Seongsu, retrained from corporate marketing to pilates instructor, tight budget, dry understated voice.
2. **User Memory (`user_memory.json`)**:
   - Relationship tracking (`stranger` → `friendly_acquaintance` → `regular` → `trusted_friend`), interaction count, known facts learned about the user.
3. **Opinion Memory (`opinions_memory.json`)**:
   - Established stances on cinema, music, food, and Seoul life to prevent contradictory statements.
4. **Recent Context (`recent_context.json`)**:
   - Rolling history of past posts and replies. Tested via Jaccard and n-gram similarity to prevent repetitive themes, opening words, or selfie frequency.
5. **Episodic Memory (`episodic_memory.jsonl`)**:
   - Chronological log of notable interactions, milestones, and reflections.
6. **Creator Relationship ("my master" / "my human")**:
   - Seo-yeon always refers to her human creator and operator as `"my master"` or `"my human"`.
   - Direct Telegram messenger (`agent/notifier.py`): If she needs to ask her master for anything, she sends an immediate Telegram message to `@Protoxide`.

---

## 4. Text Generation (OpenRouter Exclusive) & Kie.ai Image Generation
- **Text Generation**: Routed **EXCLUSIVELY** through OpenRouter API (`https://openrouter.ai/api/v1/chat/completions`).
  - Primary Model: `anthropic/claude-3.5-sonnet` (state-of-the-art intelligence, nuanced character adherence, natural dry tone without robotic exclamation marks).
  - Fallback Model: `deepseek/deepseek-chat` (fast, highly intelligent secondary on OpenRouter).
- **Image Generation**: Conditioned on the canonical face master through **Kie.ai** API (`https://api.kie.ai`) with `gpt-image-2-5-sunburst-image-to-image`. Identity-anchored to `personas/seoyeon/master/a/a1_front.png`.
- **Telegram Escalation**: When sensitive inquiries occur (e.g. users asking for real-life meetups, personal contact details) or when agent decisions require master approval, she notifies `@Protoxide` via Telegram Bot API.

---

## 5. Cloud Automation (Runs 24/7 with PC Off)
The system is fully deployed on **GitHub Actions**:
- Workflow: `.github/workflows/bluesky_scheduler.yml`.
- Schedule: Runs every 30 minutes during Seoul waking hours (07:00–01:30 KST = 22:00–16:30 UTC).
- Commits state: Automatically commits updated `data/memory/`, `data/logs/`, and `data/budget_ledger.json` back to the repository with `[skip ci]`.
- Required GitHub Secrets:
  - `BSKY_HANDLE`: `syeonhn.bsky.social`
  - `BSKY_APP_PASSWORD`: Bluesky App Password (with DM access enabled)
  - `KIE_API_KEY`: Kie.ai API key (for GPT Image 2.5 image generation)
  - `OPENROUTER_API_KEY`: OpenRouter API key (sole text provider for Claude 3.5 Sonnet / DeepSeek)
  - `TELEGRAM_BOT_TOKEN`: Telegram bot token (for outbound messages to `@Protoxide`)
  - `TELEGRAM_CHAT_ID`: Telegram chat ID / recipient for `@Protoxide` (optional, defaults to `@Protoxide`)


---

## 6. Daily Command Cheatsheet
From project root:
```powershell
# 1. View live agent dashboard (Seoul time, weather, memory, budget)
python agent_runner.py --status

# 2. Run single autonomous tick in safe DRY-RUN mode (no publishing)
python agent_runner.py --dry-run

# 3. Run live autonomous tick
python agent_runner.py --auto

# 4. Force a specific action in dry-run mode (for verification)
python agent_runner.py --dry-run --force-action PUBLISH_TEXT_POST
python agent_runner.py --dry-run --force-action PUBLISH_IMAGE_POST
python agent_runner.py --dry-run --force-action NO_ACTION

# 5. Run full test suite
python -m unittest discover -s tests -p "test_*.py"
```
