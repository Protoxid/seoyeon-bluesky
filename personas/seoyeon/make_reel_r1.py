#!/usr/bin/env python3
"""
make_reel_r1.py — R1, the TEACHES reel. "5 things nobody tells you." $0.

    python make_reel_r1.py --check                 free, verifies beats only
    python make_reel_r1.py                         builds from the three stills
    python make_reel_r1.py --video flow_clip.mp4   builds over a Flow clip

WHY THE ORIGINAL R1 WAS SCRAPPED. It was three anatomy claims, and I had
written all three from my own head:

  * "your hip flexors are not tight, they are short from sitting" — the
    shortening-from-sitting claim is REPEATED EVERYWHERE AND SUPPORTED BY
    NOTHING. The one study that looks like support (Berlin et al. 2020) is
    cross-sectional and measures limited hip EXTENSION, which is a range of
    motion, not a muscle length, and an association, not a cause.
  * "stop tucking your pelvis, neutral is not flat" — imprinting versus
    neutral is a live disagreement BETWEEN PILATES SCHOOLS. STOTT teaches both
    placements as valid. Taking a side in a thirteen-second reel picks a fight
    with half the profession, from an account with no followers.
  * "you will not feel it in your abs for about three weeks" — I made the
    number up.

A TEACHING REEL PUTS CLAIMS IN HER MOUTH AS A PROFESSIONAL. In a niche full of
actual instructors, one wrong claim in the comments costs more than the reel
earns. So the content moved from PHYSIOLOGY, which I cannot verify to the
standard this needs, to PROCEDURE — what actually happens at a first class.
Every line below is attributable, and the authority comes from insider
knowledge rather than from an anatomical assertion.

  1  fewer springs is often harder      bodymindlife.com/post/reformer-pilates-mistakes-beginners-make
  2  grip socks required                weareformfitness.com/training/reformer/first-class
                                        blog.clubpilates.com/reformer-pilates-beginners-guide
  3  ten minutes early is not padding   weareformfitness.com/training/reformer/first-class
  4  where the soreness lands           weareformfitness.com/training/reformer/soreness
  5  more mental than physical          weareformfitness.com/training/reformer/first-class

THE IMAGES ARGUE WITH THE TEXT, they do not merely accompany it. Empty studio
under the hook, the CHANGING ROOM under the socks-and-arrive-early tips because
that is literally where those happen, and her face after class under the
soreness and the payoff. That is what separates this from the slideshow: the
slideshow was eight pictures in chronological order with no idea; here the text
is the spine and each image is chosen to sit under its own line.
"""
from __future__ import annotations
import argparse, pathlib, shutil, subprocess, sys
import ffbin  # resolves ffmpeg/ffprobe; see ffbin.py for why

ROOT = pathlib.Path(__file__).resolve().parent
W, H, FPS = 1080, 1920, 30
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
WIN_FONT = "C:/Windows/Fonts/segoeuib.ttf"
MAX_LINE = 30

# Default sources. EXPLICIT PATHS, NOT A GLOB: content/week2 holds two
# w2_studio_mirror variants and only one of them was approved. A glob would
# quietly pick the last one sorted and animate a frame nobody looked at.
# Sources. EXPLICIT PATHS, NOT A GLOB: content/week2 holds two
# w2_studio_mirror variants and only one of them was approved. A glob picks the
# last one sorted, and that is how you animate a frame nobody looked at.
#
# locations/studio.png IS NOT THE STUDIO. It is a domestic living room with one
# reformer in it — rug, framed print, radiator, curtains. It was segment one
# until the QC frames were actually opened, and an establishing shot of a HOME
# under the words "5 things i tell every first-timer" destroys the authority
# the whole reel is built to earn. The real studio — reformers, mirrored wall,
# another woman by the door — is the background of w2_class_two.
# THE PLATE AND THE STILLS SHOW DIFFERENT STUDIOS, which is a live continuity
# fault beyond this reel: pov.pov_studio_open resolves plate_studio to that
# same living room, so the free POV clip would render a flat, not a studio.
SOURCES = {
    "after":    "content/week2/w2_class_two_e9302f_1.png",
    "changing": "content/week2/w2_studio_mirror_1b34a6_1.png",
}

