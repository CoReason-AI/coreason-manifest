# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

"""Pydantic models for the Coreason Manifest system.

These models define the structure and validation rules for the Agent Manifest
(OAS). They represent the source of truth for Agent definitions.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Any, Dict, List, Literal, Mapping, Optional, Tuple, Union
from uuid import UUID

from pydantic import (
    AfterValidator,
    AnyUrl,
    ConfigDict,
    Field,
    PlainSerializer,
    field_validator,
    model_validator,
)
from typing_extensions import Annotated

from coreason_manifest.definitions.base import CoReasonBaseModel
from coreason_manifest.definitions.topology import Edge, Node, validate_edge_integrity

# SemVer Regex pattern (simplified for standard SemVer)
# Modified to accept optional 'v' or 'V' prefix (multiple allowed) for input normalization
SEMVER_REGEX = (
    r"^[vV]*(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)


def normalize_version(v: str) -> str:
    """Normalize version string by recursively stripping 'v' or 'V' prefix.

    Args:
        v: The version string to normalize.

    Returns:
        The normalized version string without 'v' prefix.
    """
    while v.lower().startswith("v"):
        v = v[1:]
    return v


# Annotated type that validates SemVer regex (allowing multiple v) then normalizes to strict SemVer (no v)
VersionStr = Annotated[
    str,
    Field(pattern=SEMVER_REGEX),
    AfterValidator(normalize_version),
]

# Reusable immutable dictionary type
ImmutableDict = Annotated[
    Mapping[str, Any],
    AfterValidator(lambda x: MappingProxyType(x)),
    PlainSerializer(lambda x: dict(x), return_type=Dict[str, Any]),
]


# Strict URI type that serializes to string
StrictUri = Annotated[
    AnyUrl,
    PlainSerializer(lambda x: str(x), return_type=str),
]


class AgentMetadata(CoReasonBaseModel):
    """Metadata for the Agent.

    Attributes:
        id: Unique Identifier for the Agent (UUID).
        version: Semantic Version of the Agent.
        name: Name of the Agent.
        author: Author of the Agent.
        created_at: Creation timestamp (ISO 8601).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID = Field(..., description="Unique Identifier for the Agent (UUID).")
    version: VersionStr = Field(..., description="Semantic Version of the Agent.")
    name: str = Field(..., min_length=1, description="Name of the Agent.")
    author: str = Field(..., min_length=1, description="Author of the Agent.")
    created_at: datetime = Field(..., description="Creation timestamp (ISO 8601).")
    requires_auth: bool = Field(default=False, description="Whether the agent requires user authentication.")


class Persona(CoReasonBaseModel):
    """Definition of an Agent Persona.

    Attributes:
        name: Name of the persona.
        description: Description of the persona.
        directives: List of specific instructions or directives.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(..., description="Name of the persona.")
    description: str = Field(..., description="Description of the persona.")
    directives: List[str] = Field(..., description="List of specific instructions or directives.")


class EventSchema(CoReasonBaseModel):
    """Defines the structure of an intermediate event emitted by the agent."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(..., description="Event name (e.g., 'SEARCH_PROGRESS').")
    data_schema: ImmutableDict = Field(..., description="JSON Schema of the event payload.")


class AgentInterface(CoReasonBaseModel):
    """Interface definition for the Agent.

    Attributes:
        inputs: Typed arguments the agent accepts (JSON Schema).
        outputs: Typed structure of the result.
        events: List of intermediate events this agent produces during execution.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    inputs: ImmutableDict = Field(..., description="Typed arguments the agent accepts (JSON Schema).")
    outputs: ImmutableDict = Field(..., description="Typed structure of the result.")
    events: List[EventSchema] = Field(
        default_factory=list, description="List of intermediate events this agent produces during execution."
    )
    injected_params: List[str] = Field(default_factory=list, description="List of parameters injected by the system.")


class ModelConfig(CoReasonBaseModel):
    """LLM Configuration parameters.

    Attributes:
        model: The LLM model identifier.
        temperature: Temperature for generation.
        system_prompt: The default system prompt/persona for the agent.
        persona: The full persona definition (name, description, directives).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    model: str = Field(..., description="The LLM model identifier.")
    temperature: float = Field(..., ge=0.0, le=2.0, description="Temperature for generation.")
    system_prompt: Optional[str] = Field(None, description="The default system prompt/persona for the agent.")
    persona: Optional[Persona] = Field(None, description="The full persona definition (name, description, directives).")


