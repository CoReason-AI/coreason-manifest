from datetime import datetime, timezone
from typing import Any, Dict, Generic, Literal, Optional, Protocol, TypeVar, runtime_checkable
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

# --- CloudEvents v1.0 Implementation ---

T = TypeVar("T")


@runtime_checkable
class CloudEventSource(Protocol):
    def as_cloud_event_payload(self) -> Any: ...


class CloudEvent(BaseModel, Generic[T]):
    """Standard CloudEvent v1.0 Envelope."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    specversion: Literal["1.0"] = "1.0"
    type: str = Field(..., description="Type of occurrence (e.g. ai.coreason.node.started)")
    source: str = Field(..., description="URI identifying the event producer")
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique event identifier")
    time: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of when the occurrence happened"
    )
    datacontenttype: Literal["application/json"] = "application/json"

    data: Optional[T] = Field(None, description="The event payload")

    # Distributed Tracing Extensions (W3C)
    traceparent: Optional[str] = Field(None, description="W3C Trace Context traceparent")
    tracestate: Optional[str] = Field(None, description="W3C Trace Context tracestate")


# --- OTel Semantic Conventions ---


class GenAIUsage(BaseModel):
    """GenAI Usage metrics."""

    input_tokens: Optional[int] = Field(None, alias="input_tokens")
    output_tokens: Optional[int] = Field(None, alias="output_tokens")

    model_config = ConfigDict(populate_by_name=True)


class GenAIRequest(BaseModel):
    """GenAI Request details."""

    model: Optional[str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None


class GenAICompletion(BaseModel):
    """GenAI Completion details."""

    chunk: Optional[str] = None
    finish_reason: Optional[str] = None


class GenAISemantics(BaseModel):
    """OpenTelemetry GenAI Semantic Conventions."""

    system: Optional[str] = None
    usage: Optional[GenAIUsage] = None
    request: Optional[GenAIRequest] = None
    completion: Optional[GenAICompletion] = None


# --- Graph Event Wrapper ---


class GraphEvent(BaseModel):
    """The atomic unit of communication between the Engine (MACO) and the UI (Flutter).

    Attributes:
        event_type: The type of the event.
        run_id: The unique ID of the workflow run.
        trace_id: The trace ID (defaults to "unknown").
        node_id: The ID of the node associated with the event.
        timestamp: The timestamp of the event.
        sequence_id: Optional sequence ID.
        payload: The event payload containing logic output.
        visual_metadata: Metadata for UI visualization.
    """

    model_config = ConfigDict(extra="forbid")

    event_type: Literal[
        "NODE_INIT",
        "NODE_START",
        "NODE_STREAM",
        "NODE_DONE",
        "NODE_SKIPPED",
        "EDGE_ACTIVE",
        "COUNCIL_VOTE",
        "ERROR",
        "NODE_RESTORED",
        "ARTIFACT_GENERATED",
    ]
    run_id: str
    trace_id: str = Field(
        default_factory=lambda: "unknown"
    )  # Default for compatibility if missing in some legacy calls
    node_id: str  # Required per BRD and existing tests
    timestamp: float
    sequence_id: Optional[int] = None  # Optional for internal use

    # The payload contains the actual reasoning/data
    payload: Dict[str, Any] = Field(..., description="The logic output")

    # Visual Metadata drives the Flutter animation engine
    visual_metadata: Dict[str, str] = Field(
        ..., description="Hints for UI: color='#00FF00', animation='pulse', progress='0.5'"
    )


# --- Base Models ---


class BaseNodePayload(BaseModel):
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


class EdgeTraversed(BaseModel):
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


class WorkflowError(BaseNodePayload):
    """Payload for ERROR event."""

    error_message: str
    stack_trace: str
    input_snapshot: Dict[str, Any]
    status: Literal["ERROR"] = "ERROR"
    visual_cue: str = "RED_FLASH"


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

    # Prepare payload dict with node_id injected
    payload_dict = event.payload.copy()
    payload_dict["node_id"] = event.node_id
    # Inject timestamp if missing (required by some payloads like NodeStarted)
    if "timestamp" not in payload_dict:
        payload_dict["timestamp"] = event.timestamp

    # Mapping event types to their corresponding payload classes
    event_class_map: Dict[str, Any] = {
        "NODE_INIT": NodeInit,
        "NODE_START": NodeStarted,
        "NODE_DONE": NodeCompleted,
        "NODE_STREAM": NodeStream,
        "NODE_SKIPPED": NodeSkipped,
        "NODE_RESTORED": NodeRestored,
        "ERROR": WorkflowError,
        "ARTIFACT_GENERATED": ArtifactGenerated,
        "COUNCIL_VOTE": CouncilVote,
        "EDGE_ACTIVE": EdgeTraversed,
    }

    data: Any = None
    payload_class = event_class_map.get(event.event_type)

    if payload_class:
        try:
            # Instantiate the payload object
            payload_obj = payload_class(**payload_dict)
            if isinstance(payload_obj, CloudEventSource):
                data = payload_obj.as_cloud_event_payload()
            else:
                data = payload_obj  # pragma: no cover
        except Exception:
            # Fallback if instantiation fails
            data = event.payload
    else:
        data = event.payload

    # UI Metadata as extension
    extensions = {
        "com_coreason_ui_cue": event.visual_metadata.get("animation") or event.payload.get("visual_cue"),
        "com_coreason_ui_metadata": event.visual_metadata,
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
        data=data,
        **extensions,
    )
