"""Grep pattern search tool implementation."""

import re
import subprocess
import shutil
from typing import Any
from pydantic import BaseModel, Field
from claude_code_py.tools.base import BaseTool, validate_path_safety


class GrepInput(BaseModel):
    pattern: str = Field(description="Regex pattern to search for")
    path: str = Field(default=".", description="Subdirectory or file path to search")
    include: str | None = Field(default=None, description="Optional glob filter pattern (e.g. '*.py')")


class GrepTool(BaseTool):
    name = "Grep"
    description = "Search file contents for regular expression matches."
    input_schema = GrepInput

    def execute(self, **kwargs: Any) -> str:
        validated_input = GrepInput(**kwargs)
        pattern = validated_input.pattern
        search_path_str = validated_input.path
        include = validated_input.include

        try:
            target = validate_path_safety(search_path_str, self.project_root)
        except ValueError as err:
            return f"Error: {err}"

        if not target.exists():
            return f"Error: Path '{search_path_str}' does not exist."

        # Try ripgrep (rg) if available
        if shutil.which("rg"):
            cmd = ["rg", "--line-number", "--no-heading", "--color", "never", pattern]
            if include:
                cmd.extend(["-g", include])
            cmd.append(str(target))

            try:
                res = subprocess.run(
                    cmd,
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                output = res.stdout.strip()
                if not output:
                    return f"No matches found for pattern '{pattern}'."
                if len(output) > 10000:
                    output = output[:10000] + "\n... [Output truncated at 10,000 characters]"
                return output
            except Exception:
                pass  # Fall through to python implementation

        # Fallback Python regex search
        try:
            regex = re.compile(pattern)
            results = []

            files_to_search = []
            if target.is_file():
                files_to_search.append(target)
            else:
                glob_pat = include if include else "**/*"
                for p in target.rglob(glob_pat):
                    if p.is_file():
                        files_to_search.append(p)

            for f in files_to_search:
                try:
                    rel_f = f.relative_to(self.project_root)
                except ValueError:
                    rel_f = f

                try:
                    with open(f, "r", encoding="utf-8", errors="ignore") as file_obj:
                        for idx, line in enumerate(file_obj, start=1):
                            if regex.search(line):
                                results.append(f"{rel_f}:{idx}:{line.strip()}")
                except Exception:
                    continue

            if not results:
                return f"No matches found for pattern '{pattern}'."

            output = "\n".join(results)
            if len(output) > 10000:
                output = output[:10000] + "\n... [Output truncated at 10,000 characters]"
            return output
        except Exception as e:
            return f"Error searching pattern: {str(e)}"
