"""Unit tests for agent loop with mocked Anthropic API client."""

from unittest.mock import MagicMock
from pathlib import Path
from claude_code_py.agent import Agent


def test_agent_loop_single_text_response(tmp_path: Path):
    mock_client = MagicMock()

    # Mock message response
    mock_response = MagicMock()
    mock_block = MagicMock()
    mock_block.type = "text"
    mock_block.text = "Hello! I am Claude."
    mock_response.content = [mock_block]
    mock_response.stop_reason = "end_turn"

    mock_client.messages.create.return_value = mock_response

    agent = Agent(client=mock_client, project_root=tmp_path, stream=False)
    result = agent.run("Hi")

    assert result == "Hello! I am Claude."
    assert len(agent.messages) == 2


def test_agent_loop_tool_execution(tmp_path: Path):
    mock_client = MagicMock()

    # First turn calls tool
    resp1 = MagicMock()
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.id = "tool_1"
    tool_block.name = "Glob"
    tool_block.input = {"pattern": "*.txt"}
    resp1.content = [tool_block]
    resp1.stop_reason = "tool_use"

    # Second turn returns text
    resp2 = MagicMock()
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = "Found files."
    resp2.content = [text_block]
    resp2.stop_reason = "end_turn"

    mock_client.messages.create.side_effect = [resp1, resp2]

    agent = Agent(client=mock_client, project_root=tmp_path, stream=False)
    result = agent.run("Find text files")

    assert result == "Found files."
    assert len(agent.messages) == 4  # user, assistant tool call, user tool result, assistant text
