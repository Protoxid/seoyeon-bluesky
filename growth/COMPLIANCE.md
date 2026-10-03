# COMPLIANCE — the rules the automation is built around
Researched 5 Sep 2026 from primary sources only. Every row carries the quote and
the URL. Nothing here is from a blog, a forum, or memory.

READ THIS BEFORE PLAN.md. The architecture in PLAN.md is not a design that was
then checked for compliance; it is the shape left over once these rules are
applied. Changing a rule changes the architecture, not the other way round.

---

## 1. THE FOUR THINGS THAT CANNOT BE AUTOMATED

These are not risk judgements. Three of them have no endpoint at all.

### 1.1 Cold DMs on Instagram — NO ENDPOINT
> "Only after an Instagram user has sent your app user's Instagram professional
> account a message can your app send a message to the Instagram user."
https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/messaging-api/

The scope name says the same thing: `instagram_manage_messages` is
> "allows business users to read and respond to Instagram Direct messages"
https://developers.facebook.com/docs/permissions
Respond. Not initiate. There is no cold-DM call to write.

### 1.2 Top-level comments on other people's posts — NO ENDPOINT
The Comment Moderation guide documents exactly one write path,
`POST /<IG_COMMENT_ID>/replies`, scoped to "Instagram Media owned by your app
users". The Mentions API — the only surface that touches third-party media —
says of the nearest adjacent case:
> "Commenting on photos in which you were tagged is not supported."
https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/mentions/

Honest framing: Meta never writes the sentence "you may not comment on other
people's posts". What exists is no endpoint, scope language confined to owned or
mentioned media, and a "not supported" on the closest case. The conclusion is
the same; the reasoning should not be overstated.

### 1.3 Automated engagement, however it is produced
> "Sending spam as defined in the Community Standards is not allowed. This
> includes behavior creating bots either manually or automatically, at very
> high frequencies."
https://developers.facebook.com/devpolicy/

> "We may take enforcement action at any time, including while we investigate
> your App(s), with or without notice. Enforcement can be both automated and
> manual. It can include suspending or permanently removing your App(s) and
> account..."
https://developers.facebook.com/terms/

This covers browser automation as well as API calls. The rule is about the
behaviour, not the transport.

### 1.4 TikTok direct posting without an audit
> "All content posted by unaudited clients will be restricted to private
> viewing mode."
https://developers.tiktok.com/doc/content-sharing-guidelines/
Unaudited clients are also capped at 5 users per 24h and the account must be
private at posting time. TikTok is therefore not an unattended lane until the
audit is passed.

---

## 2. THE ONE WAY TO REACH SOMEONE WHO HAS NOT DM'd FIRST

Private replies. One message, to a person who commented, within 7 days.
> "The message must be sent within 7 days from when the comment was created for
> comments on a post, ads post, or reel"
> "Only one message can be sent to the person who commented"
> "Only when a person responds to the private message can you continue the
> conversation within the 24-hour messaging window."
https://developers.facebook.com/docs/messenger-platform/instagram/features/private-replies/

Endpoint `POST /PAGE-ID/messages` with `recipient: {"comment_id": "<ID>"}`.
Requires `instagram_manage_comments`, `pages_messaging`, the Human Agent
feature, and **Advanced Access** — which requires Business Verification and App
Review. That is the single largest unlock in this whole plan and the longest
lead time. Start it first.

Standard window for inbound conversations:
> "Your app has 24 hours to respond to any message sent from an Instagram user
> to your app user."
Human agent tag extends it:
> "If more time is needed to allow a human agent to respond, you can use the
> human agent tag to send a response within 7 days."
https://developers.facebook.com/docs/instagram-platform/overview/

Send-rate ceilings (call rates, not permission): 100 calls/sec text messages,
750 calls/hour private replies to post and reel comments.

---

## 3. PUBLISHING LIMITS, PER PLATFORM

| platform | posts/24h | cost | approval needed | verified |
|---|---|---|---|---|
| Instagram | **100** API-published posts, moving window | free | no (own account) | Content Publishing doc, "Rate Limit" heading |
| Threads | **250** posts, **1000** replies | free | no, for your own account | developers.facebook.com/docs/threads/overview |
| Bluesky | ~**1,666 records/hour**, 11,666/day (CREATE = 3 pts, 5000 pts/hr) | free | none, no API key | bsky.network/docs/advanced-guides/rate-limits/ |
| YouTube | **100 `videos.insert`/day**, own quota bucket | free | no | developers.google.com/youtube/v3/getting-started |
| Reddit | 100 queries/min per OAuth client | free tier terms UNVERIFIED (page blocked) | OAuth + descriptive User-Agent mandatory | support.reddithelp.com Data API Wiki |
| X | no documented free tier | **pay-per-use** | no | docs.x.com/x-api/getting-started/pricing |
| TikTok | 6 req/min | free | **audit required or posts stay private** | developers.tiktok.com |

