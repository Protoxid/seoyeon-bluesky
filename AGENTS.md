# Seo-yeon Han AI Persona — Autonomous Bluesky Operating Context & Architecture

This repository powers the fully autonomous presence, natural social interactions, and persistent cognitive life of **Seo-yeon Han (한서연)**, a 25-year-old Korean woman living alone in Seongsu-dong, Seoul (`@syeonhn.bsky.social`).

The project focuses exclusively on Seo-yeon's Bluesky account as her sole window to the social world.

---

## 1. Operating Objective: An Autonomous Person, Not a Bot
Seo-yeon operates her account independently without rigid schedules or predictable cron events:
- **No fixed schedules**: No "08:00 coffee", "13:00 lunch", or "20:00 pilates" clockwork.
- **Cognitive Decision Loop**: Each cycle evaluates the current Seoul environment (time, weather, season), inbound notifications, unread DMs, timeline and cultural stimulus, and her memory store before deciding what to do.
- **Natural Restraint (`NO_ACTION`)**: "Doing nothing" is a common, valid, and prominent outcome. If she has no organic reason to act, she stays quietly offline.
- **Ordinary, Diverse Human Interests**: Her thoughts cover everyday life (independent cinema, translated literature, secondhand books, Hangul typography, Seoul architecture, quiet kitchen experiments, subway observations, music, design). Pilates and coffee are small facets of her life, not constant catchphrases (strictly capped at ≤ 10% by anti-cliché gatekeepers).
- **100% Bluesky Protocol Mechanics**: Operates natively across all Bluesky social dynamics: original posts, threaded replies, quote posts (`QUOTE_POST`), community reposts (`REPOST`), follows (`FOLLOW`), direct messages, and profile updates with rich text facets (links and hashtags).
- **Multimodal Visual Balance**: Never a wall of text. Balances authentic handheld selfies/mirror selfies (conditioned on canonical face master) with first-person point-of-view (POV) environmental photographs of her world (books on cafe tables, Line 2 river crossings, quiet Seoul alleyways).

---

## 2. The Cognitive Loop Architecture
The system runs via `agent_runner.py` following this high-level loop:

```text
       OBSERVE
          │  (Sensory inputs: Seoul time & weather, notifications, DMs, feed, Discover stimulus)
          ▼
    BUILD CONTEXT
          │  (Temporal phase, weather, holidays, recency of actions, cultural landscape)
          ▼
   RECALL MEMORY
          │  (Identity facts, user profile, established opinions, recent posts, anti-cliché quotas)
          ▼
EVALUATE CANDIDATES
          │  (Scores possible actions: NO_ACTION, post, reply, quote-post, repost, follow, DM, like)
          ▼
        DECIDE
          │  (Selects highest-scoring organic action; stays offline if quality < 0.75)
          ▼
   GENERATE CONTENT
          │  (Dynamic OpenRouter LLM generation grounded in her dry, perceptive, lowercase voice)
          ▼
 CRITIC / VALIDATOR
          │  (Enforces zero '!', no marketing, anti-repetition, anti-cliché quota, anti-injection)
          ▼
       EXECUTE
          │  (Publishes to Bluesky via AT Protocol XRPC)
          ▼
    STORE IN MEMORY
             (Updates user memory, episodic memory, recent context, budget)
```

---

## 3. Persistent Memory System & Encrypted Vault (`data/memory/` & `data/vault.enc`)
1. **Identity Memory (`identity_memory.json`)**:
   - Canonical facts from `CANON.md`: 25 years old (turns 26 on 23 Oct), lives in Seongsu, retrained from corporate marketing to pilates instructor, tight budget, dry understated voice.
2. **User Memory (`user_memory.json`)**:
   - Relationship tracking (`stranger` → `friendly_acquaintance` → `regular` → `trusted_friend`), interaction count, known facts learned about the user.
   - Private DM conversations use sanitized placeholders `[private direct message]` to prevent public log leaks.
3. **Opinion Memory (`opinions_memory.json`)**:
   - Established stances on cinema, music, food, and Seoul life to prevent contradictory statements.
