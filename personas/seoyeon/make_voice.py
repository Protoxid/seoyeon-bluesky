#!/usr/bin/env python3
"""
make_voice.py — her speaking voice, via ElevenLabs on Kie.

    python make_voice.py --dry-run        free: prints the script and timings
    python make_voice.py --only hook
    python make_voice.py --all

RUNS IN POWERSHELL, LIKE EVERY OTHER GENERATION, and for the same reason: the
device shell has no network at all (a probe showed google.com failing too), and
neither the cloud container nor anything else needs to see kie_key.txt. The key
never leaves this machine.

WHAT THIS IS FOR, and the two uses want different things:
  * AS AN H3 AUDIO REFERENCE. H3's `reference_audio_urls` is a TIMBRE
    reference — MiniMax's wording is "voice timbre follows reference audio 1" —
    so any 2-15s clip in the right voice steers it. The words do not matter.
  * AS THE ACTUAL TRACK for a local ComfyUI lip-sync pass. Then the words
    matter exactly, and each segment must come in under H3's 15-SECOND CEILING
    on its own, because that ceiling is per generation and the reel is stitched.

WE CLONE NOBODY. This picks a voice from ElevenLabs' library. There is no
recording of a real person anywhere in this pipeline and there must never be.

WHAT IS NOT CONFIRMED, and I am not going to pretend otherwise:
  * Kie's docs show `voice` as a NAME ("Rachel"), while its text-to-dialogue
    example passes an ID ("EkK5I93UQWFDigLMpZcX"). So an ID probably works and
    might not. If the default below is rejected, pass --voice with a name from
    Kie's own library page.
  * I have not heard the default voice. "Jini" is listed as a warm Korean
    female; whether it carries a Korean accent into ENGLISH is exactly the
    thing that has to be judged by ear, which is what --only hook is for.
  * The price is not published anywhere I could find. Generate the hook alone
    first and read the deduction.
"""
from __future__ import annotations
import argparse, json, os, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from kie_api import Kie, load_key                       # noqa: E402
import ffbin  # resolves ffmpeg/ffprobe; see ffbin.py for why

MODEL = "elevenlabs/text-to-speech-turbo-2-5"
VOICE = "0oqpliV6dVSr9XomngOW"      # "Jini", listed as a warm Korean female
WORDS_PER_SEC = 2.6                  # instructional pace at speed 1.0
H3_CEILING = 15.0

# Each segment is ONE H3 generation, so each must fit under the ceiling alone.
# Sourced tips, strongest first — see wiki/domains/publishing/week2-plan.md.
# THE WHOLE THING AS ONE TAKE. Four separate takes were a workaround for a
# problem the voice-over structure does not have: nothing needs to sync, so the
# voice can simply run. One take also carries its own pace and breath across
# the whole reel, which four stitched files never quite do no matter what you
# pass as previous_text.
#
# LENGTH IS A CONSTRAINT, NOT A PREFERENCE. The picture is 28.0s, so the speech
# has to land under about 26s with headroom. 67 words at a natural 2.6 words a
# second is ~25.8s. Written longer, it gets cut off mid-sentence.
#
# The blank lines are load-bearing: ElevenLabs renders a paragraph break as a
# real pause, and those pauses are what build_r1.py reads to place captions.
SPEECH = (
    "Okay, three things before your first reformer class.\n\n"
    "Fewer springs is harder, not easier. Less spring means less help holding "
    "the carriage, so you're doing more work.\n\n"
    "If the carriage bangs on the way back, you're going too fast. Control the "
    "return — you want it silent.\n\n"
    "And grip socks aren't optional. Most studios won't let you on without "
    "them.\n\n"
    "Honestly, you'll be fine."
)

