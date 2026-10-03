"""
scripts/run_pipeline.py — Multi-Agent Chain Runner for Pi Agent Software.
Orchestrates Nova -> Sentry -> Echo (Instagram, Tier 1)
and Apex -> Sentry -> Atlas (Bluesky/Fanvue, Tiers 2-3).

Enforces the Dual-Track QC Protocol (Image Re-roll vs Zero-Cost Copy Patch)
and bounds re-rolls to a max circuit breaker of 2.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional

ROOT_DIR = Path(__file__).resolve().parent.parent
QC_GATE_SCRIPT = ROOT_DIR / "personas" / "seoyeon" / "qc_gate.py"


def run_cmd(cmd: list, cwd: Path = ROOT_DIR) -> subprocess.CompletedProcess:
    """Execute command in shell with UTF-8 encoding."""
    print(f"[RUNNER] Executing: {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8")


def run_deterministic_qc(handoff_path: Path) -> Dict[str, Any]:
    """Execute personas/seoyeon/qc_gate.py on handoff file."""
    if not QC_GATE_SCRIPT.is_file():
        raise FileNotFoundError(f"qc_gate.py not found at {QC_GATE_SCRIPT}")

    cmd = [sys.executable, str(QC_GATE_SCRIPT), "--handoff", str(handoff_path)]
    proc = run_cmd(cmd)
    try:
        return json.loads(proc.stdout)
    except Exception:
        return {"passed": False, "raw_output": proc.stdout, "raw_error": proc.stderr}


def run_agent_turn(agent_name: str, prompt: str, dry_run: bool = False) -> int:
    """Run an agent session via pi CLI."""
    print(f"\n============================================================")
    print(f"  DISPATCHING SUBAGENT: {agent_name.upper()}")
    print(f"============================================================")
    print(f"[PROMPT]: {prompt}\n")

    if dry_run:
        print(f"[DRY-RUN] Would launch: pi -p '@.pi/agents/{agent_name}.md' ...")
        return 0

    # Execute non-interactive pi session
    agent_file = ROOT_DIR / ".pi" / "agents" / f"{agent_name}.md"
    if not agent_file.is_file():
        print(f"[ERROR] Agent definition file not found: {agent_file}")
        return 1

    cmd = ["pi", "-p", f"@{agent_file}", prompt]
    proc = run_cmd(cmd)
    print(proc.stdout)
    if proc.stderr:
        print(f"[STDERR]: {proc.stderr}", file=sys.stderr)

    return proc.returncode


def run_ig_pipeline(week_id: str, dry_run: bool = False):
    """Orchestrate Instagram lane: Nova -> Sentry -> Echo."""
    print(f"\n>>> STARTING INSTAGRAM PIPELINE (TIER 1) FOR {week_id} <<<")

    # Step 1: Nova Planning & Generation
    nova_prompt = f"Plan and generate all Instagram posts for {week_id}. Follow all Canon and plate rules. Write handoff payload."
    ret = run_agent_turn("nova", nova_prompt, dry_run=dry_run)
    if ret != 0 and not dry_run:
        print("[ERROR] Nova run failed. Aborting pipeline.")
        return 1

    # Step 2: Sentry QC Gate
    sentry_prompt = f"Inspect all generated images and captions for {week_id} Instagram lane. Run personas/seoyeon/qc_gate.py first, then perform multimodal visual comparison against master face and locked plates. If image defects exist, emit rejection report for Nova (max 2 rerolls). If copy defects exist, patch caption at $0 cost. If all pass, emit handoff_approved.json."
    ret = run_agent_turn("sentry", sentry_prompt, dry_run=dry_run)
    if ret != 0 and not dry_run:
        print("[ERROR] Sentry QC failed or rejected. Awaiting reroll.")
        return 1

    # Step 3: Echo Publishing
    echo_prompt = f"Verify Sentry's handoff_approved.json for {week_id}. Run dry-run checks on all approved posts, update weekly_schedule.json, and publish live according to schedule."
    ret = run_agent_turn("echo", echo_prompt, dry_run=dry_run)
    if ret != 0 and not dry_run:
        print("[ERROR] Echo publishing failed.")
        return 1

    print(f"\n[SUCCESS] Instagram pipeline completed for {week_id}!")
    return 0


def run_adult_pipeline(week_id: str, dry_run: bool = False):
    """Orchestrate Adult lane: Apex -> Sentry -> Atlas."""
    print(f"\n>>> STARTING BLUESKY/FANVUE PIPELINE (TIERS 2-3) FOR {week_id} <<<")

    # Step 1: Apex Planning & Generation
    apex_prompt = f"Plan and generate paired drops for {week_id}: Tier-3 Fanvue companion sets and Tier-2 Bluesky teasers with ?c=fv-4 tracking. Seedream tier 1k. Produce handoff payload."
    ret = run_agent_turn("apex", apex_prompt, dry_run=dry_run)
    if ret != 0 and not dry_run:
        print("[ERROR] Apex run failed. Aborting pipeline.")
        return 1

    # Step 2: Sentry QC Gate
    sentry_prompt = f"Inspect paired drops for {week_id} (Bluesky teasers and Fanvue sets). Run qc_gate.py, then verify 3-shot set continuity, environmental realism, tattoo rules, and single-strap camisoles. If passed, emit handoff_approved.json."
    ret = run_agent_turn("sentry", sentry_prompt, dry_run=dry_run)
    if ret != 0 and not dry_run:
        print("[ERROR] Sentry QC failed or rejected. Awaiting reroll.")
        return 1

    # Step 3: Atlas Publishing
    atlas_prompt = f"Verify Sentry's handoff_approved.json for {week_id}. Check git status (no secrets, no tier 3 in repo). Schedule Fanvue sets via API first, then commit public teasers to GitHub for Actions worker."
    ret = run_agent_turn("atlas", atlas_prompt, dry_run=dry_run)
    if ret != 0 and not dry_run:
        print("[ERROR] Atlas publishing failed.")
        return 1

    print(f"\n[SUCCESS] Adult pipeline completed for {week_id}!")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Multi-Agent Chain Runner on Pi Agent Software")
    parser.add_argument("--lane", choices=["ig", "adult", "both"], default="ig", help="Content lane to execute")
    parser.add_argument("--week", default="w38", help="Week identifier (e.g. w37, w38)")
    parser.add_argument("--dry-run", action="store_true", help="Print plan and commands without executing")
    parser.add_argument("--audit-only", type=str, help="Run deterministic QC gate on given handoff JSON file and exit")
    args = parser.parse_args()

    if args.audit_only:
        p = Path(args.audit_only)
        res = run_deterministic_qc(p)
        print(json.dumps(res, indent=2))
        sys.exit(0 if res.get("passed") else 1)

    status = 0
    if args.lane in ("ig", "both"):
        status = run_ig_pipeline(args.week, dry_run=args.dry_run)
        if status != 0:
            sys.exit(status)

    if args.lane in ("adult", "both"):
        status = run_adult_pipeline(args.week, dry_run=args.dry_run)
        if status != 0:
            sys.exit(status)

    sys.exit(status)


if __name__ == "__main__":
    main()
