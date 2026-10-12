# Claude Code Python (`claude_code_py`)

Standalone Python implementation of Claude Code CLI coding agent built from specification.

## Features
- **Agent Loop**: Multi-turn agent loop supporting Anthropic streaming messages, tool execution, truncation/continuation (`max_tokens`), turn limits (`max_turns`), and repetition detection.
- **Seven Core Tools**: `Bash`, `Read`, `Write`, `Edit`, `Glob`, `Grep`, `TodoWrite`.
- **Path Safety**: Every file tool enforces strict path checks (`Path.resolve()` relative to `project_root`).
- **Permission Modes**:
  - `interactive`: Prompt for user approval on mutating tools (`Bash`, `Write`, `Edit`); auto-approve read-only tools (`Read`, `Glob`, `Grep`, `TodoWrite`).
  - `yolo`: Auto-approve all tools except dangerous Bash command patterns (`rm -rf /`, `mkfs`, etc.).
  - `plan`: Read-only plan mode; tool calls are printed but not executed.
- **Streaming Output**: Live streaming of assistant deltas with `rich` formatting.
- **CLI & REPL**: Run single prompts or start an interactive prompt REPL session.

## Installation

```bash
pip install -e .
```

For development dependencies (pytest, mypy):
```bash
pip install -e ".[dev]"
```

## Usage

Set your `ANTHROPIC_API_KEY`:
```bash
export ANTHROPIC_API_KEY="your-api-key"
```

### Run a single prompt
```bash
python claude_code_py/cli.py "Explain the structure of this project"
```

### Start interactive REPL
```bash
python claude_code_py/cli.py
```

### CLI Options
```
--model TEXT             Model name (default: claude-sonnet-4-20250514 or $ANTHROPIC_MODEL)
--permission-mode MODE   Permission mode: interactive, yolo, plan (default: interactive)
--max-turns INT          Maximum turns allowed (default: 30)
--project-root PATH      Root directory for file safety checks (default: current directory)
--no-stream              Disable streaming mode
--version                Print version and exit
--help                   Show help message
```

## Testing

Run tests with `pytest`:
```bash
pytest
```
