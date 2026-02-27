from typing import Annotated, Literal

from pydantic import Field

from coreason_manifest.spec.common_base import CoreasonModel
from coreason_manifest.spec.core.types import NodeID, StrictPayload


class NodeBase(CoreasonModel):
    id: NodeID
    metadata: StrictPayload = Field(default_factory=StrictPayload)


class SkillConfig(CoreasonModel):
    capabilities: list[str] = Field(default_factory=list)


class ActionNode(NodeBase):
    type: Literal["action"] = "action"
    skill: SkillConfig


class StrategyNode(NodeBase):
    type: Literal["strategy"] = "strategy"
    strategy_config: StrictPayload = Field(default_factory=StrictPayload)


NodeSpec = Annotated[ActionNode | StrategyNode, Field(discriminator="type")]
