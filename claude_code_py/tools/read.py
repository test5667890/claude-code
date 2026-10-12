"""Read tool implementation."""

from typing import Any
from pydantic import BaseModel, Field
from claude_code_py.tools.base import BaseTool, validate_path_safety


class ReadInput(BaseModel):
    file_path: str = Field(description="The path to the file to read")
    offset: int = Field(default=0, description="The line number offset to start reading from")
    limit: int = Field(default=2000, description="The maximum number of lines to read")


class ReadTool(BaseTool):
    name = "Read"
    description = "Read a file from the project directory with numbered lines."
    input_schema = ReadInput

    def execute(self, **kwargs: Any) -> str:
        validated_input = ReadInput(**kwargs)
        file_path_str = validated_input.file_path
        offset = max(0, validated_input.offset)
        limit = max(1, validated_input.limit)

        try:
            resolved_path = validate_path_safety(file_path_str, self.project_root)
        except ValueError as err:
            return f"Error: {err}"

        if not resolved_path.exists():
            return f"Error: File '{file_path_str}' does not exist."

        if not resolved_path.is_file():
            return f"Error: '{file_path_str}' is not a file."

        try:
            # File size check (1MB cap)
            file_size = resolved_path.stat().st_size
            if file_size > 1_000_000:
                return "Error: File too large. Use Grep to search for specific patterns."

            with open(resolved_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            selected_lines = lines[offset : offset + limit]
            if not selected_lines:
                return f"File '{file_path_str}' has no content in line range [{offset}:{offset + limit}]."

            formatted_lines = [
                f"{i + offset + 1:6d}  {line.rstrip('\n')}"
                for i, line in enumerate(selected_lines)
            ]

            header = f"File: {file_path_str} (Lines {offset + 1}-{offset + len(selected_lines)} of {len(lines)})\n"
            return header + "\n".join(formatted_lines)
        except Exception as e:
            return f"Error reading file '{file_path_str}': {str(e)}"
