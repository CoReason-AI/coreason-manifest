from typing import Any

from pydantic import ConfigDict, Field

from coreason_manifest.core.common_base import CoreasonModel


class AtomicSkill(CoreasonModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    id: str = Field(..., description="Unique identifier for this skill step")
    description: str = Field(..., description="Description of the action to be performed")
    immutable: bool = Field(False, description="If True, this step cannot be modified or removed by the planner")
    tool_ref: str | None = Field(None, description="Reference to the tool to be used")
    params: dict[str, Any] = Field(default_factory=dict, description="Parameters for the tool")


class ActionNode(CoreasonModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    id: str = Field(..., description="Unique identifier for this action")
    description: str = Field(..., description="Description of the action")
    skill: AtomicSkill = Field(..., description="The atomic skill to execute")
    inputs: dict[str, Any] = Field(default_factory=dict, description="Inputs for the action")


class StrategyNode(CoreasonModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    id: str = Field(..., description="Unique identifier for this strategy node")
    goal: str = Field(..., description="High-level goal description")
    strategy_name: str = Field(..., description="Name of the strategy used (e.g., 'ReAct', 'TreeOfThoughts')")
    children: list["PlanTree"] = Field(..., description="Child nodes (sub-goals)")


type PlanTree = StrategyNode | ActionNode | AtomicSkill | list["PlanTree"] | dict[str, Any]
