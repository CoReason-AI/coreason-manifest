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
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from coreason_manifest.interop.mcp import CoreasonMCPServer, create_mcp_tool_definition
from coreason_manifest.spec.v2.contracts import InterfaceDefinition
from coreason_manifest.spec.v2.definitions import AgentDefinition


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


def test_dependency_guard() -> None:
    """Test that CoreasonMCPServer raises ImportError if mcp is missing."""
    # We patch sys.modules to simulate missing mcp
    with patch.dict(sys.modules, {"mcp": None, "mcp.server": None, "mcp.types": None}):
        agent = AgentDefinition(id="a", name="A", role="R", goal="G")

        with pytest.raises(ImportError, match="pip install coreason-manifest\\[mcp\\]"):
            CoreasonMCPServer(agent, AsyncMock())


@pytest.mark.asyncio
async def test_server_list_tools() -> None:
    """Test that list_tools handler returns the correct tool definition."""
    mock_mcp = MagicMock(name="mock_mcp")
    mock_server_cls = MagicMock(name="mock_server_cls")
    mock_server_instance = MagicMock(name="mock_server_instance")
    mock_server_cls.return_value = mock_server_instance
    mock_types = MagicMock(name="mock_types")
    mock_mcp.types = mock_types

    agent = AgentDefinition(id="a", name="MyAgent", role="R", goal="G")
    callback = AsyncMock()

    with patch.dict(
        sys.modules, {"mcp": mock_mcp, "mcp.server": MagicMock(Server=mock_server_cls), "mcp.types": mock_types}
    ):
        _ = CoreasonMCPServer(agent, callback)

        # Verify list_tools decorator was called
        mock_server_instance.list_tools.assert_called_once()

        # Get the handler function
        decorator_mock = mock_server_instance.list_tools.return_value
        handler_func = decorator_mock.call_args[0][0]

        # Execute handler
        tools = await handler_func()

        assert len(tools) == 1
        # In mock, tools[0] is result of mock_types.Tool(...)
        mock_types.Tool.assert_called()
        call_kwargs = mock_types.Tool.call_args[1]
        assert call_kwargs["name"] == "myagent"
        assert call_kwargs["description"] == "G"


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
    with patch.dict(
        sys.modules, {"mcp": mock_mcp, "mcp.server": MagicMock(Server=mock_server_cls), "mcp.types": mock_types}
    ):
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

        # Access the server property to avoid F841 and verify it returns the instance
        assert server.server == mock_server_instance


@pytest.mark.asyncio
async def test_execution_callback_failure() -> None:
    """Test behavior when the runner callback raises an exception."""
    mock_mcp = MagicMock(name="mock_mcp")
    mock_server_cls = MagicMock(name="mock_server_cls")
    mock_server_instance = MagicMock(name="mock_server_instance")
    mock_server_cls.return_value = mock_server_instance
    mock_types = MagicMock(name="mock_types")
    mock_mcp.types = mock_types

    agent = AgentDefinition(id="a", name="ErrAgent", role="R", goal="G")
    # Callback raises error
    callback = AsyncMock(side_effect=ValueError("Execution failed"))

    with patch.dict(
        sys.modules, {"mcp": mock_mcp, "mcp.server": MagicMock(Server=mock_server_cls), "mcp.types": mock_types}
    ):
        _ = CoreasonMCPServer(agent, callback)

        decorator_mock = mock_server_instance.call_tool.return_value
        handler_func = decorator_mock.call_args[0][0]

        # The handler should propagate the exception (or handle it? Implementation doesn't handle it, so it propagates)
        with pytest.raises(ValueError, match="Execution failed"):
            await handler_func("erragent", {})


@pytest.mark.asyncio
async def test_execution_wrong_tool_name() -> None:
    """Test calling the handler with the wrong tool name."""
    mock_mcp = MagicMock()
    mock_server_cls = MagicMock()
    mock_server_instance = MagicMock()
    mock_server_cls.return_value = mock_server_instance
    mock_types = MagicMock()

    agent = AgentDefinition(id="a", name="MyAgent", role="R", goal="G")
    callback = AsyncMock()

    with patch.dict(
        sys.modules, {"mcp": mock_mcp, "mcp.server": MagicMock(Server=mock_server_cls), "mcp.types": mock_types}
    ):
        _ = CoreasonMCPServer(agent, callback)
        decorator_mock = mock_server_instance.call_tool.return_value
        handler_func = decorator_mock.call_args[0][0]

        # Call with wrong name
        with pytest.raises(ValueError, match="Unknown tool: wrong_name"):
            await handler_func("wrong_name", {})


