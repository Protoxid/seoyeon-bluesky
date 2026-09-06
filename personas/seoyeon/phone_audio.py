#!/usr/bin/env python3
"""
phone_audio.py — make a studio-clean TTS voice sound like it was recorded by
the phone that shot the picture.

    python phone_audio.py --audio voice/hook.mp3 --under clips/hook_raw.mp4 \
                          --mux clips/hook_raw.mp4 --out clips/hook.mp4

    python phone_audio.py --audio voice/hook.mp3 --out voice/hook_phone.mp3

WHY IT SOUNDS ADDED IN POST. It is not the voice, it is that the voice has no
ROOM in it. Five differences, all of them fixable and none of them requiring a
regeneration:

  1. NO ROOM. TTS is anechoic. A phone in a studio with a wooden floor and a
     mirrored wall picks up early reflections within the first 40ms — that is
     what tells your ear where the sound was made.
  2. FULL FREQUENCY RANGE. A phone mic rolls off below roughly 110 Hz and above
     roughly 10 kHz. TTS has deep bass and crisp air that no phone ever
     captured, and that alone reads as "studio".
  3. NO NOISE FLOOR. Silence in a TTS file is digital zero. Silence in a real
     room is HVAC, traffic, the building. Absolute silence between words is one
     of the loudest tells there is.
  4. STEREO AND PERFECTLY CENTRED. Phone voice memos are mono.
  5. TOO EVEN. Phone AGC pumps; a voice at arm's length moves in level as the
     head moves. Perfectly consistent level sounds like a booth.

THE BEST NOISE FLOOR IS THE CLIP'S OWN. If the H3 render carries a native audio
track, `--under <video>` uses it as the bed. That is literally the room the
picture was generated in, so nothing matches better. Falls back to synthesised
brown noise when the clip is silent.

Everything here is ffmpeg. No generation, no cost, and it is reversible because
the source mp3 is never modified.
"""
from __future__ import annotations
import argparse, math, pathlib, random, struct, subprocess, sys, wave
import ffbin  # resolves ffmpeg/ffprobe; see ffbin.py for why

ROOT = pathlib.Path(__file__).resolve().parent
IR = ROOT / "room_ir.wav"


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def probe(p) -> str:
    """Duration as a string, via ffbin so a missing ffprobe is survivable."""
    d = ffbin.duration(p)
    return f"{d:.6f}" if d else ""


def has_audio(p) -> bool:
    return ffbin.has_audio(p)


# WHY THE FIRST VERSION SOUNDED LIKE A TOILET. Two mistakes compounding: a
# 0.32s decay with a BRIGHT tail, mixed at wet 3.0 against dry 10. Long plus
# bright plus loud is the definition of a tiled bathroom. A real class studio
# is a big soft box - the early reflections arrive and then it dies, and
# everything above roughly 3 kHz is eaten by mats, bodies and clothing before
# it can come back. So: shorter, darker, quieter.
PRESETS = {                    # (ir seconds, tail brightness 0-1, wet amount)
    "dry":    (0.00, 0.00, 0.0),   # no room at all
    "studio": (0.16, 0.25, 1.0),   # DEFAULT: a soft-furnished class studio
    "room":   (0.24, 0.45, 1.8),   # a harder, emptier room
    "hall":   (0.34, 0.80, 3.0),   # what the first version was doing
}


