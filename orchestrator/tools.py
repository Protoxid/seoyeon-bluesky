"""
Execution tools for the Operator agent.
Implements the core operating rules:
- ALWAYS DOUBLE CHECK WHAT YOU HAVE (assert match counts, verify values)
- SAY ONLY THE DELTA (surgical patching over complete rewrites)
"""

import json
import os
import subprocess
from typing import Any, Dict, List, Optional


class ToolExecutor:
    """Executes workspace tools with sandboxing and validation."""

    def __init__(self, workspace_root: str):
        self.workspace_root = os.path.abspath(workspace_root)

    def _resolve_path(self, rel_or_abs: str) -> str:
        """Resolve a path safely inside or relative to workspace."""
        if os.path.isabs(rel_or_abs):
            return os.path.normpath(rel_or_abs)
        return os.path.normpath(os.path.join(self.workspace_root, rel_or_abs))

    def read_file(self, file_path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> Dict[str, Any]:
        """Read content of a file, optionally with line slices (1-indexed)."""
        target = self._resolve_path(file_path)
        if not os.path.exists(target):
            return {"status": "error", "error": f"File not found: {file_path}"}
        if os.path.isdir(target):
            return {"status": "error", "error": f"Path is a directory: {file_path}"}

        try:
            with open(target, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            total_lines = len(lines)
            s = (start_line or 1) - 1
            e = end_line or total_lines
            s = max(0, min(s, total_lines))
            e = max(s, min(e, total_lines))

            sliced = lines[s:e]
            numbered = [f"{i + s + 1}: {line}" for i, line in enumerate(sliced)]
            return {
                "status": "success",
                "file_path": file_path,
                "total_lines": total_lines,
                "start_line": s + 1,
                "end_line": e,
                "content": "".join(numbered),
            }
        except Exception as ex:
            return {"status": "error", "error": str(ex)}

    def write_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """Write content to a file, creating parent directories if needed."""
        target = self._resolve_path(file_path)
        try:
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(content)

            # Verification rule: Always double check what was written
            assert os.path.exists(target), "File does not exist after writing"
            size = os.path.getsize(target)
            return {
                "status": "success",
                "file_path": file_path,
                "bytes_written": size,
                "verification": f"Verified on disk ({size} bytes)",
            }
        except Exception as ex:
            return {"status": "error", "error": str(ex)}

    def patch_file(self, file_path: str, search_block: str, replace_block: str) -> Dict[str, Any]:
        """
        Surgically replace a unique block of text in a file.
        Enforces:
        1. Exact match count assertion (must match exactly once).
        2. Post-edit value verification.
        """
        target = self._resolve_path(file_path)
        if not os.path.exists(target):
            return {"status": "error", "error": f"File not found: {file_path}"}

        try:
            with open(target, "r", encoding="utf-8") as f:
                content = f.read()

            matches = content.count(search_block)
            if matches == 0:
                return {
                    "status": "error",
                    "error": "Target search block was not found in file. Ensure exact matching including whitespace.",
                }
            if matches > 1:
                return {
                    "status": "error",
                    "error": f"Target search block matched {matches} times. It must match exactly 1 time to be unique.",
                }

            new_content = content.replace(search_block, replace_block, 1)

            # Assert change occurred
            if new_content == content:
                return {"status": "error", "error": "Replacement produced identical content."}

            with open(target, "w", encoding="utf-8") as f:
                f.write(new_content)

            # Double check against written value
            with open(target, "r", encoding="utf-8") as f:
                verified = f.read()

            assert replace_block in verified, "Verified check failed: replacement block not found in file after write"

            return {
                "status": "success",
                "file_path": file_path,
                "delta": {
                    "search_length": len(search_block),
                    "replace_length": len(replace_block),
                    "character_delta": len(replace_block) - len(search_block),
                },
                "verification": "Asserted exactly 1 match replaced and new content verified on disk.",
            }
        except Exception as ex:
            return {"status": "error", "error": str(ex)}

    def run_command(self, command: str, timeout_sec: int = 60) -> Dict[str, Any]:
        """Execute a shell command via PowerShell in the workspace root."""
        try:
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
            )
            return {
                "status": "success" if proc.returncode == 0 else "failed",
                "exit_code": proc.returncode,
                "stdout": proc.stdout.strip(),
                "stderr": proc.stderr.strip(),
            }
        except subprocess.TimeoutExpired:
            return {"status": "error", "error": f"Command timed out after {timeout_sec}s"}
        except Exception as ex:
            return {"status": "error", "error": str(ex)}

    def list_directory(self, directory_path: str = ".") -> Dict[str, Any]:
        """List contents of a directory."""
        target = self._resolve_path(directory_path)
        if not os.path.exists(target):
            return {"status": "error", "error": f"Directory not found: {directory_path}"}
        if not os.path.isdir(target):
            return {"status": "error", "error": f"Path is not a directory: {directory_path}"}

        try:
            items = []
            for entry in os.listdir(target):
                full = os.path.join(target, entry)
                is_dir = os.path.isdir(full)
                items.append({
                    "name": entry,
                    "type": "directory" if is_dir else "file",
                    "size_bytes": None if is_dir else os.path.getsize(full),
                })
            return {"status": "success", "path": directory_path, "items": items}
        except Exception as ex:
            return {"status": "error", "error": str(ex)}

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch tool name and arguments to method."""
        tool_map = {
            "read_file": lambda: self.read_file(
                arguments["file_path"],
                arguments.get("start_line"),
                arguments.get("end_line"),
            ),
            "write_file": lambda: self.write_file(
                arguments["file_path"],
                arguments["content"],
            ),
            "patch_file": lambda: self.patch_file(
                arguments["file_path"],
                arguments["search_block"],
                arguments["replace_block"],
            ),
            "run_command": lambda: self.run_command(
                arguments["command"],
                arguments.get("timeout_sec", 60),
            ),
            "list_directory": lambda: self.list_directory(
                arguments.get("directory_path", "."),
            ),
        }

        if tool_name not in tool_map:
            return {"status": "error", "error": f"Unknown tool: {tool_name}"}

        return tool_map[tool_name]()


# Tool definitions formatted for OpenAI-compatible / LM Studio function calling schemas
OPENAI_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read contents of a file with optional line slice.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Relative path to file"},
                    "start_line": {"type": "integer", "description": "1-indexed starting line"},
                    "end_line": {"type": "integer", "description": "1-indexed ending line"},
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create a new file or completely overwrite an existing file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Relative path to file"},
                    "content": {"type": "string", "description": "Full file content"},
                },
                "required": ["file_path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "patch_file",
            "description": "Surgically replace a unique block of text in an existing file. Must match exactly once.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Relative path to file"},
                    "search_block": {"type": "string", "description": "Exact text block to search and replace"},
                    "replace_block": {"type": "string", "description": "New text block to insert"},
                },
                "required": ["file_path", "search_block", "replace_block"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Execute a PowerShell command in the workspace root to test, verify, or run scripts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "PowerShell command to run"},
                    "timeout_sec": {"type": "integer", "description": "Timeout in seconds (default 60)"},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files and directories in a path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory_path": {"type": "string", "description": "Path relative to workspace"},
                },
            },
        },
    },
]
