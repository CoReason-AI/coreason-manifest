# Prosperity-3.0
from typing import Union

from pydantic import Field, field_validator

from coreason_manifest.core.common.base import CoreasonModel
from coreason_manifest.spec.intent_protocols import UniversalIntentURI
from coreason_manifest.workflow.nodes.base import Node


class DecompositionStrategy(CoreasonModel):
    """
    Defines how a macro-intent is broken down at runtime.
    This establishes limits on the dynamic instantiation of swarms under the SOTA 2026 Liquid Topology orchestration.
    """

    max_micro_agents: int = Field(
        ...,
        gt=0,
        description="The strict upper bound on the number of micro-agents that can be dynamically spawned.",
        examples=[5],
    )
    allowed_sub_intents: list[str] = Field(
        ...,
        description="A predefined whitelist of sub-intents or capabilities the swarm is permitted to decompose into.",
        examples=[["fetch_data", "summarize"]],
    )
    require_human_oversight_on_synthesis: bool = Field(
        ...,
        description="Whether a human-in-the-loop confirmation is required before the swarm collapses and synthesizes its final result.",
        examples=[True],
    )


class LiquidTopologyNode(Node):
    """
    Represents an ephemeral, liquid topology node in the orchestration graph.
    Instead of mapping to a single explicit agent, this node maps to a macro-intent
    that autonomously spawns and dissolves a swarm of micro-agents at runtime.
    """

    macro_intent: Union[str, UniversalIntentURI] = Field(
        ...,
        description="The high-level goal that this topology aims to satisfy, represented either as a string or a strict URI.",
        examples=["Migrate all user data to the new schema"],
    )
    decomposition: DecompositionStrategy = Field(
        ...,
        description="The policy dictating how the orchestrator divides the macro_intent into granular micro-agents.",
    )
    ephemeral_ttl_seconds: int = Field(
        ...,
        description="The time-to-live for the dynamically generated swarm before it dissolves to free up compute resources.",
        examples=[3600],
    )

    @field_validator("ephemeral_ttl_seconds")
    @classmethod
    def validate_positive_ttl(cls, v: int) -> int:
        """Ensure TTL is strictly positive."""
        if v <= 0:
            raise ValueError("ephemeral_ttl_seconds must be a positive integer strictly greater than 0.")
        return v
