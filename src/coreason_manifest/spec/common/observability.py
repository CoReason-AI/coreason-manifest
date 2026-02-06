# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import ConfigDict, Field, model_validator

from ..common_base import CoReasonBaseModel


class EventContentType(StrEnum):
    JSON = "application/json"
    STREAM = "application/vnd.coreason.stream+json"
    ERROR = "application/vnd.coreason.error+json"
    ARTIFACT = "application/vnd.coreason.artifact+json"


class CloudEvent(CoReasonBaseModel):
    """
    A strictly typed Pydantic model compliant with the CloudEvents 1.0 JSON Format.
    https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/formats/json-format.md
    """

    model_config = ConfigDict(frozen=True)

    specversion: Literal["1.0"] = "1.0"
    id: str = Field(description="Unique event ID")
    source: str = Field(description="URI reference to the producer, e.g., urn:node:step-1")
    type: str = Field(description="Reverse-DNS type, e.g., ai.coreason.node.started")
    time: datetime = Field(description="Timestamp of when the occurrence happened (UTC)")
    datacontenttype: EventContentType | str = Field(
        default=EventContentType.JSON, description="MIME content type of data (e.g. application/json)"
    )
    data: dict[str, Any] | None = None

    # Extensions for Distributed Tracing (W3C Trace Context)
    traceparent: str | None = None
    tracestate: str | None = None


class ReasoningTrace(CoReasonBaseModel):
    """
    A structured log entry for audit trails.

    Warning:
        This model does not automatically redact PII or secrets.
        Ensure `inputs` and `outputs` are sanitized before logging.
    """

    model_config = ConfigDict(frozen=True)

    request_id: UUID
    root_request_id: UUID | None = Field(default=None, description="The original user request ID (for lineage)")
    parent_request_id: UUID | None = None
    node_id: str = Field(description="The step name")
    status: str = Field(description='"success" or "failed"')
    inputs: dict[str, Any] | None = None
    outputs: dict[str, Any] | None = None
    latency_ms: float
    timestamp: datetime

    @model_validator(mode="before")
    @classmethod
    def enforce_lineage(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Check for Broken Chain FIRST
            if data.get("parent_request_id") is not None and data.get("root_request_id") is None:
                raise ValueError("Broken Lineage: 'root_request_id' is required when 'parent_request_id' is present.")

            if (data.get("root_request_id") is None) and ("request_id" in data):
                # Auto-rooting: If root is missing, it is the root (derived from request_id)
                data["root_request_id"] = data["request_id"]
        return data


class AuditLog(CoReasonBaseModel):
    """Immutable audit record for compliance and security monitoring."""

    model_config = ConfigDict(frozen=True)

    id: UUID
    request_id: UUID
    root_request_id: UUID
    timestamp: datetime
    actor: str
    action: str
    outcome: str
    safety_metadata: dict[str, Any] | None = Field(
        default=None, description="Security context and policy decision metadata."
    )
    previous_hash: str | None = Field(None, description="Hash of the preceding log entry for tamper-evidence.")
    integrity_hash: str = Field(description="SHA-256 hash of this record.")