4. **Recent Context (`recent_context.json`)**:
   - Rolling history of past posts, replies, and persistent handled DM IDs. Tested via Jaccard and n-gram similarity to prevent repetitive themes, opening words, or duplicate processing.
5. **Episodic Memory (`episodic_memory.jsonl`)**:
   - Chronological log of notable interactions, milestones, and reflections.
6. **Creator Relationship ("my master" / "my human")**:
   - Seo-yeon always refers to her human creator and operator as `"my master"` or `"my human"`.
   - **Interactive Bidirectional Telegram Bond (`agent/notifier.py`)**: She receives inbound messages from her master, recharges her social battery, and replies directly in character.
   - **Resilient Daily Evening Check-in & Catch-up**: Delivered late evening (≥ 21:00 KST). If any day is missed due to scheduler queues, she automatically catches up on the very next tick.
7. **Encrypted Private Vault (`data/vault.enc`)**:
   - Encrypted bundle storing her internal late-night reflections (`private_journal.jsonl`) and unredacted DM transcripts (`private_dms.jsonl`).
   - Strong Fernet cryptography (AES-128-CBC + HMAC-SHA256). In production (`ENV=production` or `GITHUB_ACTIONS=true`), requires dedicated secret (`DATA_ENCRYPTION_KEY` or `VAULT_KEY`). If `DATA_ENCRYPTION_KEY` is not explicitly declared in GitHub Secrets, the production scheduler workflow (`bluesky_scheduler.yml`) automatically derives a high-entropy key from private Bluesky credentials, and `PrivateVault.load_vault()` supports seamless credential-key fallback to prevent data loss.
   - **Data Loss Prevention**: If decryption fails on load, saving and appending are strictly blocked to prevent data corruption. Creates `vault.enc.bak` backups and uses atomic temporary file replacement (`os.replace`).
8. **Dynamic Cognitive State (`agent_state.json`)**:
   - Biological circadian rhythms: social battery (0.0–1.0), physical fatigue (0.0–1.0), financial awareness, and creative drive.
9. **Visual Consistency Inventory (`wardrobe_inventory.json`)**:
   - Wardrobe items and baseline textures grounding image prompts.
10. **Weekly Living Itinerary (`weekly_schedule.json`)**:
   - 7-day schedule synthesized every Sunday evening across 4 daily slots (`morning`, `afternoon`, `evening`, `deep_night`). Grounds her thoughts, errands, transit, and photos in realistic space and time without rigid cron timing.
