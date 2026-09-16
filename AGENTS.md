# Seo-yeon Han AI Persona — Operating Context & Architecture

This repository powers the autonomous presence, content generation, and cross-platform growth funnel for **Seo-yeon Han (한서연)**, a 26-year-old Korean visual designer & Pilates practitioner based in Seongsu-dong, Seoul.

---

## 1. Active Platform Focus
We actively maintain **3 primary platforms**:
1. **Instagram (IG)**: Top-of-funnel public lifestyle aesthetic.
   - SFW, sophisticated Seoul city life, coffee, Pilates, minimalist design studio, warm architecture.
   - Audience bridge: High-intent fans funnel through the bio tracking link (`https://www.fanvue.com/syeon.hn?c=fv-2`).
2. **Bluesky (`@syeonhn.bsky.social`)**: Organic viral growth & suggestive teaser funnel.
   - Soft-NSFW candid snapshots, suggestive self-label (`com.atproto.label.defs#selfLabels` = `suggestive`).
   - Every teaser includes an immediate threaded reply with a tracked conversion link to Fanvue (`c=fv-4`).
   - Automated 24/7 dispatch via GitHub Actions and `growth/bsky_schedule_worker.py`.
3. **Fanvue (`@syeon.hn`)**: Monetization engine & exclusive subscriber sanctuary.
   - Paid 18+ subscriber feed ($9.99/mo, multi-month bundles, PPV vaults).
   - Intimate, alluring, progressive reveals delivering on Bluesky teasers.
   - Automated welcome DMs via `growth/fanvue_dm.py`.

---

## 2. The Fanvue "Seduction Standard" (Content Differentiation)
- **Instagram is SFW Lifestyle**: Wholesome, aesthetic, coffee, studio, street style.
- **Fanvue is Seductive Intimacy**: Subscriber content must be genuinely alluring, sensual, and intimate (boudoir, rumpled bedsheets, unbuttoned shirts, pulled-up loungewear, slipped straps, topless/underboob, bedroom eyes with parted lips).
- **Rule**: Do **NOT** generate wholesome lifestyle/IG photos for Fanvue subscriber sets. Deliver on what the teaser promised.

---

## 3. Image Generation & Anti-Defect Invariants
All generation runs on **Kie.ai**:
- **Generators**:
  - **Tier 1 (SFW / Lifestyle)**: `gpt-image-2-5-sunburst-image-to-image` (or `gpt-image-2-text-to-image` for no-face still-life).
  - **Tiers 2 & 3 (Suggestive / Intimate)**: `seedream/5-pro-image-to-image`.
- **Resolution Tier**: **Strictly enforce `"tier": "1k"`** (`1024×1365` for 3:4). 2K is deprecated to conserve credits (~4x cost) while 1K retains authentic filmic sensor grain.
- **Plate Policy (Plateless Default)**: Avoid using plates as much as possible; use only a couple (~2) per week. Plates are strictly for recurring indoor anchors (studio reformer room, flat). Never attach plates to outdoor walks, cafes, streets, rivers, or markets, which causes glued-on composite artifacts.
- **Canon Identity Anchors**:
  - `MASTER_A1`: `personas/seoyeon/master/a/a1_front.png` (face master)
  - `MASTER_C5`: `personas/seoyeon/master/c/c5_relax_front.png` (relaxed body master)
  - `MASTER_TATTOO`: `personas/seoyeon/master/c/tattoo_crop.png` (high-res crop of the canon botanical sprig)
- **Tattoo Invariants**:
  - Canon tattoo: Delicate, fine-line, two-branch minimalist botanical sprig on her **left ribcage** below the breast line.
  - **Zero-Tattoo Prompt Rule**: Do **NOT** mention the word "tattoo" anywhere in the text prompts (clothed or bare). Mentioning "tattoo" in text prompts triggers diffusion hallucinations and spatial flipping.
  - **Reference Anchoring**: Pass `[a1_front, c5_relax_front, tattoo_crop]` for bare-torso shots. The visual master references (`c5_relax_front.png` and `tattoo_crop.png`) permanently and accurately anchor the marking directly to HER anatomical left ribcage.
  - **Clothed Torso Rule**: For clothed torso shots, set `"exclude_body_ref": True` (passes only `a1_front.png`) so no tattoo reference is sent.
- **Zero Body Prompting**: Rely on references for her natural athletic Pilates proportions. Never prompt "tiny waist" or "hourglass" (causes unnatural CGI wasp-waist artifacts).
- **Realistic Camera & Props**: White iPhone 15 Pro with plain clear transparent case. Phone only visible in mirror selfies or propped on tables.

