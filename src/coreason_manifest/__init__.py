# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

# Builder SDK exports
from .builder import AgentBuilder, TypedCapability
from .shortcuts import simple_agent
from .spec.cap import (
    ErrorSeverity,
    HealthCheckResponse,
    HealthCheckStatus,
    ServiceRequest,
    ServiceResponse,
    SessionContext,
    StreamError,
    StreamOpCode,
    StreamPacket,
)
from .spec.common.capabilities import AgentCapabilities, CapabilityType, DeliveryMode
from .spec.common.error import ErrorDomain
from .spec.common.graph_events import (
    GraphEvent,
    GraphEventArtifactGenerated,
    GraphEventCouncilVote,
    GraphEventError,
    GraphEventNodeDone,
    GraphEventNodeRestored,
    GraphEventNodeStart,
    GraphEventNodeStream,
    GraphEventStreamEnd,
    GraphEventStreamStart,
)
from .spec.common.identity import Identity
from .spec.common.interoperability import AgentRuntimeConfig
from .spec.common.memory import MemoryConfig
from .spec.common.message import ChatMessage, Role
from .spec.common.observability import (
    AuditLog,
    CloudEvent,
    EventContentType,
    ReasoningTrace,
)
from .spec.common.presentation import (
    CitationBlock,
    CitationItem,
    MarkdownBlock,
    MediaCarousel,
    MediaItem,
    NodePresentation,
    PresentationEvent,
    PresentationEventType,
    ProgressUpdate,
)
from .spec.common.request import AgentRequest
from .spec.common.session import MemoryStrategy, SessionState
from .spec.common.stream import StreamReference, StreamState
from .spec.common_base import ToolRiskLevel
from .spec.governance import ComplianceReport, ComplianceViolation, GovernanceConfig
from .spec.interfaces.middleware import (
    InterceptorContext,
    IRequestInterceptor,
    IResponseInterceptor,
)
from .spec.interfaces.session import SessionHandle
from .spec.interfaces.stream import IStreamEmitter
from .spec.simulation import (
    AdversaryProfile,
    ChaosConfig,
    SimulationRequest,
    SimulationScenario,
    SimulationStep,
    SimulationTrace,
    StepType,
    ValidationLogic,
)
from .spec.v2.contracts import InterfaceDefinition, PolicyDefinition, StateDefinition
from .spec.v2.definitions import (
    AgentDefinition,
    AgentStep,
    CouncilStep,
    InlineToolDefinition,
    LogicStep,
    ManifestMetadata,
    ManifestV2,
    Step,
    SwitchStep,
    ToolDefinition,
    ToolRequirement,
    Workflow,
)
from .spec.v2.evaluation import EvaluationProfile, SuccessCriterion
from .spec.v2.recipe import (
    AgentNode,
    GraphTopology,
    HumanNode,
    RecipeDefinition,
    RouterNode,
)
from .spec.v2.resources import (
    ModelProfile,
    PricingUnit,
    RateCard,
    ResourceConstraints,
)
from .utils.audit import compute_audit_hash, verify_chain
from .utils.diff import ChangeCategory, DiffReport, compare_agents
from .utils.docs import render_agent_card
from .utils.mcp_adapter import create_mcp_tool_definition
from .utils.mock import generate_mock_output
from .utils.service import ServiceContract
from .utils.v2.governance import check_compliance_v2
from .utils.v2.io import dump_to_yaml, load_from_yaml
from .utils.viz import generate_mermaid_graph

__version__ = "0.22.0"

Manifest = ManifestV2
Recipe = RecipeDefinition
load = load_from_yaml
dump = dump_to_yaml

__all__ = [
    "AdversaryProfile",
    "AgentBuilder",
    "AgentCapabilities",
    "AgentDefinition",
    "AgentNode",
    "AgentRequest",
    "AgentRuntimeConfig",
    "AgentStep",
    "AuditLog",
    "CapabilityType",
    "ChangeCategory",
    "ChaosConfig",
    "ChatMessage",
    "CitationBlock",
    "CitationItem",
    "CloudEvent",
    "ComplianceReport",
    "ComplianceViolation",
    "CouncilStep",
    "DeliveryMode",
    "DiffReport",
    "ErrorDomain",
    "ErrorSeverity",
    "EvaluationProfile",
    "EventContentType",
    "GovernanceConfig",
    "GraphEvent",
    "GraphEventArtifactGenerated",
    "GraphEventCouncilVote",
    "GraphEventError",
    "GraphEventNodeDone",
    "GraphEventNodeRestored",
    "GraphEventNodeStart",
    "GraphEventNodeStream",
    "GraphEventStreamEnd",
    "GraphEventStreamStart",
    "GraphTopology",
    "HealthCheckResponse",
    "HealthCheckStatus",
    "HumanNode",
    "IRequestInterceptor",
    "IResponseInterceptor",
    "IStreamEmitter",
    "Identity",
    "InlineToolDefinition",
    "InterceptorContext",
    "InterfaceDefinition",
    "LogicStep",
    "Manifest",
    "ManifestMetadata",
    "ManifestV2",
    "MarkdownBlock",
    "MediaCarousel",
    "MediaItem",
    "MemoryConfig",
    "MemoryStrategy",
    "ModelProfile",
    "NodePresentation",
    "PolicyDefinition",
    "PresentationEvent",
    "PresentationEventType",
    "PricingUnit",
    "ProgressUpdate",
    "RateCard",
    "ReasoningTrace",
    "Recipe",
    "RecipeDefinition",
    "ResourceConstraints",
    "Role",
    "RouterNode",
    "ServiceContract",
    "ServiceRequest",
    "ServiceResponse",
    "SessionContext",
    "SessionHandle",
    "SessionState",
    "SimulationRequest",
    "SimulationScenario",
    "SimulationStep",
    "SimulationTrace",
    "StateDefinition",
    "Step",
    "StepType",
    "StreamError",
    "StreamOpCode",
    "StreamPacket",
    "StreamReference",
    "StreamState",
    "SuccessCriterion",
    "SwitchStep",
    "ToolDefinition",
    "ToolRequirement",
    "ToolRiskLevel",
    "TypedCapability",
    "ValidationLogic",
    "Workflow",
    "__version__",
    "check_compliance_v2",
    "compare_agents",
    "compute_audit_hash",
    "create_mcp_tool_definition",
    "dump",
    "generate_mermaid_graph",
    "generate_mock_output",
    "load",
    "render_agent_card",
    "simple_agent",
    "verify_chain",
]
