# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from typing import Any, Literal

from pydantic import Field, model_validator

from coreason_manifest.adapters.mcp.schemas import MCPServerManifest
from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.tooling.schemas import ToolDefinition

type MCPTransport = Literal["stdio", "sse", "http"]


class MCPClientBinding(CoreasonBaseModel):
    """
    Binding configuration for a Model Context Protocol (MCP) server.
    """

    server_uri: str = Field(description="The URI or command path to the MCP server.")
    transport_type: MCPTransport = Field(description="The transport protocol used to communicate with the MCP server.")
    allowed_mcp_tools: list[str] | None = Field(
        default=None,
        description=(
            "An explicit whitelist of tools the agent is allowed to invoke from this server. "
            "If None, all discovered tools are allowed."
        ),
    )


class ActionSpace(CoreasonBaseModel):
    """
    A curated environment of tools accessible to an agent or node.
    """

    action_space_id: str = Field(description="The unique identifier for this curated environment of tools.")
    native_tools: list[ToolDefinition] = Field(
        default_factory=list, description="The list of discrete, natively defined tools available in this space."
    )
    mcp_servers: list[MCPServerManifest] = Field(
        default_factory=list,
        description="The array of verified external Model Context Protocol servers mounted into this action space.",
    )

    @model_validator(mode="after")
    def verify_unique_tool_namespaces(self) -> Any:
        tool_names = {t.tool_name for t in self.native_tools}
        if len(tool_names) < len(self.native_tools):
            raise ValueError("Tool names within an ActionSpace must be strictly unique.")
        return self
