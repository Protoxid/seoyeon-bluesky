> Historical document. Current behavior and limitations are described in [README](../README.md) and [implementation record](2026-10-10-implementation.md). Previous test counts, simulation scores, automatic progress and readiness claims are not current guarantees.

# Seo-yeon: project review and proposed roadmap

Review date: 10 October 2026. This is a proposal, not an implemented change.

## Recommendation

Build a character whose present behavior has understandable causes in her accumulated history. The highest-value change is to connect observation, memory, choices, consequences, and expression. Adding more personality adjectives, random delays, or more generated photos will not create that continuity by itself.

The distinctive creative direction I recommend is **Seo-yeon's unfinished atlas of ordinary Seoul**: a persistent collection of small observations, typographic studies, reading notes, and conversations. Individual posts remain casual; over months they build a recognizable body of work and a character who changes through experience. This is a proposed differentiator, not a claim that no other project has similar ideas.

Keep her identity as an AI fictional persona clear in the profile and when asked. Natural conversation and a compelling fictional life do not require misleading people about a physical human existence.

## Scope and verification

- Reviewed the local architecture, generation and validation paths, action selection, memory and narrative systems, state and weekly planning, images, budgets, vault, Telegram bridge, Bluesky client, tests, simulation, documentation, and workflows.
- Queried the connected GitHub repository, recent commits, open issues, workflow runs, selected production logs, and public state files. No open issues were returned at review time.
- Local Git history ends at `e998f191ae93034c4978903450c6bc8984f96633`. The inspected GitHub snapshot is `e3d8183a7a1f419afd73ba896e03916039466790`, four state-persistence commits ahead. The comparison lists state/data changes, not application source changes.
- All **124 existing tests passed** in a temporary copy, using dummy credentials and blocking external socket connections. The latest inspected GitHub CI run also succeeded.
- Additional synthetic probes reproduced false goal progress, premature promise resolution, legitimate promise text rejection, an incorrect temporal rejection, and plaintext persistence of a private-message marker.
- Did not run the live agent, send messages, purchase generation, generate images, modify production state, or change GitHub settings. Existing generated photographs were not visually assessed.
- This is an architectural and targeted behavior review, not an exhaustive security audit or proof of human-rated conversational quality.

## What to preserve

The modular Python architecture is a workable foundation. Preserve `NO_ACTION`, successful-send checks in reply paths, canonical image references, encrypted-vault overwrite protection, budget reservations, the centralized provider boundary, and the use of persistent state. Replace weak rules behind these systems rather than replacing the entire project.

## Confirmed findings and fixes

### 1. Private information can escape the vault — first priority

`agent/consolidator.py` writes the first 80 characters of the private journal into `episodic_memory.jsonl` and prints the journal to stdout. The inspected public GitHub file contains **31 entries with journal excerpts**. Their presence is confirmed; their sensitivity was not assessed or reproduced here.

The DM handler passes raw conversation text into `detect_and_manage_loops()`. That function writes excerpts into ordinary `narrative_state.json`, which the scheduler commits. A synthetic private marker was reproduced in that plaintext file. The inspected production narrative file had zero loops, so this review does **not** establish an actual production DM leak through this route.

The same unscoped loop store is retrieved for public replies by handle, creating a potential private-to-public context path.

**Fix:** scope memories as public, private conversation, or operator-only; enforce that scope during storage, retrieval, logging, and publication. Encrypt private loop contents. Remove private journal output and excerpts from public artifacts. Review existing exposed history/logs and prepare a separate cleanup plan before any history rewrite.

**Acceptance:** a unique private marker never appears in public prompts, files, stdout, logs, or outgoing public text during an end-to-end test.

### 2. The current POV image route is broken

`agent/image_engine.py:159` removes `-image-to-image` to derive a text-to-image model name. The 10 October production job rejected the resulting `gpt-image-2-5-sunburst` with Kie error **422: unsupported model name**. The two latest image actions in the inspected ledger became text-only posts.

**Fix:** separate explicit model IDs and request schemas for selfie/image-to-image and POV/text-to-image. Validate each against current provider documentation. Do not derive API identifiers by string deletion. Store requested action and actual delivered action separately; distinguish a deliberate text-only post from image failure.

**Acceptance:** mocked contract tests cover both request bodies and error responses. A separately authorized, bounded live generation check must eventually confirm both routes; mocks alone cannot prove provider acceptance or visual quality.

### 3. Goal progress is generated from mentions and the calendar

