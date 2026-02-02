# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Any, Dict, Generic, Literal, Optional, Protocol, TypeVar, Union, runtime_checkable
from uuid import uuid4

from pydantic import ConfigDict, Field

from coreason_manifest.definitions.base import CoReasonBaseModel
from coreason_manifest.definitions.topology import RuntimeVisualMetadata

# --- CloudEvents v1.0 Implementation ---

T = TypeVar("T")


class EventContentType(str, Enum):
    """MIME content types for Coreason events."""

    JSON = "application/json"
    STREAM = "application/vnd.coreason.stream+json"
    ERROR = "application/vnd.coreason.error+json"
    ARTIFACT = "application/vnd.coreason.artifact+json"


@runtime_checkable
class CloudEventSource(Protocol):
    def as_cloud_event_payload(self) -> Any: ...


class CloudEvent(CoReasonBaseModel, Generic[T]):
    """Standard CloudEvent v1.0 Envelope."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    specversion: Literal["1.0"] = "1.0"
    type: str = Field(..., description="Type of occurrence (e.g. ai.coreason.node.started)")
    source: str = Field(..., description="URI identifying the event producer")
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique event identifier")
    time: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of when the occurrence happened"
    )
    datacontenttype: Union[EventContentType, str] = Field(
        default=EventContentType.JSON, description="MIME content type of data"
    )

    data: Optional[T] = Field(None, description="The event payload")

    # Distributed Tracing Extensions (W3C)
    traceparent: Optional[str] = Field(None, description="W3C Trace Context traceparent")
    tracestate: Optional[str] = Field(None, description="W3C Trace Context tracestate")


# --- OTel Semantic Conventions ---


class GenAIUsage(CoReasonBaseModel):
    """GenAI Usage metrics."""

    input_tokens: Optional[int] = Field(None, alias="input_tokens")
    output_tokens: Optional[int] = Field(None, alias="output_tokens")

    model_config = ConfigDict(populate_by_name=True)


class GenAIRequest(CoReasonBaseModel):
    """GenAI Request details."""

    model: Optional[str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None


class GenAICompletion(CoReasonBaseModel):
    """GenAI Completion details."""

    chunk: Optional[str] = None
    finish_reason: Optional[str] = None


class GenAISemantics(CoReasonBaseModel):
    """OpenTelemetry GenAI Semantic Conventions."""

    system: Optional[str] = None
    usage: Optional[GenAIUsage] = None
    request: Optional[GenAIRequest] = None
    completion: Optional[GenAICompletion] = None


# --- Base Models ---


class BaseNodePayload(CoReasonBaseModel):
    """Base model for node-related events."""

    model_config = ConfigDict(extra="ignore")
    node_id: str

    # Common OTel attributes that might appear in payload
    model: Optional[str] = None
    system: Optional[str] = None

    def as_cloud_event_payload(self) -> Any:
        return self


# --- Payload Models ---


class NodeInit(BaseNodePayload):
    """Payload for NODE_INIT event."""

    type: str = "DEFAULT"
    visual_cue: str = "IDLE"


class NodeStarted(BaseNodePayload):
    """Payload for NODE_START event."""

    timestamp: float
    status: Literal["RUNNING"] = "RUNNING"
    visual_cue: str = "PULSE"
    input_tokens: Optional[int] = None

    def as_cloud_event_payload(self) -> Any:
        semantics = GenAISemantics()
        has_semantics = False

        if self.input_tokens is not None:
            semantics.usage = GenAIUsage(input_tokens=self.input_tokens)
            has_semantics = True

        if self.model:
            semantics.request = GenAIRequest(model=self.model)
            has_semantics = True

        if self.system:
            semantics.system = self.system
            has_semantics = True

        return StandardizedNodeStarted(
            node_id=self.node_id,
            status=self.status,
            gen_ai=semantics if has_semantics else None,
        )


class NodeCompleted(BaseNodePayload):
    """Payload for NODE_DONE event."""

    output_summary: str
    status: Literal["SUCCESS"] = "SUCCESS"
    visual_cue: str = "GREEN_GLOW"
    cost: Optional[float] = None

    def as_cloud_event_payload(self) -> Any:
        semantics = GenAISemantics()
        has_semantics = False

        if self.model:
            semantics.request = GenAIRequest(model=self.model)
            has_semantics = True

        return StandardizedNodeCompleted(
            node_id=self.node_id,
            output_summary=self.output_summary,
            status=self.status,
            gen_ai=semantics if has_semantics else None,
        )


class NodeRestored(BaseNodePayload):
    """Payload for NODE_RESTORED event."""

    output_summary: str
    status: Literal["RESTORED"] = "RESTORED"
    visual_cue: str = "INSTANT_GREEN"


class NodeSkipped(BaseNodePayload):
    """Payload for NODE_SKIPPED event."""

    status: Literal["SKIPPED"] = "SKIPPED"
    visual_cue: str = "GREY_OUT"


class NodeStream(BaseNodePayload):
    """Payload for NODE_STREAM event."""

    chunk: str
    visual_cue: str = "TEXT_BUBBLE"

    def as_cloud_event_payload(self) -> Any:
        semantics = GenAISemantics(completion=GenAICompletion(chunk=self.chunk))
        if self.model:
            if not semantics.request:
                semantics.request = GenAIRequest()
            semantics.request.model = self.model

        return StandardizedNodeStream(node_id=self.node_id, gen_ai=semantics)


class ArtifactGenerated(BaseNodePayload):
    """Payload for ARTIFACT_GENERATED event."""

    artifact_type: str = "PDF"
    url: str


class EdgeTraversed(CoReasonBaseModel):
    """Payload for EDGE_ACTIVE event."""

    model_config = ConfigDict(extra="ignore")
    source: str
    target: str
    animation_speed: str = "FAST"

    def as_cloud_event_payload(self) -> Any:
        return self


class CouncilVote(BaseNodePayload):
    """Payload for COUNCIL_VOTE event."""

    votes: Dict[str, str]


class ErrorDomain(str, Enum):
    """Domain of the error."""

    SYSTEM = "SYSTEM"
    LLM = "LLM"
    TOOL = "TOOL"
    LOGIC = "LOGIC"
    SECURITY = "SECURITY"


class WorkflowError(BaseNodePayload):
    """Payload for ERROR event."""

    error_message: str
    stack_trace: str
    input_snapshot: Dict[str, Any]
    status: Literal["ERROR"] = "ERROR"
    visual_cue: str = "RED_FLASH"

    # Semantic Error Fields
    code: int = 500
    domain: ErrorDomain = ErrorDomain.SYSTEM
    retryable: bool = False


# --- Standardized Payloads ---


class StandardizedNodeStarted(BaseNodePayload):
    """Standardized payload for node start with OTel support."""

    gen_ai: Optional[GenAISemantics] = None
    status: Literal["RUNNING"] = "RUNNING"


class StandardizedNodeCompleted(BaseNodePayload):
    """Standardized payload for node completion with OTel support."""

    gen_ai: Optional[GenAISemantics] = None
    output_summary: str
    status: Literal["SUCCESS"] = "SUCCESS"


class StandardizedNodeStream(BaseNodePayload):
    """Standardized payload for node stream with OTel support."""

    gen_ai: Optional[GenAISemantics] = None


# --- Aliases for Backward Compatibility ---
# These ensure that code importing `NodeInitPayload` still works.
NodeInitPayload = NodeInit
NodeStartedPayload = NodeStarted
NodeCompletedPayload = NodeCompleted
NodeSkippedPayload = NodeSkipped
NodeStreamPayload = NodeStream
EdgeTraversedPayload = EdgeTraversed
ArtifactGeneratedPayload = ArtifactGenerated
CouncilVotePayload = CouncilVote
WorkflowErrorPayload = WorkflowError


# --- Graph Event Wrapper ---


class BaseGraphEvent(CoReasonBaseModel):
    """Base class for GraphEvents.

    Standardized IDs:
    - run_id: Workflow execution ID.
    - trace_id: OpenTelemetry Distributed Trace ID.
    """

    model_config = ConfigDict(extra="forbid")

    run_id: str
    trace_id: str = Field(
        default_factory=lambda: "unknown"
    )  # Default for compatibility if missing in some legacy calls
    node_id: str  # Required per BRD and existing tests
    timestamp: float
    sequence_id: Optional[int] = None  # Optional for internal use

    # Visual Metadata drives the Flutter animation engine
    visual_metadata: RuntimeVisualMetadata = Field(
        ..., description="Hints for UI: color='#00FF00', animation='pulse', progress='0.5'"
    )


class GraphEventNodeInit(BaseGraphEvent):
    event_type: Literal["NODE_INIT"] = "NODE_INIT"
    payload: NodeInit = Field(..., description="The logic output")


class GraphEventNodeStart(BaseGraphEvent):
    event_type: Literal["NODE_START"] = "NODE_START"
    payload: NodeStarted = Field(..., description="The logic output")


class GraphEventNodeStream(BaseGraphEvent):
    event_type: Literal["NODE_STREAM"] = "NODE_STREAM"
    payload: NodeStream = Field(..., description="The logic output")


class GraphEventNodeDone(BaseGraphEvent):
    event_type: Literal["NODE_DONE"] = "NODE_DONE"
    payload: NodeCompleted = Field(..., description="The logic output")


class GraphEventNodeSkipped(BaseGraphEvent):
    event_type: Literal["NODE_SKIPPED"] = "NODE_SKIPPED"
    payload: NodeSkipped = Field(..., description="The logic output")


class GraphEventEdgeActive(BaseGraphEvent):
    event_type: Literal["EDGE_ACTIVE"] = "EDGE_ACTIVE"
    payload: EdgeTraversed = Field(..., description="The logic output")


class GraphEventCouncilVote(BaseGraphEvent):
    event_type: Literal["COUNCIL_VOTE"] = "COUNCIL_VOTE"
    payload: CouncilVote = Field(..., description="The logic output")


class GraphEventError(BaseGraphEvent):
    event_type: Literal["ERROR"] = "ERROR"
    payload: WorkflowError = Field(..., description="The logic output")


class GraphEventNodeRestored(BaseGraphEvent):
    event_type: Literal["NODE_RESTORED"] = "NODE_RESTORED"
    payload: NodeRestored = Field(..., description="The logic output")


class GraphEventArtifactGenerated(BaseGraphEvent):
    event_type: Literal["ARTIFACT_GENERATED"] = "ARTIFACT_GENERATED"
    payload: ArtifactGenerated = Field(..., description="The logic output")


GraphEvent = Annotated[
    Union[
        GraphEventNodeInit,
        GraphEventNodeStart,
        GraphEventNodeStream,
        GraphEventNodeDone,
        GraphEventNodeSkipped,
        GraphEventEdgeActive,
        GraphEventCouncilVote,
        GraphEventError,
        GraphEventNodeRestored,
        GraphEventArtifactGenerated,
    ],
    Field(discriminator="event_type", description="Polymorphic graph event definition."),
]


# --- Migration Logic ---


def migrate_graph_event_to_cloud_event(event: GraphEvent) -> CloudEvent[Any]:
    """Migrates a legacy GraphEvent to a CloudEvent v1.0."""

    ce_type_map = {
        "NODE_START": "ai.coreason.node.started",
        "NODE_STREAM": "ai.coreason.node.stream",
        "NODE_DONE": "ai.coreason.node.completed",
    }
    ce_type = ce_type_map.get(event.event_type, f"ai.coreason.legacy.{event.event_type.lower()}")
    ce_source = f"urn:node:{event.node_id}"

    # Determine Content-Type based on event type
    content_type_map = {
        "NODE_STREAM": EventContentType.STREAM,
        "ERROR": EventContentType.ERROR,
        "ARTIFACT_GENERATED": EventContentType.ARTIFACT,
    }
    content_type = content_type_map.get(event.event_type, EventContentType.JSON)

    data: Any = None

    # event.payload is already a strictly typed Pydantic model (from GraphEvent union).
    # All supported payload models implement CloudEventSource protocol (duck-typed or via BaseNodePayload).
    if isinstance(event.payload, CloudEventSource):
        data = event.payload.as_cloud_event_payload()
    else:
        # Fallback for models that might not implement the protocol (e.g. unknown future extensions)
        data = event.payload

    # UI Metadata as extension
    payload_visual_cue = getattr(event.payload, "visual_cue", None)

    visual_dict = event.visual_metadata.model_dump(exclude_none=True)
    extensions = {
        "com_coreason_ui_cue": event.visual_metadata.animation or payload_visual_cue,
        "com_coreason_ui_metadata": visual_dict,
    }

    # Filter out None values in extensions
    # For dictionaries, we want to filter out empty dicts too.
    filtered_extensions = {}
    for k, v in extensions.items():
        if v is None:
            continue
        if isinstance(v, dict) and not v:
            continue
        if isinstance(v, str) and not v:
            continue
        # Also check if it's a dict containing only empty strings (recursive check not needed for now, just 1 level)
        if isinstance(v, dict) and all(isinstance(val, str) and not val for val in v.values()):
            continue

        filtered_extensions[k] = v

    extensions = filtered_extensions

    return CloudEvent(
        type=ce_type,
        source=ce_source,
        time=datetime.fromtimestamp(event.timestamp, timezone.utc),
        datacontenttype=content_type,
        data=data,
        **extensions,
    )
