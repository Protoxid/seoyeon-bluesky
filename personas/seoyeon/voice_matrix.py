#!/usr/bin/env python3
"""
voice_matrix.py — render one line across a grid of settings, and listen.

    python voice_matrix.py --dry-run
    python voice_matrix.py                 -> voice/matrix/*.mp3

WHY THIS EXISTS. Three rounds of tuning by description produced three different
failures — sleepy, then a YouTube presenter, then robotic — and each round cost
a full exchange to discover. Every one of those was me changing one number or
one adjective on a hunch and asking whether it worked.

A GRID SETTLES IT IN ONE PASS. The line is short, ElevenLabs bills per
character, and the whole sweep below is a few hundred characters. Guessing is
the expensive part; generating is not.

The axes move ONE AT A TIME from a centre point, so the result is readable. A
full cross-product would be more files and less information: if you change two
things and it improves, you have learned nothing about either.

WHAT I DO NOT KNOW, and this is the point of measuring rather than asserting:
ElevenLabs documents low stability as "more emotional and expressive, prone to
hallucinations" and high as "highly stable, less responsive". Which end reads
as ROBOTIC is not stated, and both ends plausibly could — flat and monotone at
one end, artefacts and wobble at the other. The sweep covers both.
"""
from __future__ import annotations
import argparse, json, pathlib, subprocess, sys, urllib.error, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from make_voice_el import read_first                   # noqa: E402
from make_voice import SCRIPT                          # noqa: E402
import ffbin                                           # noqa: E402

API = "https://api.elevenlabs.io/v1/text-to-speech"
LINE = dict(SCRIPT)["hook"]

# (label, model, stability, style, speed)
CENTRE = ("eleven_multilingual_v2", 0.40, 0.10, 1.00)
GRID = [
    # stability sweep — the axis most likely to be responsible
    ("stab-015", CENTRE[0], 0.15, 0.10, 1.00),
    ("stab-040", CENTRE[0], 0.40, 0.10, 1.00),
    ("stab-065", CENTRE[0], 0.65, 0.10, 1.00),
    ("stab-090", CENTRE[0], 0.90, 0.10, 1.00),
    # style sweep at the centre stability
    ("style-000", CENTRE[0], 0.40, 0.00, 1.00),
    ("style-045", CENTRE[0], 0.40, 0.45, 1.00),
    # a slower read, in case "robotic" is really "too even and too fast"
    ("slow-094", CENTRE[0], 0.40, 0.10, 0.94),
    # and a different model entirely — multilingual_v2 is not the newest, and
    # if every setting sounds mechanical the model is the thing to change
    ("turbo", "eleven_turbo_v2_5", 0.40, 0.10, 1.00),
    ("v3", "eleven_v3", 0.40, 0.10, 1.00),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--line", default=None, help="override the text")
    ap.add_argument("--voice-id", default=None)
    ap.add_argument("--outdir", default="voice/matrix")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    text = a.line or LINE
    vid = a.voice_id or read_first("ELEVENLABS_VOICE_ID", "VOICE_ID")
    print(f"  voice   {vid or '(none)'}")
    print(f"  line    {text}")
    print(f"  {len(GRID)} renders, ~{len(GRID) * len(text)} characters total\n")
    for label, model, st, sty, sp in GRID:
        print(f"  {label:<10} {model:<24} stab {st:<5} style {sty:<5} "
              f"speed {sp}")
    if a.dry_run:
        print("\n  DRY RUN — nothing sent")
        return 0
    if not vid:
        print("  ! no voice id")
        return 2
    key = read_first("ELEVENLABS_API_KEY", "ELEVENLABS_KEY", "XI_API_KEY")
    if not key:
        print("  ! no key in elevenlabs_key.txt")
        return 2

    out = ROOT / a.outdir
    out.mkdir(parents=True, exist_ok=True)
    print()
    for label, model, st, sty, sp in GRID:
        body = {"text": text, "model_id": model,
                "voice_settings": {"stability": st, "similarity_boost": 0.8,
                                   "style": sty, "speed": sp}}
        req = urllib.request.Request(
            f"{API}/{vid}?output_format=mp3_44100_128",
            data=json.dumps(body).encode(), method="POST",
            headers={"xi-api-key": key, "Content-Type": "application/json",
                     "Accept": "audio/mpeg"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                audio = r.read()
        except urllib.error.HTTPError as e:
            # A model this account cannot use is a fact worth keeping, not a
            # reason to stop: the rest of the grid is still informative.
            msg = e.read()[:160].decode(errors="replace")
            print(f"  {label:<10} HTTP {e.code}  {msg}")
            continue
        dest = out / f"{label}.mp3"
        dest.write_bytes(audio)
        print(f"  {label:<10} {dest.name:<14} {len(audio) // 1024:>3} KB  "
              f"{ffbin.duration(dest):.1f}s")

    print(f"\n  Listen in {a.outdir}/ and tell me the filename that sounds")
    print("  like a person. Then that row becomes the default and the")
    print("  guessing stops.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
