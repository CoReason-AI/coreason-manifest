# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest.spec.v2.definitions import (
    AgentDefinition,
    InlineToolDefinition,
    ToolRequirement,
)


def test_empty_tools_list() -> None:
    """Edge Case: Agent with empty tools list should be valid."""
    data = {
        "id": "agent-empty",
        "name": "Empty Tools",
        "role": "Worker",
        "goal": "Work",
        "tools": [],
    }
    agent = AgentDefinition.model_validate(data)
    assert agent.tools == []


def test_duplicate_tools() -> None:
    """Edge Case: Duplicate tools are allowed in the list (though maybe not useful)."""
    data = {
        "id": "agent-dup",
        "name": "Duplicate Tools",
        "role": "Worker",
        "goal": "Work",
        "tools": [{"type": "remote", "uri": "tool-1"}, {"type": "remote", "uri": "tool-1"}],
    }
    agent = AgentDefinition.model_validate(data)
    assert len(agent.tools) == 2
    assert agent.tools[0].uri == "tool-1"  # type: ignore[union-attr]
    assert agent.tools[1].uri == "tool-1"  # type: ignore[union-attr]


def test_complex_mixed_usage() -> None:
    """Complex Case: Mix of ID reference, Remote Requirement, and Inline Definition."""
    data = {
        "id": "agent-complex",
        "name": "Complex Agent",
        "role": "Worker",
        "goal": "Work",
        "tools": [
            {"type": "remote", "uri": "search-tool-id"},
            {"type": "remote", "uri": "mcp://weather"},
            {
                "type": "inline",
                "name": "calculator",
                "description": "Add numbers",
                "parameters": {"type": "object", "properties": {"a": {"type": "integer"}}},
            },
        ],
    }
    agent = AgentDefinition.model_validate(data)
    assert len(agent.tools) == 3

    # 1. ID Reference (converted to Remote)
    assert isinstance(agent.tools[0], ToolRequirement)
    assert agent.tools[0].uri == "search-tool-id"
    assert agent.tools[0].type == "remote"

    # 2. Remote Requirement
    assert isinstance(agent.tools[1], ToolRequirement)
    assert agent.tools[1].uri == "mcp://weather"
    assert agent.tools[1].type == "remote"

    # 3. Inline Definition
    assert isinstance(agent.tools[2], InlineToolDefinition)
    assert agent.tools[2].name == "calculator"
    assert agent.tools[2].type == "inline"


def test_deeply_nested_inline_schema() -> None:
    """Complex Case: Inline tool with deeply nested JSON Schema."""
    data = {
        "id": "agent-nested",
        "name": "Nested Schema Agent",
        "role": "Worker",
        "goal": "Work",
        "tools": [
            {
                "type": "inline",
                "name": "complex_tool",
                "description": "Complex Input",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "level1": {
                            "type": "object",
                            "properties": {
                                "level2": {
                                    "type": "array",
                                    "items": {"type": "object", "properties": {"level3": {"type": "string"}}},
                                }
                            },
                        }
                    },
                },
            }
        ],
    }
    agent = AgentDefinition.model_validate(data)
    tool = agent.tools[0]
    assert isinstance(tool, InlineToolDefinition)
    # Verify deep access
    assert (
        tool.parameters["properties"]["level1"]["properties"]["level2"]["items"]["properties"]["level3"]["type"]
        == "string"
    )
