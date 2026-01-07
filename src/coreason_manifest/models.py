# Prosperity-3.0
from __future__ import annotations

from datetime import datetime
from types import MappingProxyType
from typing import Any, Dict, List, Mapping, Optional, Tuple
from uuid import UUID

from pydantic import (
    AfterValidator,
    AnyUrl,
    BaseModel,
    ConfigDict,
    Field,
    PlainSerializer,
    field_validator,
)
from typing_extensions import Annotated

# SemVer Regex pattern (simplified for standard SemVer)
# Modified to accept optional 'v' or 'V' prefix (multiple allowed) for input normalization
SEMVER_REGEX = (
    r"^[vV]*(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)


def normalize_version(v: str) -> str:
    """Normalize version string by recursively stripping 'v' or 'V' prefix."""
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


class AgentMetadata(BaseModel):
    """Metadata for the Agent."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID = Field(..., description="Unique Identifier for the Agent (UUID).")
    version: VersionStr = Field(..., description="Semantic Version of the Agent.")
    name: str = Field(..., min_length=1, description="Name of the Agent.")
    author: str = Field(..., min_length=1, description="Author of the Agent.")
    created_at: datetime = Field(..., description="Creation timestamp (ISO 8601).")


class AgentInterface(BaseModel):
    """Interface definition for the Agent."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    inputs: ImmutableDict = Field(..., description="Typed arguments the agent accepts (JSON Schema).")
    outputs: ImmutableDict = Field(..., description="Typed structure of the result.")


class Step(BaseModel):
    """A single step in the execution graph."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(..., min_length=1, description="Unique identifier for the step.")
    description: Optional[str] = Field(None, description="Description of the step.")


class ModelConfig(BaseModel):
    """LLM Configuration parameters."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    model: str = Field(..., description="The LLM model identifier.")
    temperature: float = Field(..., ge=0.0, le=2.0, description="Temperature for generation.")


class AgentTopology(BaseModel):
    """Topology of the Agent execution."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    steps: Tuple[Step, ...] = Field(..., description="A directed acyclic graph (DAG) of execution steps.")
    llm_config: ModelConfig = Field(..., alias="model_config", description="Specific LLM parameters.")

    @field_validator("steps")
    @classmethod
    def validate_unique_step_ids(cls, v: Tuple[Step, ...]) -> Tuple[Step, ...]:
        """Ensure all step IDs are unique."""
        ids = [step.id for step in v]
        if len(ids) != len(set(ids)):
            # Find duplicates
            seen = set()
            dupes = set()
            for x in ids:
                if x in seen:
                    dupes.add(x)
                seen.add(x)
            raise ValueError(f"Duplicate step IDs found: {', '.join(dupes)}")
        return v


class AgentDependencies(BaseModel):
    """External dependencies for the Agent."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    # Use AnyUrl to enforce strictly valid URIs
    # Changed to List[StrictUri] to strictly enforce valid URI formatting and string serialization
    tools: List[StrictUri] = Field(default_factory=list, description="List of MCP capability URIs required.")
    libraries: Tuple[str, ...] = Field(
        default_factory=tuple, description="List of Python packages required (if code execution is allowed)."
    )


class AgentDefinition(BaseModel):
    """The Root Object for the CoReason Agent Manifest."""

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
    topology: AgentTopology
    dependencies: AgentDependencies
    integrity_hash: str = Field(
        ...,
        pattern=r"^[a-fA-F0-9]{64}$",
        description="SHA256 hash of the source code.",
    )
