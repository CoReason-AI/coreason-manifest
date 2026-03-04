"""
Native Model Context Protocol (MCP) Integration for the CoReason Manifest.

This module defines the core MCP connection primitives.
"""

from typing import Annotated, Any, Literal

from pydantic import Field, HttpUrl

from coreason_manifest.core.common.base import CoreasonModel


class StdioTransportConfig(CoreasonModel):
    """Configuration for local Stdio-based MCP transport."""

    type: Literal["stdio"] = "stdio"
    command: str = Field(..., description="The command executable to run (e.g., 'node', 'python').")
    args: list[str] = Field(default_factory=list, description="List of arguments to pass to the command.")
    env_vars: dict[str, str] = Field(
        default_factory=dict, description="Environment variables required by the transport."
    )


class SSETransportConfig(CoreasonModel):
    """Configuration for remote SSE-based MCP transport."""

    type: Literal["sse"] = "sse"
    uri: HttpUrl = Field(..., description="The HTTP URL endpoint for the SSE connection.")
    headers: dict[str, str] = Field(default_factory=dict, description="HTTP headers, e.g., for authentication.")


MCPTransport = Annotated[
    StdioTransportConfig | SSETransportConfig,
    Field(discriminator="type", description="Polymorphic transport configuration."),
]


class MCPServerConfig(CoreasonModel):
    """Configuration definition for connecting to an MCP Server."""

    server_id: str = Field(..., description="A unique identifier for this server instance.")
    transport: MCPTransport
    required_capabilities: list[str] = Field(
        default_factory=lambda: ["tools", "resources", "prompts"],
        description="A list of capabilities required from the MCP server.",
    )


class MCPResourceList(CoreasonModel):
    """A collection of Semantic Memory resource URIs provided by a specific MCP server."""

    server_id: str = Field(..., description="The ID of the MCP server providing these resources.")
    uris: list[str] = Field(default_factory=list, description="List of resource URIs available to the agent.")


class MCPPromptRef(CoreasonModel):
    """A dynamic reference to an MCP-provided prompt template."""

    server_id: str = Field(..., description="The ID of the MCP server providing this prompt.")
    prompt_name: str = Field(..., description="The name of the prompt template.")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Arguments to fill the prompt template.")
    fallback_persona: str | None = Field(None, description="A fallback persona if the prompt fails to load.")
    prompt_hash: str | None = Field(None, description="Cryptographic hash for prompt integrity verification.")
