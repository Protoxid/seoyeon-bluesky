"""
Command Line Interface for the Orchestrator-Operator Agentic System.
Usage:
    python -m orchestrator "Add a health check test to scratch/test.py"
    python -m orchestrator --status
    python -m orchestrator --interactive
"""

import argparse
import sys
import time

from .config import AgentConfig
from .orchestrator import OrchestratorAgent
from .providers import create_provider


def print_status(config: AgentConfig):
    print("=" * 60)
    print("  ORCHESTRATOR-OPERATOR SYSTEM STATUS")
    print("=" * 60)

    # Check LM Studio
    print("\n[1] LM Studio (Local Engine):")
    print(f"    URL:           {config.lm_studio_url}")
    print(f"    Target Model:  {config.local_model}")
    t0 = time.time()
    lms_ok = config.check_lm_studio()
    elapsed = (time.time() - t0) * 1000
    if lms_ok:
        print(f"    Status:        ONLINE ({elapsed:.1f}ms latency)")
    else:
        print("    Status:        OFFLINE (Ensure LM Studio is running)")

    # Check Gemini
    print("\n[2] Google Gemini (Cloud Engine):")
    has_gemini = config.has_gemini()
    print(f"    Key Configured: {'YES' if has_gemini else 'NO / Missing (Set GEMINI_API_KEY)'}")
    print(f"    Flash Model:    {config.gemini_flash_model}")
    print(f"    Pro Model:      {config.gemini_pro_model}")

    # Check Claude
    print("\n[3] Anthropic Claude (Cloud Engine):")
    has_claude = config.has_claude()
    print(f"    Key Configured: {'YES' if has_claude else 'NO / Missing (Set ANTHROPIC_API_KEY)'}")
    print(f"    Opus Model:     {config.claude_opus_model}")
    print(f"    Sonnet Model:   {config.claude_sonnet_model}")

    # Active Routing
    print("\n[4] Active Routing Resolution:")
    print(f"    Default Orchestrator: {config.resolve_orchestrator_provider().upper()}")
    print(f"    Default Operator:     {config.resolve_operator_provider().upper()}")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Autonomous Orchestrator-Operator Agent Runner")
    parser.add_argument("goal", nargs="?", help="High-level goal for the agents to achieve")
    parser.add_argument("--status", action="store_true", help="Show system status and provider health")
    parser.add_argument("--orchestrator", choices=["auto", "gemini", "claude", "local"], default="auto", help="Force orchestrator provider")
    parser.add_argument("--operator", choices=["local", "claude", "gemini"], default="local", help="Force operator provider")
    parser.add_argument("-i", "--interactive", action="store_true", help="Run interactive prompt session")

    args = parser.parse_args()
    config = AgentConfig()

    if args.status:
        print_status(config)
        return

    if args.interactive:
        print_status(config)
        print("Starting interactive session. Type 'exit' or 'quit' to end.\n")
        while True:
            try:
                goal = input("Agent Goal > ").strip()
                if not goal:
                    continue
                if goal.lower() in ["exit", "quit", "q"]:
                    break
                run_mission(goal, config, args.orchestrator, args.operator)
            except (KeyboardInterrupt, EOFError):
                print("\nExiting.")
                break
        return

    if not args.goal:
        parser.print_help()
        print("\nTip: Run 'python -m orchestrator --status' to check your model connections.")
        sys.exit(1)

    run_mission(args.goal, config, args.orchestrator, args.operator)


def run_mission(goal: str, config: AgentConfig, orch_override: str, op_override: str):
    config.default_orchestrator = orch_override
    config.default_operator = op_override

    orch_prov_name = config.resolve_orchestrator_provider()
    op_prov_name = config.resolve_operator_provider()

    print(f"[Run] Initializing Orchestrator ({orch_prov_name}) & Operator ({op_prov_name})...")
    orch_provider = create_provider(orch_prov_name, config)
    agent = OrchestratorAgent(config, orchestrator_provider=orch_provider)

    report = agent.execute_mission(goal)
    print("=" * 60)
    print("MISSION SUMMARY REPORT")
    print(f"Goal:   {report.goal}")
    print(f"Status: {report.overall_status}")
    for res in report.ticket_results:
        print(f"\n- Ticket [{res.ticket_id}]: {res.status}")
        if res.files_affected:
            print(f"  Files: {', '.join(res.files_affected)}")
        print(f"  Summary: {res.summary[:200]}...")
    print("=" * 60)


if __name__ == "__main__":
    main()
