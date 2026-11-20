# Runtime architecture and recovery

## Processing

The root CLI establishes mode and a whole-process state lock. Offline commands copy public state to a temporary directory, omit the vault and key files, disable credentials and block socket connections. Preview permits paid model calls in temporary state and blocks publishing. Preview spend is not added to production budgets; use sparingly and inspect the provider dashboard.

Live mode loads the encrypted vault and halts on decryption failure. It authenticates Bluesky and recovers pending deliveries before new actions. It reads environment/observations (timeline, custom feeds configured via `BSKY_CUSTOM_FEEDS` or saved account feeds with `ENABLE_CUSTOM_FEED_DISCOVERY` fallback, up to two unfollowed new-follower feeds throttled over 7 days, and public search topics), builds eligible candidates (`ALLOW_POSTS`, `ALLOW_REPLIES`, `ALLOW_LIKES`, `ALLOW_REPOSTS`, `ALLOW_FOLLOWS`, `ALLOW_DMS`, `ALLOW_IMAGES`), requests model judgment, generates and validates content, delivers and records confirmed results. Outbound posts, image posts, replies, and quote-posts infer per-text `langs` (`detect_langs`) and build UTF-8 byte-offset link, hashtag, and `@mention` facets (`build_facets`, caching handle DIDs per session and skipping DID lookups offline/`dry_run`). Empty or invalid generation remains silent, though a single transient reply-generation failure on a direct notification (`notification_attempts` in `recent_context.json`) leaves the notification open for one retry unless `chosen_silence` was returned or two attempts fail; confirmed replies clear the counter and skip auto-liking when `like_target=false`. When `MAX_ACTIONS_PER_TICK` is at least 2 and the primary non-forced action succeeds, an eligible chooser `companion` action runs in the same wakeup after fresh daily-cap and recency checks with its own `bsky_client.action_identity` and `session_companion` tick log. Model confidence below ACTION_THRESHOLD selects NO_ACTION. When model selection itself is unavailable (`selection=model_unavailable`), the tick defaults to NO_ACTION, skips the reflection LLM call, and emits a deduplicated `model_unavailable` operational alert after three consecutive live occurrences.

Before the feed chooser, an original-post pass runs when own posts are eligible and a varying gap has passed (`MIN_POST_GAP_HOURS`, default 3, plus 0 to `POST_GAP_JITTER_HOURS`, default 2, derived from the last post). It receives pacing information (including KST-normalized `photos_today`, `days_since_last_photo`, `days_since_last_selfie`, and `recent_post_languages` across recent posts for Korean/English balance) and the fictional life journal (`data/.vault/life.json`, encrypted with the vault; one day-sketch model call per Seoul date; replies and quote-posts read `LifeJournal.snapshot` without extra calls). A proposed idea is published on that tick (`selection=original_pass`) unless a direct reply, mention or DM is pending. Everyday own posts are drafted with `POST_TEXT_MODEL` (default Sonnet 5.5) through `casual_draft`; links and factual posts keep `grounded_draft`, while replies, quotes, and DMs use `PRIMARY_TEXT_MODEL` unless `REPLY_TEXT_MODEL` is set. `self_model.py` excludes self-authored replies when counting `replyCount` via `getPostThread` (falling back to raw counts on error) and summarizes recent public reply outcomes (`recent_conversations`) alongside own posts while keeping the two-post citation requirement. An unparseable chooser answer is retried once. Defaults: 3 posts and 3 image generations per day. The proposal chooses `shot: selfie|pov` for images, informed by days since the last photo and selfie, and `determine_image_scene` respects that choice so casual selfie captions are not overridden back to POV. Between own-post gaps (`>= 1.5h`), `QUOTE_POST` and media `REPOST` (`images` or `recordWithMedia`, gated by `ALLOW_REPOSTS`) remain eligible in feed evaluation for model choice. When nothing new is eligible (no direct conversation, no feed post outside the six-hour already-offered memory, no proposal), the chooser is skipped (`selection=nothing_new`) and no model call is made; reflection runs at most every six hours. `SEOYEON_CALL_TRACE=1` prints per-call model, tokens and cost. Location reference images (`personas/seoyeon/locations/`) are used only where they exist on the runner.

