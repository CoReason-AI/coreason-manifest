from typing import Any

from pydantic import ConfigDict, Field

from coreason_manifest.core.common_base import CoreasonModel


class AtomicSkill(CoreasonModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    id: str = Field(..., description="Unique identifier for this skill step.", examples=["skill_123"])
    description: str = Field(
        ..., description="Description of the action to be performed.", examples=["Fetch user details."]
    )
    immutable: bool = Field(
        False, description="If True, this step cannot be modified or removed by the planner.", examples=[False]
    )
    tool_ref: str | None = Field(None, description="Reference to the tool to be used.", examples=["fetch_user_tool"])
    params: dict[str, Any] = Field(
        default_factory=dict, description="Parameters for the tool.", examples=[{"user_id": 42}]
    )


class ActionNode(CoreasonModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    id: str = Field(..., description="Unique identifier for this action.", examples=["action_456"])
    description: str = Field(..., description="Description of the action.", examples=["Execute user fetch."])
    skill: AtomicSkill = Field(
        ...,
        description="The atomic skill to execute.",
        examples=[
            {
                "id": "skill_123",
                "description": "Fetch user details.",
                "immutable": False,
                "tool_ref": "fetch_user_tool",
                "params": {},
            }
        ],
    )
    inputs: dict[str, Any] = Field(
        default_factory=dict, description="Inputs for the action.", examples=[{"user_id": 42}]
    )


class StrategyNode(CoreasonModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    id: str = Field(..., description="Unique identifier for this strategy node.", examples=["strategy_789"])
    goal: str = Field(..., description="High-level goal description.", examples=["Gather all relevant customer data."])
    strategy_name: str = Field(
        ..., description="Name of the strategy used (e.g., 'ReAct', 'TreeOfThoughts').", examples=["ReAct"]
    )
    children: list["PlanTree"] = Field(
        ...,
        description="Child nodes (sub-goals).",
        examples=[
            [
                {
                    "id": "action_456",
                    "description": "Execute user fetch.",
                    "skill": {
                        "id": "skill_123",
                        "description": "Fetch user details.",
                        "immutable": False,
                        "tool_ref": "fetch_user_tool",
                        "params": {},
                    },
                    "inputs": {},
                }
            ]
        ],
    )


type PlanTree = StrategyNode | ActionNode | AtomicSkill | list["PlanTree"]
