"""Unit tests for core tools and path safety."""

import pytest
from pathlib import Path
from claude_code_py.tools.base import validate_path_safety
from claude_code_py.tools.bash import BashTool
from claude_code_py.tools.read import ReadTool
from claude_code_py.tools.write import WriteTool
from claude_code_py.tools.edit import EditTool
from claude_code_py.tools.glob import GlobTool
from claude_code_py.tools.grep import GrepTool
from claude_code_py.tools.todo import TodoWriteTool, TodoItem


def test_path_safety(tmp_path: Path):
    project_root = tmp_path / "project"
    project_root.mkdir()

    valid_file = project_root / "foo.txt"
    valid_file.write_text("hello")

    # Valid relative path
    resolved = validate_path_safety("foo.txt", project_root)
    assert resolved == valid_file

    # Path traversal attempt rejected
    with pytest.raises(ValueError, match="Path traversal rejected"):
        validate_path_safety("../outside.txt", project_root)


def test_bash_tool(tmp_path: Path):
    tool = BashTool(tmp_path)
    res = tool.execute(command="echo 'hello world'")
    assert "hello world" in res
    assert "Exit code: 0" in res


def test_read_tool(tmp_path: Path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("line 1\nline 2\nline 3\n")

    tool = ReadTool(tmp_path)
    res = tool.execute(file_path="test.txt", offset=0, limit=2)
    assert "line 1" in res
    assert "line 2" in res
    assert "line 3" not in res


def test_write_and_edit_tool(tmp_path: Path):
    write_tool = WriteTool(tmp_path)
    write_res = write_tool.execute(file_path="sub/test.txt", content="foo bar foo")
    assert "Successfully wrote" in write_res

    edit_tool = EditTool(tmp_path)
    # Fail on multiple matches
    fail_res = edit_tool.execute(file_path="sub/test.txt", old_string="foo", new_string="baz")
    assert "Multiple matches found" in fail_res

    # Succeed on exact unique match
    ok_res = edit_tool.execute(file_path="sub/test.txt", old_string="foo bar", new_string="hello world")
    assert "Successfully edited" in ok_res
    assert (tmp_path / "sub/test.txt").read_text() == "hello world foo"


def test_glob_and_grep_tool(tmp_path: Path):
    (tmp_path / "a.py").write_text("def hello(): pass")
    (tmp_path / "b.txt").write_text("just text")

    glob_tool = GlobTool(tmp_path)
    glob_res = glob_tool.execute(pattern="*.py")
    assert "a.py" in glob_res
    assert "b.txt" not in glob_res

    grep_tool = GrepTool(tmp_path)
    grep_res = grep_tool.execute(pattern="hello")
    assert "a.py" in grep_res


def test_todo_tool(tmp_path: Path):
    tool = TodoWriteTool(tmp_path)
    res = tool.execute(todos=[
        {"content": "Run tests", "status": "in_progress", "activeForm": "Running tests"}
    ])
    assert "Run tests" in res
    assert "[~]" in res
