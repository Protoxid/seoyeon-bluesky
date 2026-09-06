#!/usr/bin/env python3
"""
make_voice_el.py — her lines, in the voice you designed, from ElevenLabs direct.

    python make_voice_el.py --dry-run
    python make_voice_el.py --voice-id <id> --only hook
    python make_voice_el.py --voice-id <id> --all

The voice now lives in your ElevenLabs account, so this talks to ElevenLabs
rather than to a reseller: `POST /v1/text-to-speech/{voice_id}`, `xi-api-key`
header, and the response is RAW AUDIO BYTES, not a job to poll. No task queue,
no recordInfo, none of the machinery the Kie path needed.

    key       elevenlabs_key.txt   (or the ELEVENLABS_API_KEY env var)
    voice id  voice_id.txt         (or --voice-id)

THE SCRIPT IS IMPORTED FROM make_voice.py, not copied. Two lists of the same
lines is one bug waiting for someone to edit the wrong one.

`eleven_multilingual_v2` is the default and it is also the right choice here:
it is the model family that carries accent, which is the entire point of a
Korean voice speaking English. Turbo is the low-latency one and drops exactly
what we are paying attention to.

CONTINUITY BETWEEN SEGMENTS. Each call passes the neighbouring lines as
`previous_text` and `next_text`. The reel is stitched from separate takes, and
without this the pitch and pace reset at every cut — which is audible, and
reads as four clips rather than one person talking.

Each file is checked against H3's 2-15s reference window on the way out, so
anything here can be dropped straight into `reference_audio_urls`.
"""
from __future__ import annotations
import argparse, os, pathlib, subprocess, sys, urllib.error, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from make_voice import SCRIPT, WORDS_PER_SEC, H3_CEILING   # noqa: E402
import ffbin  # resolves ffmpeg/ffprobe; see ffbin.py for why

API = "https://api.elevenlabs.io/v1/text-to-speech"
MODEL = "eleven_multilingual_v2"
H3_MIN = 2.0

# DELIVERY — CANON, and chosen by ear rather than by argument.
#
# Three rounds of reasoning about these numbers produced three different
# failures: sleepy, then a YouTube presenter, then robotic. voice_matrix.py
# then rendered the same line nine ways for a fraction of a cent and the
# answer was the middle of the stability range, which is where I had never
# put it. `stab-040` won.
#
# THESE NUMBERS ARE NOW A PROPERTY OF THE ACCOUNT, not a preference. Every
# take she ever speaks has to use them or her voice changes between reels, the
# same way voice_id does. Change them only after another audition.
DELIVERY = {                    # (stability, style, speed)
    "canon":   (0.40, 0.10, 1.00),   # DEFAULT — stab-040, picked from the grid
    # kept only so a future comparison has something to compare against
    "loose":   (0.15, 0.10, 1.00),
    "flat":    (0.65, 0.10, 1.00),
    "styled":  (0.40, 0.45, 1.00),
    "slow":    (0.40, 0.10, 0.94),
}

def read_first(*candidates: str) -> str:
    for c in candidates:
        v = os.environ.get(c, "")
        if v and not v.startswith("PASTE"):
            return v.strip()
        p = ROOT / f"{c.lower()}.txt"
        if p.is_file():
            v = p.read_text(encoding="utf-8").strip()
            if v and not v.startswith("PASTE"):
                return v
    return ""


def probe(p: pathlib.Path) -> float:
    return ffbin.duration(p)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice-id", default=None)
    ap.add_argument("--only", default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--delivery", default="canon", choices=sorted(DELIVERY),
                    help="stability/style/speed together. Lower stability is "
                         "MORE expressive, not less")
    ap.add_argument("--stability", type=float, default=None)
    ap.add_argument("--style", type=float, default=None)
    ap.add_argument("--speed", type=float, default=None)
    ap.add_argument("--similarity", type=float, default=0.8)
    ap.add_argument("--outdir", default="voice")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    want = SCRIPT
    if a.only:
        ids = {s for s in a.only.replace(",", " ").split() if s}
        known = {k for k, _ in SCRIPT}
        if ids - known:
            print(f"  ! unknown: {sorted(ids - known)}\n"
                  f"    known: {sorted(known)}")
            return 1
        want = [(k, t) for k, t in SCRIPT if k in ids]
    elif not a.all:
        print("  pass --all or --only <id>. Segments: "
              + ", ".join(k for k, _ in SCRIPT))
        return 1

    st, sty, sp = DELIVERY[a.delivery]
    if a.stability is not None:
        st = a.stability
    if a.style is not None:
        sty = a.style
    if a.speed is not None:
        sp = a.speed

    vid = a.voice_id or read_first("ELEVENLABS_VOICE_ID", "VOICE_ID")
    print(f"  model     {a.model}")
    print(f"  delivery  {a.delivery}: stability {st}, style {sty}, speed {sp}")
    print(f"  voice id  {vid or '(none — pass --voice-id or make voice_id.txt)'}")
    for k, t in want:
        print(f"\n  [{k}] {len(t.split())} words, ~{len(t.split())/WORDS_PER_SEC:.1f}s"
              f"\n      {t}")
    if a.dry_run:
        print("\n  DRY RUN — nothing sent, nothing spent")
        return 0
    if not vid:
        print("\n  ! no voice id")
        return 2

    key = read_first("ELEVENLABS_API_KEY", "ELEVENLABS_KEY", "XI_API_KEY")
    if not key:
        print("  ! no key: put it in elevenlabs_key.txt or ELEVENLABS_API_KEY")
        return 2

    out = ROOT / a.outdir
    out.mkdir(parents=True, exist_ok=True)
    order = [k for k, _ in SCRIPT]
    texts = dict(SCRIPT)
    bad = 0

    for seg, text in want:
        i = order.index(seg)
        body = {
            "text": text,
            "model_id": a.model,
            # neighbouring lines, so prosody carries across the cut
            "previous_text": texts[order[i - 1]] if i > 0 else "",
            "next_text": texts[order[i + 1]] if i + 1 < len(order) else "",
            "voice_settings": {"stability": st,
                               "similarity_boost": a.similarity,
                               "style": sty,
                               "speed": sp},
        }
        import json as _j
        req = urllib.request.Request(
            f"{API}/{vid}?output_format=mp3_44100_128",
            data=_j.dumps(body).encode(), method="POST",
            headers={"xi-api-key": key, "Content-Type": "application/json",
                     "Accept": "audio/mpeg"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                audio = r.read()
        except urllib.error.HTTPError as e:
            # the body carries the real reason; the status alone never does
            print(f"  [{seg:<5}] HTTP {e.code}: {e.read()[:300].decode(errors='replace')}")
            return 1
        dest = out / f"{seg}.mp3"
        dest.write_bytes(audio)
        got = probe(dest)
        note = ""
        if got and not H3_MIN <= got <= H3_CEILING:
            note = f"  ! outside H3's {H3_MIN}-{H3_CEILING}s reference window"
            bad += 1
        print(f"  [{seg:<5}] {dest.name}  {len(audio) // 1024} KB  "
              f"{got:.1f}s{note}" if got else
              f"  [{seg:<5}] {dest.name}  {len(audio) // 1024} KB "
              f"(duration unchecked)")

    print(f"\n  {len(want)} file(s) in {a.outdir}/")
    print("  Any one of them works as an H3 audio reference — the slot is")
    print("  TIMBRE, so the words in the reference do not have to be the words")
    print("  in the shot.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
