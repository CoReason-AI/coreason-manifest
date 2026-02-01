# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import pytest
from pydantic import ValidationError

from coreason_manifest.definitions.agent import (
    AgentDependencies,
    InlineToolDefinition,
    ToolRequirement,
    ToolRiskLevel,
)


def test_inline_tool_definition_valid() -> None:
    """Test creating a valid InlineToolDefinition."""
    tool = InlineToolDefinition(
        name="my_tool",
        description="A helpful tool",
        parameters={"type": "object", "properties": {"arg": {"type": "string"}}},
        type="function",
    )
    assert tool.name == "my_tool"
    assert tool.description == "A helpful tool"
    assert tool.type == "function"
    assert tool.parameters["type"] == "object"


def test_inline_tool_definition_invalid_type() -> None:
    """Test that invalid tool type raises ValidationError."""
    with pytest.raises(ValidationError):
        InlineToolDefinition(
            name="my_tool",
            description="A helpful tool",
            parameters={},
            type="invalid_type",
        )


def test_agent_dependencies_with_mixed_tools() -> None:
    """Test AgentDependencies with both ToolRequirement and InlineToolDefinition."""
    remote_tool = ToolRequirement(
        uri="https://example.com/tool",
        hash="a" * 64,
        scopes=["read"],
        risk_level=ToolRiskLevel.SAFE,
    )

    inline_tool = InlineToolDefinition(
        name="inline_tool",
        description="An inline tool",
        parameters={"type": "object"},
    )

    deps = AgentDependencies(tools=[remote_tool, inline_tool])
    assert len(deps.tools) == 2
    assert isinstance(deps.tools[0], ToolRequirement)
    assert isinstance(deps.tools[1], InlineToolDefinition)


def test_agent_dependencies_serialization() -> None:
    """Test serialization of AgentDependencies with mixed tools."""
    remote_tool = ToolRequirement(
        uri="https://example.com/tool",
        hash="a" * 64,
        scopes=["read"],
        risk_level=ToolRiskLevel.SAFE,
    )

    inline_tool = InlineToolDefinition(
        name="inline_tool",
        description="An inline tool",
        parameters={"type": "object"},
    )

    deps = AgentDependencies(tools=[remote_tool, inline_tool])
    dumped = deps.model_dump()

    assert len(dumped["tools"]) == 2
    assert dumped["tools"][0]["uri"] == "https://example.com/tool"
    assert dumped["tools"][1]["name"] == "inline_tool"
