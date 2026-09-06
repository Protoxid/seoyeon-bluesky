#!/usr/bin/env python3
"""
bone_gate.py — identity by SKELETON, not by expression.

WHY THIS EXISTS. drift_gate scores ArcFace cosine against the canonical, and
that number moves when she squints, when her hair is up, when the light is
hard — none of which is identity. The operator's point: what does not change is
bone structure, so measure that.

WHAT IT MEASURES. Only VERTICAL proportions of the face, expressed as ratios of
each other. That choice is deliberate:
  * a ratio is SCALE-invariant, so face size in frame stops mattering
  * measured along the face's own axis (perpendicular to the eye line), so head
    ROLL cancels
  * vertical-over-vertical, so YAW barely touches it — turning your head
    compresses horizontal distance, not vertical
  * the skull sets these. Squinting does not move your nose down your face.

WHAT IT DOES NOT MEASURE. Anything horizontal (yaw destroys it), and anything
that depends on the mouth being closed. An open mouth drags the chin down and
the mouth line with it, so wide-open expressions are reported, not scored.

    python bone_gate.py --calibrate     # learn the ratios from master/a
    python bone_gate.py --in content/week

THIS IS UNTESTED. It has never been run — there is no GPU or insightface in the
environment it was written in. Calibrate first and read the spread before
trusting a single verdict from it.
"""
from __future__ import annotations
import argparse, json, pathlib, sys

ROOT = pathlib.Path(__file__).parent
MASTER = ROOT / "master" / "a"
STATS = ROOT / "bone_stats.json"
Z_FLAG = 2.5          # flag a ratio this many sigma off the master mean


def _app():
    import os, warnings, contextlib, io
    os.environ.setdefault("ORT_LOGGING_LEVEL", "3")
    warnings.filterwarnings("ignore")
    try:
        from insightface.app import FaceAnalysis
    except ImportError:
        sys.exit("pip install insightface onnxruntime-gpu opencv-python numpy")
    with contextlib.redirect_stdout(io.StringIO()):
        a = FaceAnalysis(name="buffalo_l")
        a.prepare(ctx_id=0, det_size=(640, 640))
    return a


def measure(app, path: pathlib.Path):
    """-> (ratios dict, note) or (None, why).

    Builds a face-local coordinate system from the eye line, then reads how far
    down the face the nose and mouth sit. Everything is relative to the
    eye->mouth distance, which is the most stable vertical span available.
    """
    import cv2, numpy as np
    img = cv2.imread(str(path))
    if img is None:
        return None, "unreadable"
    faces = app.get(img)
    if not faces:
        return None, "no face"
    f = max(faces, key=lambda x: (x.bbox[2] - x.bbox[0]) * (x.bbox[3] - x.bbox[1]))

    k = np.asarray(f.kps, dtype=float)      # 5 pts: Leye Reye nose Lmouth Rmouth
    leye, reye, nose, lmou, rmou = k
    eye_mid, mou_mid = (leye + reye) / 2.0, (lmou + rmou) / 2.0

    ex = reye - leye
    inter = float(np.linalg.norm(ex))
    if inter < 1e-6:
        return None, "degenerate eye line"
    ex /= inter
    ey = np.array([-ex[1], ex[0]])          # face-local "down", so ROLL cancels
    if float(np.dot(mou_mid - eye_mid, ey)) < 0:
        ey = -ey                            # keep +y pointing toward the mouth

    down = lambda p: float(np.dot(p - eye_mid, ey))
    eye_to_mouth = down(mou_mid)
    if eye_to_mouth <= 1e-6:
        return None, "degenerate face axis"

    # YAW PROXY. With the head turned, the nose tip slides off the eye midline.
    # This is not a measurement, it is a gate: past a point the geometry stops
    # being readable and the honest answer is "cannot say".
    across = lambda p: float(np.dot(p - eye_mid, ex))
    yaw = abs(across(nose)) / inter

    r = {
        # how far down the face the nose tip sits, as a fraction of eye->mouth
        "nose_drop": down(nose) / eye_to_mouth,
        # the eye->mouth span itself, against interocular width. Horizontal
        # component means yaw DOES affect this one — kept because it is
        # informative when yaw is low, and it is skipped when yaw is high.
        "face_len": eye_to_mouth / inter,
    }
    return r, f"yaw {yaw:.2f}"


def _yaw(note): return float(note.split()[1]) if note.startswith("yaw") else 9.0


# CALIBRATE ACROSS THE WHOLE STACK, not just master/a. With only the three
# frontal a-frames the sd came out 0.0099 on n=3 — statistically fragile, and
# Z_FLAG 2.5 against it is a band of +-0.025, tight enough to flag ordinary
# candid frames. A checker that cries wolf gets ignored.
# b7 (waist up) and the frontal c-frames are the same woman facing the camera.
# nose_drop is a RATIO, so it is scale-invariant — a smaller face in frame does
# not bias it, it only needs to be detectable.
CAL_DIRS = ["master/a", "master/b", "master/c"]


