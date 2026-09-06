#!/usr/bin/env python3
"""
build_r1.py — assemble the voiced R1: four clips, one continuous voice track.

    python build_r1.py --check      free: verifies every input and the timing
    python build_r1.py              -> clips/r1_voiced.mp4

THE VOICE IS ONE UNBROKEN TRACK, not four takes pinned to four clips. The first
version paired each take with its own clip and immediately hit the wall: the
hook take is 4.8s and clip 1 is 4.5s, so the line would have been cut off
mid-sentence and the only fixes were paying to regenerate the clip or cutting
words out of a sourced script.
Letting the audio run across the cuts is better than either, and free. A
voice-over does not have to respect an edit point — a line that carries over a
cut is what makes four clips read as one person talking rather than as four
clips. The only constraint left is that the whole voice track fits inside the
whole picture, which is a far easier thing to satisfy.

CAPTIONS ARE TIMED FROM THE REAL AUDIO. Each take's true duration sets where
its caption starts and ends, so nothing depends on a word-count estimate.

WHY NOT make_reel_text.py. That script carries one global BEATS list and it
holds the FIT CHECK's captions. Pointed here it would silently burn "seoul in
august is not a joke" over a pilates tutorial — an error that publishes rather
than one that raises.
"""
from __future__ import annotations
import argparse, pathlib, shutil, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import ffbin                                           # noqa: E402

W, H, FPS = 1080, 1920, 30
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
WIN_FONT = "C:/Windows/Fonts/segoeuib.ttf"
MAX_LINE = 30
GAP = 0.28              # breath between takes

# FOUR SLOTS, THREE CLIPS, AND c1 COMES BACK AT THE END. Three clips is 23.5s
# against 26.8s of voice — 3.3s short — and the cheapest thing that covers it
# is also the thing the reel needed anyway.
#
# As specced she was on screen for 4.5s of 28: the rest was an empty room, and
# that is a reel any of a thousand real instructors could have made. The one
# advantage this account has is HER. Returning to her face under the closing
# "7am tue + thu" line takes her to ~9s of 28 and puts a person behind the
# offer, which is the moment anybody actually taps through to a profile.
#
# Reusing a shot is normally the mark of a thin account. It is not, when the
# shot is the presenter and the structure is open-on-her, cut away, come back:
# that is how a piece to camera is cut.
CLIPS = ["clips/r1_c1_hook_raw.mp4",
         "clips/r1_c2_springs_raw.mp4",
         "clips/Handheld_camera_in_empty_studio_202608302130.mp4",
         "clips/r1_c1_hook_raw.mp4"]

# (take, caption). The spoken line carries the detail; the burn-in is the
# headline, so a muted viewer still gets the tip.
TAKES = [
    ("voice/hook.mp3", "3 things before your\nfirst reformer class"),
    ("voice/tip1.mp3", "fewer springs is\nHARDER, not easier"),
    ("voice/tip2.mp3", "if the carriage bangs\nyou're going too fast"),
    ("voice/tip3.mp3", "grip socks aren't\noptional"),
]
TAIL = "7am tue + thu, seongsu"


def font() -> str:
    for f in (FONT, WIN_FONT):
        if pathlib.Path(f).exists():
            return f
    sys.exit("no font found — set FONT at the top of this file")


def draw(text, start, end, tmp, tag, y=0.115) -> str:
    tf = tmp / f"{tag}.txt"
    tf.write_text(text + "\n", encoding="utf-8")
    return (f"drawtext=fontfile='{ffbin.filter_path(font())}'"
            f":textfile='{ffbin.filter_path(tf)}'"
            f":fontcolor=white:fontsize=50:line_spacing=16"
            f":x=(w-text_w)/2:y=h*{y}"
            f":box=1:boxcolor=black@0.5:boxborderw=24"
            f":enable='between(t,{start:.2f},{end:.2f})'")


def speech_blocks(path, thresh="-32dB", minsil=0.55):
    """Where the talking is, found rather than assumed.

    A single continuous take has no take boundaries to read durations from, so
    the caption timings have to come from the audio itself. ffmpeg's
    silencedetect gives the pauses; the speech is what is between them.
    `minsil` is deliberately long: short pauses are commas, and only the long
    ones are the gaps between the four lines.
    """
    import re as _re
    q = subprocess.run([ffbin.require(), "-i", str(path), "-af",
                        f"silencedetect=noise={thresh}:d={minsil}",
                        "-f", "null", "-"], capture_output=True, text=True)
    st = [float(x) for x in _re.findall(r"silence_start: ([0-9.]+)", q.stderr)]
    en = [float(x) for x in _re.findall(r"silence_end: ([0-9.]+)", q.stderr)]
    total = ffbin.duration(path)
    marks, cur = [], 0.0
    for a_, b_ in zip(st, en):
        if a_ > cur + 0.05:
            marks.append((cur, a_))
        cur = b_
    if total - cur > 0.05:
        marks.append((cur, total))
    return marks


