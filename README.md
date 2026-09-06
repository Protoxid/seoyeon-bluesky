# Seo-yeon Han — start here
An AI persona operated across Instagram, Bluesky and Fanvue.
**Read the file for your job. Do not read the whole repository.**

## IF YOU ARE AN AGENT, FIND YOUR ROLE
| your job | read |
|---|---|
| Plan the weekly Fanvue + Bluesky drops | `roles/weekly_planner.md` |
| Publish to Bluesky / Fanvue, run DMs | `roles/adult_ops.md` |
| Publish to Instagram | `roles/instagram_ops.md` |

Each role file names the two or three documents you need and tells you what
**not** to open. That list is a contract, not a suggestion — this repo is
~9,500 lines of markdown and most of it is history.

## THE FOUR CANONICAL DOCUMENTS
Everything else is history, evidence, or code.

| file | owns |
|---|---|
| `CANON.md` | who she is. Identity, life, voice, hard rules. |
| `PLATFORMS.md` | the tier model. Which rules apply where. Live status. |
| `PIPELINES.md` | how an image gets made. Both generator stacks. |
| `growth/RUNBOOK.md` | the commands and the weekly loop. |

Supporting, read only when the rule is in question:
- `growth/COMPLIANCE.md` — every platform rule quoted, with its source URL
- `personas/seoyeon/wiki/domains/persona/character.md` — the character bible
- `personas/seoyeon/wiki/domains/pipeline/playbook.md` — why each prompt rule exists

## THE RULE THAT KEEPS THIS TIDY
**One fact, one home.** A document that restates a fact from another document
will drift from it, and then a reader has two answers and no way to choose.
Link instead. This repo had three `HANDOFF.md` files that were 85% verbatim
copies of each other, and they disagreed about her age, her job and which
image generator to use.

If you find a contradiction: fix it in the file that **owns** the fact per the
table above, and delete it from the other. Never patch both.
