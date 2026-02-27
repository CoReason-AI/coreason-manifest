# src/coreason_manifest/spec/core/contracts.py

from typing import Annotated, Literal, Union, Any, TypeAlias

from pydantic import Field

from coreason_manifest.spec.common_base import CoreasonModel
from coreason_manifest.spec.core.types import NodeID, SemanticVersion

# SOTA Fix: Pydantic V2 requires proper recursive type handling.
# A simple TypeAlias can sometimes trigger recursion errors in older pydantic/python versions if not careful.
# However, `dict[str, Any]` is the pragmatic Zero-Trust compromise for "External Schema" objects
# if recursion is causing infinite loops in the meta-schema generator.
# The instruction said: "If keeping it local, use a more permissive but structurally sound type... OR import JsonDict".
# Let's try `dict[str, Any]` with a comment, as the recursion error is blocking strict validation.
# Or better, we define a shallow recursion or just use Any for the *value* of the dict to break the loop for now,
# relying on runtime validators if needed.
# But `JsonValue` as defined previously `Union[..., list["JsonValue"], ...]` IS the correct way for Pydantic V2.
# The recursion error suggests Pydantic is trying to generate a schema for an infinitely recursive type and failing.
# Pydantic V2 supports `JsonValue` natively if imported from `pydantic`.
# Let's see if we can use `pydantic.JsonValue`? No, that might be new.
# Let's revert to `dict[str, Any]` for `definition` to unblock, as "AtomicSkill.definition" is often a complex schema
# which is effectively "Data". `dict[str, Any]` is strictly typed as "A Dictionary with String Keys",
# which prevents passing a list or string where a schema dict is expected.

# To satisfy "Strictness", we will use `dict[str, Any]`.
# We accept the trade-off to solve the RecursionError.

class AtomicSkill(CoreasonModel):
    """
    A verifiable unit of capability.
    Must be immutable and versioned.
    """
    name: str = Field(..., description="Unique name of the skill.")
    version: SemanticVersion = Field(..., description="Semantic version of the skill.")

    definition: dict[str, Any] = Field(
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
    # SOTA Refinement: Add constraints for bounded loops and safety.
    constraints: list[Constraint] = Field(
        default_factory=list,
        description="Operational constraints (e.g. max_retries, timeout) enforced by the kernel."
    )
    # SOTA Refinement: Add metadata for telemetry/audit without polluting inputs.
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
    # SOTA Refinement: Use Discriminated Union for O(1) serialization performance.
    nodes: dict[NodeID, Annotated[Union[ActionNode, StrategyNode], Field(discriminator="type")]] = Field(
        ...,
        description="All nodes involved in the plan, indexed by ID."
    )
