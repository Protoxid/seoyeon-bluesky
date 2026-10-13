---
name: seoyeon-ops
description: Operate, test and diagnose the Seo-yeon Bluesky runtime, encrypted state, provider billing and delivery recovery.
---

# Seo-yeon operations

Read README and docs/OPERATIONS.md for current commands. Use `python scripts/run_tests.py`: it creates a disposable checkout, removes credentials and blocks network access.

Before pushing code, run the isolated suite, `python agent_runner.py --status`, and `python agent_runner.py --dry-run`. Offline status deliberately hides credentials and does not fetch live weather. Verify these commands leave production data unchanged. Do not require a particular action, draft or test count.

`--auto`, `--check-master`, `--daily-summary`, `--ask-master`, `--force-plan` and `--consolidate` are live operational commands. Do not run them merely as tests. `--preview` can incur real provider charges despite blocking publication and isolating state; it does not debit the production ledger.

For uncertainty, inspect `python scripts/maintain.py pending`. Verify provider receipts before reconciliation. Never automatically resend a timed-out DM or Telegram message. Never discard submitted cost reservations because time passed. Failed vault decryption blocks saving; preserve ciphertext and keys.

Do not print private messages, decrypted files or tokens. Production checkpoint configuration requires explicit operational authorization. Preserve the latest remote state when integrating source changes.

The operator is addressed as "my master" or "my human". This skill does not authorize messaging, publishing, spending or production changes outside the user's scope.

Read `docs/DISCUSSION.md` for focused knowledge contribution. Preserve source/quote validation and review before social publication; missing evidence permits only grounded interpretation, ordinary conversation or silence. No reply quotas, canned lessons, fabricated expertise or consequential personalized advice. Research must not send private messages to websites; model review is probabilistic and requires editorial evaluation.

When diagnosing inactivity, distinguish missing wakeups from chosen silence, invalid model choice, draft/review rejection, and delivered or explicitly abandoned social operations removed before selection. Abandonment must not become a successful receipt or an automatic retry. A recovered receipt is not evidence of a new like. Interaction learning logs contain status only; a valid empty update must remain permissible. External scheduler cutover requires a successful offline workflow dispatch and verified activation before removing the existing schedule; keep one periodic dispatcher.

Telegram behavior is documented in `docs/TELEGRAM.md`. Keep operator conversation scoped and encrypted; casual keywords must not authorize publication. Preserve frozen reply/command stages, receipt-based success, and explicit interrupted-command resolution. Personal check-in preferences must not disable operational alerts. No scripted devotion or automatic emotional recharge.

Checkpoint push failures use bounded retry and exact remote-commit verification. Check the categorized diagnostic; do not bypass persistence or force push to make a run green. Final workflow persistence must attempt already-created commits even with a clean index. Remote divergence requires state review, never blind encrypted-vault replacement.
