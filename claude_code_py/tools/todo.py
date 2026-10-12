"""TodoWrite task list tool implementation."""

from typing import Any, Literal
from pydantic import BaseModel, Field
from claude_code_py.tools.base import BaseTool


class TodoItem(BaseModel):
    content: str = Field(description="The task description in imperative form")
    status: Literal["pending", "in_progress", "completed"] = Field(description="Task status")
    activeForm: str = Field(description="The present continuous form of the task")


class TodoWriteInput(BaseModel):
    todos: list[TodoItem] = Field(description="Full list of todo items replacing current list")


class TodoWriteTool(BaseTool):
    name = "TodoWrite"
    description = "Manage task items list."
    input_schema = TodoWriteInput

    def __init__(self, project_root: Any) -> None:
        super().__init__(project_root)
        self.todos: list[TodoItem] = []

    def execute(self, **kwargs: Any) -> str:
        validated_input = TodoWriteInput(**kwargs)
        self.todos = validated_input.todos

        summary_lines = ["Updated TODO list:"]
        for idx, item in enumerate(self.todos, 1):
            status_mark = {
                "pending": "[ ]",
                "in_progress": "[~]",
                "completed": "[x]",
            }.get(item.status, "[ ]")
            summary_lines.append(f"{idx}. {status_mark} {item.content} (Active: {item.activeForm})")

        return "\n".join(summary_lines)