**The Instagram doc contradicts itself and it matters.** Under "Rate Limit" it
says 100 posts/24h; inside the carousel subsection it says 50. The governing
general figure is 100. Do not design against 50 and do not design against 25,
which is the number that circulates from an older version of the API.

**X's pricing has a trap that changes how we write posts:**
- Post: Create — **$0.015**
- Post: Create (with URL) — **$0.200**
A link in the post body costs 13x. **The Fanvue link goes in the bio, never in
the post.** At one post a day that is $0.45/month instead of $6.00.

---

## 4. AI DISCLOSURE — MANDATORY IN FOUR PLACES

This is not a caution. It is a published requirement on every platform that
matters to us except two, and on Fanvue it is stated as a legal obligation.

**Fanvue — mandatory, and there is a badge:**
> "All AI-generated media must include a clear and prominent disclosure (e.g.,
> watermark, caption, accompanying message or bio statement)."
https://legal.fanvue.com/community-guidelines (§D, updated 14 Jun 2026)
> "Fanvue is required by law to clearly label AI creator accounts... Every AI
> creator has an AI tag displayed in their profile bio."
https://help.fanvue.com/en/articles/14290142-how-do-i-know-if-a-creator-is-ai
> "Failure to properly disclose may result in your content being removed and/or
> your account being suspended."
https://help.fanvue.com/en/articles/9538738-is-ai-content-allowed-on-fanvue

**Meta / Instagram / Threads — mandatory for photorealistic video or audio:**
> "We'll require people to use this disclosure and label tool when they post
> organic content with a photorealistic video or realistic-sounding audio that
> was digitally created or altered... and we may apply penalties if they fail
> to do so."
https://about.fb.com/news/2024/02/labeling-ai-generated-images-on-facebook-instagram-and-threads/
Note the scope: photorealistic **video** and **audio**. Every reel we publish is
inside it. Stills are not named in that sentence.

**TikTok — the strictest wording of the set:**
> "Synthetic or manipulated media that shows realistic scenes must be clearly
> disclosed. This can be done through the use of a sticker or caption, such as
> 'synthetic', 'fake', 'not real', or 'altered'."
https://www.tiktok.com/community-guidelines/en/integrity-authenticity

**YouTube — mandatory where AI "generates a realistic scene that didn't
actually occur":**
https://support.google.com/youtube/answer/14328491

**NOT required: X** (deception-based rule only; non-deceptive synthetic media
expressly allowed) and **Bluesky** (no AI rule, but impersonation rules apply
and parody/fan accounts must identify themselves "in both display name and
bio").

**Consequence for the build:** disclosure is a field in the content pipeline,
not an afterthought. Every publisher writes it. See PLAN.md §5.

---

## 5. WHERE ADULT CONTENT MAY AND MAY NOT GO

| destination | organic adult content | source |
|---|---|---|
| **Fanvue** | **YES**, marked 18+ | "Intimate content... is permitted but must be clearly marked as 18+ Content" — legal.fanvue.com/community-guidelines §C.6 |
| **X** | YES, labelled | "You may share consensually produced and distributed adult nudity or sexual behavior, provided it's properly labeled and not prominently displayed" — help.x.com/en/rules-and-policies/media-policy |
| **Bluesky** | YES, labelled | "We allow consensual adult sexual content, including fictional depictions, when appropriately labeled" — bsky.social/about/support/community-guidelines |
| **Reddit** | subreddit-dependent; costs ad eligibility | NSFW profile marking — support.reddithelp.com |
| **Instagram / Threads** | **NO** | Meta removes "AI- or computer-generated nudity and sexual activity... regardless of 'photorealistic' appearance" — transparency.meta.com adult-nudity-sexual-activity |
| **TikTok** | **NO** | bans marketing of "sexual services"; "Displaying excessive visible skin" prohibited even in ads |

**Instagram stays SFW. That is a platform rule, not a taste decision** — and
Meta's ban names AI-generated nudity explicitly, so "it isn't a real body" is
not a defence. Instagram is the top of the funnel and nothing else.

### 5.1 FANVUE HAS TWO SURFACES, NOT ONE — AND I DESCRIBED ONLY ONE
Corrected 5 Sep 2026. An earlier draft of this file said the Fanvue public
surface must be SFW and left it there. That was true but incomplete, and the
omission mattered: read alone it implies the whole account is SFW, which would
make the account unsellable.

**THE PAYWALL — where the product is:**
> "Intimate content, provided it does not depict any of the activities banned
> within these Guidelines, is permitted but must be clearly marked as 18+
> Content." — Community Guidelines §C.6.1

"Intimate" is defined broadly and explicitly includes synthetic people:
> "any content featuring full or partial nudity (i.e. exposure of nipples,
> breasts, buttocks or genitalia), includes people (whether real or synthetic)
> wearing only lingerie, underwear or see-through clothing, or depicts a sexual
> act"

