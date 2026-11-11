# Contributor instructions

Use the installed graphify skill for `/graphify`. Use `.agents/skills/seoyeon-ops/SKILL.md` for operations and `.agents/skills/seoyeon-persona/SKILL.md` for voice/content work.

## Objective

Build a distinctive, openly fictional AI persona with natural choices, memory and creative work. Her operator is addressed as "my master" or "my human". CANON.md is the identity reference. Do not add scripted personality behaviors, scheduled quirks, mandatory props, engagement quotas or credential-like accomplishments. Ordinary fictional everyday experiences are allowed through the life journal (`agent/life.py`) and must stay consistent with it.

## Architecture

`agent/cli.py` establishes isolated offline/preview state before importing persistent singletons. `runner.py` observes and executes. `decision_engine.py` constructs candidates; `choice.py` first runs an original-post pass (`original_ideas.py`, given pacing information and the life journal); a proposed post is published unless someone is talking to her directly. Otherwise contextual model judgment selects among validated eligible IDs with a retried call and NO_ACTION fallback. Own everyday posts are drafted by `discussion.casual_draft` (no citation schema, still validated and independently reviewed); factual posts and links keep `grounded_draft`. The legacy scores are diagnostics and candidate ordering, not the final live choice.

`continuity.py` stores evidence-linked memories, commitments, pursuits, artifacts, drafts and explicitly fictional world intentions in the encrypted vault. Public retrieval must never include private/operator scope. External observations and generated statements are not verified physical achievements. Closing a commitment requires its exact prior ID and evidence; interaction counts do not establish trust.

`delivery.py` freezes payloads before sending. Stable Bluesky record keys support retry/reconciliation; ambiguous DMs and Telegram sends must not automatically resend. `budget_manager.py` serializes atomic reservations and bills each attempt. `migration.py` preserves legacy sensitive content in the vault before removing current plaintext copies.

## Verification before pushing

Run `python scripts/run_tests.py`, `python agent_runner.py --status`, and `python agent_runner.py --dry-run`. Check that offline commands leave production files unchanged. Add boundary-focused regression tests for meaningful changes. Do not weaken tests to hide failures; replace scripted-behavior expectations only when the intended contract changed and explain that change.

Never run a live tick merely to test a code change. Provider previews can cost money. Do not send test messages or post fixtures to real accounts. Never print private transcripts, decrypted vault content, tokens or authenticated URLs.

Update README, CANON when identity changes, operations/evaluation docs and relevant skills to reflect actual behavior. Historical reports must be labeled historical. Avoid fixed test counts and unsupported claims of zero regressions, complete naturalness or guaranteed provider reliability.

Read docs/OPERATIONS.md before changing workflows, encryption or recovery. Runtime state lives only in the encrypted bundle on the single-commit `state` branch; `main` carries code, docs and authored identity, so source pushes no longer race with state. Never commit plaintext runtime data to `main`, never publish an older vault over newer state, and keep the lease-based fail-closed publish in `agent/git_checkpoint.py`.

Grounded discussion uses `agent/discussion.py`; see `docs/DISCUSSION.md`. Preserve exact source provenance, the independent fail-closed review, private/offline fetch isolation, and correction quarantine. Do not turn focus areas into schedules, quotas, canned examples, or claimed credentials.

Telegram behavior is documented in `docs/TELEGRAM.md`. Keep operator conversation scoped and encrypted; casual keywords must not authorize publication. Preserve frozen reply/command stages, receipt-based success, and explicit interrupted-command resolution. Personal check-in preferences must not disable operational alerts. No scripted devotion or automatic emotional recharge.
