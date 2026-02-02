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

These models define the structure and validation rules for the Coreason Agent Manifest
(CAM). They represent the source of truth for Agent definitions.
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Any, Dict, List, Literal, Mapping, Optional, Tuple, Union
from uuid import UUID

import jsonschema
from jsonschema import ValidationError
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
from coreason_manifest.definitions.deployment import DeploymentConfig
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


class AgentStatus(str, Enum):
    """The lifecycle status of the agent."""

    DRAFT = "draft"
    PUBLISHED = "published"


class CapabilityType(str, Enum):
    """The interaction mode for the capability."""

    ATOMIC = "atomic"
    STREAMING = "streaming"


class DeliveryMode(str, Enum):
    """The delivery mechanism for the capability response."""

    REQUEST_RESPONSE = "request_response"
    SERVER_SENT_EVENTS = "server_sent_events"


class AgentCapability(CoReasonBaseModel):
    """Defines a specific mode of interaction for the agent.

    Attributes:
        name: Unique name for this capability.
        type: Interaction mode.
        description: What this mode does.
        inputs: Typed arguments the agent accepts (JSON Schema).
        outputs: Typed structure of the result.
        events: List of intermediate events this agent produces during execution.
        injected_params: List of parameters injected by the system.
        delivery_mode: The mechanism used to deliver the response.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(..., description="Unique name for this capability.")
    type: CapabilityType = Field(..., description="Interaction mode.")
    description: str = Field(..., description="What this mode does.")

    inputs: ImmutableDict = Field(..., description="Typed arguments the agent accepts (JSON Schema).")
    outputs: ImmutableDict = Field(..., description="Typed structure of the result.")
    delivery_mode: DeliveryMode = Field(
        default=DeliveryMode.REQUEST_RESPONSE, description="The mechanism used to deliver the response."
    )
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
        capabilities: List of supported capabilities.
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
    capabilities: List[AgentCapability] = Field(..., description="List of supported capabilities.")
    config: AgentRuntimeConfig
    dependencies: AgentDependencies
    policy: Optional[PolicyConfig] = Field(None, description="Governance policy configuration.")
    deployment: Optional[DeploymentConfig] = Field(None, description="Runtime deployment settings")
    observability: Optional[ObservabilityConfig] = Field(None, description="Observability configuration.")
    custom_metadata: Optional[Dict[str, Any]] = Field(
        None, description="Container for arbitrary metadata extensions without breaking validation."
    )
    status: AgentStatus = Field(default=AgentStatus.DRAFT, description="The lifecycle status of the agent.")
    integrity_hash: Optional[str] = Field(
        None,
        description="SHA256 hash of the source code. Required if status is 'published'.",
    )

    @field_validator("capabilities")
    @classmethod
    def validate_capabilities(cls, v: List[AgentCapability]) -> List[AgentCapability]:
        """Ensure at least one capability exists and names are unique."""
        if not v:
            raise ValueError("Agent must have at least one capability.")

        names = [cap.name for cap in v]
        if len(names) != len(set(names)):
            raise ValueError(f"Duplicate capability names found: {names}")
        return v

    @model_validator(mode="after")
    def validate_auth_requirements(self) -> AgentDefinition:
        """Validate that agents requiring auth have user_context injected."""
        if self.metadata.requires_auth:
            for cap in self.capabilities:
                if "user_context" not in cap.injected_params:
                    raise ValueError(
                        f"Agent requires authentication but capability '{cap.name}' does not inject 'user_context'."
                    )
        return self

    @model_validator(mode="after")
    def validate_integrity_hash_if_published(self) -> AgentDefinition:
        """Ensure integrity_hash is present and valid if published."""
        if self.status == AgentStatus.PUBLISHED:
            if self.integrity_hash is None:
                raise ValueError("Field 'integrity_hash' is required when status is 'published'.")
            if not re.match(r"^[a-fA-F0-9]{64}$", self.integrity_hash):
                raise ValueError(f"String should match pattern '^[a-fA-F0-9]{{64}}$' (got '{self.integrity_hash}')")
        return self

    @model_validator(mode="after")
    def validate_config_completeness_if_published(self) -> AgentDefinition:
        """Ensure config is complete (entry points, prompts) if published."""
        if self.status == AgentStatus.PUBLISHED:
            cfg = self.config
            has_nodes = len(cfg.nodes) > 0
            has_entry = cfg.entry_point is not None

            if has_nodes:
                if not has_entry:
                    raise ValueError("Graph execution requires an 'entry_point' when published.")
            else:
                # Atomic Agent checks
                has_global_prompt = cfg.system_prompt is not None
                has_model_prompt = cfg.llm_config.system_prompt is not None

                if not (has_global_prompt or has_model_prompt):
                    raise ValueError("Atomic Agents require a system_prompt when published.")

        return self

    @model_validator(mode="after")
    def validate_topology_if_published(self) -> AgentDefinition:
        """Ensure topology integrity if published."""
        if self.status == AgentStatus.PUBLISHED:
            validate_edge_integrity(self.config.nodes, self.config.edges)
        return self

    def validate_input(self, capability_name: str, payload: Dict[str, Any]) -> bool:
        """Validates a payload against the schema of a specific capability.

        This acts as a 'Dry Run' to ensure the input meets the contract requirements
        before execution.

        Args:
            capability_name: The name of the capability to validate against.
            payload: The input dictionary to validate.

        Returns:
            True if valid.

        Raises:
            ValueError: If the capability_name is not found.
            jsonschema.ValidationError: If the payload does not match the schema.
        """
        # 1. Find the capability
        # Iterate through self.capabilities to find the one matching capability_name
        target_capability = next((c for c in self.capabilities if c.name == capability_name), None)

        # 2. If not found:
        if not target_capability:
            raise ValueError(f"Capability '{capability_name}' not found in agent '{self.metadata.name}'.")

        # 3. If found:
        # Use jsonschema.validate(instance=payload, schema=target_capability.inputs)
        # Note: capability.inputs is an ImmutableDict, so we cast to dict for jsonschema.
        jsonschema.validate(instance=payload, schema=dict(target_capability.inputs))

        # 4. Return True
        return True
