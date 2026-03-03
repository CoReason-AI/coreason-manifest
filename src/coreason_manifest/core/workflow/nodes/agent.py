# Prosperity-3.0
from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from coreason_manifest.core.common.base import CoreasonModel
from coreason_manifest.core.common.semantic import SemanticRef
from coreason_manifest.core.compute.reasoning import FastPath, ReasoningConfig
from coreason_manifest.core.oversight.governance import OperationalPolicy
from coreason_manifest.core.oversight.intervention import EscalationCriteria
from coreason_manifest.core.primitives.types import CoercibleStringList, ProfileID
from coreason_manifest.core.state.memory import MemorySubsystem

from .base import Node


class CognitiveProfile(CoreasonModel):
    """The active processing unit of an agent."""

    role: str = Field(..., description="The role of the agent.", examples=["Assistant", "Researcher"])
    persona: str = Field(
        ..., description="The system prompt/persona description.", examples=["You are a helpful assistant."]
    )
    reasoning: ReasoningConfig | None = Field(
        None, description="The reasoning engine configuration.", examples=[{"type": "standard", "model": "gpt-4"}]
    )
    fast_path: FastPath | None = Field(
        None, description="Fast path configuration for low-latency responses.", examples=[{"model": "gpt-3.5-turbo"}]
    )
    memory: MemorySubsystem | None = Field(
        None, description="The 4-tier hierarchical memory configuration.", examples=[{"working_memory": {}}]
    )
    ui_capabilities: list[str] | None = Field(
        default=None, description="List of frontend component registry IDs this agent is permitted to render."
    )


class TransparencyLevel(StrEnum):
    opaque = "opaque"
    observable = "observable"
    interactive = "interactive"


class InterventionTrigger(StrEnum):
    on_start = "on_start"
    on_plan_generation = "on_plan_generation"
    on_tool_evaluation = "on_tool_evaluation"
    on_failure = "on_failure"
    on_completion = "on_completion"


class InspectionConfig(CoreasonModel):
    """Passive trigger schemas that yield control to a human without breaking graph topology."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    transparency: TransparencyLevel = Field(..., description="The transparency level.")
    triggers: list[InterventionTrigger] = Field(..., description="List of intervention triggers.")
    editable_pointers: list[str] = Field(..., description="List of editable JSON pointers.")

    @field_validator("editable_pointers")
    @classmethod
    def validate_editable_pointers(cls, v: list[str]) -> list[str]:
        for pointer in v:
            if not pointer.startswith("/"):
                raise ValueError(f"Invalid JSON Pointer: '{pointer}'. Must start with '/'.")
        return v


class FederatedSearchConfig(BaseModel):
    """Contract enforcing that an agent queries multiple mandatory databases to prevent bias."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    minimum_database_count: Annotated[
        int,
        Field(
            ge=1,
            description="The absolute minimum number of distinct databases that must be queried "
            "(e.g., 3 for Cochrane).",
        ),
    ] = 3
    mandatory_sources: Annotated[
        list[str],
        Field(description="Exact identifiers of required databases (e.g., ['pubmed', 'embase', 'cochrane_central'])."),
    ]
    require_grey_literature: Annotated[
        bool,
        Field(
            description="If True, forces the agent to include non-peer-reviewed registries (e.g., ClinicalTrials.gov)."
        ),
    ] = True


class AgentNode(Node):
    """Executes a cognitive task using a CognitiveProfile configuration."""

    type: Literal["agent"] = Field("agent", description="The type of the node.", examples=["agent"])
    profile: CognitiveProfile | ProfileID | SemanticRef = Field(
        ...,
        union_mode="left_to_right",
        description="The cognitive profile configuration or a reference ID.",
        examples=["profile_1", {"role": "Assistant", "persona": "You are a helpful assistant."}],
    )
    tools: CoercibleStringList | SemanticRef = Field(
        default_factory=list,
        union_mode="left_to_right",
        description="List of tool names available to this agent.",
        examples=[["calculator", "web_search"]],
    )
    operational_policy: Annotated[
        OperationalPolicy | None,
        Field(
            None,
            description="Local operational limits. Overrides global Governance limits if set.",
            examples=[{"financial": {"max_cost_usd": 10.0}}],
        ),
    ]
    output_schema: dict[str, Any] | None = Field(
        None, description="The expected JSON schema for the agent's output payload.", examples=[{"type": "object"}]
    )
    escalation_rules: list[EscalationCriteria] = Field(
        default_factory=list,
        description="Local escalation rules for this agent.",
        examples=[[{"condition": "confidence < 0.5", "role": "supervisor"}]],
    )
    inspection: InspectionConfig | None = Field(None, description="Inspection configuration for human steering.")
    federated_search: FederatedSearchConfig | None = Field(
        None,
        description="If set, computationally binds this agent to a multi-database execution "
        "contract to prevent database bias.",
    )
