# Prosperity-3.0
from typing import Annotated

from pydantic import Field

from .agent import AgentNode, CognitiveProfile
from .base import Constraint, ConstraintOperator, LockConfig, Node
from .human import HumanNode, SteeringConfig
from .oversight import EmergenceInspectorNode, InspectorNode, InspectorNodeBase
from .planner import PlannerNode
from .routing import SwitchNode
from .swarm import SwarmNode
from .system import PlaceholderNode
from .visual_oversight import MultimodalConstraint, VisualInspectorNode

AnyNode = Annotated[
    AgentNode
    | HumanNode
    | PlannerNode
    | SwarmNode
    | SwitchNode
    | InspectorNode
    | EmergenceInspectorNode
    | VisualInspectorNode
    | PlaceholderNode,
    Field(discriminator="type")
]

__all__ = [
    "AgentNode",
    "AnyNode",
    "CognitiveProfile",
    "Constraint",
    "ConstraintOperator",
    "EmergenceInspectorNode",
    "HumanNode",
    "InspectorNode",
    "InspectorNodeBase",
    "LockConfig",
    "MultimodalConstraint",
    "Node",
    "PlaceholderNode",
    "PlannerNode",
    "SteeringConfig",
    "SwarmNode",
    "SwitchNode",
    "VisualInspectorNode",
]
