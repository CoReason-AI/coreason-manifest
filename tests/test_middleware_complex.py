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
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from coreason_manifest.spec.cap import AgentRequest, StreamOpCode, StreamPacket
from coreason_manifest.spec.interfaces.middleware import (
    InterceptorContext,
)


class UppercaseInterceptor:
    """Uppercases the query."""

    async def intercept_request(
        self,
        _context: InterceptorContext,
        request: AgentRequest,
    ) -> AgentRequest:
        return request.model_copy(update={"query": request.query.upper()})


class AppendSuffixInterceptor:
    """Appends a suffix."""

    async def intercept_request(
        self,
        _context: InterceptorContext,
        request: AgentRequest,
    ) -> AgentRequest:
        return request.model_copy(update={"query": request.query + " [CHECKED]"})


@pytest.mark.asyncio
async def test_chained_interceptors() -> None:
    """Verify that multiple interceptors can be chained."""
    interceptors = [UppercaseInterceptor(), AppendSuffixInterceptor()]
    context = InterceptorContext(request_id=uuid4(), start_time=datetime.now(UTC))
    request = AgentRequest(query="hello world")

    for interceptor in interceptors:
        request = await interceptor.intercept_request(context, request)

    assert request.query == "HELLO WORLD [CHECKED]"


class CrashingInterceptor:
    """Simulates a crash."""

    async def intercept_stream(self, packet: StreamPacket) -> StreamPacket:
        if packet.op == StreamOpCode.DELTA:
            raise ValueError("Crash!")
        return packet


@pytest.mark.asyncio
async def test_interceptor_crash_in_stream() -> None:
    """Verify exception propagation from interceptor."""
    interceptor = CrashingInterceptor()
    packet = StreamPacket(op=StreamOpCode.DELTA, p="data")

    with pytest.raises(ValueError, match="Crash!"):
        await interceptor.intercept_stream(packet)


def test_metadata_immutability_depth() -> None:
    """Verify that metadata dict content is mutable but container is frozen."""
    metadata = {"key": "value", "nested": {"a": 1}}
    context = InterceptorContext(request_id=uuid4(), start_time=datetime.now(UTC), metadata=metadata)

    # The container (metadata field) cannot be reassigned
    # context.metadata = {}  # Raises ValidationError (tested elsewhere)

    # However, the dictionary content ITSELF is mutable unless we use MappingProxyType or similar.
    # Pydantic 'frozen=True' prevents reassignment of the field, but doesn't deep-freeze standard dicts.
    # This test documents the behavior: Middleware authors should treat metadata as read-only convention
    # or the engine should use deep-frozen structures if strict enforcement is needed.

    # We assert that we CAN modify it, which means we must document this as a caveat.
    context.metadata["key"] = "changed"
    assert context.metadata["key"] == "changed"


class SlowInterceptor:
    async def intercept_request(
        self,
        _context: InterceptorContext,
        request: AgentRequest,
    ) -> AgentRequest:
        await asyncio.sleep(0.01)
        return request


@pytest.mark.asyncio
async def test_concurrent_interceptors() -> None:
    """Verify async concurrency."""
    interceptor = SlowInterceptor()
    context = InterceptorContext(request_id=uuid4(), start_time=datetime.now(UTC))
    requests = [AgentRequest(query=f"req-{i}") for i in range(10)]

    # process all concurrently
    results = await asyncio.gather(*(interceptor.intercept_request(context, req) for req in requests))

    assert len(results) == 10
    for i, res in enumerate(results):
        assert res.query == f"req-{i}"
