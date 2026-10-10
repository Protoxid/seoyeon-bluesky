# Runtime architecture and recovery

## Processing

The root CLI establishes mode and a whole-process state lock. Offline commands copy public state to a temporary directory, omit the vault and key files, disable credentials and block socket connections. Preview permits paid model calls in temporary state and blocks publishing. Preview spend is not added to production budgets; use sparingly and inspect the provider dashboard.

Live mode loads the encrypted vault and halts on decryption failure. It authenticates Bluesky and recovers pending deliveries before new actions. It reads environment/observations, builds eligible candidates, requests model judgment, generates and validates content, delivers and records confirmed results. Empty or invalid generation remains silent. Model confidence below ACTION_THRESHOLD selects NO_ACTION.

The decision engine retains heuristic scores for diagnostics and legacy simulation. The live chooser does not use these scores as action instructions. Cadence caps, budget limits, authentication, privacy and idempotency remain explicit operational rules.

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

Keep a protected copy of the encryption key. The current loader supports the previous credential-derived key during migration. Fernet uses AES-128-CBC plus HMAC-SHA256; this is not an AES-256 cipher. Authentication failure blocks writes. The `.bak` ciphertext is a recovery backup, not permission to discard the current vault.

## Durable delivery

Bluesky createRecord calls freeze payloads and use a stable rkey. Before sending, the outbox is encrypted and, in production, pushed to main. If a response is lost, getRecord can confirm delivery. DMs use a bounded recent-message check with sender, text and timestamp. If delivery cannot be proved, the runtime holds the action. Telegram has no equivalent lookup here, so uncertain Telegram sends require operator resolution.

A checkpoint failure stops outbound work. The workflow must configure Git identity before the live command. SEOYEON_GIT_CHECKPOINT=1 is only for the production main checkout. It is not appropriate for feature branches or tests. The workflow's final persistence step also runs after failures and returns nonzero if state cannot be pushed.

## Operator recovery

1. Run `python scripts/maintain.py pending`. This shows IDs and statuses, not private bodies.
2. Verify the action or bill in the relevant service/dashboard. Never infer delivery merely because an exception was absent.
3. For a verified send: `python scripts/maintain.py resolve-delivery ACTION_ID --receipt REMOTE_URI_OR_ID --evidence RECEIPT_REFERENCE`.
4. To permanently decline retry of an uncertain send: `python scripts/maintain.py resolve-delivery ACTION_ID --abandon --evidence REASON`. This does not assert that the original send failed and does not delete remote content.
5. For a provider-verified bill: `python scripts/maintain.py reconcile-cost RESERVATION_ID ACTUAL_USD --evidence RECEIPT_REFERENCE`. Submitted holds deliberately do not expire. A verified zero charge can be reconciled as zero.
6. Preserve/push resulting state from the current main checkout before another cloud run. Never overwrite newer remote state with an older local vault.

These tools do not send messages or generate content. Do not put tokens or private transcripts into evidence-reference arguments.

## Images and billing

POV routes to Kie's documented text-to-image model; selfies use image-to-image with two references. The generation fee is recorded at provider completion, even if download/upload/review fails. Current image tariff is an estimate, not a provider price guarantee. A timeout retains the task ID and hold for manual verification; it does not start a duplicate generation automatically.

Every OpenRouter attempt has its own reservation and reconciliation, including billed empty/truncated output before fallback. Unknown requests retain their hold. Usage-reported cost takes precedence over token estimates. Locks prevent concurrent reservation races; they cannot guarantee that an external provider's unknown charge will equal a tariff estimate.

## Scheduling and health

GitHub wakes the runtime periodically. A wakeup does not mean a social action is due. Daily operator summaries and optional reflection maintenance are operational work, not fabricated life events. Failures of authentication, image delivery, vault loading or state persistence return nonzero rather than masquerading as dry-run success. Inspect Actions logs and `pending` when a workflow fails.

## Historical exposure

Migration removes current plaintext journal excerpts only after encrypted archival. It cannot remove past Git commits, Actions logs, forks or downloaded copies. History rewriting or deleting old Actions logs is a separate coordinated operation and is not performed by the runtime. No claim of retroactive secrecy is made.
