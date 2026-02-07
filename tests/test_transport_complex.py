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

from coreason_manifest.spec.cap import ServiceRequest, SessionContext
from coreason_manifest.spec.common.identity import Identity
from coreason_manifest.spec.common.request import AgentRequest


def test_long_request_chain() -> None:
    """Verify trace integrity over a long chain of requests (A -> B -> C -> D)."""
    # A
    root = AgentRequest(session_id=uuid4(), payload={"step": "A"})

    # B
    req_b = root.create_child(payload={"step": "B"})

    # C
    req_c = req_b.create_child(payload={"step": "C"})

    # D
    req_d = req_c.create_child(payload={"step": "D"})

    # All share same root
    assert root.root_request_id == req_b.root_request_id
    assert root.root_request_id == req_c.root_request_id
    assert root.root_request_id == req_d.root_request_id

    # Parents are correct
    assert req_d.parent_request_id == req_c.request_id
    assert req_c.parent_request_id == req_b.request_id
    assert req_b.parent_request_id == root.request_id
    assert root.parent_request_id is None


def test_forked_traces() -> None:
    """Verify multiple children from same parent (A -> B, A -> C)."""
    root = AgentRequest(session_id=uuid4(), payload={"step": "Root"})

    child1 = root.create_child(payload={"step": "Branch 1"})
    child2 = root.create_child(payload={"step": "Branch 2"})

    # Independent children
    assert child1.request_id != child2.request_id

    # Same parent
    assert child1.parent_request_id == root.request_id
    assert child2.parent_request_id == root.request_id

    # Same root
    assert child1.root_request_id == root.root_request_id
    assert child2.root_request_id == root.root_request_id


def test_nested_envelope_interop() -> None:
    """Verify ServiceRequest wrapping AgentRequest wrapping another AgentRequest (meta-programming)."""
    # This happens when an agent calls another agent via an API that accepts ServiceRequest,
    # and passes the original request as payload content.

    inner_req = AgentRequest(session_id=uuid4(), payload={"msg": "inner"})

    # Wrap in another request (as payload data)
    outer_req = AgentRequest(session_id=inner_req.session_id, payload={"wrapped_request": inner_req.model_dump()})

    # Wrap in ServiceRequest
    ctx = SessionContext(session_id="s1", user=Identity.anonymous())
    svc_req = ServiceRequest(request_id=uuid4(), context=ctx, payload=outer_req)

    # Verify nesting structure
    dump = svc_req.dump()
    assert dump["payload"]["payload"]["wrapped_request"]["payload"]["msg"] == "inner"

    # The inner request is just data at this point, but its lineage is preserved
    inner_data = dump["payload"]["payload"]["wrapped_request"]
    assert inner_data["root_request_id"] == str(inner_req.root_request_id)


def test_metadata_merge_conflict_resolution() -> None:
    """Verify metadata merging strategy (overwrite vs preserve)."""
    # Default behavior is usually shallow copy or overwrite.
    # create_child takes kwargs.

    root = AgentRequest(session_id=uuid4(), payload={}, metadata={"a": 1, "b": 2})

    # Override 'b', add 'c'
    child = root.create_child(
        payload={},
        metadata={"b": 99, "c": 3},  # This fully replaces metadata unless create_child merges
    )

    # Current implementation in create_child:
    # meta = kwargs.get("metadata", self.metadata.copy())
    # So if metadata IS provided, it replaces entirely.

    assert child.metadata == {"b": 99, "c": 3}
    assert "a" not in child.metadata

    # If we want to MERGE, user must do it manually before calling create_child
    merged_meta = root.metadata.copy()
    merged_meta.update({"b": 99, "c": 3})

    child_merged = root.create_child(payload={}, metadata=merged_meta)
    assert child_merged.metadata == {"a": 1, "b": 99, "c": 3}
