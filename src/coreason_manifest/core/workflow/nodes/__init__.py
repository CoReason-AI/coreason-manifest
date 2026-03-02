# Prosperity-3.0
from typing import Any

from coreason_manifest.core.primitives.registry import resolve_node_union

from .agent import AgentNode, CognitiveProfile
from .base import Constraint, ConstraintOperator, LockConfig, Node
from .human import CollaborationMode, HumanNode, SteeringConfig
from .oversight import EmergenceInspectorNode, InspectorNode, InspectorNodeBase
from .planner import PlannerNode
from .routing import SwitchNode
from .swarm import SwarmNode
from .system import PlaceholderNode
from .visual_oversight import MultimodalConstraint, VisBenchRubricConfig, VisualInspectorNode

# AnyNode is now resolved dynamically
AnyNode: Any = resolve_node_union()

__all__ = [
    "AgentNode",
    "AnyNode",
    "CognitiveProfile",
    "CollaborationMode",
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
    "VisBenchRubricConfig",
    "VisualInspectorNode",
]
