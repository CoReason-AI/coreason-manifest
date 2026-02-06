# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import sys
import json
from unittest.mock import MagicMock, patch, AsyncMock
import pytest

from coreason_manifest.spec.v2.definitions import AgentDefinition
from coreason_manifest.spec.v2.contracts import InterfaceDefinition
from coreason_manifest.interop.mcp import create_mcp_tool_definition, CoreasonMCPServer


def test_schema_projection() -> None:
    """Test converting AgentDefinition to MCP Tool Schema."""
    agent = AgentDefinition(
        id="test-agent",
        name="Test Agent",
        role="Tester",
        goal="Testing",
        interface=InterfaceDefinition(
            inputs={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"]
            }
        )
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
        backstory="A detailed backstory."
    )

    tool_def = create_mcp_tool_definition(agent)

    assert tool_def["name"] == "research_assistant_v2"
    assert tool_def["description"] == "A detailed backstory."


def test_dependency_guard() -> None:
    """Test that CoreasonMCPServer raises ImportError if mcp is missing."""
    # We patch sys.modules to simulate missing mcp
    with patch.dict(sys.modules, {"mcp": None, "mcp.server": None, "mcp.types": None}):
        agent = AgentDefinition(id="a", name="A", role="R", goal="G")

        with pytest.raises(ImportError, match="pip install coreason-manifest\\[mcp\\]"):
            CoreasonMCPServer(agent, AsyncMock())


@pytest.mark.asyncio
async def test_server_execution() -> None:
    """Test CoreasonMCPServer execution logic with mocked mcp."""
    mock_mcp = MagicMock(name="mock_mcp")
    mock_server_cls = MagicMock(name="mock_server_cls")
    mock_server_instance = MagicMock(name="mock_server_instance")
    mock_server_cls.return_value = mock_server_instance

    mock_types = MagicMock(name="mock_types")
    # Mock Tool class
    mock_types.Tool = MagicMock(return_value="ToolObj")
    # Mock TextContent
    mock_types.TextContent = MagicMock(return_value="ContentObj")

    # Ensure mcp.types attribute on mcp mock also points to mock_types,
    # just in case import resolution behaves oddly
    mock_mcp.types = mock_types

    agent = AgentDefinition(id="a", name="My Agent", role="R", goal="G")
    callback = AsyncMock(return_value={"result": "ok"})

    # Patch imports used inside CoreasonMCPServer.__init__
    with patch.dict(sys.modules, {
        "mcp": mock_mcp,
        "mcp.server": MagicMock(Server=mock_server_cls),
        "mcp.types": mock_types
    }):
        server = CoreasonMCPServer(agent, callback)

        # Verify server initialized with correct name
        mock_server_cls.assert_called_once()
        args, _ = mock_server_cls.call_args
        assert args[0] == "coreason-agent-my_agent"

        # Verify call_tool decorator used
        mock_server_instance.call_tool.assert_called_once()

        # Extract the handler function from the decorator
        decorator_mock = mock_server_instance.call_tool.return_value
        handler_func = decorator_mock.call_args[0][0]

        # Execute the handler
        res = await handler_func("my_agent", {"foo": "bar"})

        callback.assert_awaited_with({"foo": "bar"})

        # Verify result structure
        mock_types.TextContent.assert_called()
        call_kwargs = mock_types.TextContent.call_args[1]
        assert call_kwargs["type"] == "text"
        assert '"result": "ok"' in call_kwargs["text"]

        # Check result
        assert res == ["ContentObj"]
