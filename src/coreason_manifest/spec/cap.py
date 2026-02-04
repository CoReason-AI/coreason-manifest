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
from enum import Enum
from typing import Any, Dict, Optional, Union
from uuid import UUID

from pydantic import ConfigDict

from coreason_manifest.common import CoReasonBaseModel


class HealthCheckStatus(str, Enum):
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


class StreamPacket(CoReasonBaseModel):
    """A packet of data streaming from an agent."""

    model_config = ConfigDict(frozen=True)

    event: str
    data: Union[str, Dict[str, Any]]


class ServiceResponse(CoReasonBaseModel):
    """Synchronous response from an agent service."""

    model_config = ConfigDict(frozen=True)

    request_id: UUID
    created_at: datetime
    output: Dict[str, Any]
    metrics: Optional[Dict[str, Any]] = None


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
    # TODO: In v0.16.0, strictly type 'context' with a SessionContext model
    # once the Identity primitive is fully integrated.
    context: Dict[str, Any]
    payload: Dict[str, Any]
