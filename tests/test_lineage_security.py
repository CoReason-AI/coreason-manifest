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

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.cap import AgentRequest
from coreason_manifest.spec.common.observability import ReasoningTrace
from coreason_manifest.spec.common.session import Interaction, LineageMetadata


def test_uuid_field_dos_protection() -> None:
    """Verify that passing massive strings to UUID fields is rejected efficiently."""
    massive_string = "a" * 10_000_000  # 10MB string

    with pytest.raises(ValidationError) as excinfo:
        # Pydantic should fail fast on length or format for UUID coercion
        AgentRequest(session_id=uuid4(), payload={"query": "test"}, request_id=massive_string)

    # Ensure it's a value error related to UUID parsing
    assert "uuid" in str(excinfo.value).lower() or "input" in str(excinfo.value).lower()


def test_interaction_id_security() -> None:
    """Verify Interaction ID accepts strings but we monitor for potential injection vectors."""
    # The current model uses 'str' which is permissive.
    # This test documents that it accepts arbitrary strings, implying downstream must sanitize.

    malicious_id = "../../../etc/passwd"

    interaction = Interaction(id=malicious_id)
    assert interaction.id == malicious_id

    # Check for XSS payload
    xss_id = "<script>alert(1)</script>"
    interaction_xss = Interaction(id=xss_id)
    assert interaction_xss.id == xss_id


def test_lineage_metadata_type_coercion_attack() -> None:
    """Verify that LineageMetadata strictly enforces string types for IDs (no unexpected casting)."""
    # Passing an integer should fail because Pydantic V2 is strict on types by default in some configs,
    # or CoReasonBaseModel settings might enforce it.

    with pytest.raises(ValidationError):
        LineageMetadata(root_request_id=12345)


def test_reasoning_trace_auto_root_spoofing() -> None:
    """Verify that we cannot spoof a None root to bypass assignment."""
    # If we pass explicit None, the validator should catch it and assign request_id.

    uid = "123e4567-e89b-12d3-a456-426614174000"

    # Case 1: root_request_id is missing -> auto-root
    trace = ReasoningTrace(request_id=uid, node_id="test", status="ok", latency_ms=1, timestamp="2024-01-01T00:00:00Z")
    assert str(trace.root_request_id) == uid

    # Case 2: root_request_id is explicitly None -> auto-root
    trace_none = ReasoningTrace(
        request_id=uid,
        root_request_id=None,
        node_id="test",
        status="ok",
        latency_ms=1,
        timestamp="2024-01-01T00:00:00Z",
    )
    assert str(trace_none.root_request_id) == uid
