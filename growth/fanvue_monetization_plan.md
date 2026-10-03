# Fanvue Monetization & Automation Plan — Seo-yeon Han (@syeon.hn)

Comprehensive operational blueprint for subscription pricing, multi-month retention bundles, PPV soft-NSFW content packs, and automated direct messaging (DMs).

---

## 1. Subscription Pricing & Multi-Month Bundles

### Creator Economics & Revenue Split Reality
Based on top creator and platform benchmarks on Fanvue:
* **The "Access Door" Mindset**: Base subscriptions ($9.99/mo) account for ~15–25% of total gross revenue. Their primary function is qualifying intent and establishing a committed audience.
* **The Core Revenue Engine**: Direct messaging (DMs), tips, and Pay-Per-View (PPV) unlocks generate **75–85% of total creator revenue**.
* **Retention Rule**: Churn is minimized (<10% monthly) by providing high-continuity daily value on the subscriber feed. Subscribers must never feel nickel-and-dimed on standard posts; PPV is reserved for peak-heat or extended companion series.

### Monthly Base Subscription
* **Recommended Price**: **$9.99 / month** (€9.99 / 999 cents).
* **Rationale**: Optimal entry barrier for soft-NSFW aesthetic creators (Pilates instructor, athletic hourglass, Seoul lifestyle, intimate Seongsu flat moments). High enough to maintain perceived exclusivity; low enough to achieve strong impulse conversion from social funnels (Bluesky, Instagram, Threads).

### Multi-Month Retention Bundles
Configured in Fanvue Creator Settings (**Settings > Subscriptions > Subscription Bundles**):

| Tier | Duration | Discount | Price to Fan | Monthly Equivalent | Primary Goal |
|---|---|---|---|---|---|
| **Monthly** | 1 Month | — | **$9.99** | $9.99/mo | Initial acquisition / trial |
| **3-Month Bundle** | 3 Months | **10% OFF** | **$26.97** | $8.99/mo | Lock in first quarter retention |
| **6-Month Bundle** | 6 Months | **15% OFF** | **$50.95** | $8.49/mo | Maximize mid-term LTV |
| **12-Month VIP** | 12 Months | **25% OFF** | **$89.91** | $7.49/mo | High-intent superfans |

### Launch Promotion
* **Launch Offer**: **30% OFF First Month** ($6.99 instead of $9.99).
* **Cap**: Limited to the first 100 new subscribers to create scarcity.

---

## 2. Automatic DM & Fan Retention Architecture

Fanvue automation operates on a **2-Tier Hybrid Model**:

