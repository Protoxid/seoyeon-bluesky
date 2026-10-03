# MASTER HANDOFF DOCUMENT — Fanvue & Growth Automation
**Persona**: Seo-yeon Han (`@syeon.hn` / `@syeonhn.bsky.social`)  
**Date**: September 6, 2026  
**Status**: Core infrastructure operational across the 3 primary platforms: **Instagram**, **Bluesky**, and **Fanvue**.

---

## 1. Executive Summary & Active Platforms

| Platform | Role in Funnel | Account / Identity | Operating Status |
|---|---|---|---|
| **Instagram (IG)** | **Top-of-Funnel Aesthetic** | `@syeon.hn` | SFW lifestyle, architecture, Seongsu studio, Pilates. Funnels fans via bio link (`c=fv-2`). |
| **Bluesky** | **Viral Soft-NSFW Teasers** | `@syeonhn.bsky.social`<br>`did:plc:qmzkrqxywyhq4ar4k3nxdbvg` | Automated 24/7 cloud scheduler via GitHub Actions. Self-labeled `suggestive` posts with threaded conversion reply (`c=fv-4`). |
| **Fanvue** | **Monetization Sanctuary** | `@syeon.hn`<br>`24cd3144-7fc0-4087-a6d7-a4e328fb74ab` | $9.99/mo, multi-month bundles, PPV vaults. Seductive subscriber content, automated welcome DMs. |

---

## 2. Weekly Campaign Matrix & Cross-Platform Integrity

