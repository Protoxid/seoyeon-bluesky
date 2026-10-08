---
name: seoyeon-ops
description: >-
  Operational runbook, CLI commands, testing, and debugging procedures for the Seo-yeon Han autonomous Bluesky agent repository. Use when running ticks, inspecting dashboard metrics, executing test suites, testing dry-runs, triggering master Telegram communication, running weekly life planning, or debugging agent workflows.
---

# Seo-yeon Han Autonomous Agent — Operations & Runtime Runbook

This skill provides step-by-step procedures, runbooks, and diagnostic workflows for operating, testing, and maintaining the autonomous presence of **Han Seo-yeon (한서연)** (`@syeonhn.bsky.social`).

---

## 1. Daily CLI Command Quick Reference

Always execute from the project root (`c:\AI-Project`):

| Goal | Command | Description |
| :--- | :--- | :--- |
| **Inspect Status** | `python agent_runner.py --status` | Live dashboard: Seoul time, weather, circadian phase, memory counts, budget ledger, credentials. |
| **Safe Dry-Run** | `python agent_runner.py --dry-run` | Executes complete cognitive tick without making network mutations on Bluesky. |
| **Live Tick** | `python agent_runner.py --auto` | Runs single autonomous cognitive loop and publishes actions to Bluesky if score threshold is met. |
| **Force Action** | `python agent_runner.py --dry-run --force-action <ACTION>` | Simulates specific action: `PUBLISH_TEXT_POST`, `PUBLISH_IMAGE_POST`, `BROWSE_AND_REPLY`, `QUOTE_POST`, `BROWSE_AND_LIKE`, `NO_ACTION`. |
| **Check Master** | `python agent_runner.py --check-master` | Checks incoming Telegram messages from her master and replies in character. |
| **Daily Summary** | `python agent_runner.py --daily-summary` | Generates and sends evening check-in to her master on Telegram (auto catch-up if yesterday missed). |
| **Ask Master** | `python agent_runner.py --ask-master "<question>"` | Sends direct inquiry/question to master's Telegram. |
| **Weekly Plan** | `python agent_runner.py --plan-week` | Displays the synthesized 7-day weekly life itinerary across morning/afternoon/evening/night. |
| **Regen Week** | `python agent_runner.py --force-plan` | Force-regenerates fresh 7-day schedule with OpenRouter LLM. |
| **Consolidate** | `python agent_runner.py --consolidate` | Runs nightly memory consolidation pass and Seongsu flat private journal reflection. |
| **Run Tests** | `python -m unittest discover -s tests -p "test_*.py"` | Runs full hermetic unit test suite (67+ tests). |

---

## 2. Standard Pre-Deployment & Verification Procedure

Before committing or pushing any architectural or agent code changes, follow this exact sequence:

1. **Verify Hermetic Tests**:
   ```bash
   python -m unittest discover -s tests -p "test_*.py"
   ```
   *Requirement*: All 67+ tests must pass cleanly (`OK`).

2. **Verify Agent Status**:
   ```bash
   python agent_runner.py --status
   ```
   *Check*: Ensure no credentials report `MISSING` and emergency stop is `OFF`.

3. **Verify Safe Dry-Run**:
   ```bash
   python agent_runner.py --dry-run
   ```
   *Check*: Verify the chosen candidate, LLM model used (`anthropic/claude-sonnet-5.5`), and draft text formatting.

4. **Verify Persona Restraint**:
   - Check that the draft output contains **zero exclamation marks (`!`)**.
   - Check that draft text is not generic bot fluff or canned phrases.

---

## 3. Master Relationship & Telegram Workflow

Seo-yeon maintains a resilient, private Telegram bond with her human creator and master (`@Protoxide`):

1. **Inbound Master Messages (`agent/notifier.py`)**:
   - Authorized sender check: Sender ID must strictly match `config.master_telegram_chat_id` or `config.master_telegram_handle`. All stranger messages are dropped.
   - Master Directives: If master asks her to post a picture, write a post, or check DMs, `parse_master_directive()` extracts the order and immediately queues or executes it.
   - Master Post Marking: If master tells her to note that a post was requested by him, she explicitly incorporates `"test requested by my master"` or `"my human asked..."`.

2. **Daily Evening Check-in Resilience**:
   - Triggered late evening (≥ 21:00 KST).
   - If a scheduler skip causes yesterday's report to be missed, `check_and_send_evening_summary()` detects this on the very next tick and delivers a catch-up report.

---

## 4. LLM & OpenRouter Best Practices

- **Sole Text Provider**: Text generation is routed **exclusively** through OpenRouter (`anthropic/claude-sonnet-5.5`).
- **Reasoning Token Budget**: Claude Sonnet 5.5 on OpenRouter enforces mandatory reasoning tokens. Always ensure `effective_tokens = max(max_tokens, 700)` in `_query_openrouter()` and `timeout=35` so reasoning never starves content output.
- **Natural Restraint Principle**: If the LLM call fails or validator rejects output, she aborts with `NO_ACTION` and stays quietly offline. **Never** revert to canned platitudes ("fair point", "nodding to this").

---

## 5. GitHub Actions Cloud Automation Workflow

- **Scheduler Workflow**: `.github/workflows/bluesky_scheduler.yml`
- **Schedule**: Every 30 minutes during Seoul waking hours (07:00–01:30 KST = 22:00–16:30 UTC).
- **Auto-Commit**: Automatically commits updated `data/memory/`, `data/budget_ledger.json`, and `data/logs/` back to `main` with `[skip ci]`.
- **Required Secrets**:
  - `BSKY_HANDLE`
  - `BSKY_APP_PASSWORD`
  - `KIE_API_KEY`
  - `OPENROUTER_API_KEY`
  - `TELEGRAM_BOT_TOKEN`
  - `TELEGRAM_CHAT_ID`
