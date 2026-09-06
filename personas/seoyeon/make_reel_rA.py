#!/usr/bin/env python3
"""
make_reel_rA.py — Reel A: "7am me vs 11pm me". Contrast humor. $0. No generation.

    python make_reel_rA.py

WHY THIS WORKS AT ZERO FOLLOWERS:
  * Two approved master stills in 1080x1920: zero AI floatiness, zero skin artifacts.
  * 6.0 seconds total: loops fast, maximizing completion rate and loop count.
  * Universal contrast joke: high send rate (DMs), which is Instagram's #1 reach lever.
  * Timed text burned into top safe zone (y=h*0.125), avoiding Instagram UI overlay.
"""
from __future__ import annotations
import argparse, pathlib, subprocess, sys
import ffbin

ROOT = pathlib.Path(__file__).resolve().parent
W, H, FPS = 1080, 1920, 30

WIN_FONT = "C:/Windows/Fonts/segoeuib.ttf"
LINUX_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def get_font() -> str:
    for f in (WIN_FONT, LINUX_FONT, "C:/Windows/Fonts/arialbd.ttf"):
        if pathlib.Path(f).exists():
            return f
    return "Arial"

BEATS = [
    ("studio", 3.0, [
        ("7am me, who signed up\nfor this", 0.15, 2.95),
    ]),
    ("conv", 3.0, [
        ("11pm me, who is now\nbuying two dinners", 0.15, 2.95),
    ]),
]
MAX_LINE = 30

def check_width(t: str) -> None:
    for line in t.split("\n"):
        if len(line) > MAX_LINE:
            raise ValueError(f"line is {len(line)} chars, over {MAX_LINE}: {line!r}")

def clip(src: pathlib.Path, dest: pathlib.Path, dur: float, texts, zoom_from: float) -> None:
    frames = max(2, int(round(dur * FPS)))
    motion = (f"zoompan=z='min({zoom_from}+0.04*on/{frames},{zoom_from}+0.04)'"
              f":d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
              f":s={W}x{H}:fps={FPS}")
    font_path = get_font()
    draw = []
    for j, (t, a, b) in enumerate(texts):
        check_width(t)
        tf = dest.with_name(f"{dest.stem}_t{j}.txt")
        tf.write_text(t + "\n", encoding="utf-8")
        # Format paths for ffmpeg filter graph
        font_esc = font_path.replace("\\", "/").replace(":", "\\:")
        tf_esc = str(tf).replace("\\", "/").replace(":", "\\:")
        draw.append(
            f"drawtext=fontfile='{font_esc}'"
            f":textfile='{tf_esc}'"
            f":fontcolor=white:fontsize=52:line_spacing=18"
            f":x=(w-text_w)/2:y=h*0.14"
            f":box=1:boxcolor=black@0.45:boxborderw=24"
            f":enable='between(t,{a},{b})'"
        )
    fc = (f"[0:v]scale={W}:-2[s];[s]split[a][b];"
          f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,"
          f"crop={W}:{H},gblur=sigma=34,eq=brightness=-0.12[bg];"
          f"[bg][b]overlay=(W-w)/2:(H-h)/2,{motion},"
          + ",".join(draw) + f",format=yuv420p,fps={FPS}[v]")
    cmd = [ffbin.require(), "-y", "-i", str(src), "-filter_complex", fc,
           "-map", "[v]", "-frames:v", str(frames),
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
           "-pix_fmt", "yuv420p", "-r", str(FPS), str(dest)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        raise RuntimeError(r.stderr[-500:])
    got = ffbin.duration(dest)
    if abs(got - dur) > 0.35:
        raise RuntimeError(f"{dest.name}: asked {dur:.2f}s, wrote {got:.2f}s")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="clips/rA_7am_11pm.mp4")
    a = ap.parse_args()

    srcs = {
        "studio": ROOT / "content/grid/n_studio_taught_5e9f18_1.png",
        "conv": ROOT / "content/grid/n_conv_yawn_b3fa75_1.png",
    }
    for k, v in srcs.items():
        if not v.is_file():
            print(f"  ! {k}: {v} not found")
            return 2

    tmp = ROOT / "_rAtmp"
    tmp.mkdir(exist_ok=True)
    parts = []
    for i, (key, dur, texts) in enumerate(BEATS):
        d = tmp / f"{i}.mp4"
        clip(srcs[key], d, dur, texts, 1.0 if i == 0 else 1.02)
        parts.append(d)
        print(f"  beat {i+1}  {key:<8} {dur:.1f}s  text: {texts[0][0].replace(chr(10), ' ')}")

    lst = tmp / "list.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
    out = ROOT / a.out
    out.parent.mkdir(parents=True, exist_ok=True)

    cmd = [ffbin.require(), "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
           "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
           "-shortest", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
           str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        raise RuntimeError(r.stderr[-500:])

    # Clean tmp
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)

    dur = ffbin.duration(out)
    sz = out.stat().st_size // 1024
    print(f"\n  [OK] {out.as_posix()}  {sz} KB  {dur:.1f}s")
    print("  Ready to publish to Instagram Reels. Attach trending audio in-app.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