class AgentRuntimeConfig(CoReasonBaseModel):
    """Configuration of the Agent execution.

    Attributes:
        nodes: A collection of execution units (Agents, Tools, Logic).
        edges: Directed connections defining control flow.
        entry_point: The ID of the starting node.
        llm_config: Specific LLM parameters.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    nodes: List[Node] = Field(default_factory=list, description="A collection of execution units.")
    edges: List[Edge] = Field(default_factory=list, description="Directed connections defining control flow.")
    entry_point: Optional[str] = Field(None, description="The ID of the starting node.")
    llm_config: ModelConfig = Field(..., alias="model_config", description="Specific LLM parameters.")
    system_prompt: Optional[str] = Field(None, description="The global system prompt/instruction for the agent.")

    @model_validator(mode="after")
    def validate_topology_or_atomic(self) -> AgentRuntimeConfig:
        """Ensure valid configuration: either a Graph or an Atomic Agent."""
        has_nodes = len(self.nodes) > 0
        has_entry = self.entry_point is not None

        if has_nodes:
            if not has_entry:
                raise ValueError("Graph execution requires an 'entry_point'.")
        else:
            # Atomic Agent: Must have a system prompt (either global or in model_config)
            has_global_prompt = self.system_prompt is not None
            has_model_prompt = self.llm_config.system_prompt is not None

            if not (has_global_prompt or has_model_prompt):
                raise ValueError("Atomic Agents require a system_prompt (global or in model_config).")

        return self

    @model_validator(mode="after")
    def validate_topology_integrity(self) -> AgentRuntimeConfig:
        """Ensure that edges connect existing nodes."""
        validate_edge_integrity(self.nodes, self.edges)
        return self

    @field_validator("nodes")
    @classmethod
    def validate_unique_node_ids(cls, v: List[Node]) -> List[Node]:
        """Ensure all node IDs are unique.

        Args:
            v: The list of nodes to validate.

        Returns:
            The validated list of nodes.

        Raises:
            ValueError: If duplicate node IDs are found.
        """
        ids = [node.id for node in v]
        if len(ids) != len(set(ids)):
            # Find duplicates
            seen = set()
            dupes = set()
            for x in ids:
                if x in seen:
                    dupes.add(x)
                seen.add(x)
            raise ValueError(f"Duplicate node IDs found: {', '.join(dupes)}")
        return v


class ToolRiskLevel(str, Enum):
    """Risk level for the tool."""

    SAFE = "safe"
    STANDARD = "standard"
    CRITICAL = "critical"


class ToolRequirement(CoReasonBaseModel):
    """Requirement for an MCP tool.

    Attributes:
        uri: The MCP endpoint URI.
        hash: Integrity check for the tool definition (SHA256).
        scopes: List of permissions required.
        risk_level: The risk level of the tool.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    uri: StrictUri = Field(..., description="The MCP endpoint URI.")
    hash: str = Field(
        ..., pattern=r"^[a-fA-F0-9]{64}$", description="Integrity check for the tool definition (SHA256)."
    )
    scopes: List[str] = Field(..., description="List of permissions required.")
    risk_level: ToolRiskLevel = Field(..., description="The risk level of the tool.")


class InlineToolDefinition(CoReasonBaseModel):
    """Definition of an inline tool.

    Attributes:
        name: Name of the tool.
        description: Description of the tool.
        parameters: JSON Schema of parameters.
        type: The type of the tool (must be 'function').
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(..., description="Name of the tool.")
    description: str = Field(..., description="Description of the tool.")
    parameters: Dict[str, Any] = Field(..., description="JSON Schema of parameters.")
    type: Literal["function"] = Field("function", description="The type of the tool (must be 'function').")


class AgentDependencies(CoReasonBaseModel):
    """External dependencies for the Agent.

    Attributes:
        tools: List of MCP tool requirements.
        libraries: List of Python packages required (if code execution is allowed).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    tools: List[Union[ToolRequirement, InlineToolDefinition]] = Field(
        default_factory=list, description="List of MCP tool requirements."
    )
    libraries: Tuple[str, ...] = Field(
        default_factory=tuple, description="List of Python packages required (if code execution is allowed)."
    )


class PolicyConfig(CoReasonBaseModel):
    """Governance policy configuration.

    Attributes:
        budget_caps: Dictionary defining budget limits (e.g., {"total_cost": 10.0, "total_tokens": 1000}).
        human_in_the_loop: List of Node IDs that require human approval.
        allowed_domains: List of allowed domains for external access.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    budget_caps: Dict[str, float] = Field(default_factory=dict, description="Budget limits.")
    human_in_the_loop: List[str] = Field(default_factory=list, description="Node IDs requiring human approval.")
    allowed_domains: List[str] = Field(default_factory=list, description="Allowed domains for external access.")


class TraceLevel(str, Enum):
    """Level of tracing detail."""

    FULL = "full"
    METADATA_ONLY = "metadata_only"
    NONE = "none"


class ObservabilityConfig(CoReasonBaseModel):
    """Observability configuration.

    Attributes:
        trace_level: Level of tracing detail.
        retention_policy: Retention policy identifier (e.g., '30_days').
        encryption_key_id: Optional ID of the key used for log encryption.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    trace_level: TraceLevel = Field(default=TraceLevel.FULL, description="Level of tracing detail.")
    retention_policy: str = Field(default="30_days", description="Retention policy identifier.")
    encryption_key_id: Optional[str] = Field(None, description="Optional ID of the key used for log encryption.")


class AgentDefinition(CoReasonBaseModel):
    """The Root Object for the CoReason Agent Manifest.

    Attributes:
        metadata: Metadata for the Agent.
        interface: Interface definition for the Agent.
        config: Configuration of the Agent execution.
        dependencies: External dependencies for the Agent.
        integrity_hash: SHA256 hash of the source code.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        title="CoReason Agent Manifest",
        json_schema_extra={
            "$id": "https://coreason.ai/schemas/agent.schema.json",
            "description": "The definitive source of truth for CoReason Agent definitions.",
        },
    )

    metadata: AgentMetadata
    interface: AgentInterface
    config: AgentRuntimeConfig
    dependencies: AgentDependencies
    policy: Optional[PolicyConfig] = Field(None, description="Governance policy configuration.")
    observability: Optional[ObservabilityConfig] = Field(None, description="Observability configuration.")
    custom_metadata: Optional[Dict[str, Any]] = Field(
        None, description="Container for arbitrary metadata extensions without breaking validation."
    )
    integrity_hash: str = Field(
        ...,
        pattern=r"^[a-fA-F0-9]{64}$",
        description="SHA256 hash of the source code.",
    )

    @model_validator(mode="after")
    def validate_auth_requirements(self) -> AgentDefinition:
        """Validate that agents requiring auth have user_context injected."""
        if self.metadata.requires_auth:
            if "user_context" not in self.interface.injected_params:
                raise ValueError("Agent requires authentication but 'user_context' is not an injected parameter.")
        return self