def calibrate(app):
    import numpy as np
    rows, skipped = [], []
    files = []
    for d in CAL_DIRS:
        dd = ROOT / d
        if dd.exists():
            files += sorted(dd.glob("*.png")) + sorted(dd.glob("*.jpg"))
    for p in files:
        r, note = measure(app, p)
        (rows.append((p.name, r, note)) if r else skipped.append((p.name, note)))
    if len(rows) < 3:
        sys.exit(f"only {len(rows)} usable master frames — cannot calibrate")
    print(f"  read {len(rows)} frame(s) from {', '.join(CAL_DIRS)}")

    # YAW GATE ON EVERYTHING, not just face_len. nose_drop was let through at
    # any pose on the theory that vertical-over-vertical survives rotation. It
    # does not survive NINETY DEGREES: the face-local axis is built from the
    # eye line, and in a full profile one eye is occluded and the mouth corners
    # are foreshortened, so the coordinate system itself stops meaning what it
    # means head-on.
    # The evidence: the two profile frames landed 3.1 sd APART from each other
    # (+1.7 and -1.4) while ArcFace scored them 0.746 and 0.756 — nearly
    # identical. Two mirror poses of one skull cannot be three sd apart. The
    # measurement was broken, not the frames.
    MAX_YAW = 0.35
    keys = ["nose_drop", "face_len"]
    stats = {}
    for kk in keys:
        lim = MAX_YAW if kk == "nose_drop" else 0.12
        vals = [r[kk] for _, r, n in rows if _yaw(n) < lim]
        if len(vals) < 3:
            print(f"  ! {kk}: only {len(vals)} frontal frames, skipping")
            continue
        stats[kk] = {"mean": float(np.mean(vals)), "std": float(np.std(vals)),
                     "n": len(vals)}
    STATS.write_text(json.dumps(stats, indent=2))
    print(f"\n  calibrated on {len(rows)} master frame(s)")
    for kk, st in stats.items():
        print(f"    {kk:<11} mean {st['mean']:.4f}  sd {st['std']:.4f}  n={st['n']}")

    # PER-FRAME, because an aggregate cannot tell you WHICH frame is the
    # outlier — and that is the only thing a calibration is ever asked.
    print(f"\n  {'frame':<24}{'nose_drop':>10}{'z':>7}{'face_len':>10}{'z':>7}   yaw")
    for name, r, note in rows:
        line = f"  {name:<24}"
        for kk in ("nose_drop", "face_len"):
            st = stats.get(kk)
            v = r.get(kk)
            if st is None or v is None:
                line += f"{'--':>10}{'':>7}"
            else:
                z = (v - st["mean"]) / (st["std"] or 1e-9)
                line += f"{v:>10.4f}{z:>+7.1f}"
        line += f"   {note.split()[1] if note.startswith('yaw') else '?'}"
        print(line)
    hi = [n for n, _, note in rows if _yaw(note) >= MAX_YAW]
    if hi:
        print(f"\n  EXCLUDED from the baseline (yaw >= {MAX_YAW}): "
              + ", ".join(hi))
        print("  Not because they are bad — because NEITHER GATE CAN MEASURE A")
        print("  PROFILE. Both are frontal instruments. Judge those frames by")
        print("  eye and keep them out of the numbers.")
    if skipped:
        print(f"  skipped: {', '.join(f'{n} ({w})' for n, w in skipped)}")
    n = stats.get("nose_drop", {}).get("n", 0)
    print("\n  READ THE SD BEFORE TRUSTING THIS. If it is large, the master")
    print("  stack itself is inconsistent and no threshold built on it means")
    print("  anything.")
    if n < 6:
        print(f"  ! n={n} is a small sample. An sd from a handful of frames is")
        print("    a fragile thing to threshold against — treat STRUCTURE as a")
        print("    reason to look, never as a verdict.")


def score(app, folder: pathlib.Path):
    if not STATS.exists():
        sys.exit("no bone_stats.json — run --calibrate first")
    st = json.loads(STATS.read_text())
    files = sorted(p for p in folder.iterdir()
                   if p.suffix.lower() in (".png", ".jpg", ".jpeg"))
    if not files:
        sys.exit(f"no images in {folder}")
    print(f"\n  {len(files)} image(s) against {STATS.name}\n")
    for p in files:
        r, note = measure(app, p)
        if not r:
            print(f"  {p.name:<44} --      {note}")
            continue
        y, bits, worst = _yaw(note), [], 0.0
        for kk, s in st.items():
            if kk == "face_len" and y >= 0.12:
                bits.append(f"{kk} skipped(yaw)"); continue
            z = (r[kk] - s["mean"]) / (s["std"] or 1e-9)
            worst = max(worst, abs(z))
            bits.append(f"{kk} {r[kk]:.3f} z{z:+.1f}")
        verdict = "ok" if worst < Z_FLAG else "STRUCTURE"
        print(f"  {p.name:<44} {verdict:<10} {'  '.join(bits)}")
    print(f"\n  'STRUCTURE' = a skeletal ratio is >{Z_FLAG} sd from the master.")
    print("  It is a REASON TO LOOK, not a verdict. Open-mouthed expressions")
    print("  drag the chin and can move these legitimately.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--in", dest="folder", default="content/week")
    a = ap.parse_args()
    app = _app()
    calibrate(app) if a.calibrate else score(app, ROOT / a.folder)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
