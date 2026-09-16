#!/usr/bin/env python3
"""
growth/daily_tick.py — Unified Master Growth & Orchestration Suite for @syeonhn / @syeon.hn.

Orchestrates the complete cross-platform autonomous ecosystem:
  1. Synchronized Campaign Teaser Dispatch (campaign_orchestrator.py)
  2. Spontaneous Organic Thoughts (bsky_text_post.py)
  3. Cold-Start Follower Growth & Audience Sourcing (bsky_growth_engine.py)
  4. High-Leverage Outbound Community Engagement (bsky_engage.py)
  5. Two-Way Inbound Reply & Mention Processing (bsky_reply_worker.py)
  6. Fanvue Welcome DMs & Subscriber Chat Retention (fanvue_chat_agent.py)
  7. Financial & Attribution Ledger Sync (ledger.py)

Usage:
  python growth/daily_tick.py --dry-run      # Complete safe simulation
  python growth/daily_tick.py                # Live execution of all loops
  python growth/daily_tick.py --status       # Cross-platform live metrics dashboard
  python growth/daily_tick.py --growth-only  # Run Bluesky follower growth loop only
  python growth/daily_tick.py --reply-only   # Run inbound reply worker only
  python growth/daily_tick.py --fanvue-only  # Run Fanvue retention/welcome loop only
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import pathlib
import subprocess
import sys
from typing import List, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

GROWTH_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = GROWTH_DIR.parent


def run_cmd(cmd: List[str], cwd: pathlib.Path) -> Tuple[int, str, str]:
    """Executes a python helper cleanly with UTF-8 capture."""
    full_cmd = [sys.executable, "-Xutf8"] + cmd
    res = subprocess.run(
        full_cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return res.returncode, res.stdout, res.stderr


def display_dashboard() -> int:
    print("\n" + "=" * 70)
    print("  SEO-YEON HAN (@syeonhn / @syeon.hn) — MASTER AGENT STATUS")
    print("=" * 70)

    # 1. Bluesky Growth Engine Status
    print("\n[Bluesky Growth & Follower Acquisition]")
    code, out, _ = run_cmd(["bsky_growth_engine.py", "--status"], cwd=GROWTH_DIR)
    if code == 0:
        for line in out.strip().splitlines():
            if any(k in line for k in ("Live Followers:", "Live Follows:", "Live Total Posts:", "Follows Today:")):
                print(f"  {line.strip()}")

    # 2. Bluesky Engagement & Inbound Reply Status
    print("\n[Bluesky Inbound & Outbound Engagement]")
    code, out, _ = run_cmd(["bsky_engage.py", "--status"], cwd=GROWTH_DIR)
    if code == 0:
        for line in out.strip().splitlines():
            if any(k in line for k in ("Today's Comments:", "Gate Reason:")):
                print(f"  {line.strip()}")

    code, out, _ = run_cmd(["bsky_reply_worker.py", "--status"], cwd=GROWTH_DIR)
    if code == 0:
        for line in out.strip().splitlines():
            if any(k in line for k in ("Replies Executed Today:", "Total Inbound Replies")):
                print(f"  {line.strip()}")

    # 3. Fanvue Status
    print("\n[Fanvue Monetization & Sanctuary]")
    code, out, _ = run_cmd(["fanvue_chat_agent.py", "--status"], cwd=GROWTH_DIR)
    if code == 0:
        for line in out.strip().splitlines():
            if any(k in line for k in ("Creator Handle:", "Total Welcomed:", "Total Chat Replies:", "Subscribers:", "Balance:")):
                print(f"  {line.strip()}")

    # 4. Campaign Drops
    print("\n[Scheduled Campaign Drops (W39 & W40)]")
    code, out, _ = run_cmd(["campaign_orchestrator.py", "--status"], cwd=GROWTH_DIR)
    if code == 0:
        for line in out.strip().splitlines():
            if any(k in line for k in ("Total drops:", "Published:", "Pending:", "Matrix validation:")):
                print(f"  {line.strip()}")

    print("\n" + "=" * 70 + "\n")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Unified master growth & orchestration runner for Seo-yeon Han"
    )
    parser.add_argument("--dry-run", action="store_true", help="Simulate all operations without remote writes")
    parser.add_argument("--status", action="store_true", help="Display full cross-platform health dashboard")
    parser.add_argument("--growth-only", action="store_true", help="Run Bluesky follower growth harvester only")
    parser.add_argument("--reply-only", action="store_true", help="Run Bluesky inbound reply worker only")
    parser.add_argument("--fanvue-only", action="store_true", help="Run Fanvue welcome & chat retention only")
    parser.add_argument("--campaign-only", action="store_true", help="Run campaign teaser dispatcher only")
    args = parser.parse_args()

    if args.status:
        return display_dashboard()

    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mode_str = "[DRY-RUN] (Safe Simulation)" if args.dry_run else "[LIVE EXECUTION]"
    print("=" * 70)
    print(f"MASTER GROWTH TICK — {now}")
    print(f"Mode: {mode_str}")
    print("=" * 70)

    run_all = not (args.growth_only or args.reply_only or args.fanvue_only or args.campaign_only)
    report_items = []

    # 1. Campaign Drops
    if run_all or args.campaign_only:
        print("\n[1/6] Campaign Teaser Dispatcher (campaign_orchestrator.py)...")
        cmd = ["campaign_orchestrator.py", "--auto"]
        if args.dry_run:
            cmd.append("--dry-run")
        code, out, err = run_cmd(cmd, cwd=GROWTH_DIR)
        if code == 0:
            print("  [OK] Campaign check complete.")
            for line in out.strip().splitlines()[-3:]:
                print(f"    {line}")
            report_items.append(("Campaign Drops", "Success", "Checked scheduled slots"))
        else:
            print(f"  [ERROR] Campaign dispatcher failed: {err.strip()[:180]}")
            report_items.append(("Campaign Drops", "Error", err.strip()[:80]))

    # 2. Organic Micro-Thoughts
    if run_all:
        print("\n[2/6] Spontaneous Thoughts Dispatcher (bsky_text_post.py)...")
        cmd = ["bsky_text_post.py", "--auto"]
        if args.dry_run:
            cmd.append("--dry-run")
        code, out, err = run_cmd(cmd, cwd=GROWTH_DIR)
        if code == 0:
            print("  [OK] Organic text check complete.")
            for line in out.strip().splitlines()[-2:]:
                print(f"    {line}")
            report_items.append(("Lyra Thoughts", "Success", "Evaluated cadence"))
        else:
            print(f"  [ERROR] Thoughts dispatcher failed: {err.strip()[:180]}")
            report_items.append(("Lyra Thoughts", "Error", err.strip()[:80]))

    # 3. Follower Growth & Audience Harvester
    if run_all or args.growth_only:
        print("\n[3/6] Audience Sourcing & Follower Growth (bsky_growth_engine.py)...")
        cmd = ["bsky_growth_engine.py", "--auto"]
        if args.dry_run:
            cmd.append("--dry-run")
        code, out, err = run_cmd(cmd, cwd=GROWTH_DIR)
        if code == 0:
            print("  [OK] Follower growth cycle complete.")
            for line in out.strip().splitlines()[-3:]:
                print(f"    {line}")
            report_items.append(("Follower Harvester", "Success", "Discovered & followed targets"))
        else:
            print(f"  [ERROR] Follower harvester failed: {err.strip()[:180]}")
            report_items.append(("Follower Harvester", "Error", err.strip()[:80]))

    # 4. Outbound Community Engagement
    if run_all:
        print("\n[4/6] Outbound Community Engagement (bsky_engage.py)...")
        cmd = ["bsky_engage.py", "--auto"]
        if args.dry_run:
            cmd.append("--dry-run")
        code, out, err = run_cmd(cmd, cwd=GROWTH_DIR)
        if code == 0:
            print("  [OK] Outbound comment check complete.")
            for line in out.strip().splitlines()[-2:]:
                print(f"    {line}")
            report_items.append(("Outbound Comments", "Success", "Paced active comments"))
        else:
            print(f"  [ERROR] Outbound engagement failed: {err.strip()[:180]}")
            report_items.append(("Outbound Comments", "Error", err.strip()[:80]))

    # 5. Inbound Two-Way Reply Worker
    if run_all or args.reply_only:
        print("\n[5/6] Inbound Two-Way Reply Worker (bsky_reply_worker.py)...")
        cmd = ["bsky_reply_worker.py", "--auto"]
        if args.dry_run:
            cmd.append("--dry-run")
        code, out, err = run_cmd(cmd, cwd=GROWTH_DIR)
        if code == 0:
            print("  [OK] Inbound reply check complete.")
            for line in out.strip().splitlines()[-3:]:
                print(f"    {line}")
            report_items.append(("Inbound Replies", "Success", "Processed follower notifications"))
        else:
            print(f"  [ERROR] Inbound reply worker failed: {err.strip()[:180]}")
            report_items.append(("Inbound Replies", "Error", err.strip()[:80]))

    # 6. Fanvue Retention & Chat Agent
    if run_all or args.fanvue_only:
        print("\n[6/6] Fanvue Welcome DMs & Chat Retention (fanvue_chat_agent.py)...")
        cmd = ["fanvue_chat_agent.py", "--auto"]
        if args.dry_run:
            cmd.append("--dry-run")
        code, out, err = run_cmd(cmd, cwd=GROWTH_DIR)
        if code == 0:
            print("  [OK] Fanvue retention loop complete.")
            for line in out.strip().splitlines()[-3:]:
                print(f"    {line}")
            report_items.append(("Fanvue Retention", "Success", "Welcome DMs & chats synced"))
        else:
            print(f"  [ERROR] Fanvue retention failed: {err.strip()[:180]}")
            report_items.append(("Fanvue Retention", "Error", err.strip()[:80]))

    # Sync Financial & Activity Ledger
    print("\nSyncing Master Ledger (ledger.py)...")
    code, _, _ = run_cmd(["ledger.py", "--tick"], cwd=GROWTH_DIR)

    # Operator Summary
    print("\n" + "=" * 70)
    print("MASTER TICK EXECUTION SUMMARY")
    print("=" * 70)
    for name, status, detail in report_items:
        print(f"  - {name:<24}: [{status}] {detail}")
    print("=" * 70 + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
