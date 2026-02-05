# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from .spec.cap import (
    AgentRequest,
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
from .spec.common.capabilities import AgentCapabilities, DeliveryMode
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
)
from .spec.common.identity import Identity
from .spec.common.message import ChatMessage, Role
from .spec.common.observability import (
    AuditLog,
    CloudEvent,
    EventContentType,
    ReasoningTrace,
)
from .spec.common.presentation import (
    AnyPresentationEvent,
    ArtifactEvent,
    CitationEvent,
    PresentationEvent,
    PresentationEventType,
    UserErrorEvent,
)
from .spec.common.session import MemoryStrategy, SessionState
from .spec.common_base import ToolRiskLevel
from .spec.governance import ComplianceReport, ComplianceViolation, GovernanceConfig
from .spec.v2.contracts import InterfaceDefinition, PolicyDefinition, StateDefinition
from .spec.v2.definitions import (
    AgentDefinition,
    AgentStep,
    CouncilStep,
    LogicStep,
    ManifestMetadata,
    ManifestV2,
    Step,
    SwitchStep,
    ToolDefinition,
    Workflow,
)
from .utils.migration import migrate_graph_event_to_cloud_event
from .utils.service import ServiceContract
from .utils.v2.governance import check_compliance_v2
from .utils.v2.io import dump_to_yaml, load_from_yaml
from .utils.v2.validator import validate_integrity, validate_loose

__version__ = "0.17.0"

Manifest = ManifestV2
Recipe = ManifestV2
load = load_from_yaml
dump = dump_to_yaml

__all__ = [
    "AgentCapabilities",
    "AgentDefinition",
    "AgentRequest",
    "AgentStep",
    "AnyPresentationEvent",
    "ArtifactEvent",
    "AuditLog",
    "ChatMessage",
    "CitationEvent",
    "CloudEvent",
    "ComplianceReport",
    "ComplianceViolation",
    "CouncilStep",
    "DeliveryMode",
    "ErrorDomain",
    "ErrorSeverity",
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
    "HealthCheckResponse",
    "HealthCheckStatus",
    "Identity",
    "InterfaceDefinition",
    "LogicStep",
    "Manifest",
    "ManifestMetadata",
    "MemoryStrategy",
    "PolicyDefinition",
    "PresentationEvent",
    "PresentationEventType",
    "ReasoningTrace",
    "Recipe",
    "Role",
    "ServiceContract",
    "ServiceRequest",
    "ServiceResponse",
    "SessionContext",
    "SessionState",
    "StateDefinition",
    "Step",
    "StreamError",
    "StreamOpCode",
    "StreamPacket",
    "SwitchStep",
    "ToolDefinition",
    "ToolRiskLevel",
    "UserErrorEvent",
    "Workflow",
    "__version__",
    "check_compliance_v2",
    "dump",
    "load",
    "migrate_graph_event_to_cloud_event",
    "validate_integrity",
    "validate_loose",
]
