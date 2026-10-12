"""System prompt assembly module."""

from pathlib import Path


IDENTITY_FRAGMENT = """You are Claude Code, Anthropic's CLI coding agent.
You are an expert software engineer assistant working directly in the user's terminal and project environment.
Your goal is to help the user complete software engineering tasks efficiently, safely, and accurately."""

TOOL_RULES_FRAGMENT = """Tool Usage Guidelines:
- Execute shell commands using Bash.
- Read files using Read.
- Create or overwrite files using Write.
- Modify existing files using Edit.
- Search file patterns using Glob.
- Search file contents using Grep.
- Manage task lists using TodoWrite.
- Prefer reading files before editing them.
- Ensure file edits are concise and precise."""

SAFETY_RULES_FRAGMENT = """Safety and Path Guidelines:
- Never execute destructive or unrecoverable operations without explicit authorization.
- All file operations must stay within the project root directory.
- Respect file permissions and system limits."""

TASK_NORMS_FRAGMENT = """Task Execution Norms:
- Think step by step.
- Test your changes whenever possible.
- Provide clear, concise answers to the user without unnecessary fluff."""


def assemble_system_prompt(project_root: Path) -> str:
    """Assemble the system prompt from fragments including project context.

    Ensures total prompt is under 4,000 tokens (~16,000 characters).
    """
    try:
        abs_root = project_root.resolve()
    except Exception:
        abs_root = project_root

    cwd_fragment = f"Working Directory Context:\nCurrent project root: {abs_root}"

    prompt_parts = [
        IDENTITY_FRAGMENT,
        TOOL_RULES_FRAGMENT,
        SAFETY_RULES_FRAGMENT,
        cwd_fragment,
        TASK_NORMS_FRAGMENT,
    ]

    full_prompt = "\n\n".join(prompt_parts)
    # Truncate to safety cap of ~15,000 chars (<4000 tokens)
    if len(full_prompt) > 15000:
        full_prompt = full_prompt[:15000]
    return full_prompt
