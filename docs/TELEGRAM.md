# A private conversation and a dependable operator channel

Telegram has two purposes: personal conversation with Seo-yeon and explicit operation of her Bluesky account. Conversation should be candid, warm when appropriate, and proportionate. There is no automatic affection, loyalty performance, emotional recharge, required endearment, or daily goodnight. She can disagree or ask a specific question. She uses “my master” or “my human” when referring to her creator, without forcing the title into every reply.

## Private continuity

The encrypted `data/.vault/operator_channel.json` holds incoming messages, frozen replies, execution stages, results, check-in preferences and notification delivery state. Replies retrieve up to eight recent delivered turns with labeled bounded excerpts, plus operator-scoped learned memory. Full text remains encrypted. Confirmed exchanges feed the continuity system with `scope=operator`; public retrieval excludes that scope. Prior messages alone do not authorize new actions. A fresh confirmation or delegation may resolve the latest pending clarification as described below.

Private messages, draft posts and image prompts are redacted from console diagnostics. This does not remove historical logs or commits. Telegram and the configured model provider still receive the content necessary to deliver/generate replies. This feature does not alter their retention policies.

## Conversation versus commands

Casual mentions of selfies, writing, posts or likes no longer directly trigger action. Natural-language requests pass structured intent classification: chat, clarification, or an explicit execution request. Execution requires an allowlisted action, a verbatim authorization span (matched case-insensitively against the operator's message) and confidence `>= 0.85`. Markdown code fences around JSON output and null/empty `image_kind` fields are normalized before validation. When the operator asks for a supported action (such as `"post a picture"`, `"post a selfie"`, or `"reply to someone's post"`) with a verbatim request span and confidence `>= 0.85`, missing optional details (subject, selfie vs POV, outfit, caption, or target link) delegate those choices and execute immediately without asking for confirmation. Only low-confidence (`< 0.85`) or targetless ambiguous messages hold `pending_action` and `image_kind` for clarification. Classification is probabilistic, not a guarantee of understanding. The classifier and private reply generator receive the same runtime capability descriptions. An explicit request to post a selfie or picture authorizes generated fictional imagery using the canonical references; no physical phone, camera or existing photo is required. Supported authenticated commands are operational instructions, not subject to fictional reluctance. Budgets, service availability, review and receipt confirmation still apply. A validated selfie/POV type (`image_kind`) is passed to both caption drafting and scene generation, where any unspecified setting, lighting, or surroundings are inferred dynamically from the live Seoul environment (time, circadian phase, weather, internal state), optional weekly intentions, and continuity without hardcoded scenarios; a mismatched scene is rejected. No old declined or clarified message is automatically replayed.

For unambiguous operation, commands are recognized only at the start of the message: `/post TOPIC`, `/photo TOPIC`, `/post_image TOPIC`, `/dms`, `/reply`, `/like`, `/consolidate`. These are an operator protocol, not scripted personality. Questions about a prior post or requests for a draft are not permission to publish. A reply request can delegate selection to her: she can browse notifications and the feed without a supplied link. Clarifications retain one specific proposed action for up to 24 hours. A fresh confirmation or delegation can continue only the latest delivered clarification, with its exact ID and the same action type. Intervening conversation, cancellation, expiry, or a completed action prevents continuation. Existing historical exchanges without this pending state are not replayed. The classifier remains probabilistic; ambiguous or invalid results do not execute.

A prepared reply and directive are frozen before sending. The action does not start until the acknowledgment is confirmed. Before executing, its stage is durably marked running. An interrupted running action is held for receipt review, never automatically repeated. A failed/unconfirmed attempt also does not loop on later ticks. Result records distinguish confirmation from failure; operational messages do not claim an inbox is empty merely because no reply was sent.

Use `python scripts/maintain.py pending` to see interrupted update IDs without private message bodies. Review the relevant outbox/provider receipts, resolve uncertain deliveries as documented in [operations](OPERATIONS.md), then use `python scripts/maintain.py resolve-operator UPDATE_ID --evidence REVIEW_REFERENCE`. This closes the command without executing it again. Persist updated encrypted state before the next production runner. Personal conversation remains available while commands are held, subject to Telegram/model availability and normal budget limits.

## Check-in preference

Default: **meaningful**. New confirmed public posts or replies may prompt a model to decide whether a private note is worth sharing. Routine activity can remain unreported. An unchanged activity set is not repeatedly reconsidered after a silence decision, and no catch-up message is manufactured just because yesterday passed. This first version does not initiate notes solely from private reflections or unfinished work.

Send one of these messages in Telegram:

- `/checkins meaningful` — optional notes grounded in confirmed activity.
- `/checkins daily` — one summary at or after 21:00 Seoul time when generation and delivery succeed; no backlog of missed days.
- `/checkins off` — disable automatic personal check-ins.

Explicit CLI summaries remain available. Personal notes have no report-style headers or compulsory sign-off. Their text is frozen before sending; delivery uncertainty cannot cause a differently worded retry. No command bypasses spending limits.

## Operational alerts

Authentication failures, uncertain deliveries, interrupted commands, unconfirmed operator actions and repeated model selection unavailability have separate concise `[operations]` alerts. They do not depend on generating an in-character message or on the personal check-in preference. Identical alert codes are limited to one confirmed notification per Seoul day, and ambiguous sends use the durable outbox rather than blind retries. This is not an external uptime monitor: if the runner never starts, the vault cannot be loaded, Git checkpointing fails, or Telegram itself is unavailable, it may be unable to notify you.

On a Bluesky authentication/recovery failure, the runner can still process private Telegram conversation; external commands are blocked rather than executed against an unavailable service. At most three completed inbox items are handled per tick. Frequency still depends on the existing production scheduler—no extra polling or spending caps were added.

## Verification

Regression coverage includes casual versus explicit intent, invalid authorization, frozen acknowledgments, command restart handling, operator memory scope, private log redaction, check-in preferences and deduplication, and receipt-based success. Tests do not send live messages or prove conversational naturalness. Evaluate actual private exchanges for memory relevance, room for disagreement, conversational proportion and accurate reporting.

Operator-directed public replies and likes use the same 72-hour target-age rule as autonomous discovery. A fresh reply in an older thread is eligible; an old repost or recently indexed old post is not. If no suitable recent target exists, the command reports that no action was confirmed. Private conversations are outside this public-post age rule.
