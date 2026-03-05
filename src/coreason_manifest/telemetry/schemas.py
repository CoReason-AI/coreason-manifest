# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

import re
from typing import Annotated, Any, Literal

from pydantic import BeforeValidator, Field

from coreason_manifest.core.base import CoreasonBaseModel


def _redact_toxic_string(v: Any, depth: int = 0) -> Any:
    if depth > 100:
        raise ValueError("Data structure too deep")
    if isinstance(v, str):
        v = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[REDACTED]", v)
        return re.sub(r"\bAPI_KEY_[a-zA-Z0-9]+\b", "[REDACTED]", v)
    if isinstance(v, dict):
        return {k: _redact_toxic_string(val, depth + 1) for k, val in v.items()}
    if isinstance(v, list):
        return [_redact_toxic_string(val, depth + 1) for val in v]
    if isinstance(v, set):
        return {_redact_toxic_string(val, depth + 1) for val in v}
    if isinstance(v, tuple):
        return tuple(_redact_toxic_string(val, depth + 1) for val in v)
    return v


PrivacySentinel = Annotated[Any, BeforeValidator(_redact_toxic_string)]

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
