#!/usr/bin/env python3
"""
make_lora_dataset.py — turn generated stills into an ai-toolkit training folder.

    python make_lora_dataset.py --check          what exists, what is missing
    python make_lora_dataset.py --build          write _lora_dataset/

WHAT AI-TOOLKIT WANTS: one flat folder, an image and a matching `.txt` caption
side by side with the same stem. Nothing else. No subfolders, no json.

    _lora_dataset/
        lx_c01.png
        lx_c01.txt
        ...

THE CAPTIONS COME FROM lora_shots.py, not from a captioner. They were written
to the Krea-2 recipe's own schema and every one carries the trigger `sy3nh`.
Auto-captioning would describe her FACE, and captioning the constant teaches
the model that the constant is optional.

CURATION IS A HUMAN STEP AND THIS SCRIPT WILL NOT DO IT. Pass `--skip` with
the ids that did not come out. The recipe wants 15-40 images and says 20 good
ones are enough, so discarding ten of thirty is a normal outcome, not a
failure.
"""
from __future__ import annotations
import argparse, pathlib, re, shutil, sys

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import lora_shots                                        # noqa: E402

SRC = ROOT / "content" / "lora"
OUT = ROOT / "_lora_dataset"


def current_hashes() -> tuple[dict, str]:
    """id -> hash of the prompt that WOULD be sent today. ({}, reason) on
    failure, and the caller reports the reason rather than assuming nothing is
    stale."""
    try:
        import console
        d = console.pool_facts("lora")
    except Exception as e:                               # noqa: BLE001
        return {}, f"could not read prompt hashes: {e}"
    if d.get("error"):
        return {}, f"pool_facts: {d['error']}"
    rows = d.get("shots") or []
    if not rows:
        return {}, "pool_facts returned no shots"
    return {r["id"]: r.get("hash", "") for r in rows}, ""


def newest(sid: str, want_hash: str = ""):
    """The render for a shot id that MATCHES THE CURRENT PROMPT.

    NEWEST IS NOT THE SAME AS CURRENT, and this script originally returned the
    newest by mtime with no hash check at all. It would have built a training
    set out of 18 images generated before the clothing, hair and aspect-ratio
    fixes -- silently, because the files were there and the count looked fine.
    A dataset is the one artefact where a stale input is invisible afterwards:
    you cannot tell from a trained LoRA which images went in.

    Filename shape is <id>_<6 hex of the prompt>_<n>.png, so the hash IS the
    test. mtime only breaks ties among matching renders.
    """
    pat = re.compile(rf"^{re.escape(sid)}_[0-9a-f]{{6}}_\d+\.png$")
    if not SRC.is_dir():
        return None, None
    hits = sorted((q for q in SRC.glob(f"{sid}_*.png") if pat.match(q.name)),
                  key=lambda q: q.stat().st_mtime)
    if not hits:
        return None, None
    if not want_hash:
        return hits[-1], None
    match = [q for q in hits if f"_{want_hash}_" in q.name]
    return (match[-1] if match else None), (hits[-1] if not match else None)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--skip", default="", help="comma-separated ids to exclude")
    a = ap.parse_args()
    skip = {s.strip() for s in a.skip.split(",") if s.strip()}

    hashes, why = current_hashes()
    if why:
        print(f"  ! staleness NOT checked: {why}")
    rows, missing, stale = [], [], []
    for d in lora_shots.SHOTS:
        sid = d["id"]
        if sid in skip:
            continue
        q, old = newest(sid, hashes.get(sid, ""))
        if q:
            rows.append((sid, q, d["caption"], d["framing"]))
        elif old:
            stale.append(sid)
        else:
            missing.append((sid, None, d["caption"], d["framing"]))

    from collections import Counter
    have = Counter(f for _s, _q, _c, f in rows)
    print(f"  found   {len(rows)}/{len(lora_shots.SHOTS) - len(skip)}")
    print(f"  mix     close {have['close']}  half {have['half']}  full {have['full']}")
    if missing:
        print(f"  MISSING {len(missing)}: {', '.join(s for s, *_ in missing[:8])}"
              + (" ..." if len(missing) > 8 else ""))
    if stale:
        print(f"  STALE   {len(stale)} rendered from an OLDER prompt and will "
              f"NOT be used: {', '.join(stale[:8])}"
              + (" ..." if len(stale) > 8 else ""))
        print(f"          Regenerate them, or move them out of "
              f"{SRC.relative_to(ROOT)}/.")

    # The recipe's own numbers, checked rather than assumed.
    bad = []
    if len(rows) < 15:
        bad.append(f"{len(rows)} images — the recipe's floor is 15")
    if len(rows) > 40:
        bad.append(f"{len(rows)} images — the recipe's ceiling is 40")
    if rows and have["full"] < 3:
        bad.append(f"only {have['full']} full-body — they teach proportion; "
                   f"a set without them makes a model that only knows how to crop")
    if rows and have["close"] < 5:
        bad.append(f"only {have['close']} close shots — face detail comes from these")
    # UNIFORM ASPECT RATIO. Research on character LoRAs is explicit that
    # inconsistent aspect ratios degrade generation quality, and the first
    # batch shipped three resolutions across two ratios. Checked, not assumed.
    try:
        from PIL import Image
        ars = {}
        for _s, q, _c, _f in rows:
            w, h = Image.open(q).size
            ars.setdefault(round(w / h, 3), []).append(q.name)
        if len(ars) > 1:
            bad.append("mixed aspect ratios: "
                       + "; ".join(f"{k} ({len(v)} files)" for k, v in ars.items()))
    except ImportError:
        print("  (aspect ratios not checked — Pillow not installed)")
    for b in bad:
        print(f"  ! {b}")

    if a.check or not a.build:
        print("\n  nothing written (use --build)")
        return 1 if bad else 0
    if bad:
        print("\n  refusing to build — fix the above or pass --skip deliberately")
        return 1

    OUT.mkdir(exist_ok=True)
    for q in OUT.glob("*"):
        q.unlink()
    for sid, q, cap, _f in rows:
        shutil.copy2(q, OUT / f"{sid}.png")
        (OUT / f"{sid}.txt").write_text(cap + "\n", encoding="utf-8")
    n_png = len(list(OUT.glob("*.png")))
    n_txt = len(list(OUT.glob("*.txt")))
    print(f"\n  {OUT.name}/  {n_png} images, {n_txt} captions")
    if n_png != n_txt:
        print("  ! image and caption counts differ — do not train on this")
        return 1
    print("  Upload this ONE FOLDER to the pod. Nothing else.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
