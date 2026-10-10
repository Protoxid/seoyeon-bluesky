#!/usr/bin/env python3
"""
agent_runner.py — Root CLI entry point for Seo-yeon Han's Autonomous Bluesky Agent.

Usage:
  python agent_runner.py --status
  python agent_runner.py --dry-run
  python agent_runner.py --auto
  python agent_runner.py --daily-summary
  python agent_runner.py --check-master
  python agent_runner.py --consolidate
  python agent_runner.py --plan-week
  python agent_runner.py --force-action PUBLISH_TEXT_POST
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from agent.cli import main

if __name__ == "__main__":
    sys.exit(main())
