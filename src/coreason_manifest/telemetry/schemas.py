# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from typing import Any, Literal

from pydantic import Field, model_validator

from coreason_manifest.core.base import CoreasonBaseModel

type TelemetryScalar = str | int | float | bool | None
type MetadataDict = dict[str, TelemetryScalar | list[TelemetryScalar]]

type SpanKind = Literal["client", "server", "producer", "consumer", "internal"]
type SpanStatusCode = Literal["unset", "ok", "error"]


class SpanEvent(CoreasonBaseModel):
    name: str = Field(description="The semantic name of the event.")
    timestamp_unix_nano: int = Field(description="The precise temporal execution point.")
    attributes: dict[str, Any] = Field(default_factory=dict, description="Typed metadata bound to the event.")


class ExecutionSpan(CoreasonBaseModel):
    trace_id: str = Field(description="The global identifier for the entire execution causal tree.")
    span_id: str = Field(description="The unique identifier for this specific operation.")
    parent_span_id: str | None = Field(default=None, description="The causal link to the invoking node.")
    name: str = Field(description="The semantic identifier for the operation.")
    kind: SpanKind = Field(default="internal", description="The role of the span.")
    start_time_unix_nano: int = Field(description="Temporal start bound.")
    end_time_unix_nano: int | None = Field(default=None, description="Temporal end bound, if completed.")
    status: SpanStatusCode = Field(default="unset", description="The execution health flag.")
    events: list[SpanEvent] = Field(
        default_factory=list, max_length=10000, description="Structured log records emitted during the span."
    )

    @model_validator(mode="after")
    def validate_temporal_bounds(self) -> Any:
        if self.end_time_unix_nano is not None and self.end_time_unix_nano < self.start_time_unix_nano:
            raise ValueError("end_time_unix_nano cannot be before start_time_unix_nano")
        if hasattr(self, "_cached_hash"):
            object.__delattr__(self, "_cached_hash")
        return self

    @model_validator(mode="after")
    def sort_events(self) -> Any:
        object.__setattr__(self, "events", sorted(self.events, key=lambda e: e.timestamp_unix_nano))
        if hasattr(self, "_cached_hash"):
            object.__delattr__(self, "_cached_hash")
        return self


class TraceExportBatch(CoreasonBaseModel):
    batch_id: str = Field(description="Unique identifier for this telemetry snapshot.")
    spans: list[ExecutionSpan] = Field(
        default_factory=list, description="A collection of execution spans to be serialized."
    )

    @model_validator(mode="after")
    def sort_spans(self) -> Any:
        object.__setattr__(self, "spans", sorted(self.spans, key=lambda s: s.span_id))
        if hasattr(self, "_cached_hash"):
            object.__delattr__(self, "_cached_hash")
        return self


class ObservabilityPolicy(CoreasonBaseModel):
    traces_sampled: bool = Field(
        default=True, description="Whether the orchestrator must record telemetry for this topology."
    )
    detailed_events: bool = Field(default=False, description="Whether to include granular intra-tool loop events.")


class LogEnvelope(CoreasonBaseModel):
    """
    An out-of-band telemetry log envelope.
    """

    timestamp: float = Field(description="The UNIX timestamp of the log event.")
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        description="The severity level of the log event."
    )
    message: str = Field(description="The primary log message.")
    metadata: MetadataDict = Field(
        default_factory=dict, description="Contextual key-value metadata associated with the event."
    )


class SpanTrace(CoreasonBaseModel):
    """
    An execution window span trace.
    """

    span_id: str = Field(description="The unique identifier for this execution span.")
    parent_span_id: str | None = Field(default=None, description="The identifier of the parent span, if any.")
    start_time: float = Field(description="The UNIX timestamp when the span started.")
    end_time: float | None = Field(default=None, description="The UNIX timestamp when the span ended.")
    status: Literal["OK", "ERROR", "PENDING"] = Field(description="The completion status of the span.")
    metadata: MetadataDict = Field(
        default_factory=dict, description="Contextual key-value metadata associated with the span execution."
    )