So the subscriber side is permitted to be intimate. The only requirements are
the 18+ mark, the banned-acts list in §C.6, and AI disclosure.

**THE SHOP WINDOW — profile picture, banner, intro video, public bio, Discover.**
Prohibited there (AUP §2.6):
> "Nudity, implied nudity, or strategic covering; See-through or revealing
> clothing that exposes nipples or genitals; Hyper-sexualised posing or
> porn-style framing; Explicit sexual language; Age-baiting language (e.g.,
> 'just turned 18', 'barely legal', 'teen'); AI-generated imagery without clear
> disclosure that the Content is AI-generated."

But it is **not** "fully SFW", and this is the sentence the earlier draft
missed entirely — Community Guidelines §F:
> "You may include swimwear, lingerie, or boudoir-style content in Public Media
> as long as it is opaque (not see-through), not posed explicitly, and looks
> suitable for mainstream social media."

Enforcement is graduated and does not touch the money:
> first offence — "The profile will be disabled from appearing on the Discover
> section of the Platform until the non-compliant media is updated."
> repeat — "The entire profile will become inaccessible from public view"
and explicitly: this "does not delete your content, ban your account, or affect
your earnings from existing subscribers."

### 5.2 THE THREE TIERS, WHICH IS THE ACTUAL MODEL
Not two. Each tier is set by a different platform's rule, and mixing them up is
what gets an account limited.

| tier | where | what is allowed | whose rule |
|---|---|---|---|
| **1 — clean** | Instagram, Threads | no nudity, no AI nudity, nothing suggestive-explicit | Meta. Hard. Meta removes "AI- or computer-generated nudity and sexual activity... regardless of 'photorealistic' appearance" |
| **2 — suggestive** | X, Bluesky, **and the Fanvue public profile** | swimwear, lingerie, boudoir — opaque, not explicitly posed | Fanvue CG §F; X and Bluesky both also permit labelled adult content, so tier 2 is their floor, not their ceiling |
| **3 — intimate** | behind the Fanvue paywall | intimate content, marked 18+ | Fanvue CG §C.6.1 |

Tier 2 is the conversion layer and it is where the earlier draft's error would
have done real damage: a Fanvue profile built to tier 1 gives a visitor no
reason to pay. Tier 2 in the window, tier 3 behind it, is the design the
platform is built for.

---

## 6. PAID ADS — ONE PLATFORM SAYS YES, THREE SAY NO

**Meta — CONDITIONAL YES, and this is the written allowance:**
> "When targeting people aged 18 or older, advertisers can run ads that:
> Contain content that contains usernames, links to or logos of adult
> subscription websites"
https://transparency.meta.com/policies/ad-standards/objectionable-content/adult-sexual-solicitation-and-sexually-explicit-language/

