# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest.spec.v2.contracts import InterfaceDefinition
from coreason_manifest.spec.v2.definitions import AgentDefinition
from coreason_manifest.utils.mcp_adapter import create_mcp_tool_definition


def test_schema_projection() -> None:
    """Test converting AgentDefinition to MCP Tool Schema."""
    agent = AgentDefinition(
        id="test-agent",
        name="Test Agent",
        role="Tester",
        goal="Testing",
        interface=InterfaceDefinition(
            inputs={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
        ),
    )

    tool_def = create_mcp_tool_definition(agent)

    assert tool_def["name"] == "test_agent"
    assert tool_def["inputSchema"]["type"] == "object"
    assert tool_def["inputSchema"]["properties"]["query"]["type"] == "string"


def test_sanitization() -> None:
    """Test tool name sanitization."""
    agent = AgentDefinition(
        id="test-agent",
        name="Research Assistant (v2)",
        role="Researcher",
        goal="Research",
        backstory="A detailed backstory.",
    )

    tool_def = create_mcp_tool_definition(agent)

    assert tool_def["name"] == "research_assistant_v2"
    assert tool_def["description"] == "A detailed backstory."


def test_sanitization_edge_cases() -> None:
    """Test more aggressive name sanitization edge cases."""
    cases = [
        ("My... Agent!!!", "my_agent"),
        ("  Spaces  Here  ", "spaces_here"),
        ("___Underscores___", "underscores"),
        ("123 Start Number", "123_start_number"),
        ("Mixed-Case_And.Dots", "mixed-case_and_dots"),
        ("!@#$%^&*()", ""),  # Should result in empty string, handled by fallback?
        # If empty, MCP might reject, but our logic just strips.
        # Let's check regex behavior: sub non-alnum -> _, collapse _, strip _.
        # if all non-alnum, it becomes empty string.
        # The MCP SDK might fail, but for now we test our logic.
    ]

    for name, expected in cases:
        agent = AgentDefinition(id="x", name=name, role="R", goal="G")
        tool_def = create_mcp_tool_definition(agent)
        assert tool_def["name"] == expected, f"Failed for {name}"


def test_minimal_agent() -> None:
    """Test projection of a minimal agent without optional fields."""
    agent = AgentDefinition(id="min", name="MinAgent", role="Min", goal="Minimize")

    tool_def = create_mcp_tool_definition(agent)

    assert tool_def["name"] == "minagent"
    assert tool_def["description"] == "Minimize"  # Fallback to goal
    assert tool_def["inputSchema"] == {}  # Default dict


def test_complex_input_schema() -> None:
    """Test handling of complex/nested input schemas."""
    schema = {
        "type": "object",
        "properties": {
            "user": {
                "type": "object",
                "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
                "required": ["name"],
            },
            "tags": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["user"],
    }

    agent = AgentDefinition(
        id="complex", name="Complex Agent", role="Dev", goal="Code", interface=InterfaceDefinition(inputs=schema)
    )

    tool_def = create_mcp_tool_definition(agent)
    assert tool_def["inputSchema"] == schema
    assert tool_def["inputSchema"]["properties"]["user"]["required"] == ["name"]
