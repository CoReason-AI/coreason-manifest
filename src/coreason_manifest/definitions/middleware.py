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
from typing import Any, Dict, Protocol, runtime_checkable
from uuid import UUID

from pydantic import ConfigDict, Field

from coreason_manifest.common import CoReasonBaseModel
from coreason_manifest.definitions.presentation import StreamPacket
from coreason_manifest.definitions.request import AgentRequest
from coreason_manifest.definitions.session import SessionContext


class InterceptorContext(CoReasonBaseModel):
    """A lightweight immutable object to pass shared data between interceptors."""

    model_config = ConfigDict(frozen=True)

    request_id: UUID = Field(..., description="The unique ID of the request being processed")
    start_time: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the interception chain started",
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Shared scratchpad for interceptors")


@runtime_checkable
class IRequestInterceptor(Protocol):
    """Protocol for intercepting and modifying agent requests."""

    async def intercept_request(self, context: SessionContext, request: AgentRequest) -> AgentRequest:
        """Modify or validate the request before the agent sees it."""
        ...


@runtime_checkable
class IResponseInterceptor(Protocol):
    """Protocol for intercepting and modifying the output stream."""

    async def intercept_stream(self, packet: StreamPacket) -> StreamPacket:
        """Modify the output stream in real-time."""
        ...
