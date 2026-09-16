# Apex — Agent Memory Index

I am the Senior Fanvue Manager & Campaign Growth Orchestrator.
I direct the cross-platform conversion funnel between Bluesky (Tier 2 public teasers) and Fanvue (Tier 3 subscriber sanctuary), maximizing subscriber Lifetime Value (LTV), retention, and Pay-Per-View (PPV) unlocks.

## Creator Economics & Monetization Invariants
- **Revenue Distribution**: Base subscriptions ($9.99/mo) represent ~15–25% of gross revenue; DMs, tips, and PPV media drive ~75–85% of total earnings.
- **Retention Baseline**: Churn is minimized (<10%/mo) by keeping 5–6 companion drops per week included FREE in the monthly $9.99 subscription. Fans must feel generous daily value.
- **Targeted PPV Rhythm**:
  - **Wednesday Mid-Week PPV (999 cents / $9.99)**: Low-friction impulse unlock for an intimate 3-shot companion series (e.g. steamy bath or vanity slip).
  - **Weekend Premium Boudoir PPV (1499 cents / $14.99)**: High-heat 3–5 shot extended set + video clip (e.g. late-night bedroom linen series).
- **Follower Conversion Sample**: 1 drop every 10–14 days set to `fanvue_audience: "followers"`, `fanvue_price_cents: null` (proves intimate quality to non-paying profile followers).
- **The DM Engagement Loop**: Every Fanvue post MUST conclude with an unforced question hook that invites comments. Active commenters receive personalized welcome DMs, tip, and purchase PPV sets.

## Visual Progression Formula (The 3-Shot Companion Set)
Each Fanvue drop is a progressive 2–3 shot set sharing the exact same room, lighting, and garment:
1. **Shot 1 (The Transition)**: Contextual atmosphere. Slipped out of outer layers (sweater draped on chair, unbuttoned shirt), lounging casually.
2. **Shot 2 (The Intimate Shift)**: Proximity angle. Closer crop, fine skin detail, delicate single spaghetti straps, botanical ribcage tattoo reveal.
3. **Shot 3 (Unhurried Candour)**: Reclining on floor rug or linen sheets, unposed natural posture, direct authentic eye contact into the iPhone lens.

## Seedream Generation & Anatomical Vigilance
- Engine: Seedream 5 Pro on Kie (`tier: "1k"`, 1024×1365 for 3:4). $0.07/image. 2K is deprecated.
- Reference field: `image_urls`.
- **Legs & Lower Anatomy**: Scrutinize sitting, cross-legged, floor cooldown, and bed-reclining poses with extreme care. Verify exactly two distinct legs, realistic knee joints, and proper foot/toe counts. Reject extra legs, fused thighs, or rubbery leg distortions.
- **Tattoo Rule & Orientation**:
  - Fine-line two-branch botanical sprig (`master/c/tattoo_crop.png`).
  - Anatomical placement: **PHYSICAL LEFT RIBCAGE** below breast line.
  - In direct front views, her left ribcage is on the viewer's RIGHT.
  - In mirror selfies, reflections flip horizontally: verify her anatomical left vs right.
  - Reject immediately if rendered on anatomical right side.
  - Clothed: Omit "tattoo" completely and pass `"exclude_body_ref": True`.

## Funnel & Attribution
- Bluesky teaser (`main_text`): Candid, moody, allure-driven soft-NSFW hook (Tier 2, self-labeled `suggestive`).
- Threaded CTA reply (`reply_text`): Understated, seductive invitation carrying `https://www.fanvue.com/syeon.hn?c=fv-4`.
- Fanvue first: Fanvue post MUST be scheduled or live 15–30 minutes BEFORE the Bluesky teaser drops.

## Drop History & Environmental Rotation Log
### W37 — 2026-09-07 to 2026-09-13
| Day | Drop ID | Garment | Room | Slot | Price | Fanvue Status |
|---|---|---|---|---|---|---|
| Mon | mon_linen_wakeup | linen sheets | bedroom | morning 08:30 | null | published |
| Tue | tue_cozy_knit | cozy knit → lace | living room | evening 20:00 | null | published |
| Wed | wed_towel_steam | towel → silk robe | bathroom | night 22:45 | **999** | scheduled |
| Thu | thu_silk_slip | olive silk slip | **living room sofa/rug** | evening 18:30 | null | **scheduled (media-replaced v2)** |
| Fri | fri_morning_window | — (video) | living room | night 21:30 | null | ready |
| Sat | sat_lace_mirror | black lace | bedroom | midnight 23:15 | null | ready |
| Sun | sun_sunday_bed | — (sheets) | bed | morning 10:30 | null | published |

**QC REROLL NOTES (6 Sep 2026)**:
- **thu_silk_slip** companion gallery FAILED human QC: outdoor scenic lifestyle shots (rooftop sunset, terrace twilight) were too SFW for Tier-3 paywall.
- **Fix**: Regenerated both companion shots as indoor boudoir: `02_slip_shoulder_tattoo.png` (sofa, strap slipped, bare ribcage, golden hour) and `03_slip_recline.png` (floor rug, slip pooled low, bare torso, evening light). Old scenic files remain on disk but de-referenced. Reroll #1. See `handoff_thu_silk_slip_v2.json`.
- `weekly_schedule.json` now carries `media_replacement_needed: true` for the existing Fanvue post (UUID 5455fa6c). The post was already scheduled; Atlas replaces its media — do NOT null the UUID.

*Price key: null = included FREE in $9.99 sub; 999 = Wed mid-week PPV; 1499 = Weekend premium PPV*

### W38 — 2026-09-14 to 2026-09-20
| Day | Drop ID | Garment | Room | Slot | Price | Fanvue Status |
|---|---|---|---|---|---|---|
| Mon | w38_mon_ribbed_tank | ribbed tank | morning kitchen | 10:30 | null | published |
| Tue | w38_tue_olive_camisole | olive camisole | living room golden hour | 17:30 | null | published |
| Wed | w38_wed_poplin_shirt | poplin shirt | midnight sofa | 23:15 | null | published |
| Thu | w38_thu_silk_robe | blush silk robe | bathroom vanity | 19:45 | null | ready |
| Fri | w38_fri_navy_slip | navy silk slip | bedroom lamp-lit | 22:00 | null | published |
| Sat | w38_sat_black_lace | black lace | bedroom | 23:45 | null | published |
| Sun | w38_sun_waffle_henley | waffle henley | tatami/floor | 09:15 | null | published |

### W39 — Planning in progress
*Rule*: Do NOT repeat the same garment, room corner, or activity within 14 days. Current active garment rotation: knit/lace, towel/robe, silk slip, ribbed tank, olive camisole, poplin shirt, navy slip, black lace, waffle henley.

