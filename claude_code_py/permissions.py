"""Permission management and approval model."""

import re
from typing import Any, Literal
from dataclasses import dataclass

PermissionMode = Literal["interactive", "yolo", "plan"]

DANGEROUS_BASH_PATTERNS = [
    r"rm\s+-rf\s+/",
    r"\bmkfs\b",
    r"\bdd\s+if=",
    r":\(\)\{\s*:\|:&\s*\};:",
    r">\s*/dev/sda",
]

MUTATING_TOOLS = {"Bash", "Write", "Edit"}


@dataclass
class PermissionDecision:
    approved: bool
    reason: str | None = None


class PermissionManager:
    """Manages tool call approvals based on configured permission mode."""

    def __init__(self, mode: PermissionMode = "interactive") -> None:
        if mode not in {"interactive", "yolo", "plan"}:
            raise ValueError(f"Invalid permission mode '{mode}'. Must be interactive, yolo, or plan.")
        self.mode: PermissionMode = mode

    def check(self, tool_name: str, tool_input: dict[str, Any]) -> PermissionDecision:
        """Check if tool call is approved under current permission mode."""
        if self.mode == "plan":
            return PermissionDecision(
                approved=False,
                reason="Permission denied: Tool execution is disabled in 'plan' permission mode."
            )

        if self.mode == "yolo":
            if tool_name == "Bash":
                command = str(tool_input.get("command", ""))
                for pattern in DANGEROUS_BASH_PATTERNS:
                    if re.search(pattern, command):
                        return PermissionDecision(
                            approved=False,
                            reason=f"Permission denied: Command matches dangerous pattern '{pattern}'."
                        )
            return PermissionDecision(approved=True)

        # Interactive mode: auto-approve read-only tools, prompt for mutating tools
        if tool_name not in MUTATING_TOOLS:
            return PermissionDecision(approved=True)

        # Prompt user for mutating tools in interactive mode
        user_choice = self._prompt_user(tool_name, tool_input)
        if user_choice:
            return PermissionDecision(approved=True)
        return PermissionDecision(
            approved=False,
            reason=f"Permission denied: User rejected tool execution for {tool_name}."
        )

    def _prompt_user(self, tool_name: str, tool_input: dict[str, Any]) -> bool:
        """Prompt user via stdin for approval."""
        print(f"\n[Permission Request] Tool: {tool_name}")
        print(f"Arguments: {tool_input}")
        try:
            response = input("Allow execution? [y/N]: ").strip().lower()
            return response in {"y", "yes"}
        except (EOFError, KeyboardInterrupt):
            return False
