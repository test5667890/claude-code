"""Main agent loop implementation."""

import time
from pathlib import Path
from typing import Any
import anthropic
from pydantic import ValidationError

from claude_code_py.prompts import assemble_system_prompt
from claude_code_py.permissions import PermissionManager, PermissionMode
from claude_code_py.streaming import TerminalRenderer
from claude_code_py.tools.base import BaseTool
from claude_code_py.tools.bash import BashTool
from claude_code_py.tools.read import ReadTool
from claude_code_py.tools.write import WriteTool
from claude_code_py.tools.edit import EditTool
from claude_code_py.tools.glob import GlobTool
from claude_code_py.tools.grep import GrepTool
from claude_code_py.tools.todo import TodoWriteTool


class Agent:
    """Core Agent Loop managing Anthropic SDK messages, streaming, tool calls, and turn limits."""

    def __init__(
        self,
        client: anthropic.Anthropic | None = None,
        model: str = "claude-sonnet-4-20250514",
        permission_mode: PermissionMode = "interactive",
        max_turns: int = 30,
        project_root: Path | None = None,
        stream: bool = True,
    ) -> None:
        self.client = client or anthropic.Anthropic()
        self.model = model
        self.permission_manager = PermissionManager(permission_mode)
        self.max_turns = max_turns
        self.project_root = (project_root or Path.cwd()).resolve()
        self.stream = stream

        self.renderer = TerminalRenderer()
        self.system_prompt = assemble_system_prompt(self.project_root)

        # Initialize core 7 tools
        self.tools: dict[str, BaseTool] = {
            "Bash": BashTool(self.project_root),
            "Read": ReadTool(self.project_root),
            "Write": WriteTool(self.project_root),
            "Edit": EditTool(self.project_root),
            "Glob": GlobTool(self.project_root),
            "Grep": GrepTool(self.project_root),
            "TodoWrite": TodoWriteTool(self.project_root),
        }

        self.anthropic_tools = [tool.get_anthropic_schema() for tool in self.tools.values()]
        self.messages: list[dict[str, Any]] = []
        self.tool_call_history: list[tuple[str, str]] = []

    def _call_api_with_backoff(self, **kwargs: Any) -> Any:
        """API call helper with 3-attempt exponential backoff retry."""
        attempts = 0
        backoff = 1.0
        while attempts < 3:
            try:
                if self.stream:
                    return self.client.messages.stream(**kwargs)
                else:
                    return self.client.messages.create(**kwargs)
            except anthropic.APIError as e:
                attempts += 1
                if attempts >= 3:
                    raise e
                time.sleep(backoff)
                backoff *= 2.0

    def run(self, prompt: str) -> str:
        """Run the agent loop starting with user prompt."""
        self.messages.append({"role": "user", "content": prompt})
        turns = 0

        while turns < self.max_turns:
            turns += 1
            response_message: Any = None
            text_response = ""
            tool_calls: list[dict[str, Any]] = []

            if self.stream:
                with self._call_api_with_backoff(
                    model=self.model,
                    system=self.system_prompt,
                    messages=self.messages,
                    tools=self.anthropic_tools,
                    max_tokens=4096,
                ) as stream:
                    for text_delta in stream.text_stream:
                        self.renderer.print_text_delta(text_delta)
                    response_message = stream.get_final_message()
            else:
                response_message = self._call_api_with_backoff(
                    model=self.model,
                    system=self.system_prompt,
                    messages=self.messages,
                    tools=self.anthropic_tools,
                    max_tokens=4096,
                )

            # Process message response content
            assistant_content: list[Any] = []
            for block in response_message.content:
                if block.type == "text":
                    text_response += block.text
                    assistant_content.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    tool_calls.append({
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })
                    assistant_content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })

            self.messages.append({"role": "assistant", "content": assistant_content})

            # Check max_tokens truncation
            if response_message.stop_reason == "max_tokens":
                self.messages.append({
                    "role": "user",
                    "content": "Please continue where you left off.",
                })
                continue

            # If no tool calls, finish
            if not tool_calls:
                return text_response

            # Process tool calls
            tool_result_blocks: list[dict[str, Any]] = []
            for tc in tool_calls:
                tool_id = tc["id"]
                tool_name = tc["name"]
                tool_input = tc["input"]

                self.renderer.print_tool_call_header(tool_name, tool_input)
                self.renderer.log_stderr(f"Tool call: {tool_name} with input {tool_input}")

                # Check repetition detection (3 identical consecutive calls)
                call_sig = (tool_name, str(sorted(tool_input.items())))
                self.tool_call_history.append(call_sig)
                if len(self.tool_call_history) >= 3 and self.tool_call_history[-3:] == [call_sig] * 3:
                    result_text = "You are repeating the same action. Try a different approach or ask for help."
                else:
                    if tool_name not in self.tools:
                        result_text = f"Unknown tool: {tool_name}. Available tools: {list(self.tools.keys())}."
                    else:
                        tool_inst = self.tools[tool_name]
                        # Validate input schema
                        try:
                            tool_inst.input_schema(**tool_input)
                            perm = self.permission_manager.check(tool_name, tool_input)
                            if not perm.approved:
                                result_text = perm.reason or "Permission denied."
                            else:
                                result_text = tool_inst.execute(**tool_input)
                        except ValidationError as ve:
                            result_text = f"Invalid tool input schema for {tool_name}: {ve}"
                        except Exception as exc:
                            result_text = f"Tool execution failed: {exc}"

                self.renderer.log_stderr(f"Tool result: {result_text[:200]}...")

                tool_result_blocks.append({
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": result_text,
                })

            self.messages.append({"role": "user", "content": tool_result_blocks})

        return "Reached maximum turn limit."
