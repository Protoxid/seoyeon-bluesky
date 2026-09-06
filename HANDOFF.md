# Master Project Handoff — Seo-yeon Han AI Persona
**Date**: September 6, 2026  
**Primary Working Root**: `C:\AI-Project` (mirrored to `C:\AI-Project - Copia`)  
**Core Active Platforms**: **Instagram**, **Bluesky** (`@syeonhn.bsky.social`), **Fanvue** (`@syeon.hn`).

---

## 1. Executive Platform Architecture (The 3 Core Platforms)

```
[ Instagram (@syeon.hn) ]                [ Bluesky (@syeonhn.bsky.social) ]
   (SFW Aesthetic Lifestyle)                (Candid Soft-NSFW Teasers)
   • Seongsu daily life, Pilates, studio    • Daily automated teaser drops
   • Bio Link: c=fv-2                       • Threaded CTA Reply: c=fv-4
             │                                         │
             └───────────────────┬─────────────────────┘
                                 ▼
                     [ Fanvue (@syeon.hn) ]
                 (Seductive Subscriber Sanctuary)
                 • $9.99/mo + Multi-Month Bundles
                 • Intimate Progressive Reveals (Shot 02 & 03)
                 • Seduction Standard (18+ Boudoir / Linen)
                 • Automated Welcome DMs
```

1. **Instagram (IG)**: Top-of-funnel public lifestyle and aesthetic credibility. SFW, sophisticated visual designer persona in Seongsu-dong. High-intent traffic flows to the Fanvue bio tracking link (`https://www.fanvue.com/syeon.hn?c=fv-2`).
2. **Bluesky (`@syeonhn.bsky.social`)**: High-velocity organic reach and viral teaser funnel. Soft-NSFW suggestive snapshots published with `suggestive` self-labels. Each post automatically threads a conversion reply driving fans to Fanvue (`https://www.fanvue.com/syeon.hn?c=fv-4`). 24/7 automated scheduling via GitHub Actions.
3. **Fanvue (`@syeon.hn`)**: Direct monetization and subscriber sanctuary. Features progressive multi-shot companion sets delivering on Bluesky teasers, automated welcome DMs, and PPV vaults.

---

## 2. Cross-Platform Weekly Campaign Status

The single source of truth is [`growth/schedule_assets/weekly_schedule.json`](file:///c:/AI-Project/growth/schedule_assets/weekly_schedule.json).

| Day | Slot / Campaign | Fanvue Status (`publishAt`) | Bluesky Teaser Status | Funnel Integrity |
| :--- | :--- | :--- | :--- | :--- |
| **Monday** | `mon_linen_wakeup` | **LIVE** (`2e18ce9b...`) | **LIVE** (`3musahzizcv2n`) | `[VERIFIED]` Idempotency Locked (Will NOT republish) |
| **Tuesday** | `tue_cozy_knit` | **LIVE** (`02a350c3...`, 3-shot set) | **READY** (20:00 KST) | `[VERIFIED]` Ready for automated dispatch |
| **Wednesday** | `wed_towel_steam` | **SCHEDULED** (`a1fa6066...` @ 22:30 KST) | **READY** (22:45 KST) | `[VERIFIED]` 15m Lead Time Enforced |
| **Thursday** | `thu_silk_slip` | **SCHEDULED** (`5455fa6c...` @ 18:15 KST) | **READY** (18:30 KST) | `[VERIFIED]` 15m Lead Time Enforced |
| **Friday** | `fri_morning_window` | Pending Companion Generation | **READY** (21:30 KST video) | Awaiting Friday companion shots |
| **Saturday** | `sat_lace_mirror` | Pending Companion Generation | **READY** (23:15 KST) | Awaiting Saturday companion shots |
| **Sunday** | `sun_sunday_bed` | **LIVE** (`75681e06...`, Seductive Shot 02) | **LIVE** (`3mussukzox22c`) | `[VERIFIED]` Idempotency Locked (Will NOT republish) |

---

## 3. Key Operating Decisions & Invariants

### A. The "Seduction Standard" (Fanvue vs. Instagram)
- **Instagram**: SFW lifestyle, candid laughs, coffee mugs, architectural interiors, Pilates training.
- **Fanvue Exclusives**: Intimate, alluring, and seductive subscriber content. Boudoir intimacy, pulled-up loungewear, untangled bedsheets, slipped straps, topless/underboob, bedroom eyes, and parted lips. Wholesome lifestyle photos must **never** be posted to Fanvue.

### B. 1K Resolution Tier Strictly Enforced
- All generations on Kie.ai (Seedream 5 Pro) use `"tier": "1k"` (`1024×1365` for 3:4 aspect ratio).
- 2K tier is deprecated: 1K provides identical photographic sensor grain, faster turnaround, and conserves API credits (~4x cheaper).

### C. Canon Tattoo & Anti-Defect Rules
- **Canon Tattoo**: A delicate, fine-line, two-branch minimalist botanical sprig on her **left ribcage** below the breast line (`personas/seoyeon/master/c/tattoo_crop.png`).
- **Clothed Torso Rule**: Passing body references (`c5_relax_front.png`) or mentioning "tattoo" during clothed generations causes diffusion models to stamp tattoos onto clothing fabric. Clothed shots must use `"exclude_body_ref": True` (passes only `a1_front.png` face master) and completely omit the word "tattoo" from the text prompt.
- **Bare Torso Rule**: Bare ribcage shots condition on `[a1_front, c5_relax_front, tattoo_crop]` and explicitly locate the tattoo: `"On her bare left ribcage, running vertically just below the breast line, is the delicate fine-line botanical sprig tattoo shown in the reference."` Non-canon thick ferns or parallel-leaf mutations must be rejected.
- **Single Strap Guarantee**: Silk slips and camisoles explicitly prompt single clean spaghetti straps per shoulder to eliminate duplicate strap hallucinations.

### D. Cloud Scheduler & Idempotency
- **Workflow**: `.github/workflows/bluesky_scheduler.yml` triggers 24/7 on GitHub Actions at 23:30 UTC (08:30 KST) and 11:30 UTC (20:30 KST).
- **Fanvue-First Policy**: Full companion sets are pre-scheduled natively on Fanvue 15 minutes before the Bluesky teaser drops.
- **Idempotency Guard**: Drops marked `"status": "published"` with an active URI (e.g. Monday and Sunday) are automatically skipped by `growth/bsky_schedule_worker.py` and `growth/campaign_orchestrator.py` to prevent duplicate postings. An explicit `--force` flag is required to override.

### E. Git Privacy Policy
- Subscriber carousels in `growth/schedule_assets/sets/` are excluded from Git via `.gitignore`. Only public teasers and metadata are committed to GitHub.

---

## 4. Daily Operator Command Cheatsheet

All commands run from the repository root:

```powershell
# 1. Inspect cross-platform campaign coherence
python growth/campaign_orchestrator.py --status

# 2. Check Fanvue account identity, balance, and subscriber count
python growth/fanvue_api.py --whoami

# 3. Process new Fanvue subscriber welcome DMs (idempotent)
python growth/fanvue_dm.py --welcome

# 4. Generate Friday and Saturday companion reveal sets (1K resolution)
python growth/generate_weekly_companion_sets.py --day fri
python growth/generate_weekly_companion_sets.py --day sat

# 5. Dispatch or simulate a synchronized drop
python growth/campaign_orchestrator.py --dispatch [drop_id] --dry-run
python growth/campaign_orchestrator.py --auto
```