The single source of truth is [`growth/schedule_assets/weekly_schedule.json`](file:///c:/AI-Project/growth/schedule_assets/weekly_schedule.json).

| Day | Slot / Campaign | Fanvue Post UUID / Status | Bluesky Teaser Status | Notes |
|---|---|---|---|---|
| **Monday** | `mon_linen_wakeup` | `2e18ce9b-818c-4e17-b319-1690dc185cfc`<br>**LIVE** | **LIVE** (`at://.../3musahzizcv2n`) | Idempotency locked. Will NOT republish on Monday. |
| **Tuesday** | `tue_cozy_knit` | `02a350c3-7941-4df6-98a3-a4f34e566fac`<br>**LIVE** (3-shot set) | **READY** (20:00 KST) | Subscriber set live on Fanvue; ready for Bluesky teaser. |
| **Wednesday** | `wed_towel_steam` | `a1fa6066-1ef1-4a5b-9733-6a1c80df6fc6`<br>**SCHEDULED** (`2026-09-09T13:30Z`) | **READY** (22:45 KST) | Pre-scheduled 15m prior to Bluesky drop. Canon tattoo on ribs verified. |
| **Thursday** | `thu_silk_slip` | `5455fa6c-8f68-4830-86a2-2dccd2247ca0`<br>**SCHEDULED** (`2026-09-10T09:15Z`) | **READY** (18:30 KST) | Pre-scheduled 15m prior to Bluesky drop. Single-strap satin slip verified. |
| **Friday** | `fri_morning_window` | Pending Companion Generation | **READY** (21:30 KST video) | Video teaser ready (`fri_morning_window.mp4`). |
| **Saturday** | `sat_lace_mirror` | Pending Companion Generation | **READY** (23:15 KST) | Teaser ready (`sat_lace_mirror.png`). |
| **Sunday** | `sun_sunday_bed` | `75681e06-4ad6-4c6c-9d36-68fd6d349a45`<br>**LIVE** (Shot 02 Seductive Arch) | **LIVE** (`at://.../3mussukzox22c`) | Idempotency locked. Non-canon Shot 03 purged; Shot 02 live. |

---

## 3. Core Policy Decisions

### A. The "Fanvue Seduction Standard"
- **Instagram is SFW Lifestyle**: Wholesome, aesthetic, coffee, studio, street style.
- **Fanvue is Seductive Intimacy**: Subscriber content must be genuinely alluring, sensual, and intimate (boudoir, rumpled bedsheets, unbuttoned shirts, pulled-up loungewear, slipped straps, topless/underboob, bedroom eyes with parted lips). Wholesome lifestyle/IG photos must never be posted as Fanvue subscriber sets.

### B. 1K Resolution Tier Mandate
- All generations on Kie.ai (Seedream 5 Pro) use `"tier": "1k"` (`1024×1365` for 3:4).
- 2K tier is deprecated to conserve credits (~4x cost) while 1K retains authentic filmic sensor grain.

### C. Canon Tattoo & Anti-Defect Rules
- **Canon Tattoo**: Delicate, fine-line, two-branch minimalist botanical sprig on her **left ribcage** below the breast line (`personas/seoyeon/master/c/tattoo_crop.png`).
- **Clothed Torso Rule**: Passing body references (`c5_relax_front.png`) or mentioning "tattoo" during clothed generations causes diffusion models to stamp tattoos onto clothing fabric. Clothed shots must use `"exclude_body_ref": True` (passes only `a1_front.png` face master) and completely omit the word "tattoo" from the text prompt.
- **Bare Torso Rule**: Bare ribcage shots condition on `[a1_front, c5_relax_front, tattoo_crop]` and explicitly locate the tattoo: `"On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference."` Non-canon thick ferns or parallel-leaf mutations must be rejected.
- **Single Strap Guarantee**: Silk slips and camisoles explicitly prompt single clean spaghetti straps per shoulder to eliminate duplicate strap hallucinations.

### D. Automated Scheduling & Cloud Workers
- **GitHub Actions**: `.github/workflows/bluesky_scheduler.yml` executes 24/7 at 23:30 UTC (08:30 KST) and 11:30 UTC (20:30 KST).
- **Fanvue-First Policy**: Full companion sets are pre-scheduled natively on Fanvue 15 minutes before the Bluesky teaser drops.
- **Idempotency Guard**: Drops marked `"status": "published"` with an active URI (e.g. Monday and Sunday) are automatically skipped by `growth/bsky_schedule_worker.py` and `growth/campaign_orchestrator.py` to prevent duplicate postings. An explicit `--force` flag is required to override.

### E. Git Privacy Policy
- Subscriber carousels in `growth/schedule_assets/sets/` are excluded from Git via `.gitignore`. Only public teasers and metadata are committed to GitHub.

---

## 4. Daily Operator Command Cheatsheet

```powershell
# 1. Campaign status coherence check
python growth/campaign_orchestrator.py --status

# 2. Check Fanvue creator account status
python growth/fanvue_api.py --whoami

# 3. Process and welcome new Fanvue subscribers (idempotent)
python growth/fanvue_dm.py --welcome

# 4. Check and update financial attribution ledger
python growth/ledger.py --tick && python growth/ledger.py --report

# 5. Generate companion reveal shots (1K resolution)
python growth/generate_weekly_companion_sets.py --day fri
python growth/generate_weekly_companion_sets.py --day sat

# 6. Dispatch or simulate synchronized drops
python growth/campaign_orchestrator.py --dispatch [drop_id] --dry-run
python growth/campaign_orchestrator.py --auto
```

---

## 5. Key File Inventory

* `growth/schedule_assets/weekly_schedule.json` — Authoritative schedule metadata across Fanvue and Bluesky.
* `growth/campaign_orchestrator.py` — Synchronized campaign manager verifying Fanvue existence before Bluesky dispatch.
* `growth/bsky_schedule_worker.py` — Bluesky AT Protocol dispatch worker with self-labels, threaded replies, and idempotency checks.
* `growth/generate_weekly_companion_sets.py` — 1K multi-shot reveal generator with anti-tattoo-bleed and canon sprig conditioning.
* `growth/fanvue_api.py` — Official Fanvue API client (multipart S3 media uploads, posts, DMs, tracking links, automated messages).
* `growth/fanvue_dm.py` — Welcome message automation engine for subscribers.
* `growth/links.json` — Active Fanvue attribution tracking links.
* `growth/welcomed.json` — Registry of already-welcomed subscribers.
* `growth/ledger.jsonl` — Append-only audit trail of all automated actions and API calls.
* `.github/workflows/bluesky_scheduler.yml` — Automated cloud cron scheduler running on GitHub Actions.
