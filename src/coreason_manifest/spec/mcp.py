from typing import Annotated, Any, Literal

from pydantic import Field, StringConstraints

from coreason_manifest.spec.ontology import CoreasonBaseState


class MCPToolDefinition(CoreasonBaseState):
    """AGENT INSTRUCTION: A formal Substrate Projection representing an executable Model Context Protocol (MCP) tool."""

    topology_class: Literal["mcp_tool_definition"] = Field(default="mcp_tool_definition")
    event_cid: Annotated[str, StringConstraints(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")] = Field(
        default="mcp_tool_cid",
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark binding this node to the Merkle-DAG.",
    )
    prior_event_hash: (
        Annotated[str, StringConstraints(min_length=1, max_length=128, pattern="^[a-f0-9]{64}$")] | None
    ) = Field(
        default=None,
        description="The RFC 8785 Canonical hash of the immediate causal ancestor event. Null for genesis nodes.",
    )
    timestamp: float = Field(default=0.0)
    name: Annotated[str, StringConstraints(max_length=64, pattern="^[a-zA-Z0-9_-]+$")]
    description: Annotated[str, StringConstraints(max_length=2048)]
    input_schema: dict[str, Any] = Field(
        alias="inputSchema", description="The JSON Schema payload mirroring our Pydantic limits."
    )
