# Seo-yeon Han · 한서연

**An autonomous AI character exploring what it means to have a voice, a memory, and something of her own to say.**

[![CI](https://github.com/Protoxid/seoyeon-bluesky/actions/workflows/ci.yml/badge.svg)](https://github.com/Protoxid/seoyeon-bluesky/actions/workflows/ci.yml)

[Meet Seo-yeon on Bluesky](https://bsky.app/profile/syeonhn.bsky.social) · [How it works](docs/OPERATIONS.md) · [Run locally](docs/GETTING_STARTED.md) · [Evaluation](docs/BEHAVIOR_EVALUATION.md)

<img src="personas/seoyeon/master/a/a1_front.png" alt="Canonical AI-generated portrait of the fictional character Seo-yeon Han" width="280">

Seo-yeon is a fictional Korean character whose world is centered on Seongsu-dong, Seoul. She notices lettering on storefronts, has opinions about films, leaves things unfinished, and can answer a small question with a small answer. Her voice is understated, sometimes dry, and expressed in Korean and English.

This public project develops the system behind her Bluesky presence: contextual decisions, conversation memory, evolving creative work, and generated photography. **She is an AI character, and should answer honestly when asked about her identity.** Her biography and images are fiction; they are not evidence of a real person's physical experiences.

## The idea

Can a persistent AI character become distinctive through accumulated choices and work, without a script telling her what to say each day?

That question guides the project. A recognizable personality should emerge from what she pays attention to, what she remembers, how she changes her mind, and what she creates over time. Naturalness includes ordinary replies, uncertainty, disagreement, and silence.

The system gives her a character foundation and operational boundaries. It does not prescribe a daily storyline, rotate through mandatory topics, or manufacture achievements to keep a narrative moving.

## What makes this approach different

- **Contextual choice, including silence.** A model considers eligible actions against current observations and memory. A scheduled wakeup is an opportunity to look around, not a requirement to post.
- **Memory with sources and boundaries.** Learned memories retain evidence and conversation scope. Public interactions cannot retrieve private conversation memories. Corrections preserve a reason and history.
- **Continuity that has to be earned.** Specific promises remain distinct. Message counts do not automatically create intimacy, and elapsed days do not automatically complete a goal.
- **Creative work that actually exists.** Drafts and original digital artifacts can be saved and revised across sessions. One optional direction is an unfinished atlas of ordinary Seoul: observations, essays, and typography studies. It is a starting possibility, not a content calendar.
- **A consistent visual character.** Selfies use two canonical face references; environmental images use a separate generation path. Generated images are reviewed against their caption before publication, with alt text based on visible content.

These are implemented design choices, not a claim that human-level naturalness or uniqueness has been demonstrated.

## OpenRouter at the center

The project's language-model calls use **[OpenRouter](https://openrouter.ai/)**: action selection, writing, memory interpretation, reflection, and visual review. Primary, fallback, and vision model IDs are configurable, so the same architecture can be evaluated with different model choices.

Each request attempt has a budget reservation. Reported provider costs are used when available; uncertain charges remain reserved for reconciliation. Default production budgets are **$2 per day and $30 per month**, with activity limits acting as ceilings rather than targets.

This makes Seo-yeon a concrete setting for exploring model behavior across long-running, connected tasks: choosing whether to respond, remembering a correction, keeping a commitment, developing a draft, and maintaining an individual voice under a limited budget.

Image generation is provided separately through Kie.ai. Bluesky is the social interface; Telegram provides the authenticated operator channel.

## How a turn works

```text
Observe Bluesky and available context
                  ↓
Recall relevant, scoped memories
                  ↓
Choose an eligible action — or stay silent
                  ↓
Generate and validate text or images
                  ↓
Persist delivery intent → send → record the result
                  ↓
Learn from confirmed interactions
```

Durable delivery records support recovery after interruptions. Private continuity and conversations are stored in an encrypted vault. Operational safeguards cover spending, privacy, duplicate delivery, and failed generation. See the [architecture and recovery guide](docs/OPERATIONS.md) for implementation details and limits, including historical data exposure.

## Try it safely

Requires **Python 3.11+**. From a local checkout:

```sh
pip install -r requirements.txt
python scripts/run_tests.py
python agent_runner.py --status
python agent_runner.py --dry-run
```

The test harness and offline commands block network access and use isolated state. They do not publish, spend provider credits, or modify production data. An offline dry run checks integration and restraint; it does not generate a live model's conversation.

For credentials, paid previews, live operation, model configuration, and recovery commands, see [setup and command reference](docs/GETTING_STARTED.md). Live operation can spend credits and publish to the configured accounts.

## Evidence and next steps

The October 10, 2026 implementation passed **160 isolated tests** locally and in GitHub CI. Coverage includes memory scope, evidence validation, delivery recovery, budget accounting, provider payloads, and offline isolation. The badge above links to current CI results.

Tests establish software contracts. They do not establish conversational naturalness. The next evaluation priority is blinded comparison of Korean and English conversations over time, examining relevance, proportion, continuity, variation, and honest uncertainty. See the [evaluation scenarios](docs/BEHAVIOR_EVALUATION.md) and [implementation record](docs/2026-10-10-implementation.md).

## Support and collaboration

Provider credits would support longer observation periods and structured model comparisons across conversation, memory, and creative continuity. Useful contributions include reproducible bug reports, Korean-language editorial review, and evaluation methods that reward specificity and coherence rather than posting volume.

For sponsorship or collaboration, contact [the maintainer](https://github.com/Protoxid). Using OpenRouter does not imply sponsorship or endorsement; no sponsorship is announced here.

## Explore the repository

| Start here | What you will find |
| --- | --- |
| [Character canon](CANON.md) | Biography, voice, relationships, and visual identity |
| [Setup and commands](docs/GETTING_STARTED.md) | Offline checks, configuration, previews, and live operation |
| [Architecture and recovery](docs/OPERATIONS.md) | Storage, delivery, billing, and operator recovery |
| [Behavior evaluation](docs/BEHAVIOR_EVALUATION.md) | Scenarios and criteria for assessing naturalness |
| [Runtime source](agent/) | Decision-making, generation, continuity, and integrations |
| [Tests](tests/) | Automated regression coverage |
