"""Streaming output and terminal rendering module using rich."""

import sys
from typing import Any
from rich.console import Console
from rich.markdown import Markdown


class TerminalRenderer:
    """Renders Live streaming deltas, tool call headers, and formatted results."""

    def __init__(self) -> None:
        self.console = Console()
        self.stderr_console = Console(stderr=True)

    def print_text_delta(self, delta_text: str) -> None:
        """Stream plain text deltas with immediate flush."""
        sys.stdout.write(delta_text)
        sys.stdout.flush()

    def print_tool_call_header(self, tool_name: str, tool_input: dict[str, Any]) -> None:
        """Print tool call header with formatting."""
        sys.stdout.write("\n")
        self.console.print(f"[bold cyan]● {tool_name}[/bold cyan]({tool_input})")
        sys.stdout.flush()

    def render_markdown(self, text: str) -> None:
        """Render completed markdown text with syntax highlighting."""
        sys.stdout.write("\n")
        self.console.print(Markdown(text))
        sys.stdout.flush()

    def log_stderr(self, message: str) -> None:
        """Log debug/tool activity messages to stderr."""
        self.stderr_console.print(f"[dim]{message}[/dim]")
