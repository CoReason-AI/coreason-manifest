# Prosperity-3.0
"""Coreason Manifest Package.

This package provides the core functionality for the Coreason Manifest system,
including loading, validation, policy enforcement, and integrity checking of
agent definitions.

The `coreason-manifest` package serves as the definitive source of truth for
Asset definitions in the CoReason-AI ecosystem.

Usage:
    from coreason_manifest import ManifestEngine, ManifestConfig

    config = ManifestConfig(policy_path="./policies/gx_compliant.rego")
    engine = ManifestEngine(config)
    agent_def = engine.load_and_validate("agent.yaml", "./src")
"""

from .engine import ManifestConfig, ManifestEngine, ManifestEngineAsync
from .errors import (
    IntegrityCompromisedError,
    ManifestError,
    ManifestSyntaxError,
    PolicyViolationError,
)
from .integrity import IntegrityChecker
from .loader import ManifestLoader
from .models import (
    AgentDefinition,
    AgentDependencies,
    AgentInterface,
    AgentMetadata,
    AgentTopology,
    ModelConfig,
    Step,
)
from .policy import PolicyEnforcer
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
from .validator import SchemaValidator

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
    "IntegrityChecker",
    "IntegrityCompromisedError",
    "LogicNode",
    "ManifestConfig",
    "ManifestEngine",
    "ManifestEngineAsync",
    "ManifestError",
    "ManifestLoader",
    "ManifestSyntaxError",
    "ModelConfig",
    "Node",
    "PolicyEnforcer",
    "PolicyViolationError",
    "RecipeManifest",
    "SchemaValidator",
    "Step",
    "VisualMetadata",
]