The decision engine retains heuristic scores for diagnostics and candidate ordering. The live chooser does not use these scores as action instructions. Cadence caps, budget limits, authentication, privacy and idempotency remain explicit operational rules.

Before model selection, confirmed likes, reposts and follows are removed from the candidate set using Bluesky viewer state and durable delivery receipts. Recent likes also cover older history without outbox records. A previously liked post can still be eligible for a reply. Explicitly abandoned likes, reposts and follows are also excluded, without treating them as delivered or reopening them. This restriction applies to the same operation and target; a different operation, such as replying to that post, remains eligible. Telegram browse-and-like uses the same filter. Delivery recovery remains responsible for uncertain sends; uncertainty is not treated as completion.

Interaction learning distinguishes another person's stated preference from Seo-yeon's own expressed opinion. Both require exact evidence and preserve their original scope. Logs report `learning_status` as updated, no retained update, model unavailable or validation rejected, without printing the conversation. No retained update may be legitimate; these diagnostics do not compel new memories.

## Storage

| Store | Purpose |
| --- | --- |
| `data/memory/identity_memory.json` | Authored character baseline; birthday-derived age in prompts. |
| `data/memory/recent_context.json` | Confirmed activity, public repetition checks, handled message IDs. |
| `data/.vault/continuity.json` | Scoped source events, learned memories, commitments, pursuits, draft/artifact revisions. |
| `data/.vault/outbox.json` | Frozen outbound payloads and receipts. |
| `data/.vault/telegram_inbox.json` | Durable authenticated operator messages awaiting processing. |
| `data/.vault/legacy_unscoped.json` | Quarantined legacy journal excerpts and unscoped loops. |
| `data/vault.enc` | Encrypted bundle persisted across runners; plaintext directory is ignored. |
| `data/budget_ledger.json` | Costs, durable holds and idempotent reconciliation IDs. |

Legacy goal/narrative files remain readable for compatibility. They do not advance from elapsed days or keywords. New creative completion needs stored artifact evidence. An event reporting a physical accomplishment is still a statement, not verification of that accomplishment.

Keep a protected copy of the encryption key. The production vault is encrypted only with `DATA_ENCRYPTION_KEY`; the credential-derived migration fallback was removed on 2026-11-11 after the first run re-encrypted the vault. Losing the key means losing the vault. Fernet uses AES-128-CBC plus HMAC-SHA256; this is not an AES-256 cipher. Authentication failure blocks writes. The `.bak` ciphertext is a recovery backup, not permission to discard the current vault.

## Durable delivery

Bluesky createRecord calls freeze payloads and use a stable rkey. Before sending, the outbox is encrypted and, in production, pushed to the `state` branch. If a response is lost, getRecord can confirm delivery. DMs use a bounded recent-message check with sender, text and timestamp. If delivery cannot be proved, the runtime holds the action. Telegram has no equivalent lookup here, so uncertain Telegram sends require operator resolution.

A checkpoint failure stops outbound work.

### Durable state (changed 2026-11-11)

All runtime state is in one encrypted, compressed bundle, `data/vault.enc`: the `.vault` files plus `data/memory/*` (except the authored `identity_memory.json`), `data/historical/*`, `data/logs/tick_history.jsonl` (last 3,000 lines) and `data/budget_ledger.json`. Nothing plaintext from runtime is committed; `main` holds only code, docs and authored identity. The first vault load of a process restores the bundled files to `data/`; later reloads in the same process do not roll them back. A save whose plaintext is unchanged keeps the previous ciphertext, so nothing new is published.

