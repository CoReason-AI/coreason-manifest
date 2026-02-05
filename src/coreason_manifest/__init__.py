# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from .common import ToolRiskLevel
from .definitions.capabilities import AgentCapabilities, DeliveryMode
from .definitions.error import ErrorDomain
from .definitions.identity import Identity
from .definitions.message import (
    AttachedFile,
    ChatMessage,
    ContentPart,
    MultiModalInput,
    Role,
)
from .definitions.observability import (
    AuditLog,
    CloudEvent,
    EventContentType,
    ReasoningTrace,
)
from .definitions.presentation import (
    AnyPresentationEvent,
    ArtifactEvent,
    CitationEvent,
    PresentationEvent,
    PresentationEventType,
    UserErrorEvent,
)
from .definitions.service import ServiceContract
from .definitions.session import Interaction
from .governance import ComplianceReport, ComplianceViolation, GovernanceConfig
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
from .v2.governance import check_compliance_v2
from .v2.io import dump_to_yaml, load_from_yaml
from .v2.spec.contracts import InterfaceDefinition, PolicyDefinition, StateDefinition
from .v2.spec.definitions import (
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
from .v2.validator import validate_integrity, validate_loose

__version__ = "0.17.0"

Manifest = ManifestV2
Recipe = ManifestV2
load = load_from_yaml
dump = dump_to_yaml

__all__ = [
    "Manifest",
    "Recipe",
    "load",
    "dump",
    "__version__",
    "ManifestMetadata",
    "AgentStep",
    "Workflow",
    "AgentDefinition",
    "ToolDefinition",
    "Step",
    "LogicStep",
    "SwitchStep",
    "CouncilStep",
    "InterfaceDefinition",
    "StateDefinition",
    "PolicyDefinition",
    "ToolRiskLevel",
    "AgentCapabilities",
    "DeliveryMode",
    "GovernanceConfig",
    "ComplianceReport",
    "ComplianceViolation",
    "Identity",
    "Role",
    "ChatMessage",
    "AttachedFile",
    "ContentPart",
    "MultiModalInput",
    "Interaction",
    "ErrorDomain",
    "PresentationEventType",
    "PresentationEvent",
    "AnyPresentationEvent",
    "CitationEvent",
    "ArtifactEvent",
    "UserErrorEvent",
    "HealthCheckResponse",
    "HealthCheckStatus",
    "ServiceRequest",
    "ServiceResponse",
    "StreamPacket",
    "StreamError",
    "StreamOpCode",
    "ErrorSeverity",
    "validate_integrity",
    "validate_loose",
    "check_compliance_v2",
    "AgentRequest",
    "SessionContext",
    "ServiceContract",
    "CloudEvent",
    "EventContentType",
    "ReasoningTrace",
    "AuditLog",
]