def survey():
    vids = [(c, ffbin.duration(ROOT / c) if (ROOT / c).is_file() else 0.0)
            for c in CLIPS]
    auds = [(t, ffbin.duration(ROOT / t) if (ROOT / t).is_file() else 0.0, cap)
            for t, cap in TAKES]
    return vids, auds


def silent(out_path: str) -> int:
    """The same reel with captions and NO voice.

    Not a downgrade of the voiced build — a different, legitimate format, and
    the one most teaching reels on the platform actually use. It also uses the
    footage that has already been paid for, which the slideshow does not.
    THIS IS NOT THE SLIDESHOW. `r1_five_things.mp4` is two stills with a
    zoompan push; this is real generated video with the captions carrying the
    words the voice was going to.

    Captions are spread across the clips by READING TIME rather than evenly:
    with nothing spoken, the only thing setting the pace is how long a line
    takes to read, and a three-line card needs longer than a two-line one.
    """
    vids = [(c, ffbin.duration(ROOT / c)) for c in CLIPS
            if (ROOT / c).is_file()]
    # the bookend exists to cover the voice; with no voice it is just a repeat
    seen, uniq = set(), []
    for c, d in vids:
        if c not in seen:
            seen.add(c)
            uniq.append((c, d))
    vtot = sum(d for _c, d in uniq)
    caps = [c for _t, c in TAKES]
    weights = [len(c) for c in caps]
    span = vtot - 0.6
    marks, at = [], 0.3
    for w in weights:
        d = span * w / sum(weights)
        marks.append((at, at + d - 0.25))
        at += d
    for c, d in uniq:
        print(f"  clip   {pathlib.Path(c).name:<46} {d:5.1f}s")
    print(f"  total  {vtot:.1f}s, no audio\n")
    for i, (s0, e0) in enumerate(marks):
        if e0 - s0 < 2.0:
            print(f"  ! caption {i + 1} gets only {e0 - s0:.1f}s — too fast "
                  f"to read")
            return 1
    tmp = ROOT / "_r1stmp"
    tmp.mkdir(exist_ok=True)
    try:
        lst = tmp / "v.txt"
        lst.write_text("".join(f"file '{(ROOT / c).as_posix()}'\n"
                               for c, _d in uniq), encoding="utf-8")
        filters = [draw(cap, s0, e0, tmp, f"s{i}")
                   for i, ((s0, e0), cap) in enumerate(zip(marks, caps))]
        out = ROOT / out_path
        out.parent.mkdir(parents=True, exist_ok=True)
        r = subprocess.run(
            [ffbin.require(), "-y", "-v", "error", "-f", "concat", "-safe",
             "0", "-i", str(lst), "-an", "-vf",
             f"scale={W}:{H}:force_original_aspect_ratio=increase,"
             f"crop={W}:{H},fps={FPS}," + ",".join(filters),
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
             "-pix_fmt", "yuv420p", str(out)], capture_output=True, text=True)
        if r.returncode:
            print("  ! ffmpeg:", r.stderr[-400:])
            return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    got = ffbin.duration(out)
    print(f"  {out_path}  {out.stat().st_size // 1024} KB  {got:.2f}s")
    for i, ((s0, e0), cap) in enumerate(zip(marks, caps), 1):
        print(f"    caption {i}  {s0:5.1f}s - {e0:5.1f}s  "
              f"{cap.replace(chr(10), ' / ')}")
    print("\n  NO AUDIO TRACK. Add music in Instagram — a silent reel is")
    print("  penalised, and with no voice the music is doing real work here.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="clips/r1_voiced.mp4")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--no-voice", action="store_true",
                    help="captions over the clips, no voice track")
    a = ap.parse_args()

    if a.no_voice:
        return silent(a.out.replace("r1_voiced", "r1_text"))


    vids, auds = survey()
    bad = 0
    for c, d in vids:
        print(f"  clip   {pathlib.Path(c).name:<26} {d:5.1f}s"
              + ("" if d else "   MISSING"))
        bad += 0 if d else 1
    for t, d, cap in auds:
        print(f"  voice  {pathlib.Path(t).name:<26} {d:5.1f}s"
              + ("" if d else "   MISSING"))
        bad += 0 if d else 1
        for line in cap.split("\n"):
            if len(line) > MAX_LINE:
                print(f"  ! caption line {len(line)} chars, over {MAX_LINE}: "
                      f"{line!r}")
                bad += 1

    vtot = sum(d for _c, d in vids)
    atot = sum(d for _t, d, _c in auds) + GAP * (len(auds) - 1)
    print(f"\n  picture {vtot:5.1f}s\n  voice   {atot:5.1f}s"
          f"   ({GAP}s between takes)")
    # The ONLY timing constraint left, and it is a whole-reel one.
    if vtot and atot > vtot - 0.2:
        print(f"  ! the voice does not fit inside the picture. Lengthen a "
              f"clip, or drop GAP.")
        bad += 1
    if bad:
        print(f"\n  {bad} problem(s) — nothing built")
        return 1
    if a.check:
        print("\n  all inputs present and the voice fits — nothing built")
        return 0

    tmp = ROOT / "_r1btmp"
    tmp.mkdir(exist_ok=True)
    try:
        # 1. the picture, concatenated and normalised to 9:16
        vl = tmp / "v.txt"
        vl.write_text("".join(f"file '{(ROOT / c).as_posix()}'\n"
                              for c, _d in vids), encoding="utf-8")
        vcat = tmp / "video.mp4"
        r = subprocess.run(
            [ffbin.require(), "-y", "-v", "error", "-f", "concat", "-safe",
             "0", "-i", str(vl), "-an", "-vf",
             f"scale={W}:{H}:force_original_aspect_ratio=increase,"
             f"crop={W}:{H},fps={FPS}",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
             "-pix_fmt", "yuv420p", str(vcat)], capture_output=True, text=True)
        if r.returncode:
            print("  ! video concat:", r.stderr[-400:])
            return 1

        # 2. the voice, one track, each take delayed to its own start
        ins, chain, labels, at = [], [], [], 0.0
        marks = []
        for i, (t, d, cap) in enumerate(auds):
            ins += ["-i", str(ROOT / t)]
            chain.append(f"[{i}:a]adelay={int(at * 1000)}:all=1[a{i}]")
            labels.append(f"[a{i}]")
            marks.append((at, at + d, cap))
            at += d + GAP
        chain.append("".join(labels) +
                     f"amix=inputs={len(auds)}:normalize=0[a]")
        acat = tmp / "voice.m4a"
        r = subprocess.run(
            [ffbin.require(), "-y", "-v", "error", *ins, "-filter_complex",
             ";".join(chain), "-map", "[a]", "-c:a", "aac", "-b:a", "160k",
             "-ar", "44100", str(acat)], capture_output=True, text=True)
        if r.returncode:
            print("  ! voice build:", r.stderr[-400:])
            return 1

        # 3. THE REEL ENDS A BEAT AFTER THE LAST WORD, not when the picture
        #    runs out. Trailing silence is dead air that costs completion, and
        #    completion is the whole signal on a Trial Reel. `-shortest` was
        #    already doing this trim by accident — which quietly ate the
        #    closing caption, because it was positioned against the PICTURE
        #    length and landed past the end.
        end = min(vtot, atot + 0.9)
        filters = [draw(cap, s + 0.1, e - 0.05, tmp, f"c{i}")
                   for i, (s, e, cap) in enumerate(marks)]
        if end > 2.5:
            filters.append(draw(TAIL, end - 1.7, end - 0.15, tmp, "tail",
                                y=0.80))
        out = ROOT / a.out
        out.parent.mkdir(parents=True, exist_ok=True)
        r = subprocess.run(
            [ffbin.require(), "-y", "-v", "error", "-i", str(vcat),
             "-i", str(acat), "-vf", ",".join(filters),
             "-map", "0:v:0", "-map", "1:a:0", "-t", f"{end:.3f}",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
             "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", str(out)],
            capture_output=True, text=True)
        if r.returncode:
            print("  ! final mux:", r.stderr[-400:])
            return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    got = ffbin.duration(out)
    print(f"\n  {a.out}  {out.stat().st_size // 1024} KB  {got:.2f}s")
    for i, (s, e, cap) in enumerate(marks, 1):
        print(f"    caption {i}  {s:5.1f}s - {e:5.1f}s  "
              f"{cap.replace(chr(10), ' / ')}")
    print(f"    caption 5  {end - 1.7:5.1f}s - {end - 0.15:5.1f}s  {TAIL}")
    # compared against the INTENDED end, not the raw picture length
    if abs(got - end) > 0.4:
        print(f"  ! expected about {end:.1f}s — check before posting")
        return 1
    if vtot - end > 0.3:
        print(f"  note: {vtot - end:.1f}s of picture trimmed after the last "
              f"word")
    print("\n  Post as a TRIAL REEL. Music low or none: the voice is the point.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
