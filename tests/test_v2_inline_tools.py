import pytest
from pydantic import ValidationError

from coreason_manifest.spec.v2.definitions import (
    AgentDefinition,
    InlineToolDefinition,
    ToolRequirement,
)


def test_remote_tool_compatibility() -> None:
    """Validate remote tool compatibility (type defaults to 'remote')."""
    data = {"id": "agent-1", "name": "My Agent", "role": "Worker", "goal": "Work", "tools": [{"uri": "mcp://foo"}]}
    agent = AgentDefinition.model_validate(data)
    assert len(agent.tools) == 1
    tool = agent.tools[0]
    assert isinstance(tool, ToolRequirement)
    assert tool.type == "remote"
    assert tool.uri == "mcp://foo"


def test_inline_tool_parsing() -> None:
    """Validate inline tool parsing."""
    data = {
        "id": "agent-2",
        "name": "My Agent",
        "role": "Worker",
        "goal": "Work",
        "tools": [
            {
                "type": "inline",
                "name": "calculator",
                "description": "Add numbers",
                "parameters": {"type": "object", "properties": {}},
            }
        ],
    }
    agent = AgentDefinition.model_validate(data)
    assert len(agent.tools) == 1
    tool = agent.tools[0]
    assert isinstance(tool, InlineToolDefinition)
    assert tool.type == "inline"
    assert tool.name == "calculator"
    assert tool.parameters == {"type": "object", "properties": {}}


def test_validation_error_invalid_schema() -> None:
    """Pass an inline tool with invalid parameters (not a schema object)."""
    data = {
        "id": "agent-3",
        "name": "My Agent",
        "role": "Worker",
        "goal": "Work",
        "tools": [
            {
                "type": "inline",
                "name": "bad_tool",
                "description": "Bad Schema",
                "parameters": {"type": "string"},  # Invalid, must be object
            }
        ],
    }
    with pytest.raises(ValidationError) as exc:
        AgentDefinition.model_validate(data)

    # Check that the error is related to validation
    assert "Tool parameters must be a JSON Schema object" in str(exc.value)


def test_mixed_list() -> None:
    """Create a list containing one remote and one inline tool."""
    data = {
        "id": "agent-4",
        "name": "Mixed Agent",
        "role": "Worker",
        "goal": "Work",
        "tools": [
            {"uri": "mcp://remote"},
            {"type": "inline", "name": "local_tool", "description": "Local", "parameters": {"type": "object"}},
        ],
    }
    agent = AgentDefinition.model_validate(data)
    assert len(agent.tools) == 2
    assert isinstance(agent.tools[0], ToolRequirement)
    assert agent.tools[0].uri == "mcp://remote"

    assert isinstance(agent.tools[1], InlineToolDefinition)
    assert agent.tools[1].name == "local_tool"


def test_legacy_string_list_compatibility() -> None:
    """Validate backward compatibility for list of strings."""
    data = {
        "id": "agent-5",
        "name": "Legacy Agent",
        "role": "Worker",
        "goal": "Work",
        "tools": ["tool-1", "mcp://legacy"],
    }
    agent = AgentDefinition.model_validate(data)
    assert len(agent.tools) == 2

    t1 = agent.tools[0]
    assert isinstance(t1, ToolRequirement)
    assert t1.type == "remote"
    assert t1.uri == "tool-1"

    t2 = agent.tools[1]
    assert isinstance(t2, ToolRequirement)
    assert t2.type == "remote"
    assert t2.uri == "mcp://legacy"
