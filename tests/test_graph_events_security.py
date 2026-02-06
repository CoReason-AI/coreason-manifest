# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any

import pytest
from pydantic import ValidationError

from coreason_manifest import (
    EventContentType,
    GraphEventError,
    GraphEventNodeStart,
    GraphEventNodeStream,
)
from coreason_manifest.utils.migration import migrate_graph_event_to_cloud_event


def test_red_team_large_payload_dos() -> None:
    """DoS Attempt: Massive string payload."""
    massive_string = "A" * 1_000_000  # 1MB
    payload: dict[str, Any] = {"data": massive_string}

    event = GraphEventNodeStart(run_id="r1", trace_id="t1", node_id="n1", timestamp=100.0, payload=payload)

    # Should handle without crashing
    ce = migrate_graph_event_to_cloud_event(event)
    assert ce.data is not None
    assert ce.data["data"] == massive_string

    # Serialization check
    dumped = ce.dump()
    assert len(dumped["data"]["data"]) == 1_000_000


def test_red_team_malformed_unicode() -> None:
    """Fuzzing: Control characters and null bytes."""
    bad_chunk = "Control chars: \x00 \x1f \u2028 \u2029"

    event = GraphEventNodeStream(run_id="r1", trace_id="t1", node_id="n1", timestamp=100.0, chunk=bad_chunk)

    ce = migrate_graph_event_to_cloud_event(event)
    assert ce.data is not None
    assert ce.data["chunk"] == bad_chunk

    # Python strings handle null bytes fine, JSON serialization might escape them
    dumped = ce.to_json()
    assert "\\u0000" in dumped or "\u0000" in dumped


def test_red_team_field_injection_via_payload() -> None:
    """Injection: Attempt to overwrite CloudEvent fields via payload."""
    # CloudEvent has fields like 'source', 'type', 'id'
    malicious_payload = {"source": "spoofed-source", "type": "spoofed.type", "id": "spoofed-id", "specversion": "0.9"}

    event = GraphEventNodeStart(run_id="r1", trace_id="t1", node_id="n1", timestamp=100.0, payload=malicious_payload)

    ce = migrate_graph_event_to_cloud_event(event)

    # The migration utility puts payload into 'data', so top-level fields must remain safe
    assert ce.source == "urn:node:n1"
    assert ce.type == "ai.coreason.node.start"
    assert ce.specversion == "1.0"

    # The injected fields should end up safely inside 'data'
    assert ce.data is not None
    assert ce.data["source"] == "spoofed-source"


def test_red_team_extension_spoofing() -> None:
    """Spoofing: Attempt to inject UI extensions via payload."""
    payload = {"com_coreason_ui_cue": "spoofed-cue"}

    event = GraphEventNodeStart(
        run_id="r1", trace_id="t1", node_id="n1", timestamp=100.0, payload=payload, visual_cue="legit-cue"
    )

    ce = migrate_graph_event_to_cloud_event(event)

    dumped = ce.dump()

    # The top-level extension should be the legitimate one
    assert dumped["com_coreason_ui_cue"] == "legit-cue"

    # The spoofed one should be inside data
    assert dumped["data"]["com_coreason_ui_cue"] == "spoofed-cue"


def test_red_team_type_confusion() -> None:
    """Type Confusion: Pass list instead of dict for payload."""
    with pytest.raises(ValidationError):
        GraphEventNodeStart(
            run_id="r1",
            trace_id="t1",
            node_id="n1",
            timestamp=100.0,
            payload=["not", "a", "dict"],
        )


def test_red_team_error_stack_trace_info_disclosure() -> None:
    """Info Disclosure: Ensure stack trace is preserved but contained."""
    sensitive_trace = "File '/etc/passwd', line 1, in <module>\nroot:x:0:0:root:/root:/bin/bash"

    event = GraphEventError(
        run_id="r1", trace_id="t1", node_id="n1", timestamp=100.0, error_message="Error", stack_trace=sensitive_trace
    )

    ce = migrate_graph_event_to_cloud_event(event)
    assert ce.data is not None
    assert ce.data["stack_trace"] == sensitive_trace
    assert ce.datacontenttype == EventContentType.ERROR
