# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest.interop.openai import convert_to_openai_assistant
from coreason_manifest.spec.v2.definitions import AgentDefinition, InlineToolDefinition, ToolRequirement


def test_convert_minimal_agent() -> None:
    """Test converting a minimal agent with no tools."""
    agent = AgentDefinition(
        id="test-agent",
        name="TestAgent",
        role="Tester",
        goal="To test things",
        backstory="I was born to test.",
        model="gpt-3.5-turbo",
    )

    openai_def = convert_to_openai_assistant(agent)

    assert openai_def["name"] == "TestAgent"
    assert "Role: Tester" in openai_def["instructions"]
    assert "Goal: To test things" in openai_def["instructions"]
    assert "Backstory: I was born to test." in openai_def["instructions"]
    assert openai_def["model"] == "gpt-3.5-turbo"
    assert openai_def["tools"] == []
    assert openai_def["metadata"]["source"] == "coreason-manifest"


def test_convert_agent_with_inline_tools() -> None:
    """Test converting an agent with inline tools."""
    tool = InlineToolDefinition(
        name="calculator",
        description="Calculates things",
        parameters={
            "type": "object",
            "properties": {"expression": {"type": "string"}},
            "required": ["expression"],
        },
    )

    agent = AgentDefinition(
        id="math-agent",
        name="MathAgent",
        role="Mathematician",
        goal="Solve problems",
        tools=[tool],
    )

    openai_def = convert_to_openai_assistant(agent)

    assert len(openai_def["tools"]) == 1
    t = openai_def["tools"][0]
    assert t["type"] == "function"
    assert t["function"]["name"] == "calculator"
    assert t["function"]["description"] == "Calculates things"
    assert t["function"]["parameters"] == tool.parameters


def test_convert_agent_with_remote_tools() -> None:
    """Test converting an agent with remote tools (should be skipped)."""
    tool = ToolRequirement(
        uri="https://api.example.com/tools/v1/search"
    )

    agent = AgentDefinition(
        id="remote-agent",
        name="RemoteAgent",
        role="Searcher",
        goal="Search the web",
        tools=[tool],
    )

    openai_def = convert_to_openai_assistant(agent)

    # Remote tools should be skipped
    assert openai_def["tools"] == []


def test_default_model() -> None:
    """Test default model assignment."""
    agent = AgentDefinition(
        id="default-agent",
        name="DefaultAgent",
        role="Default",
        goal="Default",
    )

    openai_def = convert_to_openai_assistant(agent)
    assert openai_def["model"] == "gpt-4o"


def test_knowledge_ignored() -> None:
    """Test that knowledge (files) are ignored as OpenAI API requires file IDs."""
    agent = AgentDefinition(
        id="knowledge-agent",
        name="Librarian",
        role="Librarian",
        goal="Manage knowledge",
        knowledge=["/path/to/local/file.txt", "https://example.com/doc.pdf"],
    )

    openai_def = convert_to_openai_assistant(agent)

    # We do NOT map knowledge to file_ids because that requires API calls
    assert "file_ids" not in openai_def
    assert "tool_resources" not in openai_def


def test_multiple_complex_tools() -> None:
    """Test converting an agent with multiple complex inline tools."""
    tool1 = InlineToolDefinition(
        name="complex_search",
        description="Complex search tool",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "filters": {
                    "type": "object",
                    "properties": {
                        "date_range": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                    },
                },
            },
            "required": ["query"],
        },
    )

    tool2 = InlineToolDefinition(
        name="report_generator",
        description="Generates reports",
        parameters={
            "type": "object",
            "properties": {"format": {"type": "string", "enum": ["pdf", "html"]}},
            "required": ["format"],
        },
    )

    agent = AgentDefinition(
        id="analyst",
        name="Senior Analyst",
        role="Analyst",
        goal="Analyze data",
        tools=[tool1, tool2],
    )

    openai_def = convert_to_openai_assistant(agent)

    assert len(openai_def["tools"]) == 2

    t1 = openai_def["tools"][0]
    assert t1["function"]["name"] == "complex_search"
    assert t1["function"]["parameters"]["properties"]["filters"]["type"] == "object"

    t2 = openai_def["tools"][1]
    assert t2["function"]["name"] == "report_generator"
    assert "enum" in t2["function"]["parameters"]["properties"]["format"]


def test_special_characters_in_name() -> None:
    """Test handling of special characters in agent name."""
    # OpenAI names are lenient (up to 256 chars), so we pass them through.
    # We verify that they appear correctly in the output.
    name = "Agent (Special Edition) #1"
    agent = AgentDefinition(
        id="special-agent",
        name=name,
        role="Specialist",
        goal="Be special",
    )

    openai_def = convert_to_openai_assistant(agent)
    assert openai_def["name"] == name
