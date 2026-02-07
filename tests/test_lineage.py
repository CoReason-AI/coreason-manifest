# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.cap import AgentRequest
from coreason_manifest.spec.common.observability import AuditLog, ReasoningTrace
from coreason_manifest.spec.common.session import Interaction, LineageMetadata


def test_agent_request_auto_rooting() -> None:
    """Verify that an AgentRequest without a root becomes its own root."""
    req = AgentRequest(session_id=uuid4(), payload={"query": "test"})  # request_id auto-generated

    assert isinstance(req.request_id, UUID)
    assert isinstance(req.root_request_id, UUID)
    assert req.root_request_id == req.request_id
    assert req.parent_request_id is None


def test_agent_request_explicit_none_root() -> None:
    """Verify that passing None to root_request_id triggers auto-rooting."""
    req = AgentRequest(session_id=uuid4(), payload={"query": "test"}, root_request_id=None)

    assert isinstance(req.root_request_id, UUID)
    assert req.root_request_id == req.request_id


def test_agent_request_with_explicit_request_id_auto_root() -> None:
    """Verify auto-rooting works when request_id is manually provided."""
    uid = uuid4()
    req = AgentRequest(session_id=uuid4(), payload={"query": "test"}, request_id=uid)

    assert req.request_id == uid
    assert req.root_request_id == uid


def test_agent_request_validation_error() -> None:
    """Verify validation fails for invalid types."""
    # Mypy might check types before runtime, but Pydantic validates at runtime.
    # We force a type mismatch to check runtime validation.
    bad_id: Any = "not-a-uuid"
    with pytest.raises(ValidationError):
        AgentRequest(session_id=uuid4(), payload={"query": "test"}, request_id=bad_id)


def test_agent_request_auto_rooting_with_explicit_id() -> None:
    """Verify that auto-rooting works when request_id is provided."""
    uid = uuid4()
    req = AgentRequest(request_id=uid, session_id=uuid4(), payload={"query": "test"})

    assert req.request_id == uid
    assert req.root_request_id == uid


def test_agent_request_explicit_root() -> None:
    """Verify that explicitly provided root is respected."""
    root_id = uuid4()
    child_id = uuid4()

    req = AgentRequest(
        request_id=child_id,
        session_id=uuid4(),
        root_request_id=root_id,
        parent_request_id=root_id,
        payload={"query": "test"},
    )

    assert req.request_id == child_id
    assert req.root_request_id == root_id
    assert req.parent_request_id == root_id
    assert req.root_request_id != req.request_id


def test_reasoning_trace_auto_rooting() -> None:
    """Verify that ReasoningTrace auto-roots if root is missing."""
    uid = uuid4()
    trace = ReasoningTrace(
        request_id=uid, node_id="step-1", status="success", latency_ms=10.5, timestamp=datetime.now(UTC)
    )

    assert trace.request_id == uid
    assert trace.root_request_id == uid


def test_reasoning_trace_complex_lineage() -> None:
    """Verify a chain of lineage in traces."""
    # Root request
    root_id = uuid4()
    trace_root = ReasoningTrace(
        request_id=root_id,
        node_id="root-node",
        status="success",
        latency_ms=10.0,
        timestamp=datetime.now(UTC),
    )
    assert trace_root.root_request_id == root_id

    # Child request
    child_id = uuid4()
    trace_child = ReasoningTrace(
        request_id=child_id,
        root_request_id=root_id,
        parent_request_id=root_id,
        node_id="child-node",
        status="success",
        latency_ms=5.0,
        timestamp=datetime.now(UTC),
    )
    assert trace_child.root_request_id == root_id
    assert trace_child.parent_request_id == root_id

    # Grandchild request
    grandchild_id = uuid4()
    trace_grandchild = ReasoningTrace(
        request_id=grandchild_id,
        root_request_id=root_id,
        parent_request_id=child_id,
        node_id="grandchild-node",
        status="success",
        latency_ms=2.0,
        timestamp=datetime.now(UTC),
    )
    assert trace_grandchild.root_request_id == root_id
    assert trace_grandchild.parent_request_id == child_id


def test_reasoning_trace_explicit_root() -> None:
    """Verify that ReasoningTrace respects explicit root."""
    uid = uuid4()
    root = uuid4()
    trace = ReasoningTrace(
        request_id=uid,
        root_request_id=root,
        node_id="step-1",
        status="success",
        latency_ms=10.5,
        timestamp=datetime.now(UTC),
    )

    assert trace.request_id == uid
    assert trace.root_request_id == root


def test_audit_log_structure() -> None:
    """Verify AuditLog structure and serialization."""
    uid = uuid4()
    root = uuid4()
    log_id = uuid4()

    log = AuditLog(
        id=log_id,
        request_id=uid,
        root_request_id=root,
        timestamp=datetime.now(UTC),
        actor="user:123",
        action="execute",
        outcome="success",
        integrity_hash="sha256:abc...",
    )

    assert log.id == log_id
    assert log.root_request_id == root
    assert log.integrity_hash == "sha256:abc..."

    # Verify serialization
    dump = log.dump()
    assert dump["id"] == str(log_id)
    assert dump["integrity_hash"] == "sha256:abc..."


def test_interaction_lineage() -> None:
    """Verify Interaction model with LineageMetadata using string IDs."""
    root = "root-123"
    parent = "inter-456"

    meta = LineageMetadata(root_request_id=root, parent_interaction_id=parent)

    interaction = Interaction(id="inter-789", lineage=meta)

    assert interaction.id == "inter-789"
    assert interaction.lineage is not None
    assert interaction.lineage.root_request_id == root
    assert interaction.lineage.parent_interaction_id == parent


def test_broken_chain_prevention() -> None:
    """Verify that providing a parent without a root raises an error."""
    parent_id = uuid4()

    # AgentRequest: Parent provided, Root missing -> Error
    with pytest.raises(ValueError, match="Broken Trace"):
        AgentRequest(session_id=uuid4(), payload={"query": "test"}, parent_request_id=parent_id)

    # ReasoningTrace: Parent provided, Root missing -> Error
    with pytest.raises(ValueError, match="Broken Lineage"):
        ReasoningTrace(
            request_id=uuid4(),
            parent_request_id=parent_id,
            node_id="step-1",
            status="success",
            latency_ms=10.0,
            timestamp=datetime.now(UTC),
        )

    # AgentRequest: Valid case (Parent + Root) -> Success
    root_id = uuid4()
    req = AgentRequest(
        session_id=uuid4(),
        payload={"query": "test"},
        root_request_id=root_id,
        parent_request_id=parent_id,
    )
    assert req.root_request_id == root_id
    assert req.parent_request_id == parent_id

    # AgentRequest: Valid case (No Parent, No Root) -> Auto-root
    req_auto = AgentRequest(session_id=uuid4(), payload={"query": "test"})
    assert req_auto.root_request_id == req_auto.request_id
