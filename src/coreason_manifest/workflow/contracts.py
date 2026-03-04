from enum import StrEnum
from typing import Any

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel


class ChangeCategory(StrEnum):
    BREAKING = "BREAKING"
    GOVERNANCE = "GOVERNANCE"
    FEATURE = "FEATURE"
    PATCH = "PATCH"


class ChangeType(StrEnum):
    ADD = "add"
    REMOVE = "remove"
    MODIFY = "modify"


class DiffChange(CoreasonBaseModel):
    path: str = Field(..., description="JSON-Patch style pointer indicating the mutation target.")
    category: ChangeCategory = Field(..., description="Policy categorization mapped to the path mutation.")
    change_type: ChangeType = Field(..., description="'add', 'remove', or 'modify'")
    old_value: Any | None = Field(default=None, description="The old value before the change.")
    new_value: Any | None = Field(default=None, description="The new value after the change.")


class DiffReport(CoreasonBaseModel):
    changes: list[DiffChange] = Field(..., description="List of differences.")


class AtomicSkill(CoreasonBaseModel):
    id: str = Field(..., description="Unique identifier for this skill step")
    description: str = Field(..., description="Description of the action to be performed")
    immutable: bool = Field(False, description="If True, this step cannot be modified or removed by the planner")
    tool_ref: str | None = Field(None, description="Reference to the tool to be used")
    params: dict[str, Any] = Field(default_factory=dict, description="Parameters for the tool")


class ActionNode(CoreasonBaseModel):
    id: str = Field(..., description="Unique identifier for this action")
    description: str = Field(..., description="Description of the action")
    skill: AtomicSkill = Field(..., description="The atomic skill to execute")
    inputs: dict[str, Any] = Field(default_factory=dict, description="Inputs for the action")


class StrategyNode(CoreasonBaseModel):
    id: str = Field(..., description="Unique identifier for this strategy node")
    goal: str = Field(..., description="High-level goal description")
    strategy_name: str = Field(..., description="Name of the strategy used (e.g., 'ReAct', 'TreeOfThoughts')")
    children: list[PlanTree] = Field(..., description="Child nodes (sub-goals)")


type PlanTree = StrategyNode | ActionNode | AtomicSkill | list["PlanTree"]
