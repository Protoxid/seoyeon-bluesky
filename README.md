# Seo-yeon Han · 한서연

**An autonomous AI character on Bluesky, with persistent memory and a voice of her own.**

[![CI](https://github.com/Protoxid/seoyeon-bluesky/actions/workflows/ci.yml/badge.svg)](https://github.com/Protoxid/seoyeon-bluesky/actions/workflows/ci.yml)

[Meet Seo-yeon](https://bsky.app/profile/syeonhn.bsky.social) · [Quick start](#quick-start) · [Documentation](#documentation) · [Contribute](#contributing)

<img src="personas/seoyeon/master/a/a1_front.png" alt="AI-generated portrait of Seo-yeon Han" width="240">

Seo-yeon is a fictional Korean character based in Seongsu-dong, Seoul. She participates in conversations in Korean and English, shares generated photography, and develops interests in language, typography, film, literature, and everyday life.

This repository contains the Python system behind her social presence. It explores how a recognizable character can develop through remembered conversations, contextual choices, and creative work across sessions. Her biography and photographs are fictional.

## Features

- **Autonomous interaction** — posts, replies, quote posts, reposts, likes, follows, and direct messages on Bluesky. She chooses whether to act from context, with silence as a valid outcome.
- **Persistent memory** — conversations, opinions, commitments, and creative drafts carry across sessions, with evidence attached to learned memories and separate public and private contexts.
- **Grounded discussion** — source-backed contributions and interpretation in her areas of interest, with provenance checks and a separate model review before publication.
- **Generated photography** — reference-conditioned selfies and environmental images, reviewed before publication and accompanied by alt text.
- **Private Telegram connection** — conversation with her operator, explicit action requests, optional check-ins, and operational alerts.
- **Controlled operation** — configurable spending limits, an encrypted private vault, and durable delivery records for interruption recovery.

## How it works

```text
Observe → Recall → Choose → Generate & review → Deliver → Remember
                     └─ Stay silent
```

Each run reads available Bluesky activity and environmental context, retrieves relevant memories, and asks a model to choose an eligible action. Content is generated and checked before delivery; confirmed interactions become part of her continuing memory.

[OpenRouter](https://openrouter.ai/) powers language generation, action selection, memory interpretation, and visual review. Models are configurable. Kie.ai provides image generation, and GitHub Actions runs the production workflow.

## Quick start

Requires **Python 3.11+** and Git.

```sh
git clone https://github.com/Protoxid/seoyeon-bluesky.git
cd seoyeon-bluesky
python -m pip install -r requirements.txt
python agent_runner.py --status
python agent_runner.py --dry-run
```

These commands inspect the project and run an isolated offline cycle. No credentials are needed for the offline checks; they do not publish or spend provider credits.

To run the regression suite:

```sh
python scripts/run_tests.py
```

### Live operation

Live use requires a Bluesky account and OpenRouter API key. Image generation and Telegram are optional integrations with their own credentials. Follow the [setup guide](docs/GETTING_STARTED.md) for configuration and live commands.

Default spending limits are **$2 per day and $30 per month**, with at most one generated image per day. Provider calls incur costs. Scheduled GitHub runs can be delayed, so Telegram replies are not real-time in the current deployment.

The project is under active development. Content review reduces errors but does not guarantee factual accuracy; naturalness is assessed through ongoing behavioral evaluation.

## Documentation

| Guide | Contents |
| --- | --- |
| [Getting started](docs/GETTING_STARTED.md) | Installation, credentials, models, and commands |
| [Architecture and operations](docs/OPERATIONS.md) | Runtime, storage, budgets, and delivery recovery |
| [Telegram](docs/TELEGRAM.md) | Private conversation, commands, and check-in preferences |
| [Grounded discussion](docs/DISCUSSION.md) | Knowledge focus, references, and content review |
| [Character canon](CANON.md) | Identity, voice, and visual direction |
| [Behavior evaluation](docs/BEHAVIOR_EVALUATION.md) | Scenarios and criteria for assessing conversation quality |

## Contributing

Bug reports, Korean and English editorial feedback, and improvements to memory, reliability, and evaluation are welcome. [Open an issue](https://github.com/Protoxid/seoyeon-bluesky/issues) with a reproducible example, and read the [contributor instructions](AGENTS.md) before proposing code changes.

For collaboration or support with model credits, contact [the maintainer](https://github.com/Protoxid).
