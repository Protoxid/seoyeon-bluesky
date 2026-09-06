#!/usr/bin/env python3
"""
weekly_prep.py — everything that can be done without spending money, done.

    python weekly_prep.py                 -> _prep/plan.md + _prep/sheet.jpg
    python weekly_prep.py --pool week2    just one pool

WHAT THIS IS FOR. The operator has a full-time job and this project demands
twenty small decisions a week. It cannot demand fewer decisions overall -- 82%
of generations are discarded and only a human can say which -- but it can
BATCH them into one sitting instead of dripping them across the week.

SO THIS SPENDS NOTHING, EVER. No API client is imported and no key is read.
It audits, it counts what is missing, it prices what is missing, it lays out
what already exists on one sheet, and it writes the exact commands. The
operator looks at the sheet, says which numbers to kill, and one command
spends. That division is the entire point: THE MACHINE DOES THE TYPING, THE
HUMAN DOES THE LOOKING, and the looking is the part that is actually the work.

WHY A CONTACT SHEET RATHER THAN FILES. Reviewing 20 stills one at a time on a
phone is 20 decisions with no context; the same 20 on one numbered sheet is a
single glance, and inconsistency between them -- the thing that actually breaks
a persona grid -- is only visible SIDE BY SIDE. A flat that changed rooms is
invisible in isolation and obvious on a sheet.
"""
from __future__ import annotations
import argparse, datetime as _dt, importlib, io, os, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import console                                          # noqa: E402

PREP = ROOT / "_prep"
PRICE_PER_IMAGE = 0.09          # gpt-image-2 on Kie, flat
SHEET_COLS, SHEET_CELL = 5, 380


def generated(pool_dir: pathlib.Path, sid: str, want_hash: str = ""):
    """Return (all renders newest-first-ish, the ones matching the CURRENT prompt).

    ON DISK IS NOT THE SAME AS UP TO DATE. console.py already solved this and
    this file ignored it for one revision: it hashes the prompt text and marks
    which renders were made from the prompt that is in the pool RIGHT NOW. A
    still generated before the prompt changed is stale even though it is the
    newest file -- w2r_fit_door's wardrobe changed today, so a render from
    yesterday is a picture of the wrong outfit.

    The ordering fix matters too, and it is the second time in one evening:
    the hash in a filename is NOT a counter, so sorting names sorts noise.
    w2r_fit_door_279a0c is the regenerated still and sorts BEFORE the
    superseded _36013e. mtime, always.
    A rule learned in one script does not propagate to the next by itself.
    """
    pat = re.compile(rf"^{re.escape(sid)}_[0-9a-f]{{6}}_\d+\.png$")
    if not pool_dir.is_dir():
        return [], []
    hits = sorted((q for q in pool_dir.glob(f"{sid}_*.png") if pat.match(q.name)),
                  key=lambda q: q.stat().st_mtime)
    current = [q for q in hits if want_hash and f"_{want_hash}_" in q.name]
    return hits, current


def prompt_hashes(pool: str) -> tuple[dict, str]:
    """id -> 6-hex hash of the prompt outside.py would send TODAY. Free.

    Returns ({}, reason) when it cannot be computed, and the caller reports
    the reason. The first version guessed a function name that does not exist
    (`pool_state`; it is `pool_facts`) behind a hasattr check, so it returned
    an empty dict and the report printed "stale: 0" -- which read as "nothing
    is out of date" when it meant "never checked". A SILENT ZERO IS THE MOST
    EXPENSIVE KIND OF WRONG, because nobody investigates good news.
    """
    fn = getattr(console, "pool_facts", None)
    if fn is None:
        return {}, "console.pool_facts is gone — staleness NOT checked"
    try:
        d = fn(pool)
    except Exception as e:                               # noqa: BLE001
        return {}, f"pool_facts({pool}) raised: {e}"
    if d.get("error"):
        return {}, f"{pool}: {d['error']}"
    rows = d.get("shots") or []
    return {r["id"]: r.get("hash", "") for r in rows}, ""