def make_ir(path: pathlib.Path, seconds: float = 0.16,
            brightness: float = 0.25, seed: int = 7) -> None:
    """Discrete early reflections, then a decaying noise tail.

    `brightness` one-pole-lowpasses the tail. A bright tail is exactly what
    makes a small room read as tiled: real soft rooms lose their highs first,
    so the late energy must be dull even when the early reflections are crisp.

    Pure stdlib deliberately. A numpy import that works here and not on the
    other machine is a dependency failure disguised as an audio bug.
    """
    sr = 44100
    n = max(2, int(sr * seconds))
    random.seed(seed)
    tail = [0.0] * n
    prev = 0.0
    k = max(0.02, min(1.0, brightness))
    for i in range(n):
        prev = prev + k * (random.uniform(-1, 1) - prev)
        tail[i] = prev * math.exp(-7.5 * i / n)
    ir = [0.0] * n
    ir[0] = 1.0
    for ms, amp in ((7, 0.26), (11, 0.20), (17, 0.15), (24, 0.10)):
        j = int(sr * ms / 1000)
        if j < n:
            ir[j] += amp
    for i in range(n):
        ir[i] += tail[i] * 0.22
    pk = max(abs(v) for v in ir) or 1.0
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(b"".join(struct.pack("<h", int(v / pk * 0.9 * 32767))
                               for v in ir))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", required=True, help="the ElevenLabs take")
    ap.add_argument("--under", default=None,
                    help="video whose own audio becomes the room bed")
    ap.add_argument("--mux", default=None,
                    help="video to lay the finished audio onto")
    ap.add_argument("--out", required=True)
    ap.add_argument("--preset", default="studio", choices=sorted(PRESETS),
                    help="room character. 'studio' is a soft-furnished class "
                         "studio; 'hall' is what the first version did, which "
                         "sounded like a bathroom")
    ap.add_argument("--room", type=float, default=None,
                    help="override the preset's wet amount (0 = none)")
    ap.add_argument("--delay", type=float, default=0.0,
                    help="seconds of silence before the voice starts, to give "
                         "back a pause the clip has and the take does not")
    ap.add_argument("--no-normalize", action="store_true", dest="no_norm",
                    help="skip loudnorm. It gains by INTEGRATED loudness, so a "
                         "take with a long pause gets MORE gain and the pause "
                         "fills with audible floor - which is why the silence "
                         "at the top stopped sounding like silence")
    ap.add_argument("--bed", type=float, default=0.06,
                    help="noise floor level, 0 = none")
    ap.add_argument("--bed-lp", type=int, default=500, dest="bed_lp",
                    help="lowpass on a CLIP-derived bed. 500 Hz kills every "
                         "consonant, so H3's own generated speech cannot "
                         "survive as a ghost second voice under hers")
    ap.add_argument("--hp", type=int, default=110)
    ap.add_argument("--lp", type=int, default=10500)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    src = pathlib.Path(a.audio)
    if not src.is_file():
        print(f"  ! {src} not found")
        return 2
    for v in (a.under, a.mux):
        if v and not pathlib.Path(v).is_file():
            print(f"  ! {v} not found")
            return 2

    ir_sec, ir_bright, wet = PRESETS[a.preset]
    a.room = wet if a.room is None else a.room
    bed_from_clip = bool(a.under) and has_audio(a.under)
    print(f"  voice   {src.name}  {probe(src)}s")
    print(f"  band    {a.hp}-{a.lp} Hz, mono")
    print(f"  room    {a.preset}: {ir_sec * 1000:.0f}ms tail, wet {a.room} "
          f"against dry 10")
    if a.delay:
        print(f"  delay   {a.delay}s before she starts")
    if bed_from_clip:
        print(f"  bed     the clip's own room tone, from "
              f"{pathlib.Path(a.under).name}, crushed below {a.bed_lp} Hz")
    elif a.under:
        print(f"  bed     {pathlib.Path(a.under).name} has NO audio track "
              f"-> synthetic brown noise at {a.bed}")
    elif a.bed > 0:
        print(f"  bed     synthetic brown noise at {a.bed}")
    else:
        print("  bed     none")
    if a.dry_run:
        print("\n  DRY RUN — nothing written")
        return 0

    # Regenerated per preset, never cached: a stale room_ir.wav left over from
    # a different preset is silently the wrong room.
    if a.room > 0:
        make_ir(IR, ir_sec, ir_bright)

    tmp = ROOT / "_phonetmp.wav"

    # AN INPUT INDEX IS A PROPERTY OF THE INPUT LIST, so it gets counted, not
    # derived from len(). Deriving it broke immediately: "-f lavfi -i spec"
    # adds three list elements for one input while "-i path" adds two, so every
    # arithmetic guess is wrong as soon as the two are mixed.
    ins: list[str] = []
    n_in = 0

    def add(*args: str) -> int:
        nonlocal n_in
        ins.extend(args)
        n_in += 1
        return n_in - 1

    iv = add("-i", str(src))
    # Order matters: band-limit BEFORE the room, so the reverb is built from
    # the same restricted band the mic would have heard, not from full-range
    # audio that is then filtered.
    lead = f"adelay={int(a.delay * 1000)}:all=1," if a.delay > 0 else ""
    chain = (f"[{iv}:a]aformat=channel_layouts=mono,{lead}"
             f"highpass=f={a.hp},lowpass=f={a.lp},"
             f"acompressor=threshold=-18dB:ratio=3:attack=8:release=140"
             f":makeup=2dB[v]")
    cur = "[v]"

    if a.room > 0:
        ir = add("-i", str(IR))
        chain += f";{cur}[{ir}:a]afir=dry=10:wet={a.room}[r]"
        cur = "[r]"

    NORM = "anull" if a.no_norm else "loudnorm=I=-16:TP=-1.5:LRA=11"
    bed = None
    if bed_from_clip:
        # THE TRAP: H3 generates NATIVE AUDIO, and if the prompt had dialogue
        # in it that audio contains H3'S OWN VOICE saying the line. Using it
        # unfiltered as a bed puts a second, slightly-out-of-sync person under
        # her — the exact opposite of what this script is for.
        # So a clip bed is crushed to --bed-lp (500 Hz by default), which keeps
        # the room's rumble and HVAC and destroys every consonant, so no words
        # can survive. Raise it only if you have confirmed the clip's audio is
        # room tone alone.
        ib = add("-i", str(a.under))
        chain += (f";[{ib}:a]aformat=channel_layouts=mono,"
                  f"highpass=f={a.hp},lowpass=f={a.bed_lp},"
                  f"volume={a.bed}[b]")
        bed = "[b]"
    elif a.bed > 0:
        dur = probe(src) or "10"
        ib = add("-f", "lavfi", "-i",
                 f"anoisesrc=color=brown:duration={dur}:amplitude=0.4")
        chain += f";[{ib}:a]lowpass=f=1200,volume={a.bed}[b]"
        bed = "[b]"

    if bed:
        chain += (f";{cur}{bed}amix=inputs=2:duration=first"
                  f":dropout_transition=0,{NORM}[a]")
    else:
        chain += f";{cur}{NORM}[a]"

    r = run([ffbin.require(), "-y", "-v", "error", *ins, "-filter_complex", chain,
             "-map", "[a]", "-ac", "1", "-ar", "44100", str(tmp)])
    if r.returncode:
        print("  ! ffmpeg:", r.stderr[-500:])
        return 1

    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if a.mux:
        # -c:v copy, and no -shortest: re-encoding the video for an audio swap
        # throws away quality for nothing, and shortest would silently trim the
        # picture if the voice is a hair shorter.
        r = run([ffbin.require(), "-y", "-v", "error", "-i", str(a.mux),
                 "-i", str(tmp), "-map", "0:v:0", "-map", "1:a:0",
                 "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", str(out)])
    else:
        r = run([ffbin.require(), "-y", "-v", "error", "-i", str(tmp),
                 "-c:a", "libmp3lame", "-b:a", "192k", str(out)])
    try:
        tmp.unlink(missing_ok=True)
    except OSError:
        pass          # a leftover scratch file is not a reason to fail
    if r.returncode:
        print("  ! ffmpeg:", r.stderr[-500:])
        return 1

    # VERIFY THE ARTEFACT. A drift here means the voice no longer lines up with
    # the mouth, which is the one failure that makes the whole thing worthless.
    got, want = probe(out), probe(a.mux or src)
    print(f"\n  {a.out}  {out.stat().st_size // 1024} KB  {got}s")
    try:
        if abs(float(got) - float(want)) > 0.15:
            print(f"  ! source is {want}s — that drift will break lip sync")
            return 1
    except ValueError:
        pass
    print("  A/B it against the original. If it now sounds muffled rather than")
    print("  present, lower --room before touching anything else.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
