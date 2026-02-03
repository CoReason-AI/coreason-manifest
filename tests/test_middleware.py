# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from uuid import uuid4
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from coreason_manifest.definitions.middleware import (
    InterceptorContext,
    IRequestInterceptor,
    IResponseInterceptor,
)
from coreason_manifest.definitions.request import AgentRequest
from coreason_manifest.definitions.session import SessionContext
from coreason_manifest.definitions.presentation import StreamPacket


class PIIFilter:
    async def intercept_request(self, context: SessionContext, request: AgentRequest) -> AgentRequest:
        return request


class ToxicityFilter:
    async def intercept_stream(self, packet: StreamPacket) -> StreamPacket:
        return packet


def test_interceptor_protocols():
    # Verify PIIFilter implements IRequestInterceptor
    pii_filter = PIIFilter()
    assert isinstance(pii_filter, IRequestInterceptor)

    # Verify it doesn't implement IResponseInterceptor
    assert not isinstance(pii_filter, IResponseInterceptor)

    # Verify ToxicityFilter implements IResponseInterceptor
    toxicity_filter = ToxicityFilter()
    assert isinstance(toxicity_filter, IResponseInterceptor)


def test_interceptor_context_immutability():
    ctx = InterceptorContext(request_id=uuid4())

    # Verify default values
    assert ctx.metadata == {}
    assert ctx.start_time is not None

    # Verify immutability
    with pytest.raises(ValidationError):
        ctx.metadata = {"foo": "bar"}
