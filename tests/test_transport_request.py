# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import pytest
import json
from uuid import uuid4, UUID
from datetime import datetime
from pydantic import ValidationError
from coreason_manifest.spec.common.request import AgentRequest

# --- Standard Cases ---

def test_new_trace_auto_rooting() -> None:
    session_id = uuid4()
    payload = {"query": "foo"}
    req = AgentRequest(session_id=session_id, payload=payload)

    assert isinstance(req.request_id, UUID)
    assert req.root_request_id == req.request_id
    assert req.parent_request_id is None
    assert req.session_id == session_id
    assert req.payload == payload
    assert isinstance(req.created_at, datetime)

def test_trace_continuity_child_creation() -> None:
    root = AgentRequest(session_id=uuid4(), payload={"step": "root"})
    child = root.create_child({"step": "child"})

    assert child.root_request_id == root.root_request_id
    assert child.parent_request_id == root.request_id
    assert child.session_id == root.session_id
    assert child.payload == {"step": "child"}
    assert child.request_id != root.request_id
    assert isinstance(child.request_id, UUID)

def test_broken_trace_validation() -> None:
    parent_id = uuid4()
    session_id = uuid4()

    with pytest.raises(ValueError, match="Broken Trace"):
        AgentRequest(
            session_id=session_id,
            payload={},
            parent_request_id=parent_id
            # Missing root_request_id
        )

def test_valid_trace_explicit_root() -> None:
    root_id = uuid4()
    parent_id = uuid4()
    session_id = uuid4()

    req = AgentRequest(
        session_id=session_id,
        payload={},
        root_request_id=root_id,
        parent_request_id=parent_id
    )

    assert req.root_request_id == root_id
    assert req.parent_request_id == parent_id

def test_immutability() -> None:
    req = AgentRequest(session_id=uuid4(), payload={"a": 1})

    # Pydantic v2 frozen model raises ValidationError on assignment
    with pytest.raises(ValidationError):
        req.payload = {"b": 2} # type: ignore

def test_serialization() -> None:
    session_id = uuid4()
    req = AgentRequest(session_id=session_id, payload={"key": "val"})

    json_str = req.model_dump_json()
    assert str(session_id) in json_str
    assert "key" in json_str
    assert "val" in json_str
    assert str(req.request_id) in json_str

# --- Edge Cases ---

def test_missing_session_id() -> None:
    """Edge Case: session_id is mandatory."""
    with pytest.raises(ValidationError) as excinfo:
        AgentRequest(payload={"foo": "bar"}) # type: ignore
    assert "session_id" in str(excinfo.value)

def test_invalid_uuid_strings() -> None:
    """Edge Case: Invalid UUID strings should fail validation."""
    with pytest.raises(ValidationError):
        AgentRequest(
            session_id="not-a-uuid", # type: ignore
            payload={}
        )

def test_root_provided_without_parent() -> None:
    """Edge Case: Explicit root provided, but no parent.
    This represents a valid state (e.g., a detached task linked to a root trace).
    """
    root_id = uuid4()
    session_id = uuid4()
    req = AgentRequest(
        session_id=session_id,
        payload={},
        root_request_id=root_id,
        parent_request_id=None
    )

    assert req.root_request_id == root_id
    assert req.parent_request_id is None
    # request_id should be auto-generated
    assert isinstance(req.request_id, UUID)
    assert req.request_id != root_id

def test_metadata_default() -> None:
    """Edge Case: Metadata defaults to empty dict."""
    req = AgentRequest(session_id=uuid4(), payload={})
    assert req.metadata == {}

# --- Complex Cases ---

def test_deep_lineage_chain() -> None:
    """Complex Case: verify lineage over 5 generations."""
    root = AgentRequest(session_id=uuid4(), payload={"gen": 0})

    current = root
    chain = [root]

    for i in range(1, 5):
        current = current.create_child({"gen": i})
        chain.append(current)

    assert len(chain) == 5

    # Verify strict lineage
    for i in range(1, 5):
        child = chain[i]
        parent = chain[i-1]

        assert child.root_request_id == root.request_id
        assert child.parent_request_id == parent.request_id
        assert child.session_id == root.session_id
        assert child.payload["gen"] == i

def test_round_trip_serialization() -> None:
    """Complex Case: Full serialization and deserialization."""
    original = AgentRequest(
        session_id=uuid4(),
        payload={"complex": {"nested": [1, 2, 3]}},
        metadata={"source": "test"}
    )

    # 1. Dump to JSON string
    json_str = original.model_dump_json()

    # 2. Parse back to dict
    data = json.loads(json_str)

    # 3. Reconstruct object
    reconstructed = AgentRequest(**data)

    assert reconstructed.request_id == original.request_id
    assert reconstructed.session_id == original.session_id
    assert reconstructed.root_request_id == original.root_request_id
    assert reconstructed.payload == original.payload
    assert reconstructed.metadata == original.metadata
    assert reconstructed.created_at == original.created_at

def test_child_creation_overrides() -> None:
    """Complex Case: create_child with metadata overrides."""
    root = AgentRequest(session_id=uuid4(), payload={}, metadata={"a": 1})
    child = root.create_child({"p": 2}, metadata={"b": 2})

    assert child.metadata == {"b": 2} # Completely replaces, does not merge
    assert child.session_id == root.session_id
