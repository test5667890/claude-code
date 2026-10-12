"""Write tool implementation."""

from typing import Any
from pydantic import BaseModel, Field
from claude_code_py.tools.base import BaseTool, validate_path_safety


class WriteInput(BaseModel):
    file_path: str = Field(description="The path to the file to write")
    content: str = Field(description="The content to write to the file")


class WriteTool(BaseTool):
    name = "Write"
    description = "Write content to a file in the project directory."
    input_schema = WriteInput

    def execute(self, **kwargs: Any) -> str:
        validated_input = WriteInput(**kwargs)
        file_path_str = validated_input.file_path
        content = validated_input.content

        try:
            resolved_path = validate_path_safety(file_path_str, self.project_root)
        except ValueError as err:
            return f"Error: {err}"

        try:
            resolved_path.parent.mkdir(parents=True, exist_ok=True)
            with open(resolved_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Successfully wrote {len(content)} characters to {file_path_str}"
        except Exception as e:
            return f"Error writing file '{file_path_str}': {str(e)}"
