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
from uuid import uuid4

from coreason_manifest.definitions.observability import ReasoningTrace
from coreason_manifest.spec.cap import AgentRequest


def test_agent_request_auto_rooting() -> None:
    """Test that AgentRequest automatically sets root_request_id if missing."""
    # 1. Provide nothing
    req = AgentRequest(query="test")
    assert req.request_id is not None
    assert req.root_request_id == req.request_id
    assert req.parent_request_id is None

    # 2. Provide request_id but no root
    rid = uuid4()
    req2 = AgentRequest(query="test", request_id=rid)
    assert req2.request_id == rid
    assert req2.root_request_id == rid

    # 3. Provide root explicit
    rid = uuid4()
    root = uuid4()
    req3 = AgentRequest(query="test", request_id=rid, root_request_id=root)
    assert req3.request_id == rid
    assert req3.root_request_id == root


def test_reasoning_trace_auto_rooting() -> None:
    """Test that ReasoningTrace automatically sets root_request_id if missing."""
    now = datetime.now(timezone.utc)

    # 1. Provide request_id (via auto-gen or explicit) but no root
    trace = ReasoningTrace(
        node_id="test",
        status="ok",
        latency_ms=1.0,
        timestamp=now
    )
    assert trace.request_id is not None
    assert trace.root_request_id == trace.request_id

    # 2. Provide request_id explicit
    rid = uuid4()
    trace2 = ReasoningTrace(
        request_id=rid,
        node_id="test",
        status="ok",
        latency_ms=1.0,
        timestamp=now
    )
    assert trace2.request_id == rid
    assert trace2.root_request_id == rid

    # 3. Provide root explicit
    rid = uuid4()
    root = uuid4()
    trace3 = ReasoningTrace(
        request_id=rid,
        root_request_id=root,
        node_id="test",
        status="ok",
        latency_ms=1.0,
        timestamp=now
    )
    assert trace3.request_id == rid
    assert trace3.root_request_id == root
