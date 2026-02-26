from __future__ import annotations

from typing import Any

from pydantic import Field

from coreason_manifest.spec.common_base import CoreasonModel

# Backward compatibility for Step
type Step = dict[str, Any]


class AtomicSkill(CoreasonModel):
    """
    Represents a fundamental unit of execution (skill/tool call) within a plan.
    """

    id: str = Field(..., description="Unique identifier for this skill step")
    description: str = Field(..., description="Description of the action to be performed")
    immutable: bool = Field(False, description="If True, this step cannot be modified or removed by the planner")
    tool_ref: str | None = Field(None, description="Reference to the tool to be used")
    params: dict[str, Any] = Field(default_factory=dict, description="Parameters for the tool")


# Phase 1: Foundation (Contracts & Types)
class Constraint(CoreasonModel):
    """
    A validator class (e.g., TimeLimit, FormatRequirement) that imposes limits on execution.
    """

    type: str = Field(..., description="Type of constraint (e.g., 'time_limit', 'format')")
    value: Any = Field(..., description="Value of the constraint")
    description: str | None = Field(None, description="Human-readable description")


class ActionNode(CoreasonModel):
    """
    A concrete action step in the plan tree.
    """

    id: str = Field(..., description="Unique identifier for this action")
    description: str = Field(..., description="Description of the action")
    skill: AtomicSkill = Field(..., description="The atomic skill to execute")
    constraints: list[Constraint] = Field(default_factory=list, description="Constraints applied to this action")
    inputs: dict[str, Any] = Field(default_factory=dict, description="Inputs for the action")


class StrategyNode(CoreasonModel):
    """
    An abstract strategy node in the plan tree, representing a high-level goal decomposed into sub-steps.
    """

    id: str = Field(..., description="Unique identifier for this strategy node")
    goal: str = Field(..., description="High-level goal description")
    strategy_name: str = Field(..., description="Name of the strategy used (e.g., 'ReAct', 'TreeOfThoughts')")
    children: list[PlanTree] = Field(..., description="Child nodes (sub-goals)")
    constraints: list[Constraint] = Field(default_factory=list, description="Constraints propagated to children")


# Recursive definition for a PlanTree
# A PlanTree is a tree structure where nodes can be StrategyNode (abstract) or ActionNode (concrete).
# It also supports the legacy 'Step' (dict) and 'AtomicSkill' for backward compatibility during migration.
type PlanTree = StrategyNode | ActionNode | AtomicSkill | list["PlanTree" | Step]


class NodeSpec(CoreasonModel):
    id: str
    description: str
    locked: bool = False
    tool_ref: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)


class EdgeSpec(CoreasonModel):
    from_node: str = Field(..., alias="from")
    to_node: str = Field(..., alias="to")


class FlowSpec(CoreasonModel):
    nodes: list[NodeSpec]
    edges: list[EdgeSpec] = Field(default_factory=list)