The bundle is published as a single parentless commit on the `state` branch (`agent/git_checkpoint.py`), replacing the previous commit with `--force-with-lease` against the exact state commit the run restored (`data/.state_base`). A competing update therefore fails closed instead of being overwritten; there is no rebase or ciphertext merge. The workflow restores `data/vault.enc` from `state` before the run, publishes again in a final step that also runs after failures, and uploads the ciphertext as a 7-day workflow artifact (`state-<run_id>-<attempt>`) for rollback. Bounded Git commands, at most three push attempts, and a fresh remote read that must equal the new commit: a lost push acknowledgment is reconciled without replaying outbound work. Logs expose only categorized failures, never raw Git stderr or authenticated URLs. SEOYEON_GIT_CHECKPOINT=1 is only for the production workflow, never for feature branches or tests.

`DATA_ENCRYPTION_KEY` is a required repository secret; the workflow has no credential-derived fallback and fails early without it. If the state branch is missing the run fails; restore it from a recovery artifact (see rollback below). The one-time bootstrap from legacy `main` state was removed after the cutover, when the history of `main` was rewritten without runtime data.

To roll back, download an artifact, verify it decrypts locally, and publish it with the current `state` commit as the lease (step 6 below).

## Operator recovery

Bluesky posts, likes, reposts and follows use protocol-compliant timestamp IDs (TIDs), separate from internal action hashes. The first ID and payload are frozen in the encrypted outbox; retries reuse them. Old pending records are never silently assigned a new ID, because that could duplicate an action. If a legacy hash-key request was rejected, verify its exact record through `getRecord` and use the abandonment command below to close that attempt without replaying it.

1. Run `python scripts/maintain.py pending`. This shows IDs and statuses, not private bodies.
2. Verify the action or bill in the relevant service/dashboard. Never infer delivery merely because an exception was absent.
3. For a verified send: `python scripts/maintain.py resolve-delivery ACTION_ID --receipt REMOTE_URI_OR_ID --evidence RECEIPT_REFERENCE`.
4. To permanently decline retry of an uncertain send: `python scripts/maintain.py resolve-delivery ACTION_ID --abandon --evidence REASON`. This does not assert that the original send failed and does not delete remote content.
5. For a provider-verified bill: `python scripts/maintain.py reconcile-cost RESERVATION_ID ACTUAL_USD --evidence RECEIPT_REFERENCE`. Submitted holds deliberately do not expire. A verified zero charge can be reconciled as zero.
6. Pause the scheduler, fetch the current state (`git fetch origin state`, `git show origin/state:vault.enc > data/vault.enc`, `git rev-parse origin/state > data/.state_base`), run the maintenance command, then publish with `python -m agent.git_checkpoint`. The lease rejects the publish if a cloud run changed state meanwhile. Never overwrite newer remote state with an older local vault.

These tools do not send messages or generate content. Do not put tokens or private transcripts into evidence-reference arguments.

## Images and billing

POV routes to Kie's documented text-to-image model; selfies use image-to-image with two references. Vision review downscales and JPEG-compresses generated images and canonical face references so multi-megabyte reference PNGs stay within provider per-image limits. If Bluesky blob upload fails after review, `publish_image_post` fails closed (`{}`) rather than publishing an image-intended caption as a text-only post. The generation fee is recorded at provider completion, even if download/upload/review fails. Current image tariff is an estimate, not a provider price guarantee. A timeout retains the task ID and hold for manual verification; it does not start a duplicate generation automatically.

Every OpenRouter attempt has its own reservation and reconciliation, including billed empty/truncated output before fallback. Reconciled ledger history entries preserve the reservation ID and provider request ID without a second pre-reconciliation checkpoint commit; unknown requests retain their hold. Usage-reported cost takes precedence over token estimates. Locks prevent concurrent reservation races; they cannot guarantee that an external provider's unknown charge will equal a tariff estimate.

## Scheduling and health

