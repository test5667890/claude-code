"""Unit tests for permission modes and deny-list logic."""

from claude_code_py.permissions import PermissionManager


def test_permission_yolo_mode():
    pm = PermissionManager("yolo")
    # Auto approve standard command
    assert pm.check("Bash", {"command": "ls -la"}).approved is True

    # Deny dangerous command
    assert pm.check("Bash", {"command": "rm -rf /"}).approved is False
    assert pm.check("Bash", {"command": "dd if=/dev/zero"}).approved is False


def test_permission_plan_mode():
    pm = PermissionManager("plan")
    assert pm.check("Read", {"file_path": "a.txt"}).approved is False
    assert pm.check("Bash", {"command": "ls"}).approved is False


def test_permission_interactive_mode(monkeypatch):
    pm = PermissionManager("interactive")
    # Read-only tool auto approved
    assert pm.check("Read", {"file_path": "a.txt"}).approved is True

    # Mutating tool prompts user
    monkeypatch.setattr("builtins.input", lambda _: "y")
    assert pm.check("Write", {"file_path": "a.txt", "content": "x"}).approved is True

    monkeypatch.setattr("builtins.input", lambda _: "n")
    assert pm.check("Write", {"file_path": "a.txt", "content": "x"}).approved is False
