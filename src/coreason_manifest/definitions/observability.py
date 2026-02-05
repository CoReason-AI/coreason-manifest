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
from typing import Any, Dict, Literal, Optional
from uuid import UUID

from pydantic import Field

from ..common import CoReasonBaseModel


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
    datacontenttype: str = Field(default="application/json")
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

    request_id: UUID
    root_request_id: UUID = Field(description="The original user request ID (for lineage)")
    parent_request_id: Optional[UUID] = None
    node_id: str = Field(description="The step name")
    status: str = Field(description='"success" or "failed"')
    inputs: Optional[Dict[str, Any]] = None
    outputs: Optional[Dict[str, Any]] = None
    latency_ms: float
    timestamp: datetime
