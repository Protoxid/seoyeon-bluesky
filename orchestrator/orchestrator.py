"""
Orchestrator Agent implementation.
Responsible for:
1. High-level goal analysis & workspace reconnaissance.
2. Generating a structured execution plan (subtasks / tickets).
3. Supervised delegation to the Operator.
4. Reviewing Operator outputs against real artifacts.
"""

from dataclasses import dataclass, field
import json
import re
from typing import Any, Dict, List, Optional

from .config import AgentConfig
from .operator import OperatorAgent, TicketExecutionResult
from .providers import BaseProvider, create_provider


ORCHESTRATOR_PLANNER_PROMPT = """You are the Orchestrator, an elite system architect and project director.
Your role is to analyze a high-level technical goal and produce an explicit, step-by-step execution plan composed of atomic work tickets for the Operator.

GUIDELINES:
1. Break complex goals into small, verifiable tickets (e.g. 1 to 4 tickets).
2. Each ticket must have:
   - "id": "ticket_1", "ticket_2", etc.
   - "title": Short descriptive title.
   - "target_files": List of files to be touched.
   - "instructions": Exact instructions for the Operator, referencing the "SAY ONLY THE DELTA" principle.
   - "acceptance_criteria": Specific validation steps (e.g. run a test command, assert file content).
3. Do NOT attempt to execute tools yourself. You are the planner and auditor.

OUTPUT FORMAT:
Return ONLY valid JSON matching this schema:
{
  "goal_summary": "Summary of what will be achieved",
  "tickets": [
    {
      "id": "ticket_1",
      "title": "Title",
      "target_files": ["path/to/file.py"],
      "instructions": "Detailed instructions...",
      "acceptance_criteria": "How to verify..."
    }
  ]
}
"""


@dataclass
class MissionReport:
    goal: str
    orchestrator_provider: str
    operator_provider: str
    plan: Dict[str, Any]
    ticket_results: List[TicketExecutionResult] = field(default_factory=list)
    overall_status: str = "COMPLETED"


class OrchestratorAgent:
    def __init__(
        self,
        config: AgentConfig,
        orchestrator_provider: Optional[BaseProvider] = None,
        operator_agent: Optional[OperatorAgent] = None,
    ):
        self.config = config
        self.prov_name = config.resolve_orchestrator_provider()
        self.provider = orchestrator_provider or create_provider(self.prov_name, config)
        self.operator = operator_agent or OperatorAgent(config)

    def plan(self, goal: str) -> Dict[str, Any]:
        """Generate a structured execution plan for the goal."""
        messages = [
            {"role": "system", "content": ORCHESTRATOR_PLANNER_PROMPT},
            {"role": "user", "content": f"Create an execution plan for this goal:\n{goal}"},
        ]
        resp = self.provider.generate(messages=messages, temperature=0.1)

        # Parse JSON from response
        text = resp.content.strip()
        # Clean markdown code blocks if wrapped
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\n", "", text)
            text = re.sub(r"\n```$", "", text)

        try:
            plan_data = json.loads(text)
            return plan_data
        except json.JSONDecodeError:
            # Fallback: simple single ticket
            return {
                "goal_summary": goal,
                "tickets": [
                    {
                        "id": "ticket_1",
                        "title": "Execute Goal",
                        "target_files": [],
                        "instructions": goal,
                        "acceptance_criteria": "Verify required changes or outputs exist.",
                    }
                ],
            }

    def execute_mission(self, goal: str) -> MissionReport:
        """Run the complete Orchestrator -> Operator lifecycle."""
        plan_data = self.plan(goal)
        tickets = plan_data.get("tickets", [])
        report = MissionReport(
            goal=goal,
            orchestrator_provider=self.prov_name,
            operator_provider=self.config.resolve_operator_provider(),
            plan=plan_data,
        )

        print(f"\n[Orchestrator ({self.prov_name})] Plan formulated with {len(tickets)} tickets.")
        print(f"Goal: {plan_data.get('goal_summary', goal)}")

        for t in tickets:
            print(f"\n---> Dispatching [{t.get('id')}] {t.get('title')} to Operator...")
            res = self.operator.execute_ticket(t)
            report.ticket_results.append(res)
            print(f"<--- Result from Operator: {res.status}")
            print(f"     Files affected: {', '.join(res.files_affected) if res.files_affected else 'none'}")
            print(f"     Steps taken: {res.steps_taken}")

            if res.status not in ["SUCCESS", "COMPLETED"]:
                print(f"[Orchestrator] Warning: Ticket {t.get('id')} reported non-success: {res.status}")

        print(f"\n[Orchestrator] Mission complete. All tickets processed.\n")
        return report
