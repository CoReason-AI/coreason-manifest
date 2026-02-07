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
from coreason_manifest.utils.langchain_adapter import convert_to_langchain_kwargs
from coreason_manifest.spec.v2.definitions import AgentDefinition, InlineToolDefinition, ToolRequirement


def test_langchain_conversion_minimal() -> None:
    """Test converting a minimal AgentDefinition to LangChain kwargs."""
    agent = AgentDefinition(
        id="lc-agent",
        name="LangChain Agent",
        role="Prompt Engineer",
        goal="Optimize prompts",
    )

    result = convert_to_langchain_kwargs(agent)

    assert "system_message" in result
    assert "LangChain Agent" in result["system_message"]
    assert "Prompt Engineer" in result["system_message"]
    assert "Optimize prompts" in result["system_message"]
    assert result["tool_schemas"] == []
    assert result["model_name"] == "gpt-4"  # Default


def test_langchain_conversion_with_tools() -> None:
    """Test converting an AgentDefinition with tools."""
    tool = InlineToolDefinition(
        name="search",
        description="Search web",
        parameters={
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    )

    agent = AgentDefinition(
        id="search-agent",
        name="Search Bot",
        role="Searcher",
        goal="Find info",
        tools=[tool],
        model="gpt-3.5-turbo",
    )

    result = convert_to_langchain_kwargs(agent)

    assert result["model_name"] == "gpt-3.5-turbo"
    assert len(result["tool_schemas"]) == 1

    schema = result["tool_schemas"][0]
    # LangChain compatible format (OpenAI function)
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "search"
    assert schema["function"]["description"] == "Search web"
    assert schema["function"]["parameters"] == tool.parameters


def test_langchain_conversion_skips_remote_tools() -> None:
    """Test that remote tools are skipped for LangChain conversion."""
    inline = InlineToolDefinition(
        name="calc",
        description="Calculate",
        parameters={"type": "object", "properties": {}},
    )
    remote = ToolRequirement(uri="http://remote/tool")

    agent = AgentDefinition(
        id="mixed-agent",
        name="Mixed",
        role="X",
        goal="Y",
        tools=[inline, remote],
    )

    result = convert_to_langchain_kwargs(agent)

    assert len(result["tool_schemas"]) == 1
    assert result["tool_schemas"][0]["function"]["name"] == "calc"
