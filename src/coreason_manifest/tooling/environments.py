# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION: This file defines the tooling environment schemas. This is a STRICTLY KINEMATIC BOUNDARY.
These schemas govern how the agent mathematically interacts with external or embodied environments. YOU ARE EXPLICITLY
FORBIDDEN from writing raw script executors here. All tool definitions must be bounded by strict JSON-RPC schemas,
permission boundaries, and side-effect profiles."""

import re
from typing import Any, Literal, Self

from pydantic import Field, model_validator

from coreason_manifest.adapters.mcp.schemas import MCPServerManifest
from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.core.primitives import ProfileID
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


class EphemeralNamespacePartition(CoreasonBaseModel):
    """
    A hermetically sealed, ephemeral execution partition for dynamic dependency resolution.
    """

    partition_id: str = Field(min_length=1, description="Unique identifier for this ephemeral partition.")
    execution_runtime: Literal["wasm32-wasi", "riscv32-zkvm", "bpf"] = Field(
        description="The strict virtual machine target mandated for dynamic execution."
    )
    authorized_bytecode_hashes: list[str] = Field(
        min_length=1, description="The explicit whitelist of SHA-256 hashes allowed to execute within this partition."
    )
    max_ttl_seconds: int = Field(
        gt=0, description="The absolute temporal guillotine before the orchestrator drops the context."
    )
    max_vram_mb: int = Field(gt=0, description="The strict physical VRAM ceiling allocated to this partition.")
    allow_network_egress: bool = Field(
        default=False, description="Capability-based flag to allow or mathematically deny network sockets."
    )
    allow_subprocess_spawning: bool = Field(
        default=False, description="Capability-based flag to allow or deny OS-level process spawning."
    )

    @model_validator(mode="after")
    def validate_cryptographic_hashes(self) -> Self:
        for h in self.authorized_bytecode_hashes:
            if not re.match(r"^[a-f0-9]{64}$", h):
                raise ValueError(f"Invalid SHA-256 hash in whitelist: {h}")
        return self


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
    ephemeral_partitions: list[EphemeralNamespacePartition] = Field(
        default_factory=list,
        description="Hermetically sealed memory boundaries for dynamically resolved scripts and PEFT adapters.",
    )

    @model_validator(mode="after")
    def verify_unique_tool_namespaces(self) -> Any:
        tool_names = {t.tool_name for t in self.native_tools}
        if len(tool_names) < len(self.native_tools):
            raise ValueError("Tool names within an ActionSpace must be strictly unique.")
        return self


class OntologicalSurfaceProjection(CoreasonBaseModel):
    """
    A mathematically bounded, declarative subgraph of all ToolDefinitions and
    MCPServerManifests currently valid for the agent's ProfileID.
    """

    projection_id: str = Field(
        min_length=1, description="A cryptographic Lineage Watermark bounding this specific capability set."
    )
    action_spaces: list[ActionSpace] = Field(
        default_factory=list, description="The full, machine-readable declaration of accessible tools and MCP servers."
    )
    supported_personas: list[ProfileID] = Field(
        default_factory=list, description="The strict list of foundational model personas available."
    )

    @model_validator(mode="after")
    def verify_unique_action_spaces(self) -> Self:
        space_ids = {space.action_space_id for space in self.action_spaces}
        if len(space_ids) < len(self.action_spaces):
            raise ValueError("Action spaces within a projection must have strictly unique action_space_ids.")
        # Mathematically sort to guarantee deterministic hashing
        object.__setattr__(self, "action_spaces", sorted(self.action_spaces, key=lambda x: x.action_space_id))
        object.__setattr__(self, "supported_personas", sorted(self.supported_personas))
        return self
