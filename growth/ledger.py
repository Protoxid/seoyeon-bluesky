#!/usr/bin/env python3
"""
ledger.py — Financial audit and platform attribution ledger.
Section 7 of PLAN.md / OPERATOR_BRIEF.md.

Design & Principles:
  - Append-only JSONL ledger: {date, platform, kind, eur, note}
  - Spend tracking: records all generation, model, compute, and advertising costs.
  - Revenue tracking: polls live Fanvue earnings and subscriber metrics via API.
  - Attribution tracking: reads Fanvue tracking links to map subscribers and gross/net
    revenue back to originating traffic channels (Instagram, X, Bluesky, Threads, Reddit, YouTube).
  - Daily unattended tick: `python ledger.py --tick`
  - Financial & attribution report: `python ledger.py --report`
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import sys
from typing import Any, Dict, List, Optional

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = ROOT if (ROOT / "personas").exists() else ROOT.parent
GROWTH_DIR = ROOT if ROOT.name == "growth" else PROJECT_ROOT / "growth"
PERSONAS_DIR = PROJECT_ROOT / "personas" / "seoyeon"

# Add directories to sys.path
for p in [str(GROWTH_DIR), str(PERSONAS_DIR), str(PROJECT_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from fanvue_api import FanvueClient, load_key, log_ledger
except ImportError:
    from growth.fanvue_api import FanvueClient, load_key, log_ledger

FINANCIAL_LEDGER = GROWTH_DIR / "financial_ledger.jsonl"


def append_entry(
    platform: str,
    kind: str,  # "spend", "revenue", "balance", "attribution"
    eur: float,
    note: str,
    details: Optional[Dict[str, Any]] = None,
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Appends an immutable financial row:
      {date, platform, kind, eur, note, details}
    """
    GROWTH_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "date": timestamp or dt.datetime.now(dt.timezone.utc).isoformat(),
        "platform": platform,
        "kind": kind,
        "eur": round(float(eur), 4),
        "note": note,
    }
    if details:
        entry["details"] = details

    with open(FINANCIAL_LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # Also log to audit ledger.jsonl
    log_ledger(f"ledger_{kind}", platform, f"€{eur:.2f}: {note}", surface="ledger")
    return entry


def load_ledger() -> List[Dict[str, Any]]:
    if not FINANCIAL_LEDGER.is_file():
        return []
    rows = []
    for line in FINANCIAL_LEDGER.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def tick() -> Dict[str, Any]:
    """
    Daily unattended financial snapshot:
      1. Reads current Fanvue account earnings and balance.
      2. Reads all 6 Fanvue tracking links for attribution deltas (clicks, subscribers, revenue).
      3. Records snapshot rows into financial_ledger.jsonl.
    """
    print("============================================================")
    print("FINANCIAL LEDGER — DAILY TICK & ATTRIBUTION SYNC")
    print(f"Timestamp: {dt.datetime.now(dt.timezone.utc).isoformat()}")
    print("============================================================\n")

    key = load_key()
    client = FanvueClient(api_key=key)

    # 1. Account earnings & balance
    print("  Querying Fanvue creator account (/v1/users/account)...")
    account_res = client.request("GET", "/v1/users/account")
    acc = account_res.get("account", {})
    earnings = acc.get("earnings", {})
    fans = acc.get("fans", {})

    # Fanvue reports amounts in cents (minor units)
    total_gross_eur = (earnings.get("total") or 0.0) / 100.0
    avail_balance_eur = (earnings.get("availableBalance") or 0.0) / 100.0
    subscribers = fans.get("subscribers", 0)
    followers = fans.get("followers", 0)

    append_entry(
        platform="fanvue",
        kind="balance",
        eur=avail_balance_eur,
        note=f"Fanvue balance snapshot: €{avail_balance_eur:.2f} avail, €{total_gross_eur:.2f} gross all-time ({subscribers} subs, {followers} followers)",
        details={
            "available_balance": avail_balance_eur,
            "total_gross": total_gross_eur,
            "subscribers": subscribers,
            "followers": followers,
        },
    )

    print(f"  Account status:    {acc.get('status', 'active')}")
    print(f"  Available Balance: €{avail_balance_eur:.2f}")
    print(f"  All-time Gross:    €{total_gross_eur:.2f}")
    print(f"  Subscribers:       {subscribers}")
    print(f"  Followers:         {followers}\n")

    # 2. Tracking links attribution
    print("  Querying Fanvue tracking links (GET /tracking-links)...")
    links_res = client.request("GET", "/tracking-links")
    links_data = links_res.get("data", []) if isinstance(links_res, dict) else []

    attribution_summary: Dict[str, Any] = {}
    for link in links_data:
        platform_name = (link.get("name") or "unknown").lower().strip()
        clicks = link.get("clicks", 0)
        eng = link.get("engagement", {})
        acquired_subs = eng.get("acquiredSubscribers", 0)
        acquired_followers = eng.get("acquiredFollowers", 0)
        earn = link.get("earnings", {})
        gross = (earn.get("totalGross") or 0.0) / 100.0
        net = (earn.get("totalNet") or 0.0) / 100.0

        attribution_summary[platform_name] = {
            "clicks": clicks,
            "acquired_subs": acquired_subs,
            "acquired_followers": acquired_followers,
            "net_eur": net,
            "gross_eur": gross,
            "link_url": link.get("linkUrl"),
        }

        # Append attribution snapshot
        append_entry(
            platform=platform_name,
            kind="attribution",
            eur=net,
            note=f"Attribution for {platform_name}: {clicks} clicks, {acquired_subs} subs, €{net:.2f} net revenue",
            details=attribution_summary[platform_name],
        )
        print(f"  {platform_name:10} -> {clicks:4} clicks | {acquired_subs:2} subs | €{net:6.2f} net revenue")

    print("\n  Snapshot appended to growth/financial_ledger.jsonl.")
    print("============================================================\n")
    return {
        "balance_eur": avail_balance_eur,
        "total_gross_eur": total_gross_eur,
        "subscribers": subscribers,
        "attribution": attribution_summary,
    }


def sync_legacy_spend() -> int:
    """
    Ingests recorded compute/model spend from personas/seoyeon/spend.jsonl.
    """
    spend_file = PERSONAS_DIR / "spend.jsonl"
    if not spend_file.is_file():
        return 0

    ledger_rows = load_ledger()
    known_notes = {r.get("note") for r in ledger_rows if r.get("kind") == "spend"}

    new_count = 0
    for line in spend_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue

        ts_val = item.get("ts")
        cost_eur = item.get("estimated", 0.0) or item.get("reported", 0.0) or 0.0
        model = item.get("model") or "compute"
        pool = item.get("pool") or "generation"
        note = f"Legacy spend: {pool} / {model} (cmd: {' '.join(item.get('cmd', []))[:50]})"

        if note in known_notes:
            continue

        time_iso = (
            dt.datetime.fromtimestamp(ts_val, tz=dt.timezone.utc).isoformat()
            if isinstance(ts_val, (int, float))
            else dt.datetime.now(dt.timezone.utc).isoformat()
        )
        append_entry(
            platform="compute",
            kind="spend",
            eur=cost_eur,
            note=note,
            details=item,
            timestamp=time_iso,
        )
        new_count += 1

    return new_count


def generate_report() -> None:
    """
    Prints a formatted financial & attribution report:
      - All-time Spend vs Revenue vs Net Profit/Loss.
      - Per-platform breakdown.
      - Tracking link conversion metrics.
    """
    rows = load_ledger()
    print("============================================================")
    print("SEO-YEON HAN (@syeon.hn) — FINANCIAL & ATTRIBUTION REPORT")
    print("============================================================\n")

    if not rows:
        print("  Ledger is empty. Run `python ledger.py --tick` to capture the first snapshot.")
        print("============================================================\n")
        return

    total_spend = 0.0
    spend_by_platform: Dict[str, float] = {}

    latest_balance = 0.0
    latest_gross = 0.0
    latest_subs = 0
    latest_attribution: Dict[str, Dict[str, Any]] = {}

    for r in rows:
        kind = r.get("kind")
        plat = r.get("platform", "other")
        eur = float(r.get("eur", 0.0))

        if kind == "spend":
            total_spend += eur
            spend_by_platform[plat] = spend_by_platform.get(plat, 0.0) + eur
        elif kind == "balance":
            latest_balance = eur
            det = r.get("details", {})
            latest_gross = det.get("total_gross", latest_gross)
            latest_subs = det.get("subscribers", latest_subs)
        elif kind == "attribution":
            latest_attribution[plat] = r.get("details", {})

    net_profit = latest_gross - total_spend

    print("1. OVERALL FINANCIAL HEALTH")
    print("------------------------------------------------------------")
    print(f"  All-time Gross Revenue: €{latest_gross:.2f}")
    print(f"  Available Cash Balance: €{latest_balance:.2f}")
    print(f"  Total Recorded Spend:   €{total_spend:.2f}")
    print(f"  Net Profit / Loss:      €{net_profit:+.2f}")
    print(f"  Active Subscribers:     {latest_subs}\n")

    print("2. SPEND BREAKDOWN")
    print("------------------------------------------------------------")
    if not spend_by_platform:
        print("  No spend recorded yet in financial ledger.")
    else:
        for p, amt in sorted(spend_by_platform.items(), key=lambda x: x[1], reverse=True):
            print(f"  {p:15}: €{amt:.2f}")
    print()

    print("3. PLATFORM ATTRIBUTION & FUNNEL METRICS (Tracking Links)")
    print("------------------------------------------------------------")
    print(f"  {'Platform':12} {'Clicks':>8} {'Followers':>10} {'Subscribers':>12} {'Net Revenue':>14}")
    print("  " + "-" * 58)

    platforms_order = ["instagram", "x", "bluesky", "threads", "reddit", "youtube"]
    for p in platforms_order:
        data = latest_attribution.get(p, {})
        clicks = data.get("clicks", 0)
        followers = data.get("acquired_followers", 0)
        subs = data.get("acquired_subs", 0)
        net_eur = data.get("net_eur", 0.0)
        print(f"  {p:12} {clicks:8d} {followers:10d} {subs:12d} {f'€{net_eur:.2f}':>14}")

    print("============================================================\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="Financial audit & attribution ledger.")
    ap.add_argument("--tick", action="store_true", help="Capture daily financial snapshot and tracking links attribution")
    ap.add_argument("--report", action="store_true", help="Print overall financial and attribution report")
    ap.add_argument("--spend", action="store_true", help="Record an explicit spend transaction")
    ap.add_argument("--platform", default="general", help="Platform/service name for spend (e.g. kie, runpod, meta_ads)")
    ap.add_argument("--eur", type=float, default=0.0, help="Amount in EUR")
    ap.add_argument("--note", default="", help="Description or justification for spend")
    ap.add_argument("--sync-spend", action="store_true", help="Sync recorded spend from personas spend.jsonl")
    args = ap.parse_args()

    if args.spend:
        if args.eur <= 0.0 or not args.note:
            sys.exit("  ! --spend requires --eur > 0 and a non-empty --note.")
        append_entry(platform=args.platform, kind="spend", eur=args.eur, note=args.note)
        print(f"  Recorded spend: €{args.eur:.2f} on {args.platform} ({args.note})")
        return 0

    if args.sync_spend:
        count = sync_legacy_spend()
        print(f"  Synced {count} new spend records to financial ledger.")
        return 0

    if args.tick:
        tick()
        return 0

    if args.report:
        generate_report()
        return 0

    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
