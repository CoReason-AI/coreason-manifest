# Prosperity-3.0
"""Coreason Manifest Package.

This package provides the core definitions and schemas for the CoReason ecosystem.
It serves as the definitive source of truth for Asset definitions.

Usage:
    from coreason_manifest.definitions import AgentManifest
    from coreason_manifest.recipes import RecipeManifest
"""

from .models import (
    AgentDefinition,
    AgentDependencies,
    AgentInterface,
    AgentMetadata,
    AgentTopology,
    ModelConfig,
    Step,
)
from .recipes import (
    AgentNode,
    CouncilConfig,
    Edge,
    GraphTopology,
    HumanNode,
    LogicNode,
    Node,
    RecipeManifest,
    VisualMetadata,
)

__all__ = [
    "AgentDefinition",
    "AgentDependencies",
    "AgentInterface",
    "AgentMetadata",
    "AgentNode",
    "AgentTopology",
    "CouncilConfig",
    "Edge",
    "GraphTopology",
    "HumanNode",
    "LogicNode",
    "ModelConfig",
    "Node",
    "RecipeManifest",
    "Step",
    "VisualMetadata",
]