cron-job.org dispatches the GitHub Actions workflow periodically. A wakeup does not mean a social action is due. Personal Telegram check-ins default to meaningful confirmed activity; daily summaries are an explicit preference. Reflection maintenance is operational work, not a fabricated life event. Failures of authentication, image delivery, vault loading or state persistence return nonzero rather than masquerading as dry-run success. Inspect Actions logs and `pending` when a workflow fails.

The cron-job.org dispatcher is active with minutes 17 and 47, Seoul hours 07 through 01 (07:17 through 01:47), matching the previous schedule and existing budgets. The GitHub `schedule` trigger is removed; `workflow_dispatch` and the shared concurrency group remain. Its authenticated offline dispatch was verified on 2026-10-12. The first scheduled live dispatch still needs observation; HTTP acceptance alone does not prove workflow completion. Scheduler failure/recovery notifications are enabled, and response-body retention is disabled.

The repository-restricted fine-grained GitHub token has Actions write permission and is stored only by the scheduler. Its current expiry is 2026-11-11; renew it in the scheduler before then. A failed/expired credential should trigger a scheduler alert. For recovery, disable the external job before restoring a repository schedule. Never leave two periodic dispatchers active. Validate replacements with `dry_run=true` and inspect the resulting GitHub run before switching to live dispatch. GitHub runner delays and provider outages can still occur.

## Historical exposure

Migration removes current plaintext journal excerpts only after encrypted archival. It cannot remove past Git commits, Actions logs, forks or downloaded copies. History rewriting or deleting old Actions logs is a separate coordinated operation and is not performed by the runtime. No claim of retroactive secrecy is made.

## Discussion sources and review

See [grounded discussion](DISCUSSION.md) for the reference library, source-host boundary, cache freshness, correction quarantine, and selection diagnostics. Drafting and semantic review each use normal OpenRouter reservations; research HTTP reads have no provider-generation fee. A failed review leaves the action unpublished. The library lives inside the existing encrypted vault, and current production scheduling and budget caps remain unchanged.

## Telegram conversation and command recovery

See [Telegram behavior](TELEGRAM.md) for encrypted operator history, intent classification, check-in preferences, independent operational alerts, and interrupted command recovery. `pending` includes interrupted operator update IDs. `resolve-operator UPDATE_ID --evidence REVIEW_REFERENCE` closes one after receipt review without re-execution.

## Public material retrieval

The chooser receives bounded kept public drafts and recent external/user observations separately from general continuity. Private/operator records and discarded drafts are excluded. Kept drafts are also available to scoped continuity retrieval. A default retrieval omits paused, abandoned and completed pursuits; explicit topic searches can still find that history. Topic relevance outranks self-ownership, and original writing retrieves against the chosen topic. Reflection uses new public evidence excluding generated artifact events, preventing an artifact from triggering its own next revision. These changes do not remove stored history, compel publication or verify facts in drafts.

Public social actions use agent/recency.py: a 72-hour authored-date window and five-minute future-clock tolerance. Selection diagnostics record recency_exclusions by reason without retaining post text. The runner also checks forced actions, and Telegram browsing checks notifications and feed targets. This gates new selections; durable recovery of already-frozen deliveries retains its existing reconciliation rules.

Original-post development: when an original format is eligible in live/preview mode, one bounded model call proposes an optional original idea separately from feed competition. It uses public material, identity, environment and recent posts; it does not force publication or fetch sources. The existing chooser, confidence threshold, source review, budgets and delivery gates still apply. original_idea_status reports proposed/declined/invalid/unavailable/ineligible, while choice_rejection distinguishes invalid_schema, below_threshold and missing_original_idea. Diagnostics omit raw model reasoning and proposal text. The additional call uses the normal budget reservation and billing path.

Web reading is bounded to two observed allowlisted public links per planning pass. No private/operator context is used to choose fetch URLs. Original planning can develop a thought without a prior achievement or saved draft. Existing silence, confidence, billing, source review and image validation remain. On transient Windows destination locks (errors 5/32/33), atomic JSON saves retry at most five times with short waits; permanent failures still propagate and no truncating fallback is used.
