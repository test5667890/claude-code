"""Glob file search tool implementation."""

from typing import Any
from pydantic import BaseModel, Field
from claude_code_py.tools.base import BaseTool, validate_path_safety


class GlobInput(BaseModel):
    pattern: str = Field(description="Glob pattern to search for (e.g. '*.py', '**/*.txt')")
    path: str = Field(default=".", description="Subdirectory path to search within")


class GlobTool(BaseTool):
    name = "Glob"
    description = "Find files matching pattern in directory."
    input_schema = GlobInput

    def execute(self, **kwargs: Any) -> str:
        validated_input = GlobInput(**kwargs)
        pattern = validated_input.pattern
        base_path_str = validated_input.path

        try:
            search_dir = validate_path_safety(base_path_str, self.project_root)
        except ValueError as err:
            return f"Error: {err}"

        if not search_dir.exists() or not search_dir.is_dir():
            return f"Error: Search directory '{base_path_str}' does not exist or is not a directory."

        try:
            matches = sorted(list(search_dir.rglob(pattern)))
            if not matches:
                return f"No files matching '{pattern}' in '{base_path_str}'."

            rel_paths = []
            for m in matches:
                try:
                    rel_paths.append(str(m.relative_to(self.project_root)))
                except ValueError:
                    rel_paths.append(str(m))

            output = "\n".join(rel_paths)
            if len(output) > 10000:
                output = output[:10000] + "\n... [Results truncated at 10,000 characters]"
            return output
        except Exception as e:
            return f"Error executing glob search: {str(e)}"