SCRIPT = [
    # "One. Two. Three." reads as a listicle, and a listicle read is a
    # presenter read. Discourse markers — okay, so, and, oh — are what an
    # actual person puts between thoughts, and multilingual_v2 has no delivery
    # tags, so phrasing IS the only prosody control available.
    ("hook",  "Okay, three things I always tell people before their first "
              "reformer class."),
    ("tip1",  "So, fewer springs is actually harder, not easier — less spring "
              "means less help, so you're doing more of the work."),
    ("tip2",  "And if the carriage bangs when it comes back, you're going too "
              "fast. Control the return, you want it silent."),
    ("tip3",  "Oh, and grip socks. Not optional. Most studios won't let you "
              "on the reformer without them."),
]


def estimate(text: str) -> float:
    return len(text.split()) / WORDS_PER_SEC


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None, help="one segment id")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--voice", default=VOICE)
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--stability", type=float, default=0.5)
    ap.add_argument("--outdir", default="voice")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    want = SCRIPT
    if a.only:
        ids = {s for s in a.only.replace(",", " ").split() if s}
        known = {k for k, _ in SCRIPT}
        bad = ids - known
        if bad:            # refuse rather than silently do a subset
            print(f"  ! unknown segment(s): {sorted(bad)}\n"
                  f"    known: {sorted(known)}")
            return 1
        want = [(k, t) for k, t in SCRIPT if k in ids]
    elif not a.all:
        print("  pass --all, or --only <id>. Segments: "
              + ", ".join(k for k, _ in SCRIPT))
        return 1

    print(f"  model  {MODEL}\n  voice  {a.voice}\n")
    over = []
    for k, t in want:
        sec = estimate(t)
        mark = "  OVER H3's 15s CEILING" if sec > H3_CEILING else ""
        if sec > H3_CEILING:
            over.append(k)
        print(f"  [{k:<5}] {len(t.split()):>2} words  ~{sec:4.1f}s{mark}")
        print(f"          {t}")
    print(f"\n  total ~{sum(estimate(t) for _, t in want):.1f}s of speech")
    print("  COST UNKNOWN — not published. Run --only hook first and read the "
          "deduction.")
    if over:
        print(f"  ! {over} would not fit one H3 generation. Shorten them.")
        return 1
    if a.dry_run:
        print("\n  DRY RUN — nothing sent, nothing spent")
        return 0

    load_key(ROOT)
    key = os.environ.get("KIE_API_KEY", "")
    if not key or key.startswith("PASTE"):
        print("no API key in kie_key.txt", file=sys.stderr)
        return 2
    k = Kie(key)
    out = ROOT / a.outdir
    out.mkdir(parents=True, exist_ok=True)

    for seg, text in want:
        body = {"model": MODEL,
                "input": {"text": text, "voice": a.voice,
                          "stability": a.stability, "speed": a.speed,
                          "similarity_boost": 0.75, "style": 0}}
        d = k._req("POST", "/api/v1/jobs/createTask", json=body)
        tid = (d.get("data") or {}).get("taskId")
        if not tid:
            print(f"  [{seg}] no taskId: {json.dumps(d)[:220]}")
            return 1
        urls = k._wait(tid)
        url = urls[0]
        ext = ".mp3" if ".mp3" in url.lower() else pathlib.Path(url).suffix or ".mp3"
        dest = out / f"{seg}{ext}"
        n = k.download(url, dest)
        # VERIFY THE ARTEFACT. An estimate from word count is a guess; the file
        # has a real duration and H3 will reject it on the real one.
        try:
            got = ffbin.duration(dest)
            flag = "  ! OVER 15s" if got > H3_CEILING else ""
            print(f"  [{seg:<5}] {dest.name}  {n // 1024} KB  "
                  f"{got:.1f}s actual (est {estimate(text):.1f}s){flag}")
        except Exception:
            print(f"  [{seg:<5}] {dest.name}  {n // 1024} KB  "
                  f"(ffprobe unavailable — duration unchecked)")

    print("\n  LISTEN TO THE HOOK BEFORE GENERATING THE REST. The thing to")
    print("  judge is whether an English sentence carries a Korean accent —")
    print("  a Seoul instructor with a flat American voice reads as dubbed,")
    print("  which is a different AI tell but still an AI tell.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
