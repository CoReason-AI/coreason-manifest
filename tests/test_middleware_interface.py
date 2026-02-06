# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from datetime import datetime, UTC
from uuid import uuid4
from typing import Any

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.interfaces.middleware import (
    InterceptorContext,
    IRequestInterceptor,
    IResponseInterceptor,
)
from coreason_manifest.spec.cap import AgentRequest, StreamPacket, StreamOpCode

def test_interceptor_context_immutability() -> None:
    """Verify InterceptorContext is frozen."""
    context = InterceptorContext(
        request_id=uuid4(),
        start_time=datetime.now(UTC),
        metadata={"token": "abc"}
    )

    # Attempt to modify request_id
    with pytest.raises(ValidationError):
        context.request_id = uuid4()  # type: ignore

    # Attempt to modify metadata
    with pytest.raises(ValidationError):
        context.metadata = {}  # type: ignore


class PIIRedactionInterceptor:
    """Interceptor that redaction 'secret' from request query."""

    async def intercept_request(
        self,
        context: InterceptorContext,
        request: AgentRequest,
    ) -> AgentRequest:
        if "secret" in request.query:
            new_query = request.query.replace("secret", "******")
            # Create new request as AgentRequest is frozen
            return request.model_copy(update={"query": new_query})
        return request


@pytest.mark.asyncio
async def test_pii_redaction_interceptor() -> None:
    """Test modification of request data."""
    interceptor = PIIRedactionInterceptor()
    context = InterceptorContext(
        request_id=uuid4(),
        start_time=datetime.now(UTC),
        metadata={}
    )
    request = AgentRequest(query="This is a secret message.")

    processed_request = await interceptor.intercept_request(context, request)

    assert processed_request.query == "This is a ****** message."
    assert processed_request.request_id == request.request_id


class PolicyInterceptor:
    """Interceptor that blocks requests based on policy."""

    async def intercept_request(
        self,
        context: InterceptorContext,
        request: AgentRequest,
    ) -> AgentRequest:
        if context.metadata.get("block"):
            raise ValueError("Blocked by policy")
        return request


@pytest.mark.asyncio
async def test_policy_rejection_interceptor() -> None:
    """Test blocking of requests."""
    interceptor = PolicyInterceptor()
    request = AgentRequest(query="Hello")

    # Allowed
    context_allowed = InterceptorContext(
        request_id=uuid4(),
        start_time=datetime.now(UTC),
        metadata={"block": False}
    )
    assert await interceptor.intercept_request(context_allowed, request) == request

    # Blocked
    context_blocked = InterceptorContext(
        request_id=uuid4(),
        start_time=datetime.now(UTC),
        metadata={"block": True}
    )
    with pytest.raises(ValueError, match="Blocked by policy"):
        await interceptor.intercept_request(context_blocked, request)


class ResponseCensorInterceptor:
    """Interceptor that censors 'bad' words in stream."""

    async def intercept_stream(self, packet: StreamPacket) -> StreamPacket:
        if packet.op == StreamOpCode.DELTA and isinstance(packet.p, str):
            if "bad" in packet.p:
                new_payload = packet.p.replace("bad", "***")
                return packet.model_copy(update={"p": new_payload})
        return packet


@pytest.mark.asyncio
async def test_response_interceptor() -> None:
    """Test modification of stream packets."""
    interceptor = ResponseCensorInterceptor()

    packet = StreamPacket(op=StreamOpCode.DELTA, p="This is a bad word.")
    processed_packet = await interceptor.intercept_stream(packet)

    assert processed_packet.p == "This is a *** word."


def test_protocol_compliance() -> None:
    """Verify classes implement protocols correctly."""
    assert isinstance(PIIRedactionInterceptor(), IRequestInterceptor)
    assert isinstance(ResponseCensorInterceptor(), IResponseInterceptor)

    # Verify invalid implementation doesn't pass
    class InvalidInterceptor:
        pass

    assert not isinstance(InvalidInterceptor(), IRequestInterceptor)
