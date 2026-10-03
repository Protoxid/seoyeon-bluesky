# Seo-yeon Han (한서연) — Autonomous Bluesky Agent

An autonomous, living AI persona operating independently on Bluesky (`@syeonhn.bsky.social`).

---

## Overview
This repository powers the cognitive loop, persistent multi-tier memory, sensory context evaluation, and content generation for **Seo-yeon Han**, a 25-year-old Korean woman living alone in Seongsu-dong, Seoul.

All Instagram and Fanvue integrations have been removed. The system is designed to behave like an authentic person rather than a scheduled social media bot:
- **Autonomous Decisions**: Evaluates environment (Seoul time, weather, holidays), incoming mentions, DMs, and memory to decide whether to act.
- **Natural Restraint**: "Doing nothing" (`NO_ACTION`) is a valid and common outcome.
- **Persistent Memory**: Retains identity facts, user relationship progression, topic opinions, and rolling context to avoid repetition.
- **Continuous Cloud Execution**: Runs 24/7 on GitHub Actions with the user's PC completely powered off.

---

## Quickstart

```powershell
# 1. Inspect live agent dashboard & Seoul environment context
python agent_runner.py --status

# 2. Run an autonomous cognitive cycle in safe simulation mode (DRY-RUN)
python agent_runner.py --dry-run

# 3. Run live autonomous tick
python agent_runner.py --auto

# 4. Run test suite
python -m unittest discover -s tests -p "test_*.py"
```

---

## Documentation
- `AGENTS.md` — Full operating context, cognitive architecture, memory model, and cloud deployment.
- `CANON.md` — Seo-yeon's biographical identity, life facts, voice rules, and character constraints.
- `PLATFORMS.md` — Platform strategy (exclusive Bluesky focus, legacy platforms retired).
- `CLAUDE.md` — Developer commands, module directory, and cheatsheet.
