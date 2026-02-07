# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import json
import re
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from coreason_manifest.spec.v2.definitions import AgentDefinition

if TYPE_CHECKING:
    import contextlib

    with contextlib.suppress(ImportError):
        from mcp.server import Server  # noqa: F401


def create_mcp_tool_definition(agent: AgentDefinition) -> dict[str, Any]:
    """
    Converts a Coreason Agent Definition into an MCP Tool structure.
    Returns a dictionary compatible with MCP's 'Tool' type.
    """
    # Sanitize name: lowercase, replace non-alphanumeric with _, collapse _, strip _
    name = re.sub(r"[^a-zA-Z0-9_-]", "_", agent.name).lower()
    name = re.sub(r"_+", "_", name).strip("_")

    # Description: use backstory or goal or generic fallback
    description = agent.backstory or agent.goal or f"Agent {agent.name}"

    # Input Schema: use agent.interface.inputs
    # We assume agent.interface.inputs is a valid JSON Schema object.
    input_schema = agent.interface.inputs

    return {"name": name, "description": description, "inputSchema": input_schema}


class CoreasonMCPServer:
    """
    An MCP Server adapter that exposes a Coreason Agent as an MCP Tool.
    """

    _server: Any

    def __init__(self, agent: AgentDefinition, runner_callback: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]):
        """
        Initialize the MCP Server.

        Args:
            agent: The AgentDefinition to expose.
            runner_callback: Async function to execute the agent.
                             Receives arguments dict, returns result dict.
        """
        try:
            import mcp.types as types
            from mcp.server import Server
        except ImportError:
            raise ImportError(
                "The 'mcp' package is required to use CoreasonMCPServer. "
                "Install it with `pip install coreason-manifest[mcp]`."
            ) from None

        self.agent = agent
        self.runner_callback = runner_callback
        self.tool_def = create_mcp_tool_definition(agent)

        # Initialize Server
        self._server = Server(f"coreason-agent-{self.tool_def['name']}")

        @self._server.list_tools()  # type: ignore[misc]
        async def handle_list_tools() -> list[types.Tool]:
            return [
                types.Tool(
                    name=self.tool_def["name"],
                    description=self.tool_def["description"],
                    inputSchema=self.tool_def["inputSchema"],
                )
            ]

        @self._server.call_tool()  # type: ignore[misc]
        async def handle_call_tool(
            name: str, arguments: dict[str, Any] | None
        ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            if name != self.tool_def["name"]:
                raise ValueError(f"Unknown tool: {name}")

            args = arguments or {}
            result = await self.runner_callback(args)

            # Convert result to string representation for TextContent
            text = json.dumps(result, ensure_ascii=False, indent=2) if isinstance(result, (dict, list)) else str(result)

            return [types.TextContent(type="text", text=text)]

    @property
    def server(self) -> Any:
        """Returns the underlying MCP Server instance."""
        return self._server
