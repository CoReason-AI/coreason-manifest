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
    PresentationEvent,
    PresentationEventType,
    ProgressUpdate,
)
from .spec.common.session import MemoryStrategy, SessionState
from .spec.common.stream import StreamReference, StreamState
from .spec.common_base import ToolRiskLevel
from .spec.governance import ComplianceReport, ComplianceViolation, GovernanceConfig
from .spec.interfaces.stream import IStreamEmitter
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
    "AgentRuntimeConfig",
    "AgentStep",
    "AuditLog",
    "ChatMessage",
    "CitationBlock",
    "CitationItem",
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
    "GraphEventStreamEnd",
    "GraphEventStreamStart",
    "HealthCheckResponse",
    "HealthCheckStatus",
    "IStreamEmitter",
    "Identity",
    "InterfaceDefinition",
    "LogicStep",
    "Manifest",
    "ManifestMetadata",
    "MarkdownBlock",
    "MediaCarousel",
    "MediaItem",
    "MemoryConfig",
    "MemoryStrategy",
    "PolicyDefinition",
    "PresentationEvent",
    "PresentationEventType",
    "ProgressUpdate",
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
    "StreamReference",
    "StreamState",
    "SwitchStep",
    "ToolDefinition",
    "ToolRiskLevel",
    "Workflow",
    "__version__",
    "check_compliance_v2",
    "dump",
    "load",
    "migrate_graph_event_to_cloud_event",
    "validate_integrity",
    "validate_loose",
]
