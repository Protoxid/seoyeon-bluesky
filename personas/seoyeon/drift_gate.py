#!/usr/bin/env python3
"""
drift_gate.py — the numerical identity check.

You are not training a LoRA, so nothing forces a generated image to be HER.
This is what replaces that: every frame gets scored against the master stack
and routed automatically, so "does this look like her?" stops being a tired
2am judgement call and becomes a number.

How it works
  1. Compute an ArcFace face embedding for each frame in master/a/.
  2. Average them into one CANONICAL embedding — the mathematical centre of
     who she is. Saved to canonical.npy; built once, reused forever.
  3. For any new image, embed it and take the cosine similarity against the
     canonical. 1.00 = the same face. Lower = drift.

    python drift_gate.py --calibrate     # build canonical, check the stack
    python drift_gate.py                 # score + sort ./batch
    python drift_gate.py --in some/dir   # score any folder

Needs: pip install insightface onnxruntime-gpu opencv-python numpy
(onnxruntime-gpu on the 5060 Ti; plain onnxruntime works, just slower.)
"""
from __future__ import annotations
import argparse, itertools, pathlib, shutil, sys

ROOT = pathlib.Path(__file__).parent
MASTER = ROOT / "master" / "a"
# The canonical is an AVERAGE, so every frame in it moves the target. Full
# profiles score ~0.75 against a frontal-built centre by geometry alone — half
# the landmarks ArcFace aligns to are not visible — so including them makes the
# centre muddier for every frontal image we will ever score against it.
# outside.py never uses the profiles as generation references either.
# Named explicitly rather than globbed: a canonical should be a decision.
CANON_FRAMES = ["a1_front.png", "a2_tq_left.png", "a3_tq_right.png"]
CANON = ROOT / "canonical.npy"

PASS, REPAIR = 0.75, 0.62      # for a head shot; scaled down for small faces


def thresholds(face_px: int) -> tuple[float, float, str]:
    """Scale the bar to how much face the embedder actually got.

    ArcFace aligns to 112x112. A 900px face downsamples into that cleanly; a
    200px face is upscaled and its embedding is noisier, so it scores lower for
    the SAME person. Full-body frames are penalised by framing, not identity.
    Judging them against the head-shot bar produces false rejects.
    """
    if face_px >= 500:
        return PASS, REPAIR, ""
    if face_px >= 350:
        return PASS - 0.03, REPAIR - 0.03, "half-body"
    if face_px >= 200:
        return PASS - 0.07, REPAIR - 0.06, "full-body"
    return PASS - 0.11, REPAIR - 0.09, "distant"


def _app():
    import os as _os
    _os.environ.setdefault("ORT_LOGGING_LEVEL", "3")
    import warnings; warnings.filterwarnings("ignore")
    try:
        import cv2, numpy as np  # noqa: F401
        from insightface.app import FaceAnalysis
    except ImportError:
        sys.exit("pip install insightface onnxruntime-gpu opencv-python numpy")
    import contextlib, io, onnxruntime
    avail = onnxruntime.get_available_providers()
    use_gpu = "CUDAExecutionProvider" in avail
    sink = io.StringIO()
    with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
        a = FaceAnalysis(name="buffalo_l",
                         providers=["CUDAExecutionProvider", "CPUExecutionProvider"]
                         if use_gpu else ["CPUExecutionProvider"])
        a.prepare(ctx_id=0 if use_gpu else -1, det_size=(640, 640))
    real = a.models["recognition"].session.get_providers()[0]
    print(f"  device: {'GPU' if 'CUDA' in real else 'CPU'}"
          + ("" if "CUDA" in real else
             "  (onnxruntime-gpu needs a matching CUDA runtime; CPU is fine here)"))
    return a


def embed(app, path, want_size=False):
    """Returns the embedding, and optionally the face's pixel width.

    Face size matters: ArcFace works on a 112x112 aligned crop. A face 200px
    wide in frame gets upscaled to fill that, and the embedding is noisier for
    it. Full-body frames therefore score LOWER than head shots of the same
    person — which looks exactly like drift but is not.
    """
    import cv2, numpy as np
    img = cv2.imread(str(path))
    if img is None:
        return (None, 0) if want_size else None
    faces = app.get(img)
    if not faces:
        return (None, 0) if want_size else None
    f = max(faces, key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]))
    v = f.normed_embedding
    v = v / np.linalg.norm(v)
    return (v, int(f.bbox[2]-f.bbox[0])) if want_size else v


_APP_CACHE = [None]
_CANON_CACHE = [None]


def score_file(path):
    """One image -> (score, face_px), or None when no face is found.

    Exposed so other tools can ask "is this frame drifting?" without shelling
    out. Used by fix_face.py --below to repair only what actually needs it.
    """
    import numpy as np
    if _CANON_CACHE[0] is None:
        c = CANON
        if not c.exists():
            return None
        _CANON_CACHE[0] = np.load(c)
    if _APP_CACHE[0] is None:
        _APP_CACHE[0] = _app()
    e, px = embed(_APP_CACHE[0], path, want_size=True)
    if e is None:
        return None
    return float(np.dot(_CANON_CACHE[0], e)), px


