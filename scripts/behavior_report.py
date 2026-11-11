"""Summarize Seo-yeon's recent behavior from the encrypted runtime state.

Usage:
  DATA_ENCRYPTION_KEY=... python scripts/behavior_report.py --fetch-state [--days 7]
  python scripts/behavior_report.py --data-dir path/to/decrypted/data [--days 7]

--fetch-state reads the latest `state` branch commit into a temporary directory and decrypts it there;
the local data/ directory is never modified. Output contains counts and her own public posts only,
never replies to or messages from other people.
"""
import argparse
import collections
import datetime as dt
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]

TOPICS = {
    "pilates/body": r"pilates|필라테스|reformer|리포머|class|수업|cue|큐잉|anatomy|해부|muscle|근육|spine|척추|mat\b|매트|stretch|허리|back\b|legs|다리",
    "food/home": r"cook|요리|kimbap|김밥|rice|밥|soup|국|kitchen|부엌|fridge|냉장고|tea|차\b|coffee|커피|radiator|blanket|이불|room|방",
    "money/work": r"money|돈|rent|월세|savings|저축|price|가격|marketing|마케팅|job|일자리|퇴사|resign|budget|생활비",
    "people": r"jieun|지은|mom|엄마|mother|family|가족|friend|친구|classmate|동기|daegu|대구|busan|부산",
    "culture": r"film|movie|영화|book|책|novel|소설|music|음악|song|노래|playlist|album|exhibition|전시",
    "city/weather": r"street|거리|bus|버스|subway|지하철|seongsu|성수|rain|비\b|snow|눈\b|cold|추|sky|하늘|window|창",
    "language/type": r"hangul|한글|typography|타이포|font|폰트|lettering|word\b|단어|translation|번역|spelling|맞춤법",
}


def fetch_state(target: pathlib.Path):
    subprocess.run(["git", "fetch", "--quiet", "--depth=1", "origin", "refs/heads/state:refs/remotes/origin/state"],
                   cwd=ROOT, check=True)
    blob = subprocess.run(["git", "show", "origin/state:vault.enc"], cwd=ROOT, check=True, capture_output=True).stdout
    (target / "vault.enc").write_bytes(blob)
    sys.path.insert(0, str(ROOT))
    from agent.vault import PrivateVault
    vault = PrivateVault(target / ".vault", target / "vault.enc", data_dir=target)
    if not vault.load_vault():
        raise SystemExit("Could not decrypt the state bundle (check DATA_ENCRYPTION_KEY).")


def field(row, name):
    match = re.search(rf'"{name}": "([^"]*)"', json.dumps(row, ensure_ascii=False).replace('\\"', '"'))
    return match.group(1) if match else None


def report(data_dir: pathlib.Path, days: int):
    log = data_dir / "logs" / "tick_history.jsonl"
    rows = []
    if log.exists():
        for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                rows.append(json.loads(line))
            except ValueError:
                continue
    since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)).isoformat()
    rows = [r for r in rows if str(r.get("dry_run")) != "True" and r.get("ts", "") >= since]
    print(f"Ticks in the last {days} days: {len(rows)}")

    per_day = collections.defaultdict(collections.Counter)
    for r in rows:
        if r.get("executed") in (True, "True"):
            per_day[r["ts"][:10]][r.get("action", "?")] += 1
    print("\nExecuted actions per day (UTC):")
    for day in sorted(per_day):
        print(f"  {day}  " + ", ".join(f"{a}={n}" for a, n in per_day[day].most_common()))

    for label, name in (("Selection", "selection"), ("Original-post pass", "original_idea_status"),
                        ("Post kind", "post_kind"), ("Drafting status", "discussion_status")):
        counts = collections.Counter(field(r, name) or r.get(name) for r in rows)
        counts.pop(None, None)
        if counts:
            print(f"\n{label}: " + ", ".join(f"{k}={v}" for k, v in counts.most_common(10)))

    context = data_dir / "memory" / "recent_context.json"
    posts = []
    if context.exists():
        posts = [p for p in json.loads(context.read_text(encoding="utf-8")).get("posts", [])
                 if str(p.get("created_at", "")) >= since[:10]]
    print(f"\nOwn posts kept in recent context: {len(posts)} (photos: {sum(1 for p in posts if p.get('has_image'))})")
    topic_counts = collections.Counter()
    for p in posts:
        text = p.get("text", "").lower()
        hits = [t for t, pattern in TOPICS.items() if re.search(pattern, text)]
        topic_counts.update(hits or ["other"])
    if topic_counts:
        print("Topic mix (a post can count in several): " + ", ".join(f"{k}={v}" for k, v in topic_counts.most_common()))
        top, top_n = topic_counts.most_common(1)[0]
        if len(posts) >= 5 and top_n / len(posts) > 0.6:
            print(f"  ! possible fixation: '{top}' appears in {top_n}/{len(posts)} posts")
    print("\nLatest own posts:")
    for p in posts[:10]:
        print("  - " + p.get("text", "").replace("\n", " ")[:200])


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--fetch-state", action="store_true")
    parser.add_argument("--data-dir", type=pathlib.Path)
    parser.add_argument("--days", type=int, default=7)
    args = parser.parse_args()
    if args.fetch_state:
        if not os.environ.get("DATA_ENCRYPTION_KEY"):
            raise SystemExit("Set DATA_ENCRYPTION_KEY in the environment (never pass it as an argument).")
        with tempfile.TemporaryDirectory(prefix="seoyeon-report-") as tmp:
            fetch_state(pathlib.Path(tmp))
            report(pathlib.Path(tmp), args.days)
    else:
        report(args.data_dir or ROOT / "data", args.days)


if __name__ == "__main__":
    main()