def survey(only: str | None):
    rows, missing, stale, notes = [], [], [], []
    for pool, (mod_name, attr, flags, outdir) in console.POOLS.items():
        if only and pool != only:
            continue
        try:
            mod = importlib.import_module(mod_name)
            shots = getattr(mod, attr)
        except Exception as e:                           # noqa: BLE001
            rows.append((pool, "-", f"could not read: {e}", []))
            continue
        hashes, why = prompt_hashes(pool)
        if why:
            notes.append(why)
        d = ROOT / outdir
        have = []
        n_stale = 0
        for s_ in shots:
            sid = s_["id"] if isinstance(s_, dict) else s_.id
            hits, current = generated(d, sid, hashes.get(sid, ""))
            if not hits:
                missing.append((pool, sid, flags))
                continue
            have.append((sid, hits))
            is_locked = bool(s_.get("locked") if isinstance(s_, dict) else getattr(s_, "locked", False))
            if hashes.get(sid) and not current and not is_locked:
                stale.append((pool, sid, flags))
                n_stale += 1
        label = f"{len(have)}/{len(shots)}"
        if n_stale:
            label += f"  ({n_stale} stale)"
        rows.append((pool, outdir, label, have))
    return rows, missing, stale, notes


def run_audit(script: str) -> tuple[bool, str]:
    """Clean means ZERO ISSUES, not exit code 0.

    audit.py exits 0 while printing "65 issue(s)". Trusting the return code
    made this script report the audits as clean when they were not -- a status
    line that lies is worse than no status line, because it is the one thing
    read on a phone in fifteen seconds. The count is parsed out of the output.
    """
    env = {**os.environ, "PYTHONUTF8": "1"}
    r = subprocess.run([sys.executable, "-Xutf8", str(ROOT / script)],
                       capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env)
    out = ((r.stdout or "") + (r.stderr or "")).strip()
    m = re.search(r"(\d+)\s+issue\(s\)", out)
    if m:
        n = int(m.group(1))
        return n == 0, f"{n} issue(s)"
    if r.returncode != 0:
        return False, (out.splitlines() or ["failed"])[-1]
    tail = [ln.strip() for ln in out.splitlines() if ln.strip()]
    return True, tail[-1] if tail else "clean"


