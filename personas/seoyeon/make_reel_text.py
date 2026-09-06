#!/usr/bin/env python3
"""
make_reel_text.py — burn timed text onto a video generated elsewhere.

For clips that come out of Google Flow. Flow makes the picture; this puts the
hook on it, at exact times, and checks the result rather than trusting it.

    python make_reel_text.py --video content\\reels\\r01_seven_am.mp4 --out clips\\r01_seven_am.mp4

Text beats live in BEATS below — edit them there, not on the command line, so
what was actually published is in a file rather than in a shell history.

Two things this enforces, both learned the expensive way:
  * ffmpeg drawtext DOES NOT WRAP. A long line is drawn off the edge of the
    frame and a clipped line still looks like a line. MAX_LINE raises rather
    than warns, so an over-long line cannot render at all.
  * textfile= instead of text=, so colons, apostrophes and newlines never have
    to survive two layers of escaping.
"""
from __future__ import annotations
import argparse, pathlib, subprocess, sys, tempfile
import ffbin  # resolves ffmpeg/ffprobe; see ffbin.py for why

ROOT = pathlib.Path(__file__).resolve().parent
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
WIN_FONT = "C:/Windows/Fonts/segoeuib.ttf"
MAX_LINE = 30

# (text, start, end). Newlines are the wrap; keep every line under MAX_LINE.
# THE FIT CHECK (6s). The pilates beats are parked below with the concept.
# Last cue ends at 5.9, not 6.0: H3 returns "about" the requested duration and
# a cue that ends after the last frame renders NOTHING, silently.
BEATS = [
    ("seoul in august is\nnot a joke",              0.2, 2.1),
    ("this is the third fit\nand i am already late", 2.3, 4.2),
    ("we are going with it",                        4.4, 5.9),
]

_PARKED_PILATES = [
    ("the 7am slot is the one\nnobody wants",        0.2, 3.0),
    ("so it is the one they\ngive the trainee",      3.2, 6.0),
    ("i have the whole room\nfor forty minutes",     6.2, 8.0),
]

# R3, the river. ONE CARD, ON THE FRONT. The spec says no text after the first
# frame and that is right for this one: the clip is the argument, and a caption
# sitting over the best three seconds of it is subtitling a view.
_RIVER = [
    ("seoul does this every evening\nand i still stop", 0.2, 3.2),
]

# BEATS IS A GLOBAL AND IT HOLDS THE FIT CHECK. Pointed at any other clip it
# silently burns "seoul in august is not a joke" over it — an error that
# publishes rather than one that raises. --set is the fix: naming the set is
# now a required act rather than a thing you have to remember not to forget.
SETS = {"fit": None, "pilates": _PARKED_PILATES, "river": _RIVER}


def font() -> str:
    for f in (FONT, WIN_FONT):
        if pathlib.Path(f).exists():
            return f
    sys.exit("no font found — set FONT at the top of this file")


def main() -> int:
    global BEATS
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--size", type=int, default=50)
    ap.add_argument("--y", type=float, default=0.125,
                    help="text top as a fraction of frame height")
    ap.add_argument("--fit", action="store_true",
                    help="rescale the cue times to the clip's real duration")
    ap.add_argument("--set", dest="cueset", default="fit",
                    choices=sorted(SETS),
                    help="which caption set to burn in (default: fit)")
    a = ap.parse_args()
    if SETS[a.cueset] is not None:
        BEATS = SETS[a.cueset]
    print(f"  caption set: {a.cueset}  ({len(BEATS)} card(s))")

    src = pathlib.Path(a.video)
    if not src.is_file():
        print(f"  ! {src} not found. Generate the clip first:\n"
              f"        python make_fit_clip.py          (Kie, $0.52)\n"
              f"    or in Google Flow for a no-face clip, which is free.")
        return 2

    for t, _s, _e in BEATS:
        for line in t.split("\n"):
            if len(line) > MAX_LINE:
                print(f"  ! line is {len(line)} chars, over {MAX_LINE}: "
                      f"{line!r}\n    ffmpeg will draw it off the frame. "
                      f"Wrap it in BEATS.")
                return 1

    dur = ffbin.duration(src)
    span = max(e for _t, _s, e in BEATS)
    if a.fit and dur > 0.1 and abs(span - dur) > 0.05:
        # Proportional, so the gaps between cards stay proportional too. The
        # last cue lands 0.1s before the end rather than exactly on it: a cue
        # that ends on the final frame renders nothing, which looks identical
        # to a cue that was never added.
        k = (dur - 0.1) / span
        BEATS = [(t, round(s0 * k, 2), round(e * k, 2)) for t, s0, e in BEATS]
        print(f"  --fit: cues rescaled {span:.2f}s -> {dur - 0.1:.2f}s "
              f"(x{k:.3f})")
    over = [t for t, _s, e in BEATS if e > dur + 0.05]
    if over:
        print(f"  ! the clip is {dur:.2f}s but a text cue ends after that. "
              f"Nothing is rendered — pass --fit, or fix BEATS.")
        return 1

    with tempfile.TemporaryDirectory() as tmpd_str:
        tmpd = pathlib.Path(tmpd_str)
        draw = []
        for j, (t, s, e) in enumerate(BEATS):
            tf = tmpd / f"t{j}.txt"
            tf.write_text(t + "\n", encoding="utf-8")
            draw.append(
                f"drawtext=fontfile='{ffbin.filter_path(font())}'"
                f":textfile='{ffbin.filter_path(tf)}'"
                f":fontcolor=white:fontsize={a.size}:line_spacing=16"
                f":x=(w-text_w)/2:y=h*{a.y}"
                f":box=1:boxcolor=black@0.45:boxborderw=24"
                f":enable='between(t,{s},{e})'")

        out = pathlib.Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        if not ffbin.has_audio(src):
            # Instagram requires an audio track on video uploads; provide silent stereo AAC if missing
            r = subprocess.run(
                [ffbin.require(), "-y", "-i", str(src), "-f", "lavfi", "-i",
                 "anullsrc=r=44100:cl=stereo", "-shortest",
                 "-vf", ",".join(draw), "-c:v", "libx264", "-preset", "veryfast",
                 "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac",
                 "-b:a", "128k", str(out)],
                capture_output=True, text=True, encoding="utf-8", errors="replace")
        else:
            r = subprocess.run(
                [ffbin.require(), "-y", "-i", str(src), "-vf", ",".join(draw),
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
                 "-pix_fmt", "yuv420p", "-c:a", "copy", str(out)],
                capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode:
            print("  ! ffmpeg:", r.stderr[-400:])
            return 1

    print(f"  in   {src.name}  {dur:.2f}s")
    print(f"  out  {a.out}  {out.stat().st_size // 1024} KB  "
          f"{ffbin.duration(out):.2f}s")
    print(f"  {len(BEATS)} text beats burned in")
    print("  Add music IN INSTAGRAM. Post as a TRIAL REEL first.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
