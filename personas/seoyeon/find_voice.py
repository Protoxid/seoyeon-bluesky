#!/usr/bin/env python3
"""
find_voice.py — audition REAL voices from the ElevenLabs library.

    python find_voice.py                          list Korean female voices
    python find_voice.py --render                 speak the hook in each
    python find_voice.py --add <voice_id> --name seoyeon

WHY THIS, AFTER THREE ROUNDS OF DESIGNING ONE. The designed voice failed on all
three counts at once — accent not Korean, not natural, robotic — and that is
not a settings problem. `stab-040` was the least bad of nine rows, which is not
the same as good.

A DESIGNED VOICE IS SYNTHESISED FROM A DESCRIPTION. A LIBRARY VOICE IS A REAL
HUMAN RECORDING. For accent authenticity that is not a close call: a real
Korean speaker beats a paragraph describing one, and "not natural" and
"robotic" are exactly the failures a real recording does not have.

AND THE BRIEF WAS ASKING FOR THE ROBOT. It said "relaxed and slightly uneven —
some words run together, some trail off". You cannot prompt naturalness by
requesting imperfection: a TTS told to be uneven produces ARTEFACTS, and
artefacts are what robotic sounds like. Unevenness belongs in the WRITING,
where the discourse markers already put it.

THE TRADE, STATED HONESTLY: a library voice is not exclusively hers. That was
the objection that sent us to Voice Design in the first place, and it was
reasonable. It is also now measurably the wrong side of the trade — a unique
voice that does not sound like a person is worth less than a shared one that
does. Nothing here is cloned from anyone: these are voices their owners
published to the library for exactly this use.
"""
from __future__ import annotations
import argparse, json, pathlib, sys, urllib.error, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from make_voice_el import read_first                   # noqa: E402
from make_voice import SCRIPT                          # noqa: E402
import ffbin                                           # noqa: E402

BASE = "https://api.elevenlabs.io/v1"
LINE = dict(SCRIPT)["hook"]


def get(path: str, key: str, **params) -> dict:
    q = urllib.parse.urlencode({k: v for k, v in params.items()
                                if v not in (None, "")})
    req = urllib.request.Request(f"{BASE}/{path}?{q}",
                                 headers={"xi-api-key": key})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"  ! HTTP {e.code}: {e.read()[:300].decode(errors='replace')}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--language", default="ko")
    ap.add_argument("--gender", default="female")
    ap.add_argument("--age", default=None, help="young | middle_aged | old")
    ap.add_argument("--search", default=None)
    ap.add_argument("--limit", type=int, default=12)
    ap.add_argument("--render", action="store_true",
                    help="speak the hook with each one, into voice/library/")
    ap.add_argument("--model", default="eleven_multilingual_v2")
    ap.add_argument("--add", default=None, help="a public voice_id to keep")
    ap.add_argument("--public-owner", default=None)
    ap.add_argument("--name", default="seoyeon")
    a = ap.parse_args()

    key = read_first("ELEVENLABS_API_KEY", "ELEVENLABS_KEY", "XI_API_KEY")
    if not key:
        print("  ! no key in elevenlabs_key.txt")
        return 2

    if a.add:
        # A library voice has to be added to the account before text-to-speech
        # will accept it. Adding needs the OWNER id as well as the voice id,
        # which is why both are printed in the listing.
        if not a.public_owner:
            print("  ! --add also needs --public-owner (shown in the listing)")
            return 1
        req = urllib.request.Request(
            f"{BASE}/voices/add/{a.public_owner}/{a.add}",
            data=json.dumps({"new_name": a.name}).encode(), method="POST",
            headers={"xi-api-key": key, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                d = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            print(f"  ! HTTP {e.code}: {e.read()[:300].decode(errors='replace')}")
            return 1
        vid = d.get("voice_id")
        print(f"  added as {a.name}\n  voice_id  {vid}")
        if vid:
            (ROOT / "voice_id.txt").write_text(vid + "\n", encoding="utf-8")
            print("  voice_id.txt updated — this is now canon")
        return 0

    d = get("shared-voices", key, page_size=a.limit, language=a.language,
            gender=a.gender, age=a.age, search=a.search)
    voices = d.get("voices") or []
    if not voices:
        print(f"  no voices for language={a.language} gender={a.gender}. "
              f"Response keys: {sorted(d)}")
        return 1

    print(f"  {len(voices)} voice(s), language={a.language} "
          f"gender={a.gender}\n")
    out = ROOT / "voice" / "library"
    if a.render:
        out.mkdir(parents=True, exist_ok=True)

    for i, v in enumerate(voices, 1):
        vid = v.get("voice_id", "?")
        owner = v.get("public_owner_id", "?")
        print(f"  [{i:2}] {v.get('name', '?'):<22} "
              f"accent={v.get('accent', '?'):<12} age={v.get('age', '?')}")
        print(f"       voice_id {vid}")
        print(f"       owner    {owner}")
        desc = (v.get("description") or "").strip().replace("\n", " ")
        if desc:
            print(f"       {desc[:100]}")
        if not a.render:
            continue
        body = {"text": LINE, "model_id": a.model,
                "voice_settings": {"stability": 0.40, "similarity_boost": 0.8,
                                   "style": 0.10, "speed": 1.0}}
        req = urllib.request.Request(
            f"{BASE}/text-to-speech/{vid}?output_format=mp3_44100_128",
            data=json.dumps(body).encode(), method="POST",
            headers={"xi-api-key": key, "Content-Type": "application/json",
                     "Accept": "audio/mpeg"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                audio = r.read()
        except urllib.error.HTTPError as e:
            # A library voice usually has to be ADDED before it can speak.
            # That is a fact worth reporting, not a reason to stop the listing.
            print(f"       (cannot speak yet: HTTP {e.code} — add it first)")
            continue
        dest = out / f"{i:02d}_{v.get('name', 'v')}.mp3".replace(" ", "_")
        dest.write_bytes(audio)
        print(f"       -> {dest.relative_to(ROOT)}  {ffbin.duration(dest):.1f}s")

    print("\n  Listen, then keep one:")
    print("      python find_voice.py --add <voice_id> --public-owner <owner>")
    print("  That writes voice_id.txt. The canon delivery settings in")
    print("  make_voice_el.py were tuned on the OLD voice — re-run")
    print("  voice_matrix.py against the new one before trusting them.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
