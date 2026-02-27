from typing import Annotated, Literal

from pydantic import Field

from coreason_manifest.spec.common_base import CoreasonModel
from coreason_manifest.spec.core.types import NodeID, StrictJson, StrictPayload


class Constraint(CoreasonModel):
    kind: str
    params: dict[str, StrictJson] = Field(default_factory=dict)


class AtomicSkill(CoreasonModel):
    capabilities: list[str] = Field(default_factory=list)
    immutable: Literal[True] = Field(True, description="Enforces absolute definition immutability.")
    inputs_schema: dict[str, StrictJson] = Field(default_factory=dict)
    outputs_schema: dict[str, StrictJson] = Field(default_factory=dict)


class NodeBase(CoreasonModel):
    id: NodeID
    metadata: StrictPayload = Field(default_factory=StrictPayload)
    locked: bool = Field(False, description="If True, node definition is immutable during execution.")
    inputs: dict[str, StrictJson] = Field(default_factory=dict)
    outputs: dict[str, StrictJson] = Field(default_factory=dict)
    constraints: list[Constraint] = Field(default_factory=list)


class ActionNode(NodeBase):
    type: Literal["action"] = "action"
    skill: AtomicSkill


class StrategyNode(NodeBase):
    type: Literal["strategy"] = "strategy"
    strategy_config: StrictPayload = Field(default_factory=StrictPayload)


NodeSpec = Annotated[ActionNode | StrategyNode, Field(discriminator="type")]