# (source key, seconds, [(text, start, end) relative to the segment])
# THREE TIPS, NOT FIVE. Nineteen seconds of stills with text on them is a long
# time to hold someone who has never heard of her, and completion is the lever
# that matters on a Trial Reel. The original plan was right about the length
# and wrong about the content; this keeps the length and replaces the content.
# Tips 4 and 5 (where the soreness lands, and that it is more mental than
# physical) are sourced and unused — they are the next teaching reel, free.
#
# It OPENS ON HER FACE. An empty room gives nobody a reason to stop scrolling.
# The last segment returns to the same frame pushed tighter, so the offer lands
# as a bookend rather than a third unrelated picture.
SEGMENTS = [
    ("after", 5.6, [
        ("3 things i tell every\nfirst-timer in reformer",         0.15, 2.5),
        ("1. fewer springs is often\nharder. less spring means\nless help holding the carriage",
                                                                   2.7,  5.6),
    ]),
    ("changing", 5.6, [
        ("2. grip socks are required\nat most studios. bring them", 0.1,  2.7),
        ("3. come ten minutes early.\nthat is when you are shown\nthe machine",
                                                                   2.9,  5.6),
    ]),
    ("after", 1.8, [
        ("7am tue + thu, seongsu",                                 0.1,  1.8),
    ]),
]

# Segment 3 reuses segment 1's frame, so it starts noticeably tighter —
# otherwise the cut back looks like a mistake rather than a bookend.
ZOOM = [1.00, 1.02, 1.10]


def font() -> str:
    for f in (FONT, WIN_FONT):
        if pathlib.Path(f).exists():
            return f
    sys.exit("no font found — set FONT at the top of this file")


def check_beats() -> int:
    """Every guard runs BEFORE anything is rendered.

    ffmpeg drawtext does not wrap: an over-long line is drawn off the edge of
    the frame and a clipped line still looks like a line. This raises rather
    than warns, and it runs first, because the last time a check ran late the
    check sheet nearly hid the fault.
    """
    bad = 0
    total = 0.0
    for key, dur, texts in SEGMENTS:
        for t, s, e in texts:
            for line in t.split("\n"):
                if len(line) > MAX_LINE:
                    print(f"  ! {len(line)} chars, over {MAX_LINE}: {line!r}")
                    bad += 1
            if e > dur + 0.001:
                print(f"  ! [{key}] a cue ends at {e}s but the segment is "
                      f"{dur}s — it would render NOTHING")
                bad += 1
            if s >= e:
                print(f"  ! [{key}] cue starts at {s} and ends at {e}")
                bad += 1
        total += dur
    n = sum(len(t) for _, _, t in SEGMENTS)
    print(f"  {len(SEGMENTS)} segments, {n} text cards, {total:.1f}s total")
    if bad:
        print(f"  {bad} problem(s) — nothing built")
    return bad


def draw_filters(texts, tmpd, tag):
    # textfile= instead of text=, so colons, apostrophes and newlines never
    # have to survive two layers of shell and filter escaping.
    out = []
    for j, (t, s, e) in enumerate(texts):
        tf = tmpd / f"{tag}_{j}.txt"
        tf.write_text(t + "\n", encoding="utf-8")
        out.append(
            f"drawtext=fontfile='{ffbin.filter_path(font())}'"
            f":textfile='{ffbin.filter_path(tf)}'"
            f":fontcolor=white:fontsize=50:line_spacing=16"
            f":x=(w-text_w)/2:y=h*0.115"
            f":box=1:boxcolor=black@0.5:boxborderw=24"
            f":enable='between(t,{s},{e})'")
    return out


