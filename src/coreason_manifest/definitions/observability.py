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
from typing import Any, Dict, Literal, Optional, Union
from uuid import UUID, uuid4

from pydantic import Field, model_validator

from ..common import CoReasonBaseModel


class EventContentType(str, Enum):
    JSON = "application/json"
    STREAM = "application/vnd.coreason.stream+json"
    ERROR = "application/vnd.coreason.error+json"
    ARTIFACT = "application/vnd.coreason.artifact+json"


class CloudEvent(CoReasonBaseModel):
    """
    A strictly typed Pydantic model compliant with the CloudEvents 1.0 JSON Format.
    https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/formats/json-format.md
    """

    model_config = {"frozen": True}

    specversion: Literal["1.0"] = "1.0"
    id: str = Field(description="Unique event ID")
    source: str = Field(description="URI reference to the producer, e.g., urn:node:step-1")
    type: str = Field(description="Reverse-DNS type, e.g., ai.coreason.node.started")
    time: datetime = Field(description="Timestamp of when the occurrence happened (UTC)")
    datacontenttype: Union[EventContentType, str] = Field(
        default=EventContentType.JSON, description="MIME content type of data (e.g. application/json)"
    )
    data: Optional[Dict[str, Any]] = None

    # Extensions for Distributed Tracing (W3C Trace Context)
    traceparent: Optional[str] = None
    tracestate: Optional[str] = None


class ReasoningTrace(CoReasonBaseModel):
    """
    A structured log entry for audit trails.

    Warning:
        This model does not automatically redact PII or secrets.
        Ensure `inputs` and `outputs` are sanitized before logging.
    """

    model_config = {"frozen": True}

    request_id: UUID = Field(default_factory=uuid4)
    root_request_id: Optional[UUID] = Field(default=None, description="The original user request ID (for lineage)")
    parent_request_id: Optional[UUID] = None
    node_id: str = Field(description="The step name")
    status: str = Field(description='"success" or "failed"')
    inputs: Optional[Dict[str, Any]] = None
    outputs: Optional[Dict[str, Any]] = None
    latency_ms: float
    timestamp: datetime

    @model_validator(mode="before")
    @classmethod
    def _auto_root(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Ensure request_id exists
            if data.get("request_id") is None:
                data["request_id"] = uuid4()

            # Ensure root_request_id exists (copy request_id if missing)
            if data.get("root_request_id") is None:
                data["root_request_id"] = data["request_id"]
        return data


class AuditLog(CoReasonBaseModel):
    """
    Immutable audit log entry for compliance and security auditing.
    """

    model_config = {"frozen": True}

    id: UUID = Field(default_factory=uuid4)
    request_id: UUID
    root_request_id: UUID
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    actor: str
    action: str
    outcome: str
    integrity_hash: str
