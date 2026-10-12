# Porting Notes for `claude_code_py`

## Specification-Driven Build Notice
The Claude Code TypeScript implementation source code is not present in this repository (only plugin and hook type definitions exist in `mods/types/claude-code.d.ts`). Therefore, `claude_code_py` is a standalone Python reimplementation built directly from written specification.

## Implemented Features
1. **Agent Loop (`claude_code_py/agent.py`)**
   - Streamed or non-streamed messaging via `anthropic` SDK.
   - Message history maintenance across user, assistant, and tool result messages.
   - Stop reason handling (`tool_use`, `end_turn`, `max_tokens` continuation).
   - Turn limit enforcement (`max_turns`, default 30).
   - Repetition detection (injects user warning when 3 consecutive identical tool calls occur).
   - Exponential backoff retry logic (3 attempts) for Anthropic API errors.

2. **Core Tools (`claude_code_py/tools/`)**
   - `Bash`: Shell execution via `subprocess.run` with default 120s timeout, stdout/stderr capture, and 10,000 character output truncation.
   - `Read`: File reading with numbered lines, `offset`, `limit`, and 1MB size limit check.
   - `Write`: File writing with parent directory creation.
   - `Edit`: String replacement requiring exact matching (errors if missing or matching multiple times).
   - `Glob`: File pattern matching using `Path.rglob`.
   - `Grep`: Search using `ripgrep` (`rg`) if available, falling back to Python standard `re`.
   - `TodoWrite`: Task list replacement accepting `todos` with `content`, `status` (`pending`, `in_progress`, `completed`), and `activeForm`.

3. **Path Safety (`claude_code_py/tools/base.py`)**
   - Strict path verification on every file tool: `Path(path).resolve().is_relative_to(project_root.resolve())`. Traversal attempts raise explicit error messages.

4. **Permissions (`claude_code_py/permissions.py`)**
   - `interactive`: Prompts user confirmation on mutating/executing tools (`Bash`, `Write`, `Edit`); auto-approves read-only tools (`Read`, `Glob`, `Grep`, `TodoWrite`).
   - `yolo`: Auto-approves all tool calls except Bash commands matching dangerous patterns (`rm -rf /`, `mkfs`, `dd if=`, `:(){ :|:& };:`, `> /dev/sda`).
   - `plan`: Disables tool execution and returns a plan mode notification to the agent.

5. **Streaming & Terminal Formatting (`claude_code_py/streaming.py`)**
   - Real-time `text_delta` streaming using `RichConsole` with `flush=True`.
   - Tool call headers formatted with `rich` and tool execution logs sent to `stderr`.

6. **CLI & REPL (`claude_code_py/cli.py`)**
   - Full argument parsing supporting `--model`, `--permission-mode`, `--max-turns`, `--project-root`, `--version`, and `--no-stream`.
   - Work cleanly without `ANTHROPIC_API_KEY` for `--help` and `--version`.
   - Interactive prompt REPL when no positional prompt is supplied.

## Deliberately Omitted Features (TODOs for v2+)
- **Sub-agents**: Spawning isolated sub-agent loops (`subagent_type`).
- **Context Compaction**: Summarizing long transcripts to fit context windows.
- **MCP (Model Context Protocol)**: Dynamic MCP server connections and tool registration.
- **TUI (Terminal User Interface)**: Rich full-screen terminal interface (e.g., Ink/Textual).
- **Background Tasks**: Long-running background tool processes and async management.