def segment(src: pathlib.Path, dest: pathlib.Path, dur: float, texts,
            zoom_from: float, tmpd: pathlib.Path, tag: str) -> None:
    frames = max(2, int(round(dur * FPS)))
    # zoompan emits `d` frames PER INPUT FRAME — it takes one still and
    # generates the whole duration itself. -loop would multiply it, which is
    # how an 8.8s request once wrote a 246s file.
    motion = (f"zoompan=z='min({zoom_from}+0.05*on/{frames},{zoom_from}+0.05)'"
              f":d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
              f":s={W}x{H}:fps={FPS}")
    fc = (f"[0:v]scale={W}:-2[s];[s]split[a][b];"
          f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,"
          f"crop={W}:{H},gblur=sigma=34,eq=brightness=-0.12[bg];"
          f"[bg][b]overlay=(W-w)/2:(H-h)/2,{motion},"
          + ",".join(draw_filters(texts, tmpd, tag))
          + f",format=yuv420p,fps={FPS}[v]")
    r = subprocess.run(
        [ffbin.require(), "-y", "-i", str(src), "-filter_complex", fc,
         "-map", "[v]", "-frames:v", str(frames),
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
         "-pix_fmt", "yuv420p", "-r", str(FPS), str(dest)],
        capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr[-500:])
    got = probe(dest)
    # VERIFY THE ARTEFACT, NOT THE EXIT CODE.
    if abs(got - dur) > 0.35:
        raise RuntimeError(f"{dest.name}: asked {dur:.2f}s, wrote {got:.2f}s")


def probe(p: pathlib.Path) -> float:
    return ffbin.duration(p)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", help="a clip from Flow to burn the text over "
                                    "instead of building from stills")
    ap.add_argument("--out", default="clips/r1_five_things.mp4")
    ap.add_argument("--check", action="store_true",
                    help="verify the beats and stop")
    a = ap.parse_args()

    if check_beats():
        return 1
    if a.check:
        print("  beats OK — nothing built")
        return 0

    out = ROOT / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = ROOT / "_r1tmp"
    tmp.mkdir(exist_ok=True)

    try:
        if a.video:
            # THE FLOW PATH. Same beats, laid end to end over one clip.
            src = pathlib.Path(a.video)
            if not src.is_file():
                print(f"  ! {src} not found")
                return 2
            dur = probe(src)
            flat, off = [], 0.0
            for _k, d, texts in SEGMENTS:
                flat += [(t, s + off, e + off) for t, s, e in texts]
                off += d
            if off > dur + 0.05:
                print(f"  ! the clip is {dur:.2f}s but the beats need "
                      f"{off:.2f}s. Nothing would render past the end.")
                return 1
            r = subprocess.run(
                [ffbin.require(), "-y", "-i", str(src), "-vf",
                 ",".join(draw_filters(flat, tmp, "flow")),
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
                 "-pix_fmt", "yuv420p", "-c:a", "copy", str(out)],
                capture_output=True, text=True)
            if r.returncode:      # a Flow clip may carry no audio track
                r = subprocess.run(
                    [ffbin.require(), "-y", "-i", str(src), "-f", "lavfi", "-i",
                     "anullsrc=r=44100:cl=stereo", "-shortest", "-vf",
                     ",".join(draw_filters(flat, tmp, "flow")),
                     "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
                     "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
                     str(out)], capture_output=True, text=True)
                if r.returncode:
                    print("  ! ffmpeg:", r.stderr[-400:])
                    return 1
        else:
            parts = []
            for i, (key, dur, texts) in enumerate(SEGMENTS):
                src = ROOT / SOURCES[key]
                if not src.is_file():
                    print(f"  ! {key}: {SOURCES[key]} not found")
                    return 2
                d = tmp / f"{i}.mp4"
                segment(src, d, dur, texts, ZOOM[i], tmp, str(i))
                parts.append(d)
                print(f"  seg {i+1}  {key:<9}{dur:.1f}s  "
                      f"{len(texts)} cards  <- {src.name}")
            lst = tmp / "list.txt"
            lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts),
                           encoding="utf-8")
            r = subprocess.run(
                [ffbin.require(), "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                 "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                 "-shortest", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
                 str(out)], capture_output=True, text=True)
            if r.returncode:
                print("  ! concat failed:", r.stderr[-400:])
                return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    want = sum(d for _k, d, _t in SEGMENTS)
    got = probe(out)
    print(f"\n  {a.out}  {out.stat().st_size // 1024} KB  {got:.2f}s")
    if abs(got - want) > 0.5:
        print(f"  ! expected {want:.1f}s — check before posting")
        return 1
    print("  Add music IN INSTAGRAM. Post as a TRIAL REEL first.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
