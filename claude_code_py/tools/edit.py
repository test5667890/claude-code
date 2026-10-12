"""Edit tool implementation."""

from typing import Any
from pydantic import BaseModel, Field
from claude_code_py.tools.base import BaseTool, validate_path_safety


class EditInput(BaseModel):
    file_path: str = Field(description="The path to the file to edit")
    old_string: str = Field(description="The string to replace")
    new_string: str = Field(description="The replacement string")


class EditTool(BaseTool):
    name = "Edit"
    description = "Replace string in a file with exact match validation."
    input_schema = EditInput

    def execute(self, **kwargs: Any) -> str:
        validated_input = EditInput(**kwargs)
        file_path_str = validated_input.file_path
        old_string = validated_input.old_string
        new_string = validated_input.new_string

        try:
            resolved_path = validate_path_safety(file_path_str, self.project_root)
        except ValueError as err:
            return f"Error: {err}"

        if not resolved_path.exists():
            return f"Error: File '{file_path_str}' does not exist."

        try:
            with open(resolved_path, "r", encoding="utf-8") as f:
                content = f.read()

            matches = content.count(old_string)
            if matches == 0:
                return f"Error: Could not find exact match for old_string in '{file_path_str}'."
            if matches > 1:
                return f"Error: Multiple matches found ({matches}) for old_string. Provide more surrounding context."

            updated_content = content.replace(old_string, new_string, 1)
            with open(resolved_path, "w", encoding="utf-8") as f:
                f.write(updated_content)

            return f"Successfully edited {file_path_str}"
        except Exception as e:
            return f"Error editing file '{file_path_str}': {str(e)}"
