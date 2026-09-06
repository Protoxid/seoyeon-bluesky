#!/usr/bin/env python3
import pathlib, subprocess, sys
import ffbin

ROOT = pathlib.Path(__file__).resolve().parent
src = ROOT / "clips" / "r4_fit_door.mp4"
dest = ROOT / "clips" / "r4_fit_check_final.mp4"

font_path = "C:/Windows/Fonts/segoeuib.ttf"
if not pathlib.Path(font_path).exists():
    font_path = "C:/Windows/Fonts/arialbd.ttf"
font_esc = font_path.replace("\\", "/").replace(":", "\\:")

draw = [
    # Beat 1: 0.2s to 2.1s
    f"drawtext=fontfile='{font_esc}':text='seoul in august is':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=150:box=1:boxcolor=black@0.55:boxborderw=16:enable='between(t,0.2,2.1)'",
    f"drawtext=fontfile='{font_esc}':text='not a joke':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=215:box=1:boxcolor=black@0.55:boxborderw=16:enable='between(t,0.2,2.1)'",
    # Beat 2: 2.3s to 4.2s
    f"drawtext=fontfile='{font_esc}':text='this is the third fit':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=150:box=1:boxcolor=black@0.55:boxborderw=16:enable='between(t,2.3,4.2)'",
    f"drawtext=fontfile='{font_esc}':text='and i am already late':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=215:box=1:boxcolor=black@0.55:boxborderw=16:enable='between(t,2.3,4.2)'",
    # Beat 3: 4.4s to 5.9s
    f"drawtext=fontfile='{font_esc}':text='we are going with it':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=180:box=1:boxcolor=black@0.55:boxborderw=18:enable='between(t,4.4,5.9)'",
]

vf = ",".join(draw)
cmd = [
    ffbin.require(), "-y", "-i", str(src),
    "-vf", vf,
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
    "-pix_fmt", "yuv420p", "-c:a", "copy",
    str(dest)
]

r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
if r.returncode:
    print("FFmpeg error:", r.stderr[-500:])
    sys.exit(1)

dur = ffbin.duration(dest)
sz = dest.stat().st_size // 1024
print(f"[OK] {dest.as_posix()}  {sz} KB  {dur:.2f}s")
