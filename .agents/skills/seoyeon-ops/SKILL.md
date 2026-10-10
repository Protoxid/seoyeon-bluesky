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
