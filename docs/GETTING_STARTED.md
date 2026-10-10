# Setup and command reference

## Run and verify

Requires Python 3.11+ and `pip install -r requirements.txt`.

| Command | Behavior |
| --- | --- |
| `python scripts/run_tests.py` | Disposable checkout, no real credentials, blocked network. |
| `python agent_runner.py --status` | Offline snapshot of public state; credentials deliberately hidden. |
| `python agent_runner.py --dry-run` | Isolated, offline tick. No provider calls, publishing or production-state writes. |
| `python agent_runner.py --replay fixtures/example.json` | Offline supplied observations; schema below. |
| `python agent_runner.py --preview` | Paid text/model preview in isolated state; no social publishing. Costs are in the temporary ledger, not production accounting. |
| `python agent_runner.py --auto` | Live autonomous tick; can spend and publish. |
| `python agent_runner.py --plan-week` | Read optional intentions; never fills an invented calendar. |
| `python agent_runner.py --force-plan` | Explicitly request model-proposed intentions; can spend. |
| `python agent_runner.py --consolidate` | Private reflection; no automatic achievements or relationship upgrades. |
| `python scripts/maintain.py pending` | Private-content-free list of unresolved delivery IDs and cost reservations. |
| `python scripts/maintain.py export-work output/work` | Export existing public creative artifacts as Markdown; does not generate or publish. |

Replay JSON has optional `notifications`, `dms`, and `feed` arrays in Bluesky response shape. Offline mode validates integration/restraint; it does not evaluate a live model's personality. Forced draft generation without a provider yields no draft.

## Credentials and models

Use local `.env` or GitHub Secrets. Never commit keys. Required for live operation: `BSKY_HANDLE`, `BSKY_APP_PASSWORD`, `OPENROUTER_API_KEY`. Images additionally require `KIE_API_KEY`; Telegram requires `TELEGRAM_BOT_TOKEN` and a numeric private `TELEGRAM_CHAT_ID` matching the sender. Prefer a dedicated `DATA_ENCRYPTION_KEY` (or `VAULT_KEY`). The existing workflow retains credential-derived key compatibility; rotating credentials without preserving that key can lock out the vault.

Model IDs are configurable through `PRIMARY_TEXT_MODEL`, `FALLBACK_TEXT_MODEL`, `VISION_MODEL`, `KIE_IMAGE_MODEL`, `KIE_POV_MODEL`, and `KIE_RESOLUTION`. Text uses OpenRouter exclusively. POV images use `gpt-image-2-5-sunburst-text-to-image`; selfies use `gpt-image-2-5-sunburst-image-to-image` with both canonical references. Availability and tariffs are external dependencies, not test guarantees.

Spending defaults: $2/day and $30/month, one generated image/day. `MAX_POSTS_PER_DAY`, `MAX_REPLIES_PER_DAY`, `MAX_DMS_PER_DAY`, `MAX_LIKES_PER_DAY` are ceilings, never targets. `ACTION_THRESHOLD` defaults to 0.50 for model choice confidence; it is not a calibrated probability of naturalness.

## Reliability and privacy

- The vault encrypts private conversations, continuity, operator inbox and delivery outbox. Public logs contain metadata, not journal excerpts or Telegram message bodies.
- Legacy unscoped loops and journal excerpts are encrypted before removing their current plaintext copies. This does not erase Git history, old Actions logs or existing clones.
- Social actions have durable, frozen payloads. Bluesky records use stable keys; ambiguous non-idempotent messages are held for reconciliation. Exactly-once delivery across every provider is not promised.
- Each model attempt is accounted for. Submitted requests do not expire silently. Reported provider cost is preferred; otherwise tariffs are estimates. Unknown bills remain reserved until verified.
- Generated pixels are reviewed before publishing; unavailable review blocks the image. There is no text fallback for a failed image request. Vision review is probabilistic, not identity verification.
- CI runs on all branches. Production wakeups are infrastructure polling, not a daily life schedule. Live state is checkpointed before outbound effects when `SEOYEON_GIT_CHECKPOINT=1`.

See [architecture and recovery](OPERATIONS.md), [behavior evaluation](BEHAVIOR_EVALUATION.md), [canon](../CANON.md), and [implementation record](2026-10-10-implementation.md).
