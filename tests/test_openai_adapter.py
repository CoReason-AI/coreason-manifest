# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest.spec.v2.definitions import AgentDefinition, InlineToolDefinition, ToolRequirement
from coreason_manifest.utils.openai_adapter import convert_to_openai_assistant


def test_openai_conversion_minimal() -> None:
    """Test converting a minimal AgentDefinition to OpenAI format."""
    agent = AgentDefinition(
        id="test-agent-1",
        name="Minimal Agent",
        role="Assistant",
        goal="Help the user.",
    )

    result = convert_to_openai_assistant(agent)

    assert result["name"] == "Minimal Agent"
    assert result["model"] == "gpt-4-turbo-preview"  # Default
    assert "Assistant" in result["instructions"]
    assert "Help the user." in result["instructions"]
    assert result["tools"] == []
    assert result["metadata"]["coreason_agent_id"] == "test-agent-1"


def test_openai_conversion_with_tools() -> None:
    """Test converting an AgentDefinition with inline tools."""
    tool = InlineToolDefinition(
        name="get_weather",
        description="Get current weather",
        parameters={
            "type": "object",
            "properties": {"location": {"type": "string"}},
            "required": ["location"],
        },
    )

    agent = AgentDefinition(
        id="weather-agent",
        name="Weather Bot",
        role="Meteorologist",
        goal="Provide weather info.",
        tools=[tool],
        model="gpt-3.5-turbo",
    )

    result = convert_to_openai_assistant(agent)

    assert result["name"] == "Weather Bot"
    assert result["model"] == "gpt-3.5-turbo"
    assert len(result["tools"]) == 1

    openai_tool = result["tools"][0]
    assert openai_tool["type"] == "function"
    assert openai_tool["function"]["name"] == "get_weather"
    assert openai_tool["function"]["description"] == "Get current weather"
    assert openai_tool["function"]["parameters"] == tool.parameters


def test_openai_conversion_skips_remote_tools() -> None:
    """Test that remote tools (ToolRequirement) are skipped during conversion."""
    inline_tool = InlineToolDefinition(
        name="local_tool",
        description="Local tool",
        parameters={"type": "object", "properties": {}},
    )

    remote_tool = ToolRequirement(uri="http://example.com/remote-tool")

    agent = AgentDefinition(
        id="hybrid-agent",
        name="Hybrid Agent",
        role="Worker",
        goal="Work",
        tools=[inline_tool, remote_tool],
    )

    result = convert_to_openai_assistant(agent)

    # Only the inline tool should be present
    assert len(result["tools"]) == 1
    assert result["tools"][0]["function"]["name"] == "local_tool"
