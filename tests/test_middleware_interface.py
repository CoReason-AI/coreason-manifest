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
from uuid import uuid4

import pytest
from pydantic import ValidationError

try:
    from datetime import UTC
except ImportError:
    from datetime import timezone

    UTC = timezone.utc

from coreason_manifest import (
    AgentRequest,
    InterceptorContext,
    IRequestInterceptor,
    IResponseInterceptor,
    SessionContext,
    StreamPacket,
)


class MockPIIFilter:
    """Mock implementation of a request interceptor."""

    async def intercept_request(
        self, context: SessionContext, request: AgentRequest
    ) -> AgentRequest:
        return request


class MockToxicityFilter:
    """Mock implementation of a response interceptor."""

    async def intercept_stream(self, packet: StreamPacket) -> StreamPacket:
        return packet


def test_request_interceptor_compliance():
    """Verify that MockPIIFilter satisfies the IRequestInterceptor protocol."""
    interceptor = MockPIIFilter()
    assert isinstance(interceptor, IRequestInterceptor)


def test_response_interceptor_compliance():
    """Verify that MockToxicityFilter satisfies the IResponseInterceptor protocol."""
    interceptor = MockToxicityFilter()
    assert isinstance(interceptor, IResponseInterceptor)


def test_interceptor_context_immutability():
    """Verify that InterceptorContext is immutable."""
    ctx = InterceptorContext(request_id=uuid4(), start_time=datetime.now(UTC))

    # Test reassigning a field
    with pytest.raises(ValidationError):
        ctx.request_id = uuid4()

    with pytest.raises(ValidationError):
        ctx.start_time = datetime.now(UTC)


def test_interceptor_context_defaults():
    """Verify defaults for InterceptorContext."""
    ctx = InterceptorContext(request_id=uuid4(), start_time=datetime.now(UTC))
    assert ctx.metadata == {}
