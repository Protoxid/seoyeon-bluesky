# AGENTS.md

Operating rules for any agent working in this repository.

**Read `CLAUDE.md` first. It is the operative layer and it is loaded
automatically.** This file exists because the LLM-Wiki convention expects it;
it is a pointer, not a second copy. A second copy of the truth drifts, and this
project has proved that twice — a published playbook that went a dozen
corrections stale, and a model id that stayed wrong in code after being
corrected in prose.

## Layout

    CLAUDE.md              operative layer: stack, absolute rules, the index
    AGENTS.md              this pointer
    *.py                   the code. Stays at the root: every module imports by
                           bare name and every documented command says
                           `python outside.py`
    wiki/index.md          catalog of every document
    wiki/overview.md       the domain map
    wiki/log.md            append-only decision log
    wiki/domains/persona/     who she is, her week, her stories
    wiki/domains/pipeline/    playbook.md — the full reasoning. handoff.md
    wiki/domains/publishing/  plans, reels, captions
    wiki/archive/          superseded, kept for the reasoning in it
    content/, master/, locations/, publish/, clips/   generated assets
    _trash/                spent one-shot scripts. Nothing is deleted here

## Where things run — check this before anything else

Generations happen in the OPERATOR'S PowerShell. `device_bash` reaches his
machine but has **no network at all**, so it edits and inspects and never
generates; the cloud shell reaches PyPI and nothing else. API keys live on his
machine and never move. Two whole classes of bug came from forgetting this:
every ffmpeg script worked in development and died in PowerShell, first on a
missing `ffprobe` and then on a Windows drive-letter colon splitting a
filtergraph. `ffbin.py` handles both.

## Rules

1. **Read the relevant playbook section before changing a rule.** Every entry
   was paid for with a failed generation. When a rule looks wrong, read it
   before overriding it.
2. **Correct the value, not just the prose.** Writing SUPERSEDED above a wrong
   model id leaves the wrong model id in a file that scripts read.
3. **Verify the artefact, not the exit code.** ffprobe the duration, re-read
   the file, print the constant. A tool that returns 0 has reported that it
   ran, not that it was right.
4. **Prefer the artefact the pipeline PRODUCED over any record kept about it.**
   `publish/feed` cannot go stale; `posts.json` can.
5. **The operator's plain statement outranks this repository's bookkeeping.**
6. **Append to `wiki/log.md` when a decision changes.** Do not rewrite history
   in place; the corrections are the most valuable content here.
7. **Cross-link with relative markdown links.** Update `wiki/index.md` when a
   page is added.
8. **Decide whether the PROMPT or the CHECKER is wrong before changing
   either.** Six of the first eight flags `audit_video.py` raised were the
   checker's fault, and the same run missed a real fault that was already
   known. A checker that encodes an over-correction makes the mistake
   permanent while looking principled.
9. **When a mechanical edit touches many files, grep for the REPLACEMENT
   text.** A sweep once replaced every duration check with `0.0`. Everything
   imported, everything ran, and every guard passed forever. A crash announces
   itself; a disabled check does not.
10. **A superseded file gets a banner AND a move.** Prose marked SUPERSEDED
    above a live value leaves the live value in place for scripts to read, and
    a dead file beside a live one with a similar name gets used by mistake.
