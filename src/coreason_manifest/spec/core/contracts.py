from typing import Annotated, Literal

from pydantic import ConfigDict, Field

from coreason_manifest.spec.common_base import CoreasonModel
from coreason_manifest.spec.core.primitives.types import NodeID

type StrictJsonValue = str | int | float | bool | None | list["StrictJsonValue"] | dict[str, "StrictJsonValue"]
type StrictJsonDict = dict[str, StrictJsonValue]

SemanticVersion = Annotated[
    str,
    Field(
        pattern=r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
    ),
]


class AtomicSkill(CoreasonModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    name: str
    version: SemanticVersion
    definition: StrictJsonDict
    capabilities: list[str] = Field(default_factory=list)
    immutable: Literal[True] = True


class Constraint(CoreasonModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    type: str
    value: str | int | float


class NodeSpec(CoreasonModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    id: NodeID
    locked: bool = False
    constraints: list[Constraint] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)


class ActionNode(NodeSpec):
    type: Literal["action"] = "action"
    skill: AtomicSkill
    inputs: dict[str, str] = Field(default_factory=dict)
    outputs: dict[str, str] = Field(default_factory=dict)
    next_node: NodeID | None = None


class StrategyNode(NodeSpec):
    type: Literal["strategy"] = "strategy"
    routes: dict[str, NodeID] = Field(default_factory=dict)
    default_route: NodeID


class PlanTree(CoreasonModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    id: str
    root_node: NodeID
    nodes: dict[NodeID, Annotated[ActionNode | StrategyNode, Field(discriminator="type")]]
