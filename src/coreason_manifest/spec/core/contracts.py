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


# Recursive definition for a PlanTree
# A PlanTree can be a single AtomicSkill, a list of steps (linear plan), or a nested structure
type PlanTree = AtomicSkill | list["PlanTree" | Step]
