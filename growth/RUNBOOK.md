# RUNBOOK — the commands and the weekly loop
Every flag below was read out of the script's own `add_argument` calls on
6 Sep 2026, not copied from an older cheatsheet. If a command errors on an
unknown flag, the script changed — fix it here rather than working around it.

**All API calls run on the Windows box.** `queue.fal.run` and `api.kie.ai` are
blocked from the cloud container and from `device_bash`. Run everything from
`C:\AI-Project` in PowerShell.

---

## THE DAILY LOOP

```powershell
# 1. Does the plan still hold together? Verifies Fanvue before Bluesky.
python growth\campaign_orchestrator.py --status

# 2. Dispatch today's drop — dry run first, always.
python growth\campaign_orchestrator.py --dispatch <drop_id> --dry-run
python growth\campaign_orchestrator.py --dispatch <drop_id>

# 3. Welcome any new subscriber. Idempotent: a second run sends nothing.
python growth\fanvue_dm.py --welcome --dry-run
python growth\fanvue_dm.py --welcome

# 4. Record the day.
python growth\ledger.py --tick
```

`--auto` on the orchestrator picks the drop by day instead of naming one. That
is what GitHub Actions runs; use `--dispatch` by hand so you know what went.

## THE WEEKLY LOOP

```powershell
# Sunday — plan, then generate what the plan needs
python growth\generate_weekly_companion_sets.py --day fri --dry-run
python growth\generate_weekly_companion_sets.py --day fri

# Read the week back
python growth\bsky_schedule_worker.py --list
python growth\ledger.py --report
```

## CHECKS BEFORE PUBLISHING

```powershell
python growth\fanvue_api.py --whoami                 # token, account, balance
python personas\seoyeon\check_reel.py <file>         # video vs Meta's spec
python personas\seoyeon\audit.py                     # prompt-rule audit
python personas\seoyeon\audit_video.py
```

## MONEY

```powershell
python growth\ledger.py --report
python growth\ledger.py --spend --platform kie --eur 5.00 --note "top-up"
```
Every script that spends takes `--budget` and refuses without one.

---

## FLAG REFERENCE — verified 6 Sep 2026

| script | flags |
|---|---|
| `campaign_orchestrator.py` | `--status --sync-fanvue --sync-drop --dispatch --auto --dry-run --force` |
| `bsky_schedule_worker.py` | `--auto --drop --list --dry-run --force` |
| `fanvue_api.py` | `--whoami --make-links --post --text --image --audience --price-cents --list-automated --setup-automated --set-price --create-promo --promo-group --dry-run` |
| `fanvue_dm.py` | `--welcome --dry-run --test-idempotency` |
| `generate_weekly_companion_sets.py` | `--day --shot --force --dry-run` |
| `ledger.py` | `--tick --report --spend --platform --eur --note --sync-spend` |
| `syndicate.py` | `--due --all --dry-run --queue --lanes --budget` |

## WHAT NOT TO RUN

- **`syndicate.py --due` against the old queue.** `queue.jsonl` was retired on
  6 Sep 2026; everything schedules from `weekly_schedule.json` now.
- **Anything with `--force`** unless you have read why the guard fired.

## AUTOMATION THAT RUNS WITHOUT YOU

`.github/workflows/bluesky_scheduler.yml` — GitHub Actions, 23:30 and 11:30
UTC. Credentials come from GitHub Secrets (`BSKY_HANDLE`,
`BSKY_APP_PASSWORD`), never from the repo. It calls
`bsky_schedule_worker.py --auto`, and skips any drop already marked published.