`agent/goal_manager.py:410` adds 15 pages for matching words; nightly processing adds 20. The probe **“I did not read the novel today.” advanced the page count from 65 to 80**. Sign documentation and plant progress also advance through fixed rules. Completed goals can retain their preceding metric value because completion is called before saving the final metric update.

**Fix:** distinguish mentioning an activity, intending it, doing it within the fictional simulation, and reflecting on it. Only a validated activity event changes progress. Apply event and metric changes together, once per event ID. Generalize away from hardcoded October 2026 goal IDs; support new goals after the seeds finish.

**Acceptance:** mentions and negations produce no progress; replaying an event produces no second increment; completed metrics equal the target; inactivity and abandonment are valid outcomes.

### 4. Promises can disappear without being fulfilled

`agent/narrative_engine.py:267` resolves an outstanding loop whenever it is the only loop with that person. A “good morning” exchange reproduced the resolution of an unrelated book commitment. Multiple recommendations are also reduced to generic topics such as “book recommendation.”

**Fix:** record the specific work/object, who promised what, source message, privacy scope, status, and evidence of completion. Separate acknowledgment from fulfillment. A new message alone must not resolve a commitment.

**Acceptance:** two separate book recommendations remain distinguishable; an unrelated exchange closes neither; a real matching follow-up closes the intended one only.

### 5. The validator blocks ordinary speech

`agent/validator.py:212` strips openings including “i will” and “i'll.” The probe “i will read it tomorrow.” became empty and was rejected. The temporal validator rejected “i had dinner yesterday.” at 09:00. Minimum length and terminal punctuation rules also exclude some natural short replies.

**Fix:** use structured generation responses to separate content from metadata. Stop treating ordinary sentence openings as model commentary. Validate tense and referenced date, not meal keywords alone. Separate hard safety constraints from optional style preferences. Preserve existing punctuation canon initially; any relaxation should be a conscious persona decision.

**Acceptance:** ordinary commitments, past-tense recollections, short acknowledgments, Korean replies, and truthful AI disclosure survive validation; actual malformed output and unsupported claims are still caught.

### 6. Memory exists, but important learning paths are not connected

`record_opinion()` and `discovered_fact` exist, but the reviewed production call sites do not populate them as part of normal conversation. The generator does not retrieve the opinion store into its normal prompt. Nightly consolidation promotes users by interaction count: 15 interactions can yield `trusted_friend`.

**Fix:** propose small, evidence-linked memory updates after successful interactions, with confidence, source, timestamp, and privacy scope. Retrieve only relevant memories. Separate familiarity, warmth, reciprocity, boundaries, and trust. Trust must never grant operational permissions. Store an opinion's history and reasons for revision rather than enforcing permanent agreement with an old stance.

**Acceptance:** she recalls a previously supplied preference correctly, does not invent facts, can correct a mistaken memory, and does not treat repeated spam as friendship.

### 7. Candidate ranking can lose the distinction between people

`agent/decision_engine.py:521` converts candidate scores into a dictionary keyed only by action type. Multiple reply candidates overwrite one another, then receive the same score when it is copied back. The external threshold is **0.50**, while documentation repeatedly says **0.75**. `FOLLOW` has an execution branch but no corresponding candidate creation in the reviewed decision engine; the repost candidate's fixed 0.40 score cannot clear the current threshold under the present modulation rules.

**Fix:** score individual candidate IDs, keep confidence separate, document the actual threshold, and test each advertised action's reachability. Rank genuine conversational value and unresolved commitments, not just broad topic matches.

**Acceptance:** changing the order of candidate input does not erase a stronger candidate's advantage; advertised actions are reachable in appropriate scenarios without forcing them.

### 8. Daily life still follows fixed assumptions

`state_manager.py` assumes morning reformer classes and recurring tea-related moods by hour. Updates add or subtract energy per call, so repeated context reads affect her state. The weekly planner, state rules, and narrative progress can disagree. Consolidation is keyed by calendar day, which also deserves tests around midnight and repeated sleep-period ticks.

**Fix:** one event-based life state with flexible activity windows, elapsed-time updates, location, available time, belongings, and current commitments. Plans may be delayed, interrupted, abandoned, or not worth mentioning. Derive age from birth date. Remove permanent autumn defaults from fallbacks.

**Acceptance:** rerunning observation at the same instant does not consume energy; missed ticks do not invent a whole day of activity; travel, clothing, weather, caption, and event time agree.

