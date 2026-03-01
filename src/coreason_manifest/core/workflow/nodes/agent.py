# Prosperity-3.0
from typing import Annotated, Literal

from pydantic import Field

from coreason_manifest.core.common.semantic import SemanticRef
from coreason_manifest.core.common_base import CoreasonModel
from coreason_manifest.core.compute.reasoning import FastPath, ReasoningConfig
from coreason_manifest.core.oversight.governance import OperationalPolicy
from coreason_manifest.core.oversight.intervention import EscalationCriteria
from coreason_manifest.core.primitives.registry import register_node
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


@register_node
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
    escalation_rules: list[EscalationCriteria] = Field(
        default_factory=list,
        description="Local escalation rules for this agent.",
        examples=[[{"condition": "confidence < 0.5", "role": "supervisor"}]],
    )
