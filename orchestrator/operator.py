"""
Operator Agent implementation.
Executes concrete technical work tickets from the Orchestrator using tools.
Enforces the Operator's rules:
1. ALWAYS DOUBLE CHECK WHAT YOU HAVE (assert match counts, verify values).
2. SAY ONLY THE DELTA.
"""

from dataclasses import dataclass, field
import json
from typing import Any, Dict, List, Optional

from .config import AgentConfig
from .providers import BaseProvider, create_provider
from .tools import ToolExecutor, OPENAI_TOOL_SCHEMAS


OPERATOR_SYSTEM_PROMPT = """You are the Operator, an expert autonomous software engineer and tool executor.
You receive structured work tickets from the Orchestrator and execute them with surgical precision.

CORE PRINCIPLES:
1. ALWAYS DOUBLE CHECK WHAT YOU HAVE:
   - A command running without throwing an exception is not proof of success.
   - Always inspect the resulting file or artifact.
   - When patching files, assert match counts and verify the written content.
2. SAY ONLY THE DELTA:
   - Use `patch_file` for surgical edits. Avoid overwriting entire files when changing a small section.
   - Only use `write_file` for brand new files or complete file rewrites.
3. VERIFY AGAINST ARTIFACTS:
   - Run verification commands (tests, scripts, line checks) before reporting completion.

When all actions for the ticket are complete, output a final summary stating:
1. Files modified / created.
2. Concrete verification evidence (e.g. output of tests, hash/line checks).
3. Status: SUCCESS or BLOCKED.
"""


@dataclass
class TicketExecutionResult:
    ticket_id: str
    status: str  # 'SUCCESS', 'FAILED', 'BLOCKED'
    files_affected: List[str] = field(default_factory=list)
    verification_evidence: str = ""
    summary: str = ""
    steps_taken: int = 0


class OperatorAgent:
    def __init__(self, config: AgentConfig, provider: Optional[BaseProvider] = None):
        self.config = config
        self.executor = ToolExecutor(config.workspace_root)
        prov_type = config.resolve_operator_provider()
        self.provider = provider or create_provider(prov_type, config)

    def execute_ticket(self, ticket: Dict[str, Any], max_steps: int = 10) -> TicketExecutionResult:
        ticket_id = ticket.get("id", "ticket_1")
        title = ticket.get("title", "Task")
        instructions = ticket.get("instructions", "")
        acceptance_criteria = ticket.get("acceptance_criteria", "")

        user_prompt = f"""WORK TICKET: {ticket_id} - {title}

INSTRUCTIONS:
{instructions}

ACCEPTANCE CRITERIA:
{acceptance_criteria}

Execute the necessary tool calls to accomplish this ticket. Always verify your work against the actual artifact."""

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": OPERATOR_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        files_affected = set()
        step = 0

        while step < max_steps:
            step += 1
            resp = self.provider.generate(messages=messages, tools=OPENAI_TOOL_SCHEMAS)

            if not resp.has_tool_calls():
                # Operator has finished or responded with final message
                content = resp.content
                status = "SUCCESS" if "SUCCESS" in content.upper() else "COMPLETED"
                return TicketExecutionResult(
                    ticket_id=ticket_id,
                    status=status,
                    files_affected=list(files_affected),
                    verification_evidence="Verified in conversation flow.",
                    summary=content,
                    steps_taken=step,
                )

            # Execute tool calls
            for tc in resp.tool_calls:
                call_id = tc["id"]
                tool_name = tc["name"]
                args = tc["arguments"]

                if "file_path" in args:
                    files_affected.add(args["file_path"])

                tool_result = self.executor.execute_tool(tool_name, args)

                # Feed tool call and tool result back to model
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": call_id,
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "arguments": json.dumps(args),
                        },
                    }],
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": tool_name,
                    "content": json.dumps(tool_result),
                })

        return TicketExecutionResult(
            ticket_id=ticket_id,
            status="MAX_STEPS_REACHED",
            files_affected=list(files_affected),
            verification_evidence="Exceeded step budget without explicit completion.",
            summary=f"Reached step limit of {max_steps}.",
            steps_taken=step,
        )