---

## 4. Weekly Funnel & Cloud Orchestration
- **Single Source of Truth**: [`growth/schedule_assets/weekly_schedule.json`](file:///c:/AI-Project/growth/schedule_assets/weekly_schedule.json).
- **Policy — Fanvue First**: Fanvue full companion sets must publish or be scheduled (`publishAt`) **15 minutes before** the Bluesky teaser goes live.
- **Integrity Invariant**: Never tease on Bluesky what is not live on Fanvue.
- **Idempotency Guardrails**: Published posts have `"status": "published"` and their AT Protocol URI in `weekly_schedule.json`. Both `bsky_schedule_worker.py` and `campaign_orchestrator.py` skip published drops automatically to prevent duplicate posts.
- **GitHub Privacy Policy**: Subscriber sets in `growth/schedule_assets/sets/` are strictly ignored by Git (`.gitignore`). Whitelist only public teasers (`*.png`, `*.mp4`, `*.json`).

---

## 5. Organic Bluesky Presence & Engagement Suite
Lyra (@syeonhn.bsky.social) maintains active, authentic organic engagement alongside scheduled campaign teasers:
- **Daily Quota**: **Strictly 2 comments per day** on relevant community posts (Korean coffee/cafe, Seongsu neighborhood, Pilates, commute textures).
- **Pacing & Cadence**:
  - Comment 1: Morning / midday active window (07:00–13:30 KST).
  - Comment 2: Afternoon / evening active window (14:00–23:30 KST).
  - Cooldown: Minimum 3.5h spacing (relaxed to 2.5h late evening).
- **Voice Invariants**:
  - Zero promotional copy, zero Fanvue mentions, zero links, zero exclamation marks.
  - Lowercase, dry, understated humor, authentic Seoul sensory textures.
  - Generated via DeepSeek Flash (OpenRouter) with Gemini 3.6 Flash and deterministic offline canon fallbacks.
- **Workflow Decoupling**: Runs independently in `.github/workflows/bluesky_scheduler.yml` with `continue-on-error` on teaser drops, guaranteeing daily execution regardless of upstream campaign states.

---

## 6. Autonomous Follower Growth & Two-Way Community Loops
To solve the cold-start problem (0 to 1,000+ followers) and maximize conversion into Fanvue:
1. **Audience Sourcing (`growth/bsky_growth_engine.py`)**:
   - Discovers real active accounts engaging with Seoul culture, coffee, pilates, and illustration.
   - Executes 15–20 curated follows/day (yielding ~5–8 follow-backs/day, ~150–240 followers/month).
   - Automatically unfollows non-reciprocating accounts after 7 days (max 5/day).
2. **Two-Way Reply Acceleration (`growth/bsky_reply_worker.py`)**:
   - Continuously monitors follower comments and mentions.
   - Replies in Seo-yeon's signature dry, lowercase voice to double thread engagement velocity.
3. **Feed & Tag Optimization**:
   - Injects `langs: ["ko", "en"]` into all post records.
   - Emits richtext hashtag facets (`app.bsky.richtext.facet#tag`) for all `#hashtags` to index into Bluesky topic feeds.
4. **Profile Anchor**:
   - Hero soft-NSFW teaser post pinned at the top of `@syeonhn.bsky.social` with threaded Fanvue link (`c=fv-4`).
5. **Fanvue Autonomous Retention (`growth/fanvue_chat_agent.py`)**:
   - Greets all new paying subscribers ($9.99/mo) with Option 1 welcome DM from `fanvue_profile.md`.
   - Polls active subscriber chats and delivers intimate, personal, lowercase conversational replies.

---

## 7. Daily Command Cheatsheet
From project root:
```powershell
# 1. Master cross-platform dashboard status
python growth/daily_tick.py --status

# 2. Run master autonomous growth tick (safe dry-run)
python growth/daily_tick.py --dry-run

# 3. Follower growth engine status and auto tick
python growth/bsky_growth_engine.py --status
python growth/bsky_growth_engine.py --auto

# 4. Inbound Bluesky reply worker
python growth/bsky_reply_worker.py --status
python growth/bsky_reply_worker.py --auto

# 5. Outbound organic comment engagement
python growth/bsky_engage.py --status
python growth/bsky_engage.py --auto

# 6. Fanvue autonomous welcome DMs and chat responder
python growth/fanvue_chat_agent.py --status
python growth/fanvue_chat_agent.py --auto

# 7. Campaign matrix status check
python growth/campaign_orchestrator.py --status
```


