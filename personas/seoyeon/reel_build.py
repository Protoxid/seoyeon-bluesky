#!/usr/bin/env python3
"""
reel_build.py — a photo-dump Reel from stills we already have. No generation.

    python reel_build.py --from-posts            # everything marked posted
    python reel_build.py a.png b.png c.png
    python reel_build.py --from-posts --static   # hard cuts, no push-in

WHY THIS EXISTS. The generated Reel read as AI, and the mechanism is not a bad
roll. First-frame-to-last-frame is not motion, it is INTERPOLATION: two fixed
endpoints force the model to find a path between them and land exactly on the
second, so it eases in and eases out, and that easing is the floatiness. On top
of that a video model re-renders skin on every frame, so its own prior
reasserts and the matte skin of the source still does not survive -- the same
mechanism as the facial highlight in the stills, which took four rounds to
find.

A photo-dump Reel has no generated motion, so it cannot have AI-motion tells.
It costs nothing, it uses frames that have already passed QC, and it is a
format real accounts post constantly. Until there is income, this is the
correct default and generated video is the exception that has to justify
itself.

FORMAT DECISIONS, and the reasons:
  * 1080x1920. Not because the stills are 9:16 -- they are 3:4 -- but because
    that is the Reel frame. The still is fitted by WIDTH and the band above and
    below is a blurred, darkened copy of the same image. Cropping 3:4 to 9:16
    would throw away a quarter of the width, which is where the room is, and
    the room is what makes these read as photographs of a life.
  * The push-in is 4% over the whole clip and it is optional. More than that
    reads as a slideshow template. --static turns it off entirely; hard cuts
    are just as normal in this format.
  * ~1.1s per still. Photo dumps are FAST. Held frames read as a slideshow.
  * A SILENT AUDIO TRACK is muxed in. Instagram handles a video with no audio
    stream inconsistently, and music should be added in the app anyway -- a
    Creator account keeps the full music catalogue, and in-app audio is a
    discovery signal that an embedded mp3 is not.

Needs ffmpeg on PATH. If it is missing:  winget install Gyan.FFmpeg
"""
from __future__ import annotations
import argparse, json, pathlib, shutil, subprocess, sys
import ffbin  # resolves ffmpeg/ffprobe; see ffbin.py for why

ROOT = pathlib.Path(__file__).resolve().parent
W, H, FPS = 1080, 1920, 30


def have_ffmpeg() -> bool:
    return bool(shutil.which("ffmpeg"))


def clip(src: pathlib.Path, dest: pathlib.Path, dur: float,
         static: bool) -> None:
    """One still -> one clip. Blurred fill behind, subtle push-in on top."""
    frames = max(2, int(round(dur * FPS)))
    # zoompan works on the COMPOSED frame, after the overlay, so the blurred
    # band pushes in with the photo instead of sliding against it.
    #
    # THE TRAP, and it produced a 246-second "8.8-second" reel: zoompan emits
    # `d` frames FOR EVERY INPUT FRAME. Combined with `-loop 1 -t 1.1`, which
    # feeds it 33 identical frames, it emitted 33 x 33. So the zoom path takes
    # ONE input frame and generates the duration itself, and only the static
    # path uses -loop. ffprobe the duration of anything this writes — the file
    # played correctly at the start, which is exactly why nobody would notice.
    motion = (f"zoompan=z='min(1+0.04*on/{frames},1.04)':d={frames}"
              f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
              f":s={W}x{H}:fps={FPS}")
    # Scale to 1080 wide ONCE and split, rather than scaling the full-size
    # source twice. The stills are 1744x2336, and blurring at that size was
    # slow enough to time out an eight-image build.
    fc = (
        f"[0:v]scale={W}:-2[s];[s]split[a][b];"
        f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H},gblur=sigma=32,eq=brightness=-0.10[bg];"
        f"[bg][b]overlay=(W-w)/2:(H-h)/2"
        + ("" if static else "," + motion)
        + f",format=yuv420p,fps={FPS}[v]"
    )
    pre = (["-loop", "1", "-t", f"{dur:.3f}"] if static else [])
    post = ([] if static else ["-frames:v", str(frames)])
    cmd = ([ffbin.require(), "-y", *pre, "-i", str(src),
            "-filter_complex", fc, "-map", "[v]", *post,
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-pix_fmt", "yuv420p", "-r", str(FPS), str(dest)])
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"{src.name}: {r.stderr[-400:]}")

    # Verify what was actually written, not what was asked for.
    got = ffbin.duration(dest)
    if abs(got - dur) > 0.35:
        raise RuntimeError(f"{src.name}: asked for {dur:.2f}s, wrote "
                           f"{got:.2f}s — filter graph is wrong")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("images", nargs="*")
    ap.add_argument("--from-posts", action="store_true",
                    help="use every image in posts.json marked posted, in order")
    ap.add_argument("--dur", type=float, default=1.1,
                    help="seconds per still (default 1.1 — photo dumps are fast)")
    ap.add_argument("--static", action="store_true", help="no push-in")
    ap.add_argument("--out", default="clips/reel_photodump.mp4")
    a = ap.parse_args()

    if not have_ffmpeg():
        print("  ! ffmpeg is not on PATH.  winget install Gyan.FFmpeg")
        return 2

    files = [ROOT / p for p in a.images]
    if a.from_posts:
        rows = json.loads((ROOT / "posts.json").read_text(encoding="utf-8"))
        files = [ROOT / r["image"] for r in rows if r.get("posted") and r.get("image")]
    files = [f for f in files if f.is_file()]
    if len(files) < 2:
        print("  ! need at least two stills")
        return 1

    tmp = ROOT / "_reeltmp"
    tmp.mkdir(exist_ok=True)
    parts = []
    for n, f in enumerate(files):
        d = tmp / f"{n:02d}.mp4"
        clip(f, d, a.dur, a.static)
        parts.append(d)
        print(f"  {n + 1:>2}/{len(files)}  {f.name}")

    lst = tmp / "list.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts),
                   encoding="utf-8")
    out = ROOT / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    # Silent stereo track: Instagram is inconsistent with an audio-less file,
    # and the music goes on in the app.
    cmd = [ffbin.require(), "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
           "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
           "-shortest", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
           str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print("  ! concat failed:", r.stderr[-400:])
        return 1
    shutil.rmtree(tmp, ignore_errors=True)

    total = a.dur * len(files)
    print(f"\n  {a.out}  {out.stat().st_size // 1024} KB  "
          f"{len(files)} stills  {total:.1f}s")
    print("  Add music IN INSTAGRAM, not here — a Creator account keeps the "
          "full catalogue\n  and in-app audio is a discovery signal an "
          "embedded track is not.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
