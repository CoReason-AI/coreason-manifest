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
from datetime import datetime, timezone
from typing import List, Union
from uuid import uuid4

import pytest
from pydantic import ValidationError

from coreason_manifest.definitions.middleware import (
    InterceptorContext,
    IRequestInterceptor,
    IResponseInterceptor,
)
from coreason_manifest.definitions.presentation import StreamOpCode, StreamPacket
from coreason_manifest.definitions.request import AgentRequest
from coreason_manifest.definitions.session import SessionContext

# --- Mock Implementations ---


class PIIFilter:
    async def intercept_request(self, context: SessionContext, request: AgentRequest) -> AgentRequest:
        return request


class ToxicityFilter:
    async def intercept_stream(self, packet: StreamPacket) -> StreamPacket:
        return packet


class FailingInterceptor:
    async def intercept_request(self, context: SessionContext, request: AgentRequest) -> AgentRequest:
        raise ValueError("Simulated failure")


class ReplacementInterceptor:
    async def intercept_request(self, context: SessionContext, request: AgentRequest) -> AgentRequest:
        # Return a completely new request object
        return AgentRequest(session_id=request.session_id, payload={"replaced": True}, metadata=request.metadata)


class StatefulInterceptor:
    def __init__(self) -> None:
        self.call_count = 0

    async def intercept_stream(self, packet: StreamPacket) -> StreamPacket:
        self.call_count += 1
        return packet


# --- Basic Protocol Tests ---


def test_interceptor_protocols() -> None:
    # Verify PIIFilter implements IRequestInterceptor
    pii_filter = PIIFilter()
    assert isinstance(pii_filter, IRequestInterceptor)

    # Verify it doesn't implement IResponseInterceptor
    assert not isinstance(pii_filter, IResponseInterceptor)

    # Verify ToxicityFilter implements IResponseInterceptor
    toxicity_filter = ToxicityFilter()
    assert isinstance(toxicity_filter, IResponseInterceptor)


def test_interceptor_context_immutability() -> None:
    ctx = InterceptorContext(request_id=uuid4())

    # Verify default values
    assert ctx.metadata == {}
    assert ctx.start_time is not None

    # Verify immutability
    with pytest.raises(ValidationError):
        ctx.metadata = {"foo": "bar"}  # type: ignore[misc]


# --- Edge Case Tests ---


@pytest.mark.asyncio
async def test_interceptor_failure() -> None:
    """Test that an interceptor raising an exception propagates it."""
    interceptor = FailingInterceptor()
    # Create minimal valid objects
    session_id = uuid4()
    context = SessionContext(
        session_id=session_id,
        agent_id=uuid4(),
        user={"user_id": "u1", "tier": "free", "locale": "en-US"},
        trace={"trace_id": uuid4(), "span_id": uuid4()},
        permissions=[],
        created_at=datetime.now(timezone.utc),
    )
    request = AgentRequest(session_id=session_id, payload={})

    with pytest.raises(ValueError, match="Simulated failure"):
        await interceptor.intercept_request(context, request)


@pytest.mark.asyncio
async def test_interceptor_replacement() -> None:
    """Test that an interceptor can return a completely new request object."""
    interceptor = ReplacementInterceptor()
    session_id = uuid4()
    context = SessionContext(
        session_id=session_id,
        agent_id=uuid4(),
        user={"user_id": "u1", "tier": "free", "locale": "en-US"},
        trace={"trace_id": uuid4(), "span_id": uuid4()},
        permissions=[],
        created_at=datetime.now(timezone.utc),
    )
    request = AgentRequest(session_id=session_id, payload={"original": True})

    new_request = await interceptor.intercept_request(context, request)
    assert new_request.payload == {"replaced": True}
    assert new_request.request_id != request.request_id  # Should be different if recreated


# --- Complex Scenario Tests ---


@pytest.mark.asyncio
async def test_chained_interceptors() -> None:
    """Simulate a chain of interceptors (Manager logic simulation)."""

    class AppendingInterceptor:
        def __init__(self, key: str, value: str):
            self.key = key
            self.value = value

        async def intercept_request(self, context: SessionContext, request: AgentRequest) -> AgentRequest:
            new_payload = request.payload.copy()
            new_payload[self.key] = self.value
            return AgentRequest(
                session_id=request.session_id,
                payload=new_payload,
                metadata=request.metadata,
                root_request_id=request.root_request_id,
            )

    chain: List[Union[IRequestInterceptor, AppendingInterceptor]] = [
        AppendingInterceptor("step1", "done"),
        AppendingInterceptor("step2", "done"),
    ]

    session_id = uuid4()
    context = SessionContext(
        session_id=session_id,
        agent_id=uuid4(),
        user={"user_id": "u1", "tier": "free", "locale": "en-US"},
        trace={"trace_id": uuid4(), "span_id": uuid4()},
        permissions=[],
        created_at=datetime.now(timezone.utc),
    )
    request = AgentRequest(session_id=session_id, payload={})

    # Simulate manager applying chain
    current_request = request
    for interceptor in chain:
        current_request = await interceptor.intercept_request(context, current_request)

    assert current_request.payload == {"step1": "done", "step2": "done"}


@pytest.mark.asyncio
async def test_async_concurrency() -> None:
    """Test multiple requests hitting a stateful interceptor concurrently."""
    interceptor = StatefulInterceptor()

    packets = [
        StreamPacket(stream_id=uuid4(), seq=i, op=StreamOpCode.DELTA, t=datetime.now(timezone.utc), p="test")
        for i in range(100)
    ]

    # Process all concurrently
    await asyncio.gather(*[interceptor.intercept_stream(p) for p in packets])

    assert interceptor.call_count == 100