def sheet(pairs, dest: pathlib.Path) -> int:
    """Numbered contact sheet. Returns how many cells were drawn."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("  ! Pillow not installed — no sheet. pip install pillow")
        return 0
    if not pairs:
        return 0
    cols = SHEET_COLS
    rows = (len(pairs) + cols - 1) // cols
    cell = SHEET_CELL
    label = 34
    sheet_img = Image.new("RGB", (cols * cell, rows * (cell + label)), "white")
    dr = ImageDraw.Draw(sheet_img)
    for i, (tag, path) in enumerate(pairs, 1):
        try:
            im = Image.open(path).convert("RGB")
        except Exception:                                # noqa: BLE001
            continue
        im.thumbnail((cell, cell))
        cx = ((i - 1) % cols) * cell
        cy = ((i - 1) // cols) * (cell + label)
        sheet_img.paste(im, (cx + (cell - im.width) // 2, cy + label))
        dr.text((cx + 6, cy + 8), f"{i:2}. {tag}"[:46], fill="black")
    dest.parent.mkdir(parents=True, exist_ok=True)
    sheet_img.save(dest, quality=88)
    return len(pairs)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", default=None)
    ap.add_argument("--sheet-pools", default="week2,week2_reel",
                    help="which pools go on the contact sheet")
    a = ap.parse_args()

    PREP.mkdir(exist_ok=True)
    rows, missing, stale, notes = survey(a.pool)
    ok_img, last_img = run_audit("audit.py")
    ok_vid, last_vid = run_audit("audit_video.py")

    want_pools = [p.strip() for p in a.sheet_pools.split(",") if p.strip()]
    pairs = []
    for pool, outdir, _c, have in rows:
        if pool not in want_pools:
            continue
        for sid, hits in have:
            pairs.append((sid, hits[-1]))
    # A DATED FILENAME EVERY RUN, ON PURPOSE. The device mount hardlinks a
    # file once it has been staged to the cloud session and then REFUSES to
    # stage that path again. A fixed sheet.jpg therefore stages on the first
    # run and fails on every run after it -- the scheduled job would have
    # died at the send step, silently, forever. A fresh name sidesteps it.
    stamp = _dt.datetime.now().strftime('%Y-%m-%d_%H%M')
    sheet_path = PREP / f'sheet_{stamp}.jpg'
    n = sheet(pairs, sheet_path)
    for old in sorted(PREP.glob('sheet_*.jpg'))[:-6]:
        try:
            old.unlink()          # keep the last six
        except OSError:
            pass                  # the mount forbids delete; harmless

    today = _dt.date.today().isoformat()
    L = [f"# Week prep · {today}", "",
         "Nothing here spent anything. This file lists what exists, what does",
         "not, what the missing work costs, and the exact commands.", "",
         "## Pools", "", "| pool | on disk | folder |", "|---|---|---|"]
    for pool, outdir, count, _have in rows:
        L.append(f"| `{pool}` | {count} | `{outdir}` |")

    L += ["", "## Audits", "",
          f"- `audit.py` — {'clean' if ok_img else 'ISSUES'} — {last_img}",
          f"- `audit_video.py` — {'clean' if ok_vid else 'ISSUES'} — {last_vid}",
          "", "## Not generated yet", ""]
    if not missing:
        L.append("Nothing pending.")
    else:
        L.append(f"{len(missing)} shot(s), about "
                 f"**${len(missing) * PRICE_PER_IMAGE:.2f}** at "
                 f"${PRICE_PER_IMAGE:.2f} an image.")
        L.append("")
        by_pool: dict[str, list[str]] = {}
        for pool, sid, flags in missing:
            by_pool.setdefault(pool, []).append((sid, flags))
        for pool, items in by_pool.items():
            ids = ",".join(s for s, _f in items)
            flags = " ".join(items[0][1])
            L.append(f"**{pool}** — {len(items)}")
            L.append("```")
            L.append(f"python outside.py {flags} --only {ids} --dry-run")
            L.append(f"python outside.py {flags} --only {ids}")
            L.append("```")
            L.append("")

    L += ["", "## Generated, but from an OLD prompt", ""]
    for w in notes:
        L.append(f"- **could not check:** {w}")
    if notes:
        L.append("")
    if not stale and not notes:
        L.append("None — every render on disk matches the prompt in the pool.")
    elif not stale:
        L.append("None found, but see the unchecked pools above.")
    else:
        L.append(f"{len(stale)} shot(s) whose prompt has changed since the "
                 f"image was made. The file exists, so nothing flags it as "
                 f"missing, but it is a picture of the old wording.")
        L.append("")
        for pool, sid, flags in stale:
            L.append(f"- `{sid}` ({pool}) — `python outside.py "
                     f"{' '.join(flags)} --only {sid}`")
    L += ["", "## The sheet", "",
          f"`_prep/{sheet_path.name}` — {n} image(s), numbered, pools: "
          f"{', '.join(want_pools)}.",
          "Reply with the numbers to kill. Anything killed gets regenerated",
          "on the next run; anything not killed is approved and gets used.", ""]
    io.open(PREP / "plan.md", "w", encoding="utf-8",
            newline="\n").write("\n".join(L) + "\n")

    print(f"  _prep/plan.md")
    print(f"  _prep/{sheet_path.name}   {n} image(s)")
    print(f"  pending: {len(missing)} shot(s), "
          f"~${len(missing) * PRICE_PER_IMAGE:.2f}")
    print(f"  stale:   {len(stale)} shot(s) made from an older prompt"
          + (f"   ({len(notes)} pool(s) NOT CHECKED)" if notes else ""))
    print(f"  audits: image {'ok' if ok_img else 'ISSUES'}, "
          f"video {'ok' if ok_vid else 'ISSUES'}")
    print("\n  Nothing was spent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
