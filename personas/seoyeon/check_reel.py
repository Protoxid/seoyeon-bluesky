#!/usr/bin/env python3
"""
check_reel.py — validate a video against Meta's published Reels specification
BEFORE it is uploaded to a public URL.

    python check_reel.py clips/r4_fit_door.mp4

WHY THIS EXISTS AS A SEPARATE FILE. ig_publish.py has a gate, and the gate is
good, but read its first line: `if is_image and not a.force`. Every check in it
-- the two-renders-exist check, the stale-prompt hash check -- is skipped
entirely for a video. Half the week's content is reels, and for that half the
publisher checked nothing at all except that the file existed. A reel went out
having been validated on precisely one property: its filename.

THE SPEC IS META'S, QUOTED, NOT REMEMBERED. Source:
https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media/
    container    MOV or MP4 (MPEG-4 Part 14), no edit lists, moov atom at front
    audio        AAC, 48kHz sample rate maximum, 1 or 2 channels, 128kbps
    video        HEVC or H264, progressive scan, closed GOP, 4:2:0 chroma
    frame rate   23-60 FPS
    picture      1920 pixels maximum horizontal resolution
    aspect       between 0.01:1 and 10:1, 9:16 recommended
    bitrate      VBR, 25Mbps maximum
    duration     15 minutes maximum, 3 seconds minimum
    file size    300MB maximum

TWO OF THOSE LINES ARE DOWNGRADED TO WARNINGS, AND THE EVIDENCE IS OURS.
`clips/r1_text.mp4` and `clips/r3_river.mp4` were both published successfully
to this account. Both carry edit lists. Both have moov at the END of the file,
not the front. r3_river is 768x1344, which is not 1080p and not a spec size.
Meta accepted all three facts. So "no edit lists" and "moov at the front" are
what Meta's encoder guidance asks for, not what its ingest enforces, and a
checker that FAILS on them would block files we have already proven publish.
It says so instead, which is the honest strength of the claim.

An AAC track in an MP4 essentially always carries a priming edit (media_time
1024). It is not removable through ffmpeg without rewriting the box, and it is
not worth rewriting a box over.
"""
from __future__ import annotations
import json, pathlib, subprocess, sys

SPEC_URL = ("https://developers.facebook.com/docs/instagram-platform/"
            "instagram-graph-api/reference/ig-user/media/")


def probe(p: pathlib.Path) -> dict:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_streams",
                        "-show_format", "-of", "json", str(p)],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"  ! ffprobe failed: {r.stderr[-300:]}")
    return json.loads(r.stdout)


def main() -> int:
    if len(sys.argv) < 2:
        return int(bool(sys.stderr.write(
            "usage: python check_reel.py <video>\n")))
    p = pathlib.Path(sys.argv[1])
    if not p.is_file():
        print(f"  ! {p} not found")
        return 2

    d = probe(p)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in d["streams"] if s["codec_type"] == "audio"), None)
    if v is None:
        print("  ! no video stream")
        return 1

    raw = p.read_bytes()
    moov, mdat = raw.find(b"moov"), raw.find(b"mdat")
    w, h = int(v["width"]), int(v["height"])
    num, den = (v.get("r_frame_rate") or "0/1").split("/")
    fps = int(num) / int(den or 1)
    secs = float(d["format"]["duration"])
    mb = int(d["format"]["size"]) / 1e6
    vbr = int(v.get("bit_rate") or 0) / 1e6
    ar = w / h

    FAIL, WARN = [], []

    def need(ok, msg):
        (FAIL if not ok else WARN).append(msg) if not ok else None

    if p.suffix.lower() not in (".mp4", ".mov"):
        FAIL.append(f"container is {p.suffix}; Meta takes MOV or MP4 only")
    if v["codec_name"] not in ("h264", "hevc"):
        FAIL.append(f"video codec {v['codec_name']}; Meta takes H264 or HEVC")
    if v.get("pix_fmt") != "yuv420p":
        FAIL.append(f"pix_fmt {v.get('pix_fmt')}; Meta requires 4:2:0")
    if not (23 <= fps <= 60):
        FAIL.append(f"{fps:.2f} fps is outside Meta's 23-60")
    if w > 1920:
        FAIL.append(f"width {w}px exceeds Meta's 1920px maximum")
    if not (0.01 <= ar <= 10):
        FAIL.append(f"aspect {ar:.3f}:1 is outside Meta's 0.01:1 to 10:1")
    if secs < 3:
        FAIL.append(f"{secs:.2f}s is under Meta's 3s minimum")
    if secs > 15 * 60:
        FAIL.append(f"{secs:.1f}s is over Meta's 15min maximum")
    if mb > 300:
        FAIL.append(f"{mb:.1f} MB is over Meta's 300MB maximum")
    if vbr > 25:
        FAIL.append(f"{vbr:.1f} Mbps is over Meta's 25Mbps maximum")
    if a is None:
        WARN.append("no audio track — Instagram is inconsistent with "
                    "audio-less files; a silent AAC track is safer")
    else:
        if a["codec_name"] != "aac":
            FAIL.append(f"audio codec {a['codec_name']}; Meta requires AAC")
        if int(a["sample_rate"]) > 48000:
            FAIL.append(f"{a['sample_rate']}Hz is over Meta's 48kHz maximum")
        if int(a["channels"]) not in (1, 2):
            FAIL.append(f"{a['channels']} channels; Meta allows 1 or 2")

    # the two Meta asks for and does not enforce -- see the docstring
    if raw.count(b"elst"):
        WARN.append(f"{raw.count(b'elst')} edit list(s); Meta's spec says "
                    "none, but r1_text and r3_river both published with them")
    if not (0 <= moov < mdat):
        WARN.append("moov atom is at the END, not the front; Meta's spec asks "
                    "for the front, but r1_text and r3_river both published "
                    "this way")
    if abs(ar - 9 / 16) > 0.005:
        WARN.append(f"aspect is {ar:.4f}:1, not 9:16 ({9/16:.4f}); accepted, "
                    "but the Reels player is 9:16 and will crop or pad")

    print(f"  {p.name}")
    print(f"  {w}x{h}  {ar:.4f}:1   {fps:.0f} fps   {secs:.2f}s   "
          f"{mb:.2f} MB   {vbr:.2f} Mbps")
    print(f"  {v['codec_name']}/{v.get('profile','?')} {v.get('pix_fmt')}"
          + (f"   {a['codec_name']} {a['sample_rate']}Hz "
             f"{a['channels']}ch" if a else "   NO AUDIO"))
    print(f"  moov@{moov} mdat@{mdat}  faststart="
          f"{0 <= moov < mdat}  elst={raw.count(b'elst')}\n")

    for m in WARN:
        print(f"  ~ {m}")
    for m in FAIL:
        print(f"  ! {m}")
    print()
    if FAIL:
        print(f"  {len(FAIL)} blocking issue(s) — do NOT publish")
        return 1
    print(f"  passes Meta's Reels spec"
          + (f"  ({len(WARN)} advisory)" if WARN else ""))
    print(f"  spec: {SPEC_URL}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