Three conditions stack on it, all published:
1. **18+ targeting is mandatory** — the allowance is scoped by that phrase.
2. **The creative must be clean.** No nudity or near-nudity ("nudity covered
   only by digital overlay" is named), no simulated sex or sexual dancing.
   Suggestive poses and revealing clothing are allowed but age-gated to 18+.
3. **The landing page is reviewed too** — "as well as an ad's associated landing
   page or other destinations". A clean creative pointing at a non-compliant
   destination is still reviewable.
   https://transparency.meta.com/policies/ad-standards/

The unresolved variable, and it is unresolved **in Meta's own text**: Meta bans
"logos, screenshots or video clips of known pornographic websites" but permits
"links to... adult subscription websites", and publishes **no definition of
either term and no list**. Which side Fanvue sits on is not answerable from the
documentation. Combined with "We reserve the right to reject, approve or remove
any ad for any reason, at our sole discretion", the allowance is real but is not
a guarantee of approval. Treat a rejection as an enforcement judgement, not
proof we broke a rule — and never scale spend before one ad has been approved.

**TikTok — NO.** "Displaying excessive visible skin", "Wearing underwear,
stripping, or undressing" all prohibited; no subscription-platform allowance
exists. https://ads.tiktok.com/help/article/tiktok-ads-policy-adult-content

**X — NO.** "X prohibits the promotion of adult sexual content globally", and
separately bans "Adult clubs, sexually suggestive online chats, live streamings"
and pay-per-communication models. X's permissive *organic* adult policy does not
extend to ads.
https://business.x.com/en/help/ads-policies/ads-content-policies/adult-or-sexual-products-and-services

**Reddit — NO.** Prohibited: "Nudity or implied nudity within the creative **or
on the landing page**".
https://advertising.reddithelp.com/en/categories/reddit-advertising-policy/reddit-advertising-policy-prohibited-advertisements

**Marketing API access:** for an app managing only our own ad account,
> "If your app is only managing your ad account, standard access to the ads_read
> and ads_management permissions are sufficient."
https://developers.facebook.com/docs/marketing-api/get-started/authorization
So no App Review for ads. Advanced Access is only for acting on behalf of third
parties. (The Business Manager / payment-method setup requirements live in the
Business Help Centre, which is robots.txt-disallowed — UNVERIFIED, confirm in
the UI.)

---

## 7. FANVUE — THE PART THAT CHANGES THE PLAN

Fanvue has a **full public API**, and it is the single most important finding
in this research.

https://api.fanvue.com/docs/welcome — "One API spans chats, posts, media,
subscribers, insights, and agency operations." 140+ endpoints.

Permitted use, quoted from https://legal.fanvue.com/api-policy (5 Feb 2026) §4:
> "**Chats:** Listing chats, retrieving chat messages, creating new chats,
> sending messages, sending mass messages, deleting messages..."
> "**Posts:** Creating new posts."
> "**Creators:** Reading followers and subscribers."
> "**Insights:** Reading earnings data, top-spending fans, and subscriber counts."
> "**Media & Vault:** Creating multipart upload sessions..."
> "**Tracking Links:** Listing tracking links, creating tracking links..."

Mechanics: `X-Fanvue-API-Key` header, `X-Fanvue-API-Version: YYYY-MM-DD`,
**one active API key per user**, keys at https://www.fanvue.com/api-keys,
rate limit **100 requests per 60 seconds**. Requires a creator account with KYC
completed.

Access caveat: §4 also says "API access is controlled and may be limited to
whitelisted or approved users during rollout", and a stale June-2025 help
article still says keys are waitlisted. The Feb 2026 policy and the live
developer portal supersede it, but confirm the key issues before building
against it.

**Automation is permitted ONLY through the API.** Everything else is barred:
> "Do not use any automated program, tool or process (such as web crawlers,
> robots, bots, spiders, and automated scripts) to access Fanvue"
https://legal.fanvue.com/acceptable-use-policy §5
> "Create 'bot' Accounts or any Account which is controlled by other automated
> means" — prohibited. T&Cs §2.2

So: Fanvue API = yes. Browser automation against Fanvue = account termination.

**AI creators are a recognised category with a higher account limit:**
"2 for Human Creators, 15 for AI Creators".

**KYC is on the human owner and is unavoidable:**
> "Even if you are not using your face in the content, we will need an image of
> your valid, in-date, government-issued international ID or passport, and a
> selfie to verify your match. This information will not be shared on your
> profile."
https://help.fanvue.com/en/articles/9539091-passing-kyc-and-creating-multiple-accounts-as-an-ai-creator

**Off-platform promotion is explicitly allowed:**
> "Creators may promote their Fanvue profile on: Social media platforms;
> Personal websites and blogs; Email newsletters; Search engines and paid
> traffic platforms (subject to their terms)."
https://legal.fanvue.com/creator-advertising-promotion §1.1

**The hard limit is money, not marketing.** Creator Terms §5: no accepting
payment outside the platform, no promoting external payment links, no delivering
content off-platform for value. Breach = "immediate account suspension, payout
withholding, and possible permanent removal."

**Earnings mechanics:** 80% creator rate. Pending period 7 days, extendable to
28. Payout initiated within 10 business days. Balances unclaimed 12 months go
dormant. Payout methods: bank transfer (universal), Masspay, Cosmo, crypto. No
PayPal.

---

## 8. WHAT COULD NOT BE VERIFIED

Stated so nobody later mistakes a gap for a green light.

- Meta's current-year AI labelling text. transparency.meta.com is a JS SPA and
  several policy pages returned metadata only or 404. The quotes in §4 are from
  Meta's own newsroom (about.fb.com), dated 2024. Newer official items exist
  that could not be read. **Re-check before launch.**
- Whether the `HUMAN_AGENT` tag string applies to Instagram specifically — the
  tag reference page returned 429 repeatedly. The 7-day mechanism is verified;
  the constant name is not.
- Instagram's "Allow access to messages" account toggle — setup page 429'd.
- `content_publishing_limit` response field names — reference page 404s.
- Reddit's Data API Terms and sitewide Rules — blocked to both fetching and the
  browser. Reddit free-tier commercial-use terms are therefore UNKNOWN.
- Meta Business Manager payment/setup prerequisites — robots.txt-disallowed.
- Fanvue pricing for any AI feature, and any country restrictions on creator
  signup — no official page found.
- TikTok's daily per-creator post cap (~15/day is referenced in error codes but
  not stated on the pages read).