### Tier 1: Client-Side Automated DM Engine (`growth/fanvue_dm.py`)
* **Status**: **Fully Live & Operational** (uses verified `read:fan`, `read:chat`, `write:chat` scopes).
* **The 24–48h Golden Window**: New subscribers are most emotionally invested within their first 24–48 hours. The welcome engine initiates warm, non-sales interaction immediately upon subscription.
* **How it Works**:
  1. Polls new subscribers from `GET /v1/chats/lists/smart/subscribers`.
  2. Diffs against local registry [`growth/welcomed.json`](file:///c:/AI-Project/growth/welcomed.json).
  3. Sends warm, in-character welcome DM dynamically extracted from [`growth/fanvue_profile.md`](file:///c:/AI-Project/growth/fanvue_profile.md).
  4. Immediately records the subscriber in `welcomed.json` (crash-resilient) and logs the transaction to [`growth/ledger.jsonl`](file:///c:/AI-Project/growth/ledger.jsonl).
  5. 100% idempotent (running consecutive times with no new subscribers sends 0 messages).

**Active Welcome DM Copy**:
> *"hey, thank you for subscribing. i'm usually either at the studio in seongsu or drinking cold brew at my desk in my flat. i post the quieter, more personal side of things here that doesn't go on instagram.*
> 
> *what time is it where you are right now?"*

### Tier 2: Fanvue Server-Side Automated Message Triggers
Configured via `PUT /chats/automated-messages/{trigger}` to deliver instant, sub-second responses 24/7 without requiring local script polling:

| Trigger Event | Target Audience | Copy & Strategy | Price |
|---|---|---|---|
| `new_subscriber` | New paying subscriber | Warm instant greeting with low-friction timezone question. | FREE |
| `new_follower` | Free profile followers | Alluring hook explaining that the candid/private soft-NSFW side stays on the subscriber feed. | FREE |
| `renewed` | Subscription auto-renewal | Gratitude DM acknowledging their loyalty and teasing upcoming drops. | FREE |
| `subscription_canceled` | Unsubscribed fans | Warm, zero-pressure check-in thanking them for being part of the circle. | FREE |
| `first_message_reply` | Fan's first incoming DM | Auto-acknowledgment that she is in the studio/gym and will reply once at her desk. | FREE |

> [!NOTE]
> Setting server-side triggers and updating creator pricing via API requires the `write:creator` OAuth scope. If Shade checks `write:creator` in the Fanvue Developer Portal, running `python growth/fanvue_api.py --setup-automated` deploys all 5 triggers in one command. In the meantime, Tier 1 (`growth/fanvue_dm.py`) handles welcome DMs automatically with our active chat scopes.

---

## 3. Weekly Posting Cadence & Pay-Per-View (PPV) Catalog

### Weekly Content & Monetization Rhythm
To balance high subscriber retention with maximum Lifetime Value (LTV):
* **5–6 Base Drops/Week (`subscribers`, included FREE)**: Builds subscriber loyalty, reinforces parasocial intimacy, and keeps churn <10%.
* **1 Mid-Week Impulse PPV (`subscribers`, €9.99 / 999 cents)**: Low-friction unlock for a high-intimacy 3-shot series (e.g. steamy bathroom or post-shower vanity).
* **1 Weekend Premium Boudoir PPV (`subscribers`, €14.99 / 1499 cents)**: High-heat 3–5 shot extended companion set + short video clip (e.g. late-night bedroom linen candlelit series).
* **1 Follower Conversion Sample Every 10–14 Days (`followers`, FREE)**: High-converting sample to convert non-paying profile followers.

All images rendered at `"tier": "1k"` via Seedream 5 Pro (1024×1365 for 3:4 ratio; filmic grain, 4x cheaper than 2K).

### PPV Bundle Catalog

| Bundle Name | Contents | Delivery Method | Price | Description & Angle |
|---|---|---|---|---|
| **Bundle 1: Morning Intimates** | 3 × 1K Soft-NSFW Shots (`fv_ex_lace_mirror`, `fv_ex_unbuttoned_linen`, + exclusive bed variant) | PPV Feed Post or Mass DM | **€9.99** ($9.99) | Raw morning light, unmade white linen sheets, delicate black lace bralette & briefs, unbuttoned oversized shirt. |
| **Bundle 2: Steamy Bathroom Series** | 3 × 1K Soft-NSFW Shots (`fv_ex_towel_steam`, tub edge slip, post-shower mirror check) | PPV DM with free preview | **€14.99** ($14.99) | Steamy bathroom atmosphere, wet hair, bath towel draped low, condensation on glass, unretouched skin texture. |
| **Bundle 3: Late-Night Boudoir** | 5 × 1K Intimate Shots + 1 Short Video Clip | Locked PPV DM | **€24.99** ($24.99) | Dim warm lamp lighting, silk chemise/loungewear, candlelit Seongsu bedroom, intimate conversation tone. |

### Technical Execution via CLI
* **Publish PPV Feed Post**:
  ```bash
  python growth/fanvue_api.py --post --image personas/seoyeon/content/fanvue/fv_ex_lace_mirror.png --text "private morning set 🖤☕" --audience subscribers --price-cents 999
  ```
* **Send In-Character Welcome DMs**:
  ```bash
  python growth/fanvue_dm.py --welcome
  ```

---

## 4. Attribution & Revenue Funnel

Every acquisition link directs to Fanvue with automated channel tracking tags in [`growth/links.json`](file:///c:/AI-Project/growth/links.json):
* **Instagram**: `https://www.fanvue.com/syeon.hn?c=fv-2`
* **X**: `https://www.fanvue.com/syeon.hn?c=fv-3`
* **Bluesky**: `https://www.fanvue.com/syeon.hn?c=fv-4` (active in profile bio)
* **Threads**: `https://www.fanvue.com/syeon.hn?c=fv-5`
* **Reddit**: `https://www.fanvue.com/syeon.hn?c=fv-6`
* **YouTube**: `https://www.fanvue.com/syeon.hn?c=fv-7`

Financial performance, click-through rates, conversion to paid subscribers, and net revenue per channel are synced automatically to [`growth/financial_ledger.jsonl`](file:///c:/AI-Project/growth/financial_ledger.jsonl) via:
```bash
python growth/ledger.py --tick && python growth/ledger.py --report
```
