"""
Native Model Context Protocol (MCP) Integration for the CoReason Manifest.

This module defines the core MCP connection primitives and universal canvas API tools.
"""

from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import Field, HttpUrl, model_validator

from coreason_manifest.core.common.base import CoreasonModel
from coreason_manifest.presentation.scivis.scivis_provenance import ActorIdentity


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


class MCPToolName(StrEnum):
    """Names of the Universal Canvas API tools."""

    CANVAS_ADD_ELEMENT = "CANVAS_ADD_ELEMENT"
    CANVAS_UPDATE_ELEMENT = "CANVAS_UPDATE_ELEMENT"
    CANVAS_REMOVE_ELEMENT = "CANVAS_REMOVE_ELEMENT"
    CANVAS_GROUP_ELEMENTS = "CANVAS_GROUP_ELEMENTS"
    CANVAS_ADD_CONNECTION = "CANVAS_ADD_CONNECTION"
    CANVAS_APPLY_STYLE = "CANVAS_APPLY_STYLE"
    CANVAS_IMPORT_ARTIFACT = "CANVAS_IMPORT_ARTIFACT"
    CANVAS_ADD_MATH_NODE = "CANVAS_ADD_MATH_NODE"
    CANVAS_UPDATE_MATH_NODE = "CANVAS_UPDATE_MATH_NODE"


class MCPOperation(CoreasonModel):
    """An atomic design action executed on a headless canvas."""

    operation_id: str = Field(..., description="Unique ID for tracing and logging this specific action.")
    tool_name: MCPToolName
    target_element_id: str | None = Field(
        default=None, description="The ID of the specific canvas object being mutated. Crucial for targeted edits."
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="The kwargs payload for the tool (e.g., x, y, width, fill_color)."
    )
    actor: ActorIdentity | None = Field(
        default=None, description="Cryptographically tags the specific agent/human issuing this canvas command."
    )

    @model_validator(mode="after")
    def enforce_strict_provenance(self) -> "MCPOperation":
        if (
            self.tool_name in {MCPToolName.CANVAS_ADD_MATH_NODE, MCPToolName.CANVAS_UPDATE_MATH_NODE}
            and self.actor is None
        ):
            raise ValueError("Regulatory SciVis operations require a cryptographically verifiable ActorIdentity.")
        return self

    @model_validator(mode="after")
    def validate_target_element_id(self) -> "MCPOperation":
        requires_id = {
            MCPToolName.CANVAS_UPDATE_ELEMENT,
            MCPToolName.CANVAS_REMOVE_ELEMENT,
            MCPToolName.CANVAS_UPDATE_MATH_NODE,
        }
        if self.tool_name in requires_id and self.target_element_id is None:
            raise ValueError(f"target_element_id cannot be None when tool_name is {self.tool_name}")
        return self


class MCPOperationSequence(CoreasonModel):
    """An ordered, transactional sequence of atomic design actions."""

    sequence_id: str
    operations: list[MCPOperation]
    transaction_mode: Literal["atomic_commit", "sequential_best_effort"] = Field(
        default="atomic_commit",
        description="If atomic, the downstream engine must snapshot the canvas and rollback if any operation fails.",
    )
    expected_canvas_state_hash: str | None = Field(
        default=None,
        description="Ensures the sequence is applied to the correct diagram version to prevent races.",
    )