### 9. Dry-run and success reporting need clearer boundaries

The normal generator can still make billed calls during a runner dry-run. Context building and action completion update state, and vault saving is not universally excluded. Authentication failure switches into dry-run and can end successfully. Some like/repost/follow paths report success without validating the provider result.

**Fix:** explicit offline replay, paid preview, and live modes. Inject clock, storage, provider clients, and publisher. Offline replay should forbid all external calls and production writes. Report intentional silence, rejected draft, provider failure, authentication failure, partial delivery, and confirmed success separately.

**Acceptance:** production state hashes remain unchanged after offline replay; no outbound socket opens; authentication and delivery failures produce visible actionable health signals.

### 10. Persistence and billing claims exceed implementation guarantees

The budget ledger uses direct JSON writes without a cross-process transaction. Workflow concurrency serializes its own jobs but does not cover local runs. Only the successful final model response is reconciled; a billed empty primary result followed by fallback can be missed. An image job may finish and bill after a polling/download failure. Git state is saved after external publication, leaving a crash window in which a delivered action is not durably recorded. The push retry loop does not explicitly fail after all attempts fail.

**Fix:** transactional private state and an action outbox, durable provider request IDs, delivery reconciliation, and per-attempt billing. Persist accepted state before acknowledging work. Use provider-reported cost when available and version pricing assumptions. Make exhaustion of persistence retries a failure. Keep encrypted backups and recovery drills.

**Acceptance:** a process restart after a successful external send does not duplicate the post; failed persistence is surfaced; primary-plus-fallback and timed-out image jobs remain reconcilable.

### 11. Scheduler timing is not conversational timing

The latest four inspected scheduled runs were created hours apart despite a 30-minute cron definition. These observations establish sparse wakeups, not the exact cause of every delay. GitHub also documents that scheduled workflows can be delayed or dropped under load.

**Fix:** first measure wakeup gaps, inbox age, provider failure, and persistence health. For sustained conversation, consider a small persistent worker with a durable inbox and next-action queue; retain GitHub Actions for CI. Calculate response windows from sleep, ongoing conversation, and availability. Do not add arbitrary delays merely to imitate a human.

**Acceptance:** actionable inbox latency meets an agreed awake-hours target; sleep remains undisturbed; duplicate wakeups and restarts are safe. Hosting cost must be included before migration is approved.

### 12. Current simulation is not a naturalness evaluation

The 30-day harness uses scripted utterances, artificial stimuli, and fixed cost assumptions. Its restraint and completion metrics are useful regression checks, not evidence of compelling dialogue, accurate real billing, or meaningful promises. The existing suite passes while the targeted behavior probes above fail their intended expectations.

**Fix:** retain deterministic tests, then add archived-input replay, adversarial privacy tests, and blind human review of conversation sequences. Use native Korean review for register and pragmatics. Evaluate context across multiple turns and days, not only isolated posts.

**Acceptance:** a held-out set improves on continuity, specificity, appropriate brevity, emotional fit, and Korean naturalness without regressions in privacy, factual grounding, cost, or restraint. Measure latency and delivered actions separately from intended actions.

## Proposed creative additions

### A. An unfinished atlas that produces real digital artifacts

Build persistent typography sketches, short essays, annotated reading notes, and small fictional neighborhood studies. Each artifact has versions and a reason for changing. A follower's public suggestion can influence one, and she can later share the result. The evidence is the actual created digital work, not an invented counter saying she photographed ten signs.

Start with one pursuit, not several new content series. The atlas is a private organizing idea; it should not force numbered daily posts or turn every conversation into promotion.

### B. A coherent fictional world with explicit sources

Each event is labeled internally as an external observation, a user statement, a fictional life event, or an inference. Captions, images, goals, and memory draw from the same event. External claims such as exhibitions, prices, weather, or book details require an actual source or explicit uncertainty. Public screenshots and generated photos must not become evidence for invented real-world claims.

### C. Relationships with distinct histories

Remember that one person likes long book discussions while another exchanges one-line jokes. Learn preferred language and formality from evidence. Allow brief replies, disagreement, unanswered rhetorical questions, delayed follow-ups, and quiet exits. Remember boundaries more reliably than trivia. Do not optimize dependency or maximize response counts.

### D. Selective expression and a private draft notebook

Not every observation needs a post. Save interesting fragments, revisit only those that still matter, and discard many. A private scene can affect a later opinion without becoming a public diary entry. Offline reflection should use actual logged events rather than a generic nightly prompt and canned gratitude.

