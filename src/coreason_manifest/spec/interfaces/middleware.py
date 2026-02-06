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
from typing import Any, Protocol, runtime_checkable
from uuid import UUID

from pydantic import ConfigDict, Field

from coreason_manifest.spec.cap import AgentRequest, SessionContext, StreamPacket
from coreason_manifest.spec.common_base import CoReasonBaseModel


class InterceptorContext(CoReasonBaseModel):
    """Context for middleware interception."""

    model_config = ConfigDict(frozen=True)

    request_id: UUID
    start_time: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


@runtime_checkable
class IRequestInterceptor(Protocol):
    """Protocol for intercepting and modifying requests."""

    async def intercept_request(
        self,
        context: SessionContext,
        request: AgentRequest,
    ) -> AgentRequest:
        """Modify or validate the request before the agent sees it."""
        ...


@runtime_checkable
class IResponseInterceptor(Protocol):
    """Protocol for intercepting and modifying output streams."""

    async def intercept_stream(self, packet: StreamPacket) -> StreamPacket:
        """Modify the output stream in real-time."""
        ...