def calibrate():
    import numpy as np
    if not MASTER.exists():
        sys.exit(f"no {MASTER} — run phase a first")
    app = _app()
    embs, names = [], []
    skipped = []
    for p in sorted(MASTER.glob("*.png")):
        if p.name not in CANON_FRAMES:
            skipped.append(p.name)
            continue
        e = embed(app, p)
        if e is None:
            print(f"  {p.name:<18} no face detected — cannot go in the centre")
            continue
        embs.append(e); names.append(p.name)
    if skipped:
        print(f"  not in the canonical: {', '.join(skipped)}")
        print("  (frontal frames only — see CANON_FRAMES)\n")
    if len(embs) < 2:
        sys.exit("need at least 2 frames with detectable faces")

    canon = np.mean(embs, axis=0); canon /= np.linalg.norm(canon)
    np.save(CANON, canon)

    print(f"\n  {'FRAME':<20}{'vs CANONICAL':>14}")
    print("  " + "-"*34)
    scores = []
    for n, e in zip(names, embs):
        s = float(np.dot(canon, e)); scores.append(s)
        print(f"  {n:<20}{s:>14.3f}")
    pair = [float(np.dot(a, b)) for a, b in itertools.combinations(embs, 2)]
    print(f"\n  stack agreement: mean {np.mean(pair):.3f}  worst pair "
          f"{np.min(pair):.3f}  ({len(embs)} frames)")
    print(f"  canonical saved -> {CANON.name}")

    worst = min(scores)
    if worst < 0.75:
        print(f"\n  ! The weakest frame scores {worst:.3f} against the stack's own")
        print("    centre. That frame is pulling the canonical away from her.")
        print("    Regenerate it, or delete it and recalibrate.")
    else:
        print(f"\n  Healthy. Set PASS just below the weakest frame ({worst:.3f}) —")
        print("    the stack itself defines what 'still her' means.")


def score(indir: pathlib.Path, move: bool):
    import numpy as np
    if not CANON.exists():
        sys.exit("no canonical.npy — run: python drift_gate.py --calibrate")
    canon = np.load(CANON)
    app = _app()
    files = sorted(p for p in indir.glob("*.png"))
    if not files:
        sys.exit(f"no PNGs in {indir}")
    buckets = {"pass": 0, "repair": 0, "reject": 0}
    small = []
    print(f"  {'FRAME':<28}{'SCORE':>8}{'FACE px':>9}   verdict")
    print("  " + "-"*56)
    for p in files:
        e, fw = embed(app, p, want_size=True)
        if e is None:
            print(f"  {p.name:<28}{'—':>8}{'—':>9}   no face, skipped"); continue
        s = float(np.dot(canon, e))
        pth, rth, band = thresholds(fw)
        b = "pass" if s >= pth else "repair" if s >= rth else "reject"
        note = f"  [{band} bar {pth:.2f}]" if band else ""
        if band:
            small.append(p.name)
        buckets[b] += 1
        print(f"  {p.name:<28}{s:>8.3f}{fw:>9}   {b}{note}")
        if move:
            d = indir / b; d.mkdir(exist_ok=True)
            shutil.move(str(p), d / p.name)
    print(f"\n  {buckets['pass']} pass · {buckets['repair']} repair · "
          f"{buckets['reject']} reject")
    print(f"  head shot  pass >= {PASS:.2f}   ·  half-body >= {PASS-0.03:.2f}"
          f"  ·  full-body >= {PASS-0.07:.2f}  ·  distant >= {PASS-0.11:.2f}")
    print(f"  reject <  {REPAIR}  delete. Do not 'fix in post', do not use it "
          f"because it is pretty.")
    if small:
        print(f"\n  {len(small)} frame(s) judged on a relaxed bar because the face "
              f"is small in\n  frame. That is framing, not drift — a full-body shot "
              f"scores 0.05-0.08\n  below a head shot of the same person purely "
              f"because ArcFace has fewer\n  pixels to work with.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--in", dest="indir", default=None,
                    help="folder to score. Omit to score every master/* folder.")
    ap.add_argument("--move", action="store_true",
                    help="sort files into pass/repair/reject subfolders")
    a = ap.parse_args()
    if a.calibrate:
        calibrate()
    elif a.indir:
        score(pathlib.Path(a.indir), a.move)
    else:
        # no folder given: score everything under master/ that is not the
        # reference stack itself
        dirs = sorted(d for d in (ROOT / "master").glob("*")
                      if d.is_dir() and any(d.glob("*.png")))
        if not dirs:
            sys.exit("nothing to score. Run a phase first, or pass --in <folder>.")
        for i, d in enumerate(dirs):
            print(f"\n{'='*60}\n  {d.relative_to(ROOT)}\n{'='*60}")
            score(d, a.move)
