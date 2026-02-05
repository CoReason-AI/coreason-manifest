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
from typing import Any
from uuid import UUID, uuid4

from pydantic import ConfigDict, Field, model_validator

from coreason_manifest.spec.common.identity import Identity
from coreason_manifest.spec.common_base import CoReasonBaseModel


class HealthCheckStatus(StrEnum):
    """Status of the health check."""

    OK = "ok"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"


class HealthCheckResponse(CoReasonBaseModel):
    """Response for a health check request."""

    model_config = ConfigDict(frozen=True)

    status: HealthCheckStatus
    agent_id: UUID
    version: str
    uptime_seconds: float


class ErrorSeverity(StrEnum):
    """Severity of a stream error."""

    TRANSIENT = "transient"
    FATAL = "fatal"


class StreamOpCode(StrEnum):
    """Operation code for a stream packet."""

    DELTA = "delta"
    EVENT = "event"
    ERROR = "error"
    CLOSE = "close"


class StreamError(CoReasonBaseModel):
    """Strict error model for stream exceptions."""

    model_config = ConfigDict(frozen=True)

    code: str
    message: str
    severity: ErrorSeverity
    details: dict[str, Any] | None = None


class StreamPacket(CoReasonBaseModel):
    """A packet of data streaming from an agent."""

    model_config = ConfigDict(frozen=True)

    op: StreamOpCode
    p: StreamError | str | dict[str, Any] | None = Field(union_mode="left_to_right")

    @model_validator(mode="after")
    def validate_structure(self) -> "StreamPacket":
        if self.op == StreamOpCode.ERROR and not isinstance(self.p, StreamError):
            raise ValueError("Payload 'p' must be a valid StreamError when op is ERROR.")

        if self.op == StreamOpCode.DELTA and not isinstance(self.p, str):
            raise ValueError("Payload 'p' must be a string when op is DELTA.")

        return self


class ServiceResponse(CoReasonBaseModel):
    """Synchronous response from an agent service."""

    model_config = ConfigDict(frozen=True)

    request_id: UUID
    created_at: datetime
    output: dict[str, Any]
    metrics: dict[str, Any] | None = None


class AgentRequest(CoReasonBaseModel):
    """Strictly typed payload inside a ServiceRequest."""

    model_config = ConfigDict(frozen=True)

    request_id: UUID = Field(default_factory=uuid4)
    root_request_id: UUID | None = Field(
        default=None, description="The ID of the original user request. Must always be present."
    )
    parent_request_id: UUID | None = Field(default=None, description="The ID of the immediate caller.")

    query: str
    files: list[str] = Field(default_factory=list)
    conversation_id: str | None = None
    session_id: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def enforce_lineage(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Ensure request_id is present (needed for auto-rooting)
            if "request_id" not in data:
                data["request_id"] = uuid4()

            # Auto-rooting: If root is missing, it is the root
            if "root_request_id" not in data or data["root_request_id"] is None:
                data["root_request_id"] = data["request_id"]
        return data


class SessionContext(CoReasonBaseModel):
    """Strict context containing authentication and session details."""

    model_config = ConfigDict(frozen=True)

    session_id: str
    user: Identity
    agent: Identity | None = None


class ServiceRequest(CoReasonBaseModel):
    """Request to an agent service.

    Attributes:
        request_id: Unique trace ID for the transaction.
        context: Metadata about the request (User Identity, Auth, Session).
                 Separated from logic to enable consistent security policies.
        payload: The actual arguments for the Agent's execution.
    """

    model_config = ConfigDict(frozen=True)

    request_id: UUID
    context: SessionContext
    payload: AgentRequest
