#!/usr/bin/env python3
"""
make_reel_r2.py — R2, "the washing machine". Funny. Free. No generation.

WHY THIS IS NOT THE SLIDESHOW AGAIN. The slideshow was eight pretty pictures
with no idea in them. This is a two-beat joke: a setup, a gap, a punchline. The
TEXT is the content and the images are the backdrop, which is the format that
actually works when you have one good frame and no footage.

Three things make it read as a reel rather than a carousel:
  1. TEXT ARRIVES IN BEATS, not all at once. Something changes every ~2s, so
     there is a reason to still be watching at second 5.
  2. A SLOW PUSH-IN under everything. Not decoration — a static frame with text
     on it looks like a screenshot, and a screenshot gets swiped past.
  3. A HARD CUT on the punchline. No fade. The gap between 9am and 9:30pm IS
     the joke, and a dissolve softens exactly the thing that should land.

Text is burned in rather than added in the app: it is the content, so it should
survive a repost, and the timing has to be exact. Music still goes on in
Instagram.

Built at 1080x1920 with a blurred fill, because the sources are 3:4 and
cropping to 9:16 would throw away a quarter of the width — which here is the
puddle and the machine door, i.e. the whole point of the frame.
"""
from __future__ import annotations
import argparse, pathlib, shutil, subprocess, sys
import ffbin  # resolves ffmpeg/ffprobe; see ffbin.py for why

ROOT = pathlib.Path(__file__).resolve().parent
W, H, FPS = 1080, 1920, 30
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# (source, seconds, [(text, start, end), ...])
# Beats are deliberately uneven: the setup gets room, the punchline lands fast.
# PRE-WRAPPED. At fontsize 50 on a 1080 frame a line runs out of room at about
# 30 characters, and ffmpeg does not wrap — it just draws off the edge. The
# first build lost "...since july" off the right-hand side and the check sheet
# nearly hid it, because a clipped line still looks like a line.
BEATS = [
    ("machine", 4.4, [
        ("it has been making\nthe noise since july", 0.15, 2.3),
        ("today it stopped\npretending",             2.45, 4.4),
    ]),
    ("laundry", 4.2, [
        ("so this is my\nwednesday night",           0.15, 2.4),
        ("half nine, and i am\nthe only one here",   2.55, 4.2),
    ]),
]
MAX_LINE = 30


def check_width(t: str) -> None:
    for line in t.split("\n"):
        if len(line) > MAX_LINE:
            raise ValueError(f"line is {len(line)} chars, over {MAX_LINE}: "
                             f"{line!r} — it will be drawn off the frame")


def clip(src: pathlib.Path, dest: pathlib.Path, dur: float,
         texts, zoom_from: float) -> None:
    frames = max(2, int(round(dur * FPS)))
    # zoompan emits `d` frames PER INPUT FRAME, so it takes ONE frame and
    # generates the duration itself. -loop would multiply it. See the playbook.
    motion = (f"zoompan=z='min({zoom_from}+0.05*on/{frames},{zoom_from}+0.05)'"
              f":d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
              f":s={W}x{H}:fps={FPS}")
    # textfile= instead of text=, so nothing has to survive two layers of
    # escaping. Colons, apostrophes and newlines all pass through untouched.
    draw = []
    for j, (t, a, b) in enumerate(texts):
        check_width(t)
        tf = dest.with_name(f"{dest.stem}_t{j}.txt")
        tf.write_text(t + "\n", encoding="utf-8")
        draw.append(
            f"drawtext=fontfile='{ffbin.filter_path(FONT)}'"
            f":textfile='{ffbin.filter_path(tf)}'"
            f":fontcolor=white:fontsize=50:line_spacing=16"
            f":x=(w-text_w)/2:y=h*0.125"
            f":box=1:boxcolor=black@0.45:boxborderw=24"
            f":enable='between(t,{a},{b})'")
    fc = (f"[0:v]scale={W}:-2[s];[s]split[a][b];"
          f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,"
          f"crop={W}:{H},gblur=sigma=34,eq=brightness=-0.12[bg];"
          f"[bg][b]overlay=(W-w)/2:(H-h)/2,{motion},"
          + ",".join(draw) + f",format=yuv420p,fps={FPS}[v]")
    cmd = [ffbin.require(), "-y", "-i", str(src), "-filter_complex", fc,
           "-map", "[v]", "-frames:v", str(frames),
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
           "-pix_fmt", "yuv420p", "-r", str(FPS), str(dest)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr[-500:])
    got = ffbin.duration(dest)
    if abs(got - dur) > 0.35:
        raise RuntimeError(f"{dest.name}: asked {dur:.2f}s, wrote {got:.2f}s")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--machine", required=True)
    ap.add_argument("--laundry", required=True)
    ap.add_argument("--out", default="clips/r2_washing_machine.mp4")
    a = ap.parse_args()
    srcs = {"machine": pathlib.Path(a.machine), "laundry": pathlib.Path(a.laundry)}
    for k, v in srcs.items():
        if not v.is_file():
            print(f"  ! {k}: {v} not found")
            return 2

    tmp = ROOT / "_r2tmp"
    tmp.mkdir(exist_ok=True)
    parts = []
    for i, (key, dur, texts) in enumerate(BEATS):
        d = tmp / f"{i}.mp4"
        # second half starts slightly wider so the cut has a visible jump
        clip(srcs[key], d, dur, texts, 1.0 if i == 0 else 1.02)
        parts.append(d)
        print(f"  beat {i+1}  {key:<8}{dur:.1f}s  {len(texts)} text cues")

    lst = tmp / "list.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts),
                   encoding="utf-8")
    out = ROOT / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        [ffbin.require(), "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
         "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", str(out)],
        capture_output=True, text=True)
    if r.returncode:
        print("  ! concat failed:", r.stderr[-400:])
        return 1
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n  {a.out}  {out.stat().st_size // 1024} KB  "
          f"{ffbin.duration(out):.2f}s")
    print("  Add music IN INSTAGRAM. Post as a TRIAL REEL first.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
