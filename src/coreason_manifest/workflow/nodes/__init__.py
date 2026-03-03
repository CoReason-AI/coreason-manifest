# Prosperity-3.0
from typing import Annotated

import pydantic
from pydantic import Field

from .agent import AgentNode, CognitiveProfile
from .base import Constraint, ConstraintOperator, LockConfig, Node
from .etl import AuditorNode, ExtractorNode, SemanticNode
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
    Field(discriminator=pydantic.Discriminator("type")),
]

__all__ = [
    "AgentNode",
    "AnyNode",
    "AuditorNode",
    "CognitiveProfile",
    "Constraint",
    "ConstraintOperator",
    "EmergenceInspectorNode",
    "ExtractorNode",
    "HumanNode",
    "InspectorNode",
    "InspectorNodeBase",
    "LockConfig",
    "MultimodalConstraint",
    "Node",
    "PlaceholderNode",
    "PlannerNode",
    "SemanticNode",
    "SteeringConfig",
    "SwarmNode",
    "SwitchNode",
    "VisualInspectorNode",
]
