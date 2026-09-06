#!/usr/bin/env python3
"""
design_voice_el.py — design her voice on ElevenLabs, where the voice lives.

    python design_voice_el.py --dry-run
    python design_voice_el.py                       -> voice/design/*.mp3
    python design_voice_el.py --save <generated_id> -> a permanent voice_id

WHY THIS REPLACES make_voice_design.py. That script calls MINIMAX's Voice
Design through fal. It was written before the voice existed, when Kie carried
no voice-design model at all. The voice is now an ElevenLabs voice, voice_id.txt
holds an ElevenLabs id, and the prompting guide the brief is written against is
ElevenLabs' own — so pointing at MiniMax would have minted a second, different
voice on a second platform. Same key as make_voice_el.py, nothing new to set up.

TWO STEPS, ON PURPOSE. `design` returns SEVERAL previews of the same brief and
none of them is saved. You listen, pick one, and only then does `--save` turn
that preview into a permanent voice with an id. Auditioning is the point: a
brief is a guess, and hearing four readings of it is worth more than another
round of adjectives.

    voice_description   20-1000 chars
    text (preview)      100-1000 chars, and the floor is why a short preview
                        was never a good idea
    guidance_scale      0-100, DEFAULT 5 — how closely it follows the brief.
                        Five is very loose. Everything we have been fighting
                        (sleepy, then presenter) is the model filling in what
                        the brief did not pin down, so this is the lever that
                        makes the brief actually count.
"""
from __future__ import annotations
import argparse, base64, json, os, pathlib, sys, urllib.error, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from make_voice_el import read_first                   # noqa: E402

API = "https://api.elevenlabs.io/v1/text-to-voice"

# ElevenLabs' recommended three-line format. Their slots, their order.
#   Native <Language>. <Gender>, <Age range>. <Quality level>.
#   Persona: <2-5 words>. Emotion: <2-3 adjectives>.
#   <1-2 sentences about timbre, pacing, delivery>
#
# Persona is the RELATIONSHIP, not the occupation. "Pilates instructor" asks
# for someone doing their job, and the job is addressing a room — that is what
# produced the YouTube-host read. "Perfect audio quality" describes the
# recording, not the performance; phone_audio.py puts the room back afterwards.
DESCRIPTION = (
    "Native Korean. Female, in her mid twenties. Perfect audio quality.\n"
    "Persona: friend sending a voice note. Emotion: warm, casual, amused.\n"
    "Speaking English with a thick Korean accent, in a light mid-pitched "
    "voice. Relaxed and slightly uneven — some words run together, some trail "
    "off, small pauses in the middle of sentences, talking to one person "
    "rather than to an audience."
)

# The preview is a performance script and must not contradict the brief. The
# discourse markers are load-bearing: "One. Two. Three." is a listicle read,
# and a listicle read is a presenter read.
PREVIEW = (
    "Okay, three things I always tell people before their first reformer "
    "class. So, fewer springs is actually harder, not easier — less spring "
    "means less help, so you're doing more of the work. And if the carriage "
    "bangs when it comes back, you're going too fast. Control the return, you "
    "want it silent. Oh, and grip socks. Not optional. Most studios won't let "
    "you on the reformer without them."
)


def post(path: str, body: dict, key: str) -> dict:
    req = urllib.request.Request(
        f"{API}/{path}", data=json.dumps(body).encode(), method="POST",
        headers={"xi-api-key": key, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=240) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        # the body carries the reason; the status code never does
        sys.exit(f"  ! HTTP {e.code}: {e.read()[:400].decode(errors='replace')}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--save", default=None,
                    help="a generated_voice_id from a previous run")
    ap.add_argument("--name", default="seoyeon")
    ap.add_argument("--model", default="eleven_multilingual_ttv_v2",
                    help="or eleven_ttv_v3")
    ap.add_argument("--guidance", type=float, default=35.0,
                    help="0-100 prompt adherence. The API default is 5, which "
                         "is loose enough that the brief barely lands")
    ap.add_argument("--loudness", type=float, default=0.5)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--outdir", default="voice/design")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    nd, npv = len(DESCRIPTION), len(PREVIEW)
    print(f"  description  {nd} chars   (limit 20-1000)")
    print(f"  preview      {npv} chars   (limit 100-1000)")
    print(f"  model        {a.model}")
    print(f"  guidance     {a.guidance}  (API default is 5)")
    bad = []
    if not 20 <= nd <= 1000:
        bad.append("description")
    if not 100 <= npv <= 1000:
        bad.append("preview")
    if bad:
        print(f"  ! {bad} outside the documented limits")
        return 1
    print()
    for i, line in enumerate(DESCRIPTION.split("\n"), 1):
        print(f"  {i}| {line}")
    print(f"\n  preview says:\n{PREVIEW}\n")

    if a.dry_run:
        print("  DRY RUN — nothing sent")
        return 0

    key = read_first("ELEVENLABS_API_KEY", "ELEVENLABS_KEY", "XI_API_KEY")
    if not key:
        print("  ! no key: elevenlabs_key.txt or ELEVENLABS_API_KEY")
        return 2

    if a.save:
        d = post("create", {"voice_name": a.name,
                            "voice_description": DESCRIPTION,
                            "generated_voice_id": a.save}, key)
        vid = d.get("voice_id") or (d.get("voice") or {}).get("voice_id")
        print(f"  saved as {a.name}\n  voice_id  {vid}")
        if vid:
            # Written, not printed and forgotten: every later line has to use
            # the same id or she changes voice mid-account.
            (ROOT / "voice_id.txt").write_text(vid + "\n", encoding="utf-8")
            print("  voice_id.txt updated — this is now canon")
        return 0

    body = {"voice_description": DESCRIPTION, "text": PREVIEW,
            "model_id": a.model, "guidance_scale": a.guidance,
            "loudness": a.loudness}
    if a.seed is not None:
        body["seed"] = a.seed
    d = post("design", body, key)

    previews = d.get("previews") or []
    if not previews:
        print(f"  ! no previews in the response. Keys: {sorted(d)}")
        return 1
    out = ROOT / a.outdir
    out.mkdir(parents=True, exist_ok=True)
    for i, pv in enumerate(previews, 1):
        gid = pv.get("generated_voice_id", "?")
        # the audio field name is not something to guess at
        b64 = next((pv[k] for k in ("audio_base_64", "audio_base64", "audio")
                    if isinstance(pv.get(k), str)), None)
        if not b64:
            print(f"  ! preview {i}: no audio field. Keys: {sorted(pv)}")
            continue
        dest = out / f"{i:02d}_{gid[:8]}.mp3"
        dest.write_bytes(base64.b64decode(b64))
        print(f"  [{i}] {dest.relative_to(ROOT)}  "
              f"{dest.stat().st_size // 1024} KB")
        print(f"      generated_voice_id  {gid}")

    print(f"\n  {len(previews)} preview(s). LISTEN, then save the one you want:")
    print(f"      python design_voice_el.py --save <generated_voice_id>")
    print("  Nothing is permanent until you do — previews expire.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
