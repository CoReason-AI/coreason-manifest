# src/coreason_manifest/spec/core/contracts.py

from typing import Annotated, Literal, Union, TypeAlias

from pydantic import Field

from coreason_manifest.spec.common_base import CoreasonModel
from coreason_manifest.spec.core.types import NodeID, SemanticVersion

# SOTA Fix: Strict Recursive JSON Types using PEP 695 syntax to avoid RecursionError
# This eradicates 'Any' while supporting complex schemas.
type StrictJsonValue = str | int | float | bool | None | list[StrictJsonValue] | dict[str, StrictJsonValue]
type StrictJsonDict = dict[str, StrictJsonValue]


class AtomicSkill(CoreasonModel):
    """
    A verifiable unit of capability.
    Must be immutable and versioned.
    """
    name: str = Field(..., description="Unique name of the skill.")
    version: SemanticVersion = Field(..., description="Semantic version of the skill.")

    definition: StrictJsonDict = Field(
        ...,
        description="Strict definition of the skill (JSON Schema compatible).",
        examples=[{"input": {"type": "object", "properties": {"q": {"type": "string"}}}}]
    )
    capabilities: list[str] = Field(
        default_factory=list,
        description="List of capabilities this skill grants (e.g., 'computer_use', 'network_access')."
    )
    immutable: Literal[True] = Field(
        True,
        description="Enforces immutability of the skill definition."
    )


class Constraint(CoreasonModel):
    """
    Defines execution boundaries for nodes (e.g., timeouts, max loops).
    Essential for Zero-Trust bounded execution.
    """
    type: str = Field(..., description="Type of constraint (e.g., 'time_limit', 'max_iterations')")
    value: str | int | float = Field(..., description="Deterministic value of the constraint")


class NodeSpec(CoreasonModel):
    """
    Base contract for all execution nodes in the zero-trust kernel.
    """
    id: NodeID = Field(..., description="Unique identifier for the node.")
    locked: bool = Field(
        False,
        description="If True, enforces that this node must be executed on all valid paths (cannot be bypassed)."
    )
    constraints: list[Constraint] = Field(
        default_factory=list,
        description="Operational constraints (e.g. max_retries, timeout) enforced by the kernel."
    )
    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Sterile sandbox for audit tags, trace headers, and human-readable rationales."
    )


class ActionNode(NodeSpec):
    """
    Represents a deterministic action execution node.
    """
    type: Literal["action"] = "action"
    skill: AtomicSkill = Field(..., description="The immutable skill to execute.")
    inputs: dict[str, str] = Field(..., description="Mapping of input arguments to variable names.")
    outputs: dict[str, str] = Field(..., description="Mapping of output keys to variable names.")

    # SOTA Fix: Add next_node for chaining without StrategyNode
    next_node: NodeID | None = Field(
        None,
        description="The node to transition to after successful action execution."
    )


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
    # SOTA Fix: Enforce deterministic fallback routing.
    default_route: NodeID = Field(
        ...,
        description="Fallback node if strategy outcome does not match any key in routes."
    )


class PlanTree(CoreasonModel):
    """
    Represents a compiled, strictly typed execution plan.
    """
    id: str = Field(..., description="Unique ID for this plan instance.")
    root_node: NodeID = Field(..., description="The entry point node ID.")
    nodes: dict[NodeID, Annotated[Union[ActionNode, StrategyNode], Field(discriminator="type")]] = Field(
        ...,
        description="All nodes involved in the plan, indexed by ID."
    )
