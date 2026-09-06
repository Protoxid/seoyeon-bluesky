#!/usr/bin/env python3
"""
build_reel_c_7am.py — Concept 2: "The 7am Studio Unlock". Full motion video. $0.

Narrative:
  Beat 1 (0.2 - 2.8s): "the 7am slot is the one\nnobody wants"
  Beat 2 (3.0 - 5.8s): "so it is the one they\ngive the trainee"
  Beat 3 (6.0 - 8.8s): "i have the whole room\nfor forty minutes"

Total duration: 9.0s
Format: 1080x1920 (9:16 vertical), 24 fps.
"""
import pathlib, subprocess, sys
import ffbin

ROOT = pathlib.Path(__file__).resolve().parent
src = ROOT / "clips" / "Handheld_camera_in_empty_studio_202608302130.mp4"
dest = ROOT / "clips" / "rC_studio_7am.mp4"

font_path = "C:/Windows/Fonts/segoeuib.ttf"
if not pathlib.Path(font_path).exists():
    font_path = "C:/Windows/Fonts/arialbd.ttf"
font_esc = font_path.replace("\\", "/").replace(":", "\\:")

draw = [
    # Beat 1: 0.2s to 2.8s
    f"drawtext=fontfile='{font_esc}':text='the 7am slot is the one':fontcolor=white:fontsize=56:x=(w-text_w)/2:y=240:box=1:boxcolor=black@0.55:boxborderw=20:enable='between(t,0.2,2.8)'",
    f"drawtext=fontfile='{font_esc}':text='nobody wants':fontcolor=white:fontsize=56:x=(w-text_w)/2:y=315:box=1:boxcolor=black@0.55:boxborderw=20:enable='between(t,0.2,2.8)'",
    # Beat 2: 3.0s to 5.8s
    f"drawtext=fontfile='{font_esc}':text='so it is the one they':fontcolor=white:fontsize=56:x=(w-text_w)/2:y=240:box=1:boxcolor=black@0.55:boxborderw=20:enable='between(t,3.0,5.8)'",
    f"drawtext=fontfile='{font_esc}':text='give the trainee':fontcolor=white:fontsize=56:x=(w-text_w)/2:y=315:box=1:boxcolor=black@0.55:boxborderw=20:enable='between(t,3.0,5.8)'",
    # Beat 3: 6.0s to 8.8s
    f"drawtext=fontfile='{font_esc}':text='i have the whole room':fontcolor=white:fontsize=56:x=(w-text_w)/2:y=240:box=1:boxcolor=black@0.55:boxborderw=20:enable='between(t,6.0,8.8)'",
    f"drawtext=fontfile='{font_esc}':text='for forty minutes':fontcolor=white:fontsize=56:x=(w-text_w)/2:y=315:box=1:boxcolor=black@0.55:boxborderw=20:enable='between(t,6.0,8.8)'",
]

vf = ",".join(draw)
cmd = [
    ffbin.require(), "-y", "-i", str(src),
    "-t", "9.0",
    "-vf", vf,
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
    str(dest)
]

r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
if r.returncode:
    print("FFmpeg error:", r.stderr[-500:])
    sys.exit(1)

dur = ffbin.duration(dest)
sz = dest.stat().st_size // 1024
print(f"[OK] {dest.as_posix()}  {sz} KB  {dur:.2f}s")
