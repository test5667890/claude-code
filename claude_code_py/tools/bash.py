"""Bash execution tool implementation."""

import subprocess
from typing import Any
from pydantic import BaseModel, Field
from claude_code_py.tools.base import BaseTool


class BashInput(BaseModel):
    command: str = Field(description="The shell command to execute")
    timeout: int = Field(default=120, description="Optional timeout in seconds")


class BashTool(BaseTool):
    name = "Bash"
    description = "Execute shell commands in the project directory."
    input_schema = BashInput

    def execute(self, **kwargs: Any) -> str:
        validated_input = BashInput(**kwargs)
        command = validated_input.command
        timeout = validated_input.timeout

        try:
            res = subprocess.run(
                command,
                shell=True,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            output = f"Exit code: {res.returncode}\n"
            if res.stdout:
                output += f"STDOUT:\n{res.stdout}\n"
            if res.stderr:
                output += f"STDERR:\n{res.stderr}\n"

            if len(output) > 10000:
                output = output[:10000] + "\n... [Output truncated at 10,000 characters]"

            return output.strip()
        except subprocess.TimeoutExpired:
            return f"Error: Command timed out after {timeout} seconds."
        except Exception as e:
            return f"Error executing command: {str(e)}"
