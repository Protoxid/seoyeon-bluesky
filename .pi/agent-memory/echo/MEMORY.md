# Echo — Agent Memory Index

I am the Instagram-only publisher (tier 1). I create nothing; I publish what Nova approved, after verification. No Bluesky / Fanvue / Kie credentials — never acquire them.

## Key facts
- **Boot gate**: first command is `git rev-parse --git-dir` — if it says `gitdir: .../worktrees/...`, stop and return `relaunch needed — worktree`. Content pools, plates and cap files exist only in the main tree.
- **Loop**: `check_reel.py` (video only) → `ig_publish.py --video <file> --caption-file <caps/x.txt> --dry-run` → live. Never skip the dry run; its free GET proves token/account/scope.
- **Image assets**: W37+ weeks are PNG photos. `ig_publish.py` auto-detects (is_image) and posts as photo — `check_reel.py` is N/A for PNGs (it is a video validator).
- **Path semantics**: `--video` resolves relative to `personas/seoyeon/` (so `content/w37_..._1.png` works from repo root), but `--caption-file` is CWD-relative — from repo root pass `personas/seoyeon/caps/<file>.txt`.
- **Dry-run side effects**: running ig_publish dry-run on a PNG writes a temp JPEG into `personas/seoyeon/_prep/feed/` (gitignored, pipeline artifact, not content). Real run would FTP to protoxiderpg.it + POST to graph.instagram.com; dry-run returns before both.
- **Gate on images**: sibling check (1 render per shot id, else needs `--i-picked-this`) and stale-prompt hash (silently skipped for pools not in `console.POOLS` — w37 pool has no POOLS row, documented gap).
- **Schedule**: tier-1 IG week rows live in `growth/schedule_assets/weekly_schedule.json`; shape = id, tier 1, lanes ["instagram"], media_type image, media_file repo-root-relative (`personas/seoyeon/content/...`), caption_file `personas/seoyeon/caps/...`, publish_at, status ready, platforms ["instagram"]. No funnel/link/credential fields for tier 1.
- **W37 (2026-09-07)**: 7 entries, all verified, all dry-run OK (token OK @syeon.hn MEDIA_CREATOR), registered 8→15 rows, zero published. Details in `w37_2026-09-07.md`.

## Refusals I must issue (never fix myself)
- `render_approved: false` → back to Nova. `renders_available > 1` → refuse until `--i-picked-this`.
- Caption wrong/ugly/restates image/missing tag block → back to Nova. Never edit captions.
- Tier/policy refusal from `growth/syndicate.py` → report, never work around.

## Post-publish bookkeeping
Mark `status: published` + permalink in weekly_schedule.json; append run record to `growth/STATUS.md`. Idempotency lives in STATUS.md.