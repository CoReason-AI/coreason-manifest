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
from uuid import UUID, uuid4

from coreason_manifest.definitions.observability import AuditLog, ReasoningTrace
from coreason_manifest.definitions.session import Interaction, LineageMetadata
from coreason_manifest.spec.cap import AgentRequest


def test_agent_request_auto_rooting() -> None:
    """Verify that an AgentRequest without a root becomes its own root."""
    req = AgentRequest(query="test")  # request_id auto-generated

    assert isinstance(req.request_id, UUID)
    assert isinstance(req.root_request_id, UUID)
    assert req.root_request_id == req.request_id
    assert req.parent_request_id is None


def test_agent_request_auto_rooting_with_explicit_id() -> None:
    """Verify that auto-rooting works when request_id is provided."""
    uid = uuid4()
    req = AgentRequest(request_id=uid, query="test")

    assert req.request_id == uid
    assert req.root_request_id == uid


def test_agent_request_explicit_root() -> None:
    """Verify that explicitly provided root is respected."""
    root_id = uuid4()
    child_id = uuid4()

    req = AgentRequest(request_id=child_id, root_request_id=root_id, parent_request_id=root_id, query="test")

    assert req.request_id == child_id
    assert req.root_request_id == root_id
    assert req.parent_request_id == root_id
    assert req.root_request_id != req.request_id


def test_reasoning_trace_auto_rooting() -> None:
    """Verify that ReasoningTrace auto-roots if root is missing."""
    uid = uuid4()
    trace = ReasoningTrace(
        request_id=uid, node_id="step-1", status="success", latency_ms=10.5, timestamp=datetime.now(timezone.utc)
    )

    assert trace.request_id == uid
    assert trace.root_request_id == uid


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
        timestamp=datetime.now(timezone.utc),
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
        timestamp=datetime.now(timezone.utc),
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
