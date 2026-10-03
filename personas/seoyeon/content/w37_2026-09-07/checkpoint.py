"""
checkpoint.py — one approved W37 render, moved from blocked -> entries.

Usage:
    python checkpoint.py <shot_id> <media_file> "<publish_at>"
Writes caps/<shot_id>.txt from handoff.json["captions"][shot_id], moves the
entry, refreshes the generation stats, and prints the OK line. Run it the
instant a render is approved: if the session dies afterwards, handoff.json is
still truthful and Echo-consumable.
"""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]      # personas/seoyeon
POOL = ROOT / "content" / "w37_2026-09-07"
HF = POOL / "handoff.json"
CAPS = ROOT / "caps"


def main(shot_id, media_file, publish_at):
    j = json.loads(HF.read_text(encoding="utf-8"))
    cap = (j.get("captions") or {}).get(shot_id)
    if not cap:
        sys.exit(f"no caption in handoff.json for {shot_id}")
    media = POOL / media_file
    if not media.is_file():
        sys.exit(f"missing media: {media}")

    CAPS.mkdir(exist_ok=True)
    cpath = CAPS / f"{shot_id}.txt"
    # Hashtags stay OUT of the body: PLATFORMS/instagram_ops never say whether
    # they go in the caption or a first comment, so the mechanism note stands.
    cpath.write_text(cap.rstrip() + "\n", encoding="utf-8", newline="\n")

    blocked = j.get("blocked") or []
    rest = [b for b in blocked if b.get("id") != shot_id]
    if len(rest) == len(blocked):
        print(f"  note: {shot_id} was not in blocked (added fresh)")
    entry = {
        "id": shot_id,
        "tier": 1,
        "lanes": ["instagram"],
        "media_file": str(media.relative_to(ROOT)),
        "caption_file": str(cpath.relative_to(ROOT)),
        "publish_at": publish_at,
        "render_approved": True,
        "renders_available": 1,
        "plate": None,
        "shot": None,
    }
    old = next((b for b in blocked if b.get("id") == shot_id), {})
    for k in ("plate", "shot", "aspect"):
        if old.get(k):
            entry[k] = old[k]
    j["blocked"] = rest
    ids = [e["id"] for e in j.get("entries") or []]
    if shot_id in ids:
        j["entries"][ids.index(shot_id)] = entry
    else:
        j.setdefault("entries", []).append(entry)
    j["entries"].sort(key=lambda e: e.get("publish_at") or "")

    n = int((j.get("generation") or {}).get("images_generated") or 0)
    g = j.setdefault("generation", {})
    g["images_generated"] = max(n, 0)   # refreshed by stats.py after each run
    HF.write_text(json.dumps(j, ensure_ascii=False, indent=2) + "\n",
                  encoding="utf-8", newline="\n")
    print(f"OK {shot_id} {media.relative_to(ROOT)} 1")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2], sys.argv[3])
