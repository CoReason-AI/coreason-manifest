# Prosperity-3.0
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

# SemVer Regex pattern (simplified for standard SemVer)
SEMVER_REGEX = (
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)


class AgentMetadata(BaseModel):
    """Metadata for the Agent."""

    id: UUID = Field(..., description="Unique Identifier for the Agent (UUID).")
    version: str = Field(..., description="Semantic Version of the Agent.")
    name: str = Field(..., description="Name of the Agent.")
    author: str = Field(..., description="Author of the Agent.")
    created_at: str = Field(..., description="Creation timestamp (ISO 8601).")

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        if not re.match(SEMVER_REGEX, v):
            raise ValueError(f"Version '{v}' is not a valid SemVer string.")
        return v


class AgentInterface(BaseModel):
    """Interface definition for the Agent."""

    inputs: Dict[str, Any] = Field(..., description="Typed arguments the agent accepts (JSON Schema).")
    outputs: Dict[str, Any] = Field(..., description="Typed structure of the result.")


class Step(BaseModel):
    """A single step in the execution graph."""

    id: str = Field(..., description="Unique identifier for the step.")
    description: Optional[str] = Field(None, description="Description of the step.")
    # Additional fields can be added as per specific needs of the DAG,
    # but for now we keep it generic as per the high-level spec.


class ModelConfig(BaseModel):
    """LLM Configuration parameters."""

    model: str = Field(..., description="The LLM model identifier.")
    temperature: float = Field(..., ge=0.0, le=2.0, description="Temperature for generation.")
    # Config is locked per version, so no dynamic loading here.


class AgentTopology(BaseModel):
    """Topology of the Agent execution."""

    steps: List[Step] = Field(..., description="A directed acyclic graph (DAG) of execution steps.")
    llm_config: ModelConfig = Field(..., alias="model_config", description="Specific LLM parameters.")


class AgentDependencies(BaseModel):
    """External dependencies for the Agent."""

    tools: List[str] = Field(default_factory=list, description="List of MCP capability URIs required.")
    libraries: List[str] = Field(
        default_factory=list, description="List of Python packages required (if code execution is allowed)."
    )


class AgentDefinition(BaseModel):
    """The Root Object for the CoReason Agent Manifest."""

    metadata: AgentMetadata
    interface: AgentInterface
    topology: AgentTopology
    dependencies: AgentDependencies
    integrity_hash: Optional[str] = Field(None, description="SHA256 hash of the source code.")
