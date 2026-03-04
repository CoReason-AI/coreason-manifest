from typing import Literal

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel

type TelemetryScalar = str | int | float | bool | None
type MetadataDict = dict[str, TelemetryScalar | list[TelemetryScalar]]


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