@pytest.mark.asyncio
async def test_run_stdio() -> None:
    """Test running server via stdio transport."""
    mock_mcp = MagicMock(name="mock_mcp")
    mock_server_cls = MagicMock(name="mock_server_cls")
    mock_server_instance = MagicMock(name="mock_server_instance")
    mock_server_instance.run = AsyncMock()
    mock_server_cls.return_value = mock_server_instance
    mock_types = MagicMock(name="mock_types")

    mock_stdio = MagicMock(name="mock_stdio")
    mock_stdio_server = MagicMock(name="stdio_server")
    mock_stdio_server.return_value.__aenter__.return_value = ("read", "write")
    mock_stdio.stdio_server = mock_stdio_server

    agent = AgentDefinition(id="a", name="My Agent", role="R", goal="G")
    callback = AsyncMock()

    with patch.dict(
        sys.modules, {
            "mcp": mock_mcp,
            "mcp.server": MagicMock(Server=mock_server_cls),
            "mcp.types": mock_types,
            "mcp.server.stdio": mock_stdio
        }
    ):
        server = CoreasonMCPServer(agent, callback)
        await server.run_stdio()

        # Verify stdio_server context manager usage
        mock_stdio_server.assert_called_once()

        # Verify server.run called with correct args
        mock_server_instance.run.assert_awaited_once()
        args, _ = mock_server_instance.run.call_args
        assert args[0] == "read"
        assert args[1] == "write"

        # Verify init options creation
        mock_server_instance.create_initialization_options.assert_called_once()


@pytest.mark.asyncio
async def test_run_stdio_missing_dependency() -> None:
    """Test run_stdio raises ImportError when mcp.server.stdio is missing."""
    mock_mcp = MagicMock(name="mock_mcp")
    mock_server_cls = MagicMock(name="mock_server_cls")
    mock_server_instance = MagicMock(name="mock_server_instance")
    mock_server_cls.return_value = mock_server_instance
    mock_types = MagicMock(name="mock_types")

    # We only mock up to mcp.types and mcp.server, but ensure mcp.server.stdio is missing
    # Since we are mocking sys.modules, if we don't provide mcp.server.stdio, importing it might fail if not careful.
    # But wait, 'from mcp.server.stdio import stdio_server'.
    # We need to simulate that specific import failure.

    with patch.dict(
        sys.modules,
        {
            "mcp": mock_mcp,
            "mcp.server": MagicMock(Server=mock_server_cls),
            "mcp.types": mock_types,
            # We explicitly ensure mcp.server.stdio is NOT in sys.modules
            # And accessing it via import raises ImportError.
        },
    ):
        # We need to make sure the import statement fails.
        # Ideally we wrap the import mechanism, but simplest is to just not provide it
        # AND ensure the parent package doesn't automatically provide it.
        # But 'from mcp.server.stdio' requires 'mcp.server.stdio' module.

        # Let's try to patch builtins.__import__ or simpler: just assume if we don't put it in sys.modules
        # and we mocked the parent, it might fail? No, MagicMock usually creates children.
        pass

    # Better approach: Patch sys.modules with a side_effect for that specific module?
    # Or just use patch.dict and ensure 'mcp.server.stdio' maps to None?
    # No, mapping to None usually indicates "module not found" in Python import system (for relative imports etc).

    with patch.dict(sys.modules, {"mcp.server.stdio": None}):
        agent = AgentDefinition(id="a", name="My Agent", role="R", goal="G")
        # We need __init__ to succeed, so we need mcp, mcp.server, mcp.types
        # But run_stdio does the import.

        # We need to ensure __init__ works.
        # If we patch sys.modules with mcp, mcp.server, mcp.types, but map mcp.server.stdio to None.

        with patch.dict(
            sys.modules,
            {
                "mcp": mock_mcp,
                "mcp.server": MagicMock(Server=mock_server_cls),
                "mcp.types": mock_types,
                "mcp.server.stdio": None,
            },
        ):
            server = CoreasonMCPServer(agent, AsyncMock())
            with pytest.raises(ImportError, match="pip install coreason-manifest\\[mcp\\]"):
                await server.run_stdio()
