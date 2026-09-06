#!/usr/bin/env python3
"""
ffbin.py — find ffmpeg and ffprobe, wherever this machine keeps them.

    python ffbin.py            report what was found, and where

WHY THIS EXISTS. Every ffmpeg script in this project ran on the Linux side
during development, where both binaries are on PATH. The first time one ran in
PowerShell it died with a bare `FileNotFoundError: [WinError 2]` from
subprocess, which names no file and reads like a bug in the script. It is not:
it means Windows could not find `ffprobe`.

Since every one of those scripts would fail the same way, the lookup lives here
once rather than in each of them.

THREE THINGS THIS DOES BEYOND `shutil.which`:

  1. LOOKS WHERE WINDOWS ACTUALLY PUTS IT — winget, scoop, chocolatey, a
     hand-unzipped C:\\ffmpeg, and the build that ships inside the
     `imageio-ffmpeg` package, which a ComfyUI install very often already has.
  2. SURVIVES A MISSING FFPROBE. ffprobe is the one people end up without, and
     it is only ever used here to read a duration — which `ffmpeg -i` also
     prints. So duration() falls back to parsing ffmpeg's own output instead of
     failing.
  3. SAYS WHAT IS WRONG. A missing binary produces an instruction, not a
     traceback.

Override everything with the FFMPEG_DIR environment variable, or by putting a
path in ffmpeg_dir.txt next to this file.
"""
from __future__ import annotations
import os, pathlib, re, shutil, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent


def _candidates(name: str):
    """Every plausible location, cheapest first."""
    exe = f"{name}.exe"

    # 1. an explicit override always wins
    override = os.environ.get("FFMPEG_DIR", "")
    if not override and (ROOT / "ffmpeg_dir.txt").is_file():
        override = (ROOT / "ffmpeg_dir.txt").read_text(encoding="utf-8").strip()
    if override:
        d = pathlib.Path(override)
        yield d / exe
        yield d / name
        yield d / "bin" / exe

    # 2. PATH
    w = shutil.which(name)
    if w:
        yield pathlib.Path(w)

    # 3. the usual Windows homes
    home = pathlib.Path.home()
    la = os.environ.get("LOCALAPPDATA", str(home / "AppData" / "Local"))
    roots = [
        pathlib.Path("C:/ffmpeg/bin"),
        pathlib.Path("C:/ProgramData/chocolatey/bin"),
        home / "scoop" / "apps" / "ffmpeg" / "current" / "bin",
        home / "scoop" / "shims",
    ]
    for r in roots:
        yield r / exe
    # winget nests the version in the folder name, so it has to be globbed
    wg = pathlib.Path(la) / "Microsoft" / "WinGet" / "Packages"
    if wg.is_dir():
        try:
            for hit in wg.glob(f"*FFmpeg*/**/{exe}"):
                yield hit
        except OSError:
            pass

    # 4. the copy inside imageio-ffmpeg, which ComfyUI installs very often have
    if name == "ffmpeg":
        try:
            import imageio_ffmpeg                          # noqa: PLC0415
            yield pathlib.Path(imageio_ffmpeg.get_ffmpeg_exe())
        except Exception:                                  # noqa: BLE001
            pass


def find(name: str) -> str | None:
    for c in _candidates(name):
        try:
            if c.is_file():
                return str(c)
        except OSError:
            continue
    return None


FFMPEG = find("ffmpeg")
FFPROBE = find("ffprobe")

INSTALL = (
    "  ffmpeg was not found. Install it, then run this again:\n"
    "      winget install Gyan.FFmpeg\n"
    "  Close and reopen PowerShell afterwards so PATH refreshes.\n"
    "  If it is already installed somewhere unusual, put the folder holding\n"
    "  ffmpeg.exe into ffmpeg_dir.txt next to these scripts, or set FFMPEG_DIR."
)


def require() -> str:
    """The ffmpeg path, or a clear exit. Never a WinError 2."""
    if not FFMPEG:
        sys.exit(INSTALL)
    return FFMPEG


def run(args: list[str], binary: str = "ffmpeg") -> subprocess.CompletedProcess:
    exe = FFMPEG if binary == "ffmpeg" else FFPROBE
    if not exe:
        if binary == "ffprobe" and FFMPEG:
            exe = FFMPEG          # caller must cope; duration() already does
        else:
            sys.exit(INSTALL)
    return subprocess.run([exe, *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


_DUR = re.compile(r"Duration:\s*(\d+):(\d\d):(\d\d(?:\.\d+)?)")


def duration(path) -> float:
    """Seconds, from ffprobe if present and from ffmpeg's own output if not.

    ffprobe is the binary people most often end up without, and every use of it
    in this project is this one question. Falling back costs one extra process
    and removes the dependency entirely.
    """
    if FFPROBE:
        q = run(["-v", "error", "-show_entries", "format=duration",
                 "-of", "csv=p=0", str(path)], "ffprobe")
        try:
            return float(q.stdout.strip())
        except ValueError:
            pass
    if not FFMPEG:
        sys.exit(INSTALL)
    # `ffmpeg -i` with no output writes the stream summary to stderr and exits
    # non-zero. That is expected, not a failure.
    q = subprocess.run([FFMPEG, "-i", str(path)], capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    m = _DUR.search(q.stderr)
    if not m:
        return 0.0
    h, mnt, s = m.groups()
    return int(h) * 3600 + int(mnt) * 60 + float(s)


def has_audio(path) -> bool:
    if FFPROBE:
        q = run(["-v", "error", "-select_streams", "a", "-show_entries",
                 "stream=codec_type", "-of", "csv=p=0", str(path)], "ffprobe")
        return "audio" in q.stdout
    if not FFMPEG:
        sys.exit(INSTALL)
    q = subprocess.run([FFMPEG, "-i", str(path)], capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    return "Stream" in q.stderr and "Audio:" in q.stderr


def filter_path(p) -> str:
    """A path safe to put inside an ffmpeg FILTERGRAPH argument.

    In a filtergraph `:` separates options, so a Windows drive letter splits
    the filter mid-argument and ffmpeg reports it as "Error opening output
    file" — which points at the output and is nothing to do with it.
    Backslashes are separators too, so they become forward slashes first.

        C:/Windows/Fonts/segoeuib.ttf  ->  C\\:/Windows/Fonts/segoeuib.ttf

    On Linux this is a no-op, which is exactly why every drawtext script in
    this project worked in development and none of them worked in PowerShell.
    """
    t = str(p).replace("\\", "/")
    return t.replace(":", "\\:")


def main() -> int:
    print(f"  ffmpeg   {FFMPEG or 'NOT FOUND'}")
    print(f"  ffprobe  {FFPROBE or 'NOT FOUND (duration falls back to ffmpeg)'}")
    if not FFMPEG:
        print()
        print(INSTALL)
        return 1
    v = subprocess.run([FFMPEG, "-version"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    print(f"  version  {v.stdout.splitlines()[0] if v.stdout else '?'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
