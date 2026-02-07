# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import json
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.common.request import AgentRequest


def test_new_trace_auto_rooting() -> None:
    """Verify that a new request becomes the root of its own trace."""
    session_id = uuid4()
    payload = {"query": "start"}

    req = AgentRequest(session_id=session_id, payload=payload)

    assert isinstance(req.request_id, UUID)
    assert req.request_id == req.root_request_id
    assert req.parent_request_id is None
    assert req.session_id == session_id
    assert req.payload == payload


def test_trace_continuity_child_creation() -> None:
    """Verify strict lineage inheritance in child requests."""
    root = AgentRequest(session_id=uuid4(), payload={"step": 1})

    child_payload = {"step": 2}
    child = root.create_child(payload=child_payload)

    # Trace context
    assert child.root_request_id == root.root_request_id
    assert child.parent_request_id == root.request_id

    # Session context
    assert child.session_id == root.session_id

    # New identifiers
    assert child.request_id != root.request_id
    assert isinstance(child.request_id, UUID)

    # Payload
    assert child.payload == child_payload

    # Metadata copy behavior (default: copy)
    root_meta = AgentRequest(session_id=uuid4(), payload={}, metadata={"foo": "bar"})
    child_meta = root_meta.create_child(payload={})
    assert child_meta.metadata == {"foo": "bar"}
    # Ensure it's a copy
    assert child_meta.metadata is not root_meta.metadata

    # Metadata override behavior
    child_override = root_meta.create_child(payload={}, metadata={"baz": "qux"})
    assert child_override.metadata == {"baz": "qux"}


def test_broken_trace_prevention() -> None:
    """Verify validation logic catches broken traces."""
    parent_id = uuid4()

    # Case: Parent exists, Root missing -> Error
    with pytest.raises(ValueError, match="Broken Trace"):
        AgentRequest(
            session_id=uuid4(),
            payload={},
            parent_request_id=parent_id,
            # root_request_id missing -> defaults to None initially, validator catches it
        )


def test_immutability_and_serialization() -> None:
    """Verify the request envelope is immutable and serializes correctly."""
    req = AgentRequest(session_id=uuid4(), payload={"query": "test"})

    # Immutability
    with pytest.raises(ValidationError):
        req.payload = {"query": "hacked"}  # type: ignore

    # Serialization
    json_str = req.to_json()
    data = json.loads(json_str)

    assert data["request_id"] == str(req.request_id)
    assert data["root_request_id"] == str(req.root_request_id)
    assert data["session_id"] == str(req.session_id)
    assert data["payload"] == {"query": "test"}
    # Check datetime format (ISO 8601)
    assert "created_at" in data
