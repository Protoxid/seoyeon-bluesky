#!/usr/bin/env python3
"""
score_set.py — score a folder of images against the identity gates.

    python offline/score_set.py content/week2
    python offline/score_set.py content/grid --json out.json

Prints, per image: drift_gate cosine (+ face pixel width) and bone_gate's two
vertical ratios (nose_drop, face_len), then the mean of each column.

REUSES drift_gate.py and bone_gate.py — it does not reimplement the scoring.
drift_gate.score_file() gives the cosine; bone_gate.measure() gives the raw
ratios. This file is glue: it does not compute an embedding or a ratio itself.

Must be run from personas/seoyeon/ (or point --in at a folder relative to it),
because that is where canonical.npy, bone_stats.json and the gate modules
live. The script adds that folder to sys.path itself so it can be invoked as
`python offline/score_set.py <folder>` from the project root too.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

SEOYEON = pathlib.Path(__file__).resolve().parent.parent / "personas" / "seoyeon"
sys.path.insert(0, str(SEOYEON))

import drift_gate  # noqa: E402
import bone_gate    # noqa: E402


def resolve_folder(raw: str) -> pathlib.Path:
    """Accept a path relative to the CWD, the project root, or seoyeon/."""
    for base in (pathlib.Path.cwd(), SEOYEON.parent.parent, SEOYEON):
        p = (base / raw).resolve()
        if p.is_dir():
            return p
    sys.exit(f"no such folder: {raw}")


def score_folder(folder: pathlib.Path) -> list[dict]:
    files = sorted(p for p in folder.iterdir()
                   if p.suffix.lower() in (".png", ".jpg", ".jpeg"))
    if not files:
        sys.exit(f"no images in {folder}")

    if not drift_gate.CANON.exists():
        sys.exit("no canonical.npy — run: python drift_gate.py --calibrate "
                 "(from personas/seoyeon/)")
    if not bone_gate.STATS.exists():
        sys.exit("no bone_stats.json — run: python bone_gate.py --calibrate "
                 "(from personas/seoyeon/)")
    bone_app = bone_gate._app()

    rows = []
    for p in files:
        row = dict(file=p.name)
        drift = drift_gate.score_file(p)
        if drift is None:
            row["cosine"] = None
            row["face_px"] = None
        else:
            row["cosine"], row["face_px"] = drift

        ratios, note = bone_gate.measure(bone_app, p)
        if ratios is None:
            row["nose_drop"] = None
            row["face_len"] = None
            row["bone_note"] = note
        else:
            row["nose_drop"] = ratios["nose_drop"]
            row["face_len"] = ratios["face_len"]
            row["bone_note"] = note
        rows.append(row)
    return rows


def mean(vals: list[float | None]) -> float | None:
    got = [v for v in vals if v is not None]
    return sum(got) / len(got) if got else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", help="folder of images to score, e.g. content/week2")
    ap.add_argument("--json", help="also write the per-file rows to this path")
    a = ap.parse_args()

    folder = resolve_folder(a.folder)
    rows = score_folder(folder)

    print(f"\n  {len(rows)} image(s) in {folder}\n")
    print(f"  {'FILE':<32}{'COSINE':>8}{'FACE px':>9}{'nose_drop':>11}{'face_len':>10}")
    print("  " + "-" * 70)
    for r in rows:
        cos = f"{r['cosine']:.3f}" if r["cosine"] is not None else "—"
        px = f"{r['face_px']}" if r["face_px"] is not None else "—"
        nd = f"{r['nose_drop']:.4f}" if r["nose_drop"] is not None else "—"
        fl = f"{r['face_len']:.4f}" if r["face_len"] is not None else "—"
        print(f"  {r['file']:<32}{cos:>8}{px:>9}{nd:>11}{fl:>10}")

    m_cos = mean([r["cosine"] for r in rows])
    m_nd = mean([r["nose_drop"] for r in rows])
    m_fl = mean([r["face_len"] for r in rows])
    print("  " + "-" * 70)
    print(f"  {'MEAN':<32}"
          f"{(f'{m_cos:.3f}' if m_cos is not None else '—'):>8}"
          f"{'':>9}"
          f"{(f'{m_nd:.4f}' if m_nd is not None else '—'):>11}"
          f"{(f'{m_fl:.4f}' if m_fl is not None else '—'):>10}")

    no_face = [r["file"] for r in rows if r["cosine"] is None]
    if no_face:
        print(f"\n  {len(no_face)} file(s) with no face detected by drift_gate: "
              f"{', '.join(no_face)}")

    if a.json:
        out = pathlib.Path(a.json)
        out.write_text(json.dumps(
            dict(folder=str(folder), rows=rows,
                 mean_cosine=m_cos, mean_nose_drop=m_nd, mean_face_len=m_fl),
            indent=2), encoding="utf-8")
        print(f"\n  wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
