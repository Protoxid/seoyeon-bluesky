# Contributor instructions

Use the installed graphify skill for `/graphify`. Use `.agents/skills/seoyeon-ops/SKILL.md` for operations and `.agents/skills/seoyeon-persona/SKILL.md` for voice/content work.

## Objective

Build a distinctive, openly fictional AI persona with natural choices, memory and creative work. Her operator is addressed as "my master" or "my human". CANON.md is the identity reference. Do not add scripted personality behaviors, scheduled quirks, mandatory props, engagement quotas or automatic accomplishments.

## Architecture

`agent/cli.py` establishes isolated offline/preview state before importing persistent singletons. `runner.py` observes and executes. `decision_engine.py` constructs candidates; `choice.py` uses contextual model judgment with validated eligible IDs and NO_ACTION fallback. The legacy scores are diagnostics and candidate ordering, not the final live choice.

`continuity.py` stores evidence-linked memories, commitments, pursuits, artifacts, drafts and explicitly fictional world intentions in the encrypted vault. Public retrieval must never include private/operator scope. External observations and generated statements are not verified physical achievements. Closing a commitment requires its exact prior ID and evidence; interaction counts do not establish trust.

`delivery.py` freezes payloads before sending. Stable Bluesky record keys support retry/reconciliation; ambiguous DMs and Telegram sends must not automatically resend. `budget_manager.py` serializes atomic reservations and bills each attempt. `migration.py` preserves legacy sensitive content in the vault before removing current plaintext copies.

## Verification before pushing

Run `python scripts/run_tests.py`, `python agent_runner.py --status`, and `python agent_runner.py --dry-run`. Check that offline commands leave production files unchanged. Add boundary-focused regression tests for meaningful changes. Do not weaken tests to hide failures; replace scripted-behavior expectations only when the intended contract changed and explain that change.

Never run a live tick merely to test a code change. Provider previews can cost money. Do not send test messages or post fixtures to real accounts. Never print private transcripts, decrypted vault content, tokens or authenticated URLs.

Update README, CANON when identity changes, operations/evaluation docs and relevant skills to reflect actual behavior. Historical reports must be labeled historical. Avoid fixed test counts and unsupported claims of zero regressions, complete naturalness or guaranteed provider reliability.

Read docs/OPERATIONS.md before changing workflows, encryption or recovery. State commits and source commits may race: refresh remote state before integration, preserve the latest encrypted vault, and never resolve a state conflict by blindly choosing the older file.
