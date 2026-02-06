# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest
from pydantic import ValidationError

from coreason_manifest import (
    AgentRequest,
    Identity,
    InterceptorContext,
    IRequestInterceptor,
    IResponseInterceptor,
    SessionContext,
    StreamPacket,
)


class MockPIIFilter:
    """Mock implementation of a request interceptor."""

    async def intercept_request(self, context: SessionContext, request: AgentRequest) -> AgentRequest:
        _ = context  # Suppress unused argument warning
        return request


class MockToxicityFilter:
    """Mock implementation of a response interceptor."""

    async def intercept_stream(self, packet: StreamPacket) -> StreamPacket:
        return packet


def test_request_interceptor_compliance() -> None:
    """Verify that MockPIIFilter satisfies the IRequestInterceptor protocol."""
    interceptor = MockPIIFilter()
    assert isinstance(interceptor, IRequestInterceptor)


def test_response_interceptor_compliance() -> None:
    """Verify that MockToxicityFilter satisfies the IResponseInterceptor protocol."""
    interceptor = MockToxicityFilter()
    assert isinstance(interceptor, IResponseInterceptor)


def test_interceptor_context_immutability() -> None:
    """Verify that InterceptorContext is immutable."""
    ctx = InterceptorContext(request_id=uuid4(), start_time=datetime.now(UTC))

    # Test reassigning a field
    with pytest.raises(ValidationError):
        ctx.request_id = uuid4()  # type: ignore

    with pytest.raises(ValidationError):
        ctx.start_time = datetime.now(UTC)  # type: ignore


def test_interceptor_context_defaults() -> None:
    """Verify defaults for InterceptorContext."""
    ctx = InterceptorContext(request_id=uuid4(), start_time=datetime.now(UTC))
    assert ctx.metadata == {}


class ModifyingInterceptor:
    """Interceptor that modifies the request query."""

    async def intercept_request(self, context: SessionContext, request: AgentRequest) -> AgentRequest:
        _ = context
        # Use model_copy to create a modified version (since AgentRequest is frozen)
        return request.model_copy(update={"query": request.query + " [REDACTED]"})


def test_interceptor_modification() -> None:
    """Test that an interceptor can modify a request."""
    # Create dependencies
    req = AgentRequest(query="My secret is 1234", request_id=uuid4(), root_request_id=uuid4())
    ctx = SessionContext(session_id="test-session", user=Identity.anonymous())

    interceptor = ModifyingInterceptor()

    async def run_test() -> None:
        new_req = await interceptor.intercept_request(ctx, req)
        assert new_req.query == "My secret is 1234 [REDACTED]"
        assert new_req.request_id == req.request_id

    asyncio.run(run_test())


def test_interceptor_context_edge_cases() -> None:
    """Test edge cases for InterceptorContext."""

    # 1. Large Metadata
    large_metadata = {f"key_{i}": f"value_{i}" for i in range(1000)}
    ctx_large = InterceptorContext(request_id=uuid4(), start_time=datetime.now(UTC), metadata=large_metadata)
    assert len(ctx_large.metadata) == 1000

    # 2. Nested Metadata
    nested_metadata: dict[str, Any] = {"level1": {"level2": {"level3": "deep"}}}
    ctx_nested = InterceptorContext(request_id=uuid4(), start_time=datetime.now(UTC), metadata=nested_metadata)
    # Cast to ensure type checking passes if strict
    assert ctx_nested.metadata["level1"]["level2"]["level3"] == "deep"

    # 3. Future Timestamp
    future_time = datetime.now(UTC) + timedelta(days=365)
    ctx_future = InterceptorContext(request_id=uuid4(), start_time=future_time)
    assert ctx_future.start_time == future_time


class ErrorInterceptor:
    """Interceptor that raises an error."""

    async def intercept_request(self, context: SessionContext, request: AgentRequest) -> AgentRequest:
        _ = (context, request)
        raise ValueError("Block this request")


def test_interceptor_error_propagation() -> None:
    """Test that exceptions from interceptors propagate."""
    interceptor = ErrorInterceptor()
    req = AgentRequest(query="Bad", request_id=uuid4(), root_request_id=uuid4())
    ctx = SessionContext(session_id="test-session", user=Identity.anonymous())

    async def run_test() -> None:
        with pytest.raises(ValueError, match="Block this request"):
            await interceptor.intercept_request(ctx, req)

    asyncio.run(run_test())
