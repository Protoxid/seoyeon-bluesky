"""
gen_meta.py — batch-2 handoff meta helper (Nova, W37). NOT shared pipeline code.

Two jobs checkpoint.py deliberately does not do:
  --tag-captions   append the inline hashtag line to the BATCH-2 captions in
                   handoff.json["captions"] (owner ruling 6 Sep: tags go inline,
                   matching week-2. Batch 1 is backfilled by the owner — untouched
                   here).
  --stats          write absolute generation numbers (images_generated, spend_usd,
                   rerolls, approved, batch). Absolute, not incremental, so a
                   re-run after a quota wall cannot double-count.

Run AFTER checkpoint.py for a shot, with the totals as of that approval.
"""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
HF = ROOT / "content" / "w37_2026-09-07" / "handoff.json"

TAGS = "#seongsu #seoul #daily #filmphoto #everyday"
BATCH2 = ["w37_studio_after", "w37_jieun_roof", "w37_market_peaches",
          "w37_table_sunday"]


def main():
    a = sys.argv[1:]
    j = json.loads(HF.read_text(encoding="utf-8"))
    if a and a[0] == "--tag-captions":
        caps = j.setdefault("captions", {})
        for k in BATCH2:
            v = caps.get(k)
            if not v:
                sys.exit(f"no caption for {k}")
            if TAGS not in v:
                caps[k] = v.rstrip() + "\n\n" + TAGS
                print(f"  tagged {k}")
            else:
                print(f"  already tagged {k}")
    elif a and a[0] == "--stats":
        d = {}
        for pair in a[1:]:
            k, v = pair.split("=", 1)
            d[k] = float(v) if "." in v else int(v)
        g = j.setdefault("generation", {})
        g.update(d)
        print("  generation:", json.dumps({k: g[k] for k in d}, ensure_ascii=False))
    else:
        sys.exit(__doc__)
    HF.write_text(json.dumps(j, ensure_ascii=False, indent=2) + "\n",
                  encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