### E. Change with a reason

Let tastes and priorities evolve slowly after specific experiences or conversations. She may enjoy a book less than expected, lose interest in a project, or revise a judgment. Record why. Avoid scheduled quirks, manufactured typos, forced mood swings, or arbitrary “imperfection percentages.”

### F. Visual continuity beyond the face

Track a small set of belongings, clothes, weather constraints, and ongoing projects. Use the same scene specification for caption and image, then inspect generated output before publication for identity and scene agreement. Build alt text from the delivered image rather than the intended prompt alone. Missing identity references should block a selfie rather than silently produce an unanchored face.

## Suggested delivery sequence

| Phase | Scope | Exit gate |
| --- | --- | --- |
| 1. Repair | Privacy boundaries, POV model routing, promise and validator bugs, candidate IDs, truthful action outcomes | Targeted regressions pass; no private markers escape; provider contracts match documentation |
| 2. Reliable state | Offline replay mode, transactional state/outbox, billing reconciliation, recovery and monitoring | Restart/replay tests preserve memory and prevent duplicate delivery |
| 3. Continuity | Unified event model, evidence-linked memory, real commitment tracking, flexible activities, elapsed-time state | Multi-day replay has no unsupported progress or private-to-public retrieval |
| 4. Distinctive behavior | One atlas pursuit, evolving artifacts, relationship-aware voice, selective drafts, visual continuity | Reviewed conversation sequences and artifacts show recognizable development |
| 5. Evaluate and expand | Held-out replay, native Korean review, shadow drafts, bounded rollout, optional worker migration | Better blind review scores within the agreed total budget and health targets |

These are implementation batches, not guaranteed delivery dates. Stabilize one vertical slice before expanding: public recommendation → scoped memory → chosen activity → real digital artifact → appropriate follow-up → durable delivery record.

## Cost and complexity discipline

- Do not start with a multi-agent society, model fine-tuning, a vector database, or a larger model. None fixes the confirmed state and privacy defects.
- Start with simple structured storage and selective retrieval. A small private transactional store is sufficient until measured retrieval needs justify more infrastructure.
- Most observation/wakeup decisions should be cheap and deterministic. Spend model calls on ambiguous interpretation, useful drafts, and selected reviews.
- Retain the existing spending caps; explicitly account for previews, retries, critics, reflection, images, and any future hosting cost. The simulation's dollar figure is not a forecast of this expanded design.

## Skills and plugins

No additional plugin is required to begin. The connected GitHub tools and existing operations/persona skills are sufficient for the repair phase. Graphify has no prebuilt graph in this checkout; the findings here come from source tracing, live repository inspection, and executable probes, not a generated graph report.

After the architecture changes, update the operations and persona skills to match tested behavior. Add a small project-specific behavior-evaluation skill covering privacy, promises, Korean register, event provenance, repetition, and blind-review procedure. A second useful skill would maintain the fictional world's continuity rules and source labels.

Native Korean reviewers would provide more value for linguistic authenticity than another general plugin. Optional future integrations are curated public cultural sources and reliable private hosting; choose those only when the feature and budget are concrete.

## Evidence links

- [Reviewed repository](https://github.com/Protoxid/seoyeon-bluesky)
- [Latest inspected CI run](https://github.com/Protoxid/seoyeon-bluesky/actions/runs/37891324418)
- [Production run containing the unsupported POV model response](https://github.com/Protoxid/seoyeon-bluesky/actions/runs/38013039794)
- [Narrative engine](https://github.com/Protoxid/seoyeon-bluesky/blob/e3d8183a7a1f419afd73ba896e03916039466790/agent/narrative_engine.py)
- [Goal manager](https://github.com/Protoxid/seoyeon-bluesky/blob/e3d8183a7a1f419afd73ba896e03916039466790/agent/goal_manager.py)
- [Consolidator](https://github.com/Protoxid/seoyeon-bluesky/blob/e3d8183a7a1f419afd73ba896e03916039466790/agent/consolidator.py)
- [GitHub scheduling limitations](https://docs.github.com/en/actions/how-tos/troubleshoot-workflows)
- [Kie model documentation](https://docs.kie.ai/market/gpt/gpt-image-2-image-to-image)

Provider documentation is a moving target: verify the exact selected model's text-to-image and image-to-image contracts at implementation time. No new model is endorsed by this report without a project-specific evaluation.
