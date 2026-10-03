#!/usr/bin/env python3
"""
growth/daily_tick.py — Compatibility Bridge to the Autonomous Social Agent.

Redirects commands to the new agent architecture in agent/runner.py:
  python growth/daily_tick.py --status
  python growth/daily_tick.py --dry-run
  python growth/daily_tick.py --auto
"""

from __future__ import annotations

import argparse
import pathlib
import sys

# Ensure UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

GROWTH_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = GROWTH_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent.runner import run_tick, show_status


def main() -> int:
    ap = argparse.ArgumentParser(description="Seo-yeon Autonomous Agent Tick Bridge")
    ap.add_argument("--auto", action="store_true", help="Execute single autonomous tick")
    ap.add_argument("--dry-run", action="store_true", help="Simulate tick without publishing")
    ap.add_argument("--status", action="store_true", help="Display agent status dashboard")
    ap.add_argument("--growth-only", action="store_true", help="Legacy flag: runs agent tick")
    ap.add_argument("--reply-only", action="store_true", help="Legacy flag: runs agent tick")
    ap.add_argument("--fanvue-only", action="store_true", help="Legacy flag (Fanvue disabled)")
    args = ap.parse_args()

    if args.fanvue_only:
        print("[NOTICE] Fanvue integration has been permanently removed. Bluesky is the sole platform.")
        return 0

    if args.status:
        return show_status()

    return run_tick(dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
