# Index

Every document in the project. `CLAUDE.md` at the root is the operative layer
and is loaded automatically; everything here is read on demand.

Last checked **4 Sep 2026**.

## Start here

| page | what it is |
|---|---|
| [`../CLAUDE.md`](../CLAUDE.md) | stack, absolute rules, the **149-rule index**. Loaded automatically |
| [`domains/pipeline/handoff.md`](domains/pipeline/handoff.md) | **read this first if you are new.** Current state, where things run, what is open |
| [`../AGENTS.md`](../AGENTS.md) | how an agent works in this repository |
| [`overview.md`](overview.md) | the three domains and what changes when |
| [`log.md`](log.md) | append-only decision log |

## persona — slowest moving

| page | what it is |
|---|---|
| [`domains/persona/character.md`](domains/persona/character.md) | who she is, her gear, the decisions behind her |
| [`domains/persona/profile.md`](domains/persona/profile.md) | the account's positioning |
| [`domains/persona/week-structure.md`](domains/persona/week-structure.md) | her week as slots, and the fixed neighbourhoods |
| [`domains/persona/grid-stories-week1.md`](domains/persona/grid-stories-week1.md) | week 1 as one real week, shot by shot |

## pipeline — fastest moving

| page | what it is |
|---|---|
| [`domains/pipeline/playbook.md`](domains/pipeline/playbook.md) | **the full reasoning.** 149 rules, each with the failure that produced it |
| [`domains/pipeline/handoff.md`](domains/pipeline/handoff.md) | written for a model that has never seen the project |

## publishing — weekly

| page | what it is |
|---|---|
| [`domains/publishing/week2-plan.md`](domains/publishing/week2-plan.md) | **the current week.** Posts, captions, calendar, per-reel status |
| [`domains/publishing/reels-week2.md`](domains/publishing/reels-week2.md) | the reel slate and why each one exists |
| [`domains/publishing/reel-r1-voiceover.md`](domains/publishing/reel-r1-voiceover.md) | **R1, live spec.** Voice-over build: studio plate, clip 1, three POV clips, audio |
| [`domains/publishing/reel-r4-comfyui.md`](domains/publishing/reel-r4-comfyui.md) | **R4, live spec.** ComfyUI ref2v prompts, positive and negative split |
| [`domains/publishing/reel-r2-washing-machine.md`](domains/publishing/reel-r2-washing-machine.md) | R2 — **RETIRED**, killed before publication. Kept for the reasoning |
| [`domains/publishing/captions-week1-day1.md`](domains/publishing/captions-week1-day1.md) | week 1 captions |
| [`domains/publishing/captions-week1-day2.md`](domains/publishing/captions-week1-day2.md) | week 1 captions |

## archive — superseded, kept for the reasoning

Each carries a banner saying what replaced it and why.

| page | superseded by |
|---|---|
| [`archive/reel-01-first.md`](archive/reel-01-first.md) | `reel-r1-voiceover.md` — R1 as a Flow clip, before Flow refused her face |
| [`archive/reel-voiced-comfyui.md`](archive/reel-voiced-comfyui.md) | `reel-r1-voiceover.md` — the lip-sync build |
| [`archive/reel-voiced-full.md`](archive/reel-voiced-full.md) | `reel-r1-voiceover.md` — all four segments lip-synced |
| [`archive/voiced-reel-pipeline.md`](archive/voiced-reel-pipeline.md) | `reel-r1-voiceover.md` — the route comparison |
| [`archive/grid-seed.md`](archive/grid-seed.md) | the current grid |
| [`archive/playground.md`](archive/playground.md) | `domains/persona/character.md` |

## Publishing — automated since 4 Sep

| script | what it does |
|---|---|
| `ig_publish.py` | posts one reel or still to Instagram via Meta's API. Uploads to protoxiderpg.it over FTP, Meta fetches it once, the file is deleted. `--dry-run` proves the token for free |
| `publish_queue.py` | the approved queue. `--add` puts something in it, `--due` posts what is ready. **Nothing publishes that a human did not queue** |
| `weekly_prep.py` | Sunday's contact sheet and plan. Spends nothing |
| `publish_prep.py` | sRGB, sizing and the per-shot crop anchor. `ig_publish` calls it — do not convert images any other way |

Secrets, all gitignored: `ig_token.txt` · `ig_user_id.txt` · `ftp_host.txt` ·
`ftp_public.txt`. The Meta app secret is not stored anywhere in the project.

## Not in the wiki, but canon

`identity_block.txt` · `body_block.txt` · `identity_brief.txt` at the root are
prompt fragments read by the code. They are canon and they are not duplicated
here — a second copy of the truth drifts, and this project has proved that
twice.
