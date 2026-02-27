# src/coreason_manifest/spec/core/contracts.py

from typing import Annotated, Literal

from pydantic import Field

from coreason_manifest.spec.common_base import CoreasonModel
from coreason_manifest.spec.core.types import NodeID, SemanticVersion


class AtomicSkill(CoreasonModel):
    """
    A verifiable unit of capability.
    Must be immutable and versioned.
    """
    name: str = Field(..., description="Unique name of the skill.")
    version: SemanticVersion = Field(..., description="Semantic version of the skill.")
    definition: dict[str, str] = Field(
        ...,
        description="Strict definition of the skill. No 'Any' allowed.",
        examples=[{"input": "str", "output": "str"}]
    )
    capabilities: list[str] = Field(
        default_factory=list,
        description="List of capabilities this skill grants (e.g., 'computer_use', 'network_access')."
    )
    immutable: Literal[True] = Field(
        True,
        description="Enforces immutability of the skill definition."
    )


class NodeSpec(CoreasonModel):
    """
    Base contract for all execution nodes in the zero-trust kernel.
    """
    id: NodeID = Field(..., description="Unique identifier for the node.")
    locked: bool = Field(
        False,
        description="If True, enforces that this node must be executed on all valid paths (cannot be bypassed)."
    )


class ActionNode(NodeSpec):
    """
    Represents a deterministic action execution node.
    """
    type: Literal["action"] = "action"
    skill: AtomicSkill = Field(..., description="The immutable skill to execute.")
    inputs: dict[str, str] = Field(..., description="Mapping of input arguments to variable names.")
    outputs: dict[str, str] = Field(..., description="Mapping of output keys to variable names.")


class StrategyNode(NodeSpec):
    """
    Represents a decision point (routing logic).
    """
    type: Literal["strategy"] = "strategy"
    strategy_name: str = Field(..., description="Name of the strategy to apply.")
    inputs: dict[str, str] = Field(..., description="Inputs required for the strategy.")
    routes: dict[str, NodeID] = Field(
        ...,
        description="Mapping of strategy outcomes to next node IDs."
    )


class PlanTree(CoreasonModel):
    """
    Represents a compiled, strictly typed execution plan.
    """
    id: str = Field(..., description="Unique ID for this plan instance.")
    root_node: NodeID = Field(..., description="The entry point node ID.")
    nodes: dict[NodeID, ActionNode | StrategyNode] = Field(
        ...,
        description="All nodes involved in the plan, indexed by ID."
    )
