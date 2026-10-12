"""CLI entry point and REPL implementation."""

import os
import sys
import argparse
from pathlib import Path
from rich.console import Console

import claude_code_py
from claude_code_py.agent import Agent
from claude_code_py.permissions import PermissionMode


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="claude-py",
        description="Claude Code Python - Standalone CLI coding agent",
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default=None,
        help="Initial prompt to run. If omitted, enters interactive REPL mode.",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
        help="Anthropic model name (default: claude-sonnet-4-20250514 or $ANTHROPIC_MODEL)",
    )
    parser.add_argument(
        "--permission-mode",
        choices=["interactive", "yolo", "plan"],
        default="interactive",
        help="Permission mode for tool execution (default: interactive)",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=30,
        help="Maximum turns per agent run (default: 30)",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root path for file safety checks (default: current directory)",
    )
    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Disable streaming response mode",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {claude_code_py.__version__}",
    )
    return parser.parse_args(args)


def run_repl(agent: Agent, console: Console) -> None:
    """Run interactive REPL loop maintaining conversation history."""
    console.print("\n[bold green]Claude Code Python Interactive REPL[/bold green]")
    console.print("Type 'exit' or 'quit' or press Ctrl+D to exit.\n")

    while True:
        try:
            user_input = input("> ").strip()
            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit"}:
                console.print("Goodbye!")
                break

            response = agent.run(user_input)
            console.print("\n")
        except (KeyboardInterrupt, EOFError):
            console.print("\nGoodbye!")
            break


def main(args: list[str] | None = None) -> None:
    parsed = parse_args(args)
    console = Console()

    # Verify API key when prompt or REPL is executed
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[bold red]Error: ANTHROPIC_API_KEY environment variable is missing.[/bold red]")
        sys.exit(1)

    project_root = parsed.project_root.resolve()
    console.print(f"[bold]Model:[/bold] {parsed.model}")
    console.print(f"[bold]Project Root:[/bold] {project_root}")
    console.print(f"[bold]Permission Mode:[/bold] {parsed.permission_mode}")

    agent = Agent(
        model=parsed.model,
        permission_mode=parsed.permission_mode,
        max_turns=parsed.max_turns,
        project_root=project_root,
        stream=not parsed.no_stream,
    )

    if parsed.prompt:
        response = agent.run(parsed.prompt)
        console.print("\n" + response)
    else:
        run_repl(agent, console)


if __name__ == "__main__":
    main()
