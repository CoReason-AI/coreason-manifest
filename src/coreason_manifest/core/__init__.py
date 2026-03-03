# Core specification package
from __future__ import annotations

from coreason_manifest.compute.reasoning import (
    AttentionReasoning,
    BaseReasoning,
    BufferReasoning,
    ComputerUseReasoning,
    CouncilReasoning,
    DecompositionReasoning,
    EnsembleReasoning,
    FastPath,
    GraphReasoning,
    ModelCriteria,
    ModelRef,
    Optimizer,
    ReasoningConfig,
    RedTeamingReasoning,
    StandardReasoning,
    TreeSearchReasoning,
    WasmExecutionReasoning,
)
from coreason_manifest.core.primitives.types import WasmMiddlewareDef
from coreason_manifest.oversight.governance import (
    Audit,
    CircuitBreaker,
    Governance,
    Safety,
)
from coreason_manifest.oversight.resilience import (
    ErrorDomain,
    ErrorHandler,
    EscalationStrategy,
    FallbackStrategy,
    ReflexionStrategy,
    ResilienceStrategy,
    RetryStrategy,
    SupervisionPolicy,
)
from coreason_manifest.state.persistence import Checkpoint, JSONPatchOperation, PersistenceConfig, StateCheckpoint
from coreason_manifest.state.tools import MCPPrompt, MCPResourceTemplate, MCPTool, ToolPack
from coreason_manifest.workflow.evals import EvalsManifest, FuzzingTarget
from coreason_manifest.workflow.evals import SimulationScenario as TestCase
from coreason_manifest.workflow.flow import (
    Blackboard,
    Edge,
    FlowDefinitions,
    FlowInterface,
    FlowMetadata,
    Graph,
    GraphFlow,
    LinearFlow,
    VariableDef,
)
from coreason_manifest.workflow.nodes import (
    AgentNode,
    CognitiveProfile,
    EmergenceInspectorNode,
    HumanNode,
    InspectorNode,
    InspectorNodeBase,
    Node,
    PlaceholderNode,
    PlannerNode,
    SwarmNode,
    SwitchNode,
)

__all__ = [
    # Nodes
    "AgentNode",
    # Flow
    # Engines
    "AttentionReasoning",
    # Governance
    "Audit",
    "BaseReasoning",
    "Blackboard",
    "BufferReasoning",
    "Checkpoint",
    "CircuitBreaker",
    "CognitiveProfile",
    "ComputerUseReasoning",
    "CouncilReasoning",
    "DecompositionReasoning",
    "Edge",
    "EmergenceInspectorNode",
    "EnsembleReasoning",
    "ErrorDomain",
    "ErrorHandler",
    "EscalationStrategy",
    "EvalsManifest",
    "FallbackStrategy",
    "FastPath",
    "FlowDefinitions",
    "FlowInterface",
    "FlowMetadata",
    "FuzzingTarget",
    "Governance",
    "Graph",
    "GraphFlow",
    "GraphReasoning",
    "HumanNode",
    "InspectorNode",
    "InspectorNodeBase",
    "JSONPatchOperation",
    "LinearFlow",
    "MCPPrompt",
    "MCPResourceTemplate",
    "MCPTool",
    "ModelCriteria",
    "ModelRef",
    "Node",
    "Optimizer",
    "PersistenceConfig",
    "PlaceholderNode",
    "PlannerNode",
    "ReasoningConfig",
    "RedTeamingReasoning",
    "ReflexionStrategy",
    "ResilienceStrategy",
    "RetryStrategy",
    "Safety",
    "StandardReasoning",
    "StateCheckpoint",
    "SupervisionPolicy",
    "SwarmNode",
    "SwitchNode",
    "TestCase",
    # Tools
    "ToolPack",
    "TreeSearchReasoning",
    "VariableDef",
    "WasmExecutionReasoning",
    "WasmMiddlewareDef",
]

# Late binding resolution for recursive types
GraphFlow.model_rebuild()
AgentNode.model_rebuild()
HumanNode.model_rebuild()
SwarmNode.model_rebuild()
SwitchNode.model_rebuild()
PlaceholderNode.model_rebuild()
EmergenceInspectorNode.model_rebuild()
PlannerNode.model_rebuild()
InspectorNode.model_rebuild()
InspectorNodeBase.model_rebuild()
Node.model_rebuild()
