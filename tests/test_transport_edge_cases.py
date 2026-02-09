# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import contextlib
from typing import Any
from uuid import uuid4

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.common.request import AgentRequest


def test_circular_lineage() -> None:
    """Verify behavior when a request is its own parent (pathological case)."""
    # The validator doesn't explicitly forbid this (as it's just UUID checks),
    # but it shouldn't crash.
    req_id = uuid4()

    # Self-parenting
    req = AgentRequest(
        request_id=req_id,
        session_id=uuid4(),
        root_request_id=req_id,  # Valid: root can be self
        parent_request_id=req_id,  # Valid: parent can technically be self in a graph cycle
        payload={},
    )

    assert req.request_id == req.parent_request_id
    assert req.request_id == req.root_request_id


def test_uuid_collision_simulation() -> None:
    """Simulate a UUID collision (extremely unlikely but good to check equality logic)."""
    uid = uuid4()

    req1 = AgentRequest(request_id=uid, session_id=uuid4(), payload={"q": 1})
    req2 = AgentRequest(request_id=uid, session_id=uuid4(), payload={"q": 2})

    # They have same ID but different content.
    # Equality depends on ManifestBaseModel/Pydantic implementation.
    # Usually pydantic models are equal if all fields are equal.
    assert req1 != req2
    assert req1.request_id == req2.request_id


def test_payload_complex_types() -> None:
    """Verify payload handles complex python types that might fail JSON serialization."""
    # Sets are not standard JSON. Pydantic's model_dump(mode='json') handles them by converting to list.
    payload = {
        "tags": {"a", "b", "c"},
        "tuple": (1, 2),
    }

    req = AgentRequest(session_id=uuid4(), payload=payload)

    # Dump should handle sets/tuples (convert to list)
    dump = req.model_dump(mode="json", by_alias=True, exclude_none=True)
    assert set(dump["payload"]["tags"]) == {"a", "b", "c"}  # serialized as list
    assert dump["payload"]["tuple"] == [1, 2]  # serialized as list


def test_deep_recursion_payload() -> None:
    """Verify deep recursion in payload doesn't crash validation, though serialization might fail."""
    deep_dict: dict[str, Any] = {}
    curr = deep_dict
    for _ in range(2000):  # Exceeds default recursion limit usually
        curr["n"] = {}
        curr = curr["n"]

    req = AgentRequest(session_id=uuid4(), payload=deep_dict)

    # Validation passes because dict is just a reference
    assert isinstance(req, AgentRequest)

    # Serialization might fail
    with contextlib.suppress(RecursionError, ValueError):
        req.model_dump(mode="json", by_alias=True, exclude_none=True)


def test_concurrent_modification_attempt() -> None:
    """Verify that despite payload being a mutable dict reference, the model instance is frozen."""
    payload = {"count": 0}
    req = AgentRequest(session_id=uuid4(), payload=payload)

    # Modifying the external dict reference effects the model's view of data
    # (since Pydantic shallow copies or keeps reference depending on config).
    # By default, it might keep reference.
    payload["count"] = 1

    # This is an important behavior to document/test: The envelope is frozen, but the payload content
    # (if strictly a reference) is mutable via the original reference.
    # Ideally, we'd want deep copy, but performance usually dictates reference.
    # UPDATE: Pydantic V2/ManifestBaseModel seemingly makes a copy during validation, isolating the model.
    # This is safer behavior.
    assert req.payload["count"] == 0


def test_invalid_payload_keys() -> None:
    """Test payload with non-string keys (JSON requirements)."""
    # Pydantic Dict[str, Any] expects string keys.
    # If we pass int keys, Pydantic coercion might convert them to strings or fail.

    payload = {123: "value"}

    # ManifestBaseModel / Pydantic V2 often coerces keys to strings for Dict[str, Any]
    # But it seems strict validation rejects int keys here.
    with pytest.raises(ValidationError):
        AgentRequest(session_id=uuid4(), payload=payload)
