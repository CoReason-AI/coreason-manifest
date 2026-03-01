from typing import Any

from pydantic import ConfigDict, Field

from coreason_manifest.core.common_base import CoreasonModel


class AtomicSkill(CoreasonModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    id: str = Field(..., description="Unique identifier for this skill step.", examples=["skill_fetch_user"])
    description: str = Field(
        ..., description="Description of the action to be performed.", examples=["Fetch user details from database."]
    )
    immutable: bool = Field(
        False, description="If True, this step cannot be modified or removed by the planner.", examples=[False]
    )
    tool_ref: str | None = Field(
        default=None, description="Reference to the tool to be used.", examples=["db_query_tool"]
    )
    params: dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters for the tool.",
        examples=[{"user_id": "u123", "include_profile": True}],
    )


class ActionNode(CoreasonModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    id: str = Field(..., description="Unique identifier for this action.", examples=["action_get_user"])
    description: str = Field(..., description="Description of the action.", examples=["Retrieve user information."])
    skill: AtomicSkill = Field(
        ...,
        description="The atomic skill to execute.",
        examples=[
            {
                "id": "skill_fetch_user",
                "description": "Fetch user details from database.",
                "immutable": False,
                "tool_ref": "db_query_tool",
                "params": {"user_id": "u123"},
            }
        ],
    )
    inputs: dict[str, Any] = Field(
        default_factory=dict, description="Inputs for the action.", examples=[{"user_id": "u123"}]
    )


class StrategyNode(CoreasonModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    id: str = Field(..., description="Unique identifier for this strategy node.", examples=["strategy_resolve_ticket"])
    goal: str = Field(..., description="High-level goal description.", examples=["Resolve customer support ticket."])
    strategy_name: str = Field(..., description="Name of the strategy used.", examples=["ReAct", "TreeOfThoughts"])
    children: list["PlanTree"] = Field(
        ...,
        description="Child nodes or sub-goals.",
        examples=[
            [
                {
                    "id": "action_get_user",
                    "description": "Retrieve user information.",
                    "skill": {
                        "id": "skill_fetch_user",
                        "description": "Fetch user details from database.",
                        "immutable": False,
                        "tool_ref": "db_query_tool",
                        "params": {"user_id": "u123"},
                    },
                    "inputs": {"user_id": "u123"},
                }
            ]
        ],
    )


type PlanTree = StrategyNode | ActionNode | AtomicSkill | list["PlanTree"]