11. **Autonomous Goal Lifecycle (`agent/goal_manager.py` & `data/memory/active_goals.json`)**:
   - Tracks ongoing personal pursuits across lifecycle states (`PROPOSED`, `ACTIVE`, `IN_PROGRESS`, `COMPLETED`, `PAUSED`, `ABANDONED`).
   - Grounded in canon interests (cinema, essay writing, plant propagation, Hangul typography, vintage film, neighborhood walking).
   - Strict Anti-Cliché Quota: Pilates and coffee/tea goals are capped at ≤ 10% of total active goals.
   - Substantive Quantitative Advancement: `detect_and_record_goal_activity()` and nightly `advance_active_goals_daily()` advance concrete progress metrics (+20 pages read toward 310 total on Han Kang's *We Do Not Part*, root node maturation days on kitchen ivy cuttings, storefront signs cataloged), automatically marking goals `COMPLETED` when targets are reached.
12. **Narrative Continuity Engine (`agent/narrative_engine.py` & `data/memory/narrative_state.json`)**:
   - **Live Open Conversational Loops**: `detect_and_manage_loops()` is integrated directly across live interaction handlers (`REPLY_COMMENT`, `ANSWER_MENTION`, `ANSWER_DM`, `BROWSE_AND_REPLY`). Tracks promises, book recommendations, and mutual questions across sessions without amnesia.
   - **Multi-Day Narrative Arcs**: Tracks temporal unfolding of multi-day projects (drying autumn persimmons, reading lengthy literature, seasoning ceramic cookware) across progressive stages (`started` → `in_progress` → `maturing` → `concluded`). Advanced nightly via `advance_arcs_daily()`.
   - **Temporal Coherence Validator**: Detects and rejects chronological paradoxes in generated content (e.g. claiming to eat dinner at 09:00 KST, or claiming deep-night rest at midday).

---

## 4. Text Generation (OpenRouter Exclusive), Image Engine & Atomic Budgeting
- **Text Generation**: Routed **EXCLUSIVELY** through OpenRouter API (`https://openrouter.ai/api/v1/chat/completions`).
  - Primary Model: `anthropic/claude-sonnet-5.5` (state-of-the-art intelligence, nuanced character adherence, natural dry tone without robotic exclamation marks).
  - Reasoning Token Headroom: Enforces `effective_tokens = max(max_tokens, 700)` with `timeout=35s` so mandatory reasoning never starves completion text.
  - Fallback Model: `deepseek-v4.1-flash` (fast, highly intelligent secondary on OpenRouter).
  - Truthful AI Disclosure: Consistently allowed across generator prompts and validation rules when asked directly, without generic assistant jargon.
  - Natural Restraint Over Canned Fallbacks: Completely free of canned bot platitudes. If generation is unavailable or rejected by the validator, she cleanly stays offline (`NO_ACTION`).
  - Direct Opinion Answering: When a post poses a question, dilemma, or choice, she answers directly from her personal life, routine, and tastes with dry humor, rather than non-committal evasion.
- **Multi-Candidate Feed Evaluation (`agent/decision_engine.py`)**:
  - Scores up to 10 candidates from timeline and discovery feeds based on relationship tier, open conversational loops with the author, relevant active goal keywords, recency, and language quality.
- **Atomic Budgeting & Durable Reservations (`agent/budget_manager.py`)**:
  - Durable Reservations: Pre-flight reservations stored in `data["active_reservations"]` survive process and CI runner restarts, with automatic 15-minute expiration of stale holds.
  - Model-Aware Cost Estimation: Accurately sizes Sonnet 5.5 reasoning token margins before sending requests.
  - Decoupled Image Billing: Image generation cost ($0.045) is reconciled immediately upon image byte retrieval from Kie.ai, ensuring accurate accounting even if subsequent Bluesky uploads fail.
  - Consolidated single-entry accounting prevents double-billing across generator tokens and runner actions. Hard daily ($2.00) and monthly ($30.00) caps.
- **Discovery Feed & Multi-Language Filters (`agent/validator.py`)**:
  - Operates strictly in Korean and English. Rejects non-target scripts (Japanese Kana, Cyrillic, Arabic, CJK ideographs without Hangul, and non-target Romance text) and automatically drops commercial financial spam and bot advisors.
- **Image Generation & Anonymous Settings Architecture**:
  - **The Consistency Solution**: Because generative image models cannot reproduce identical indoor room layouts (such as her private flat or gym studio) across weeks, daytime and evening photos prioritize **anonymous outdoor settings** (Seongsu red-brick sidewalks, crosswalks, fallen ginkgo leaves, Line 2 transit bridge) or **incidental POV macros** (a stray cat met on the way to the studio, hands holding a warm tea cup, book on an outdoor table with heavy background bokeh). Deep night is strictly tight in-bed selfies (under duvet, messy bedhead, dim night lamp).
  - **Identity Anchoring**: Selfies are conditioned on dual canonical face masters through **Kie.ai** API (`gpt-image-2-5-sunburst-image-to-image`) anchored to `personas/seoyeon/master/a/a1_front.png` and `personas/seoyeon/master/c/c5_relax_front.png`.
  - **POV Auto-Detection**: Incidental environmental shots (stray cats, tea cups, books, transit) automatically omit face references to produce pure 35mm film street captures. Contextual image alt text is derived automatically from the visual scene prompt.
- **Telegram Escalation**: When sensitive inquiries occur (e.g. users asking for real-life meetups, personal contact details) or when agent decisions require master approval, she notifies her master via Telegram Bot API.

---

## 5. Google Antigravity Agent Skills Standard (`.agents/skills/`)
The workspace leverages the open [Google Antigravity Agent Skills](https://antigravity.google/docs/skills/) standard for progressive-disclosure workflows:
1. **[`seoyeon-ops`](.agents/skills/seoyeon-ops/SKILL.md)**:
   - Full operational runbook for all 11 CLI commands, testing procedures, master Telegram bidirectional communications, and diagnostic routines.
2. **[`seoyeon-persona`](.agents/skills/seoyeon-persona/SKILL.md)**:
   - Persona and linguistic invariants: zero exclamation marks (`!`), natural Korean banmal, dry lowercase English.
   - Anti-cliché quota enforcement (≤10% pilates/coffee).
   - Architectural rules for the "Consistency Solution" (anonymous outdoor settings, 35mm POV environmental macros, and in-bed deep-night shots).

---

## 6. Cloud Automation & Continuous Integration
The system is fully automated on **GitHub Actions** across two coordinated workflows:
1. **Production Scheduler (`.github/workflows/bluesky_scheduler.yml`)**:
   - Schedule: Runs every 30 minutes during Seoul waking hours (07:00–01:30 KST = 22:00–16:30 UTC).
   - Commits state: Automatically commits updated `data/memory/`, `data/logs/`, `data/vault.enc`, and `data/budget_ledger.json` back to `main` with `[skip ci]`.
   - Vault Resilience: Automatically supplies `DATA_ENCRYPTION_KEY` derived from `BSKY_APP_PASSWORD` and `BSKY_HANDLE` if a dedicated secret is not explicitly set in repository settings.
2. **Hermetic CI Pipeline (`.github/workflows/ci.yml`)**:
   - Runs on all pushes and pull requests to `main` and `feature/*` branches.
   - Executes all 124 unit tests across 13 test suites with isolated environment configuration (`ENV=test`), guaranteeing production readiness.

- **Required GitHub Secrets**:
  - `BSKY_HANDLE`: `syeonhn.bsky.social`
  - `BSKY_APP_PASSWORD`: Bluesky App Password (with DM access enabled)
  - `KIE_API_KEY`: Kie.ai API key (for GPT Image 2.5 image generation)
  - `OPENROUTER_API_KEY`: OpenRouter API key (sole text provider for Claude Sonnet 5.5 / DeepSeek)
  - `TELEGRAM_BOT_TOKEN`: Telegram bot token (for bidirectional communication with her master)
  - `TELEGRAM_CHAT_ID`: Telegram chat ID / recipient for master alerts
  - `DATA_ENCRYPTION_KEY`: (Optional) Dedicated AES-256 key for `data/vault.enc` (automatically falls back to private credential derivation if omitted)

---

## 7. Daily Command Cheatsheet
From project root:
```powershell
# 1. View live agent dashboard (Seoul time, weather, memory, goals, budget, cognitive state)
python agent_runner.py --status

# 2. Run single autonomous tick in safe DRY-RUN mode (no publishing)
python agent_runner.py --dry-run

# 3. Run live autonomous tick
python agent_runner.py --auto

# 4. Generate & send daily evening check-in to my master (with catch-up resilience)
python agent_runner.py --daily-summary --dry-run
python agent_runner.py --daily-summary

# 5. Check & reply to incoming Telegram messages from my master
python agent_runner.py --check-master

# 6. Run nightly memory consolidation pass & private journal reflection
python agent_runner.py --consolidate

# 7. Force a specific action in dry-run mode (for verification)
python agent_runner.py --dry-run --force-action PUBLISH_TEXT_POST
python agent_runner.py --dry-run --force-action PUBLISH_IMAGE_POST
python agent_runner.py --dry-run --force-action BROWSE_AND_REPLY
python agent_runner.py --dry-run --force-action QUOTE_POST
python agent_runner.py --dry-run --force-action NO_ACTION

# 8. View / plan 7-day weekly life itinerary
python agent_runner.py --plan-week
python agent_runner.py --force-plan

# 9. Run 30-day deterministic simulation harness
python scripts/simulate_30_days.py --days 30

# 10. Run full test suite (124 hermetic tests)
python -m unittest discover -s tests -p "test_*.py"
```

