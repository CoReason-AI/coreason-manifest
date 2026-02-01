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
from datetime import datetime
from uuid import uuid4

import pytest
from coreason_manifest.definitions.events import (
    GraphEventNodeStart,
    GraphEventNodeStream,
    StandardizedNodeStarted,
    StandardizedNodeStream,
    migrate_graph_event_to_cloud_event,
)
from coreason_manifest.definitions.simulation import SimulationStep
from coreason_manifest.definitions.topology import (
    ConditionalEdge,
    RouterExpression,
)
from pydantic import ValidationError

# --- Topology Security Edge Cases ---


def test_router_ref_regex_boundaries() -> None:
    """Test boundary conditions for RouterRef regex."""
    valid_paths = ["router", "router.sub", "router.sub.leaf", "my_router", "Router_1", "_internal.logic"]
    for path in valid_paths:
        edge = ConditionalEdge(source_node_id="start", router_logic=path, mapping={"a": "b"})
        assert edge.router_logic == path

    invalid_paths = [
        "",  # Empty
        ".",  # Just dot
        "router.",  # Trailing dot
        ".router",  # Leading dot
        "router..sub",  # Double dot
        "router-sub",  # Hyphen (not allowed)
        "router/sub",  # Slash
        "router()",  # Parens
        "router+1",  # Operator
        "1router",  # Start with digit
    ]

    # Wait, let's verify the regex: ^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*$
    # 1router -> Starts with digit -> Should fail.

    for path in invalid_paths:
        with pytest.raises(ValidationError, match="String should match pattern"):
            ConditionalEdge(source_node_id="start", router_logic=path, mapping={"a": "b"})


def test_router_expression_complex_args() -> None:
    """Test RouterExpression with complex nested arguments."""
    complex_args = [{"nested": "dict", "val": 1}, [1, 2, 3], None, True]
    expr = RouterExpression(operator="custom_op", args=complex_args)
    edge = ConditionalEdge(source_node_id="start", router_logic=expr, mapping={"a": "b"})
    assert isinstance(edge.router_logic, RouterExpression)
    assert edge.router_logic.args == complex_args


# --- Simulation Edge Cases ---


def test_simulation_snapshot_serialization() -> None:
    """Test serialization of complex SimulationStep snapshots."""
    complex_snapshot = {"deep": {"nested": {"list": [1, 2, {"key": "value"}]}}, "none_val": None, "bool_val": True}

    step = SimulationStep(
        step_id=uuid4(),
        timestamp=datetime.now(),
        node_id="node1",
        inputs={},
        thought="",
        action={},
        observation={},
        snapshot=complex_snapshot,
    )

    # Should not raise
    json_str = step.model_dump_json()
    data = json.loads(json_str)
    assert data["snapshot"] == complex_snapshot


# --- Event Polymorphism Edge Cases ---


def test_migration_resilience_extra_fields() -> None:
    """Test that migration ignores massive amounts of extra fields (fuzzing-lite)."""
    payload = {"status": "RUNNING", "input_tokens": 100, "node_id": "node1", "timestamp": 1234567890.0}
    # Add 100 junk fields
    for i in range(100):
        payload[f"junk_{i}"] = f"value_{i}"

    event = GraphEventNodeStart(
        event_type="NODE_START",
        run_id="run1",
        node_id="node1",
        timestamp=1234567890.0,
        payload=payload,
        visual_metadata={},
    )

    ce = migrate_graph_event_to_cloud_event(event)
    assert isinstance(ce.data, StandardizedNodeStarted)
    assert ce.data.status == "RUNNING"
    # Extra fields should be stripped in the standardized model
    # StandardizedNodeStarted has `extra="ignore"` via BaseNodePayload
    dump = ce.data.model_dump()
    assert "junk_0" not in dump


def test_migration_resilience_type_mismatch() -> None:
    """Test fallback when types are fundamentally incompatible."""
    # input_tokens expects int. Providing a dict should fail instantiation.
    payload = {"status": "RUNNING", "input_tokens": {"not": "an int"}}

    # Now raises ValidationError because strict typing
    with pytest.raises(ValidationError):
        GraphEventNodeStart(
            event_type="NODE_START",
            run_id="run1",
            node_id="node1",
            timestamp=1234567890.0,
            payload=payload,
            visual_metadata={},
        )


def test_migration_minimal_node_stream() -> None:
    """Test NODE_STREAM with minimal fields."""
    # Chunk is required by NodeStream payload model
    payload = {"chunk": "foo", "node_id": "node1"}

    event = GraphEventNodeStream(
        event_type="NODE_STREAM",
        run_id="run1",
        node_id="node1",
        timestamp=1234567890.0,
        payload=payload,
        visual_metadata={},
    )

    ce = migrate_graph_event_to_cloud_event(event)
    assert isinstance(ce.data, StandardizedNodeStream)
    assert ce.data.gen_ai is not None
    assert ce.data.gen_ai.completion is not None
    assert ce.data.gen_ai.completion.chunk == "foo"
    # Optional fields should be None
    assert ce.data.gen_ai.request is None


def test_migration_node_stream_missing_chunk() -> None:
    """Test NODE_STREAM missing required chunk."""
    payload = {"model": "gpt-4"}  # Missing chunk

    # Now raises ValidationError
    with pytest.raises(ValidationError):
        GraphEventNodeStream(
            event_type="NODE_STREAM",
            run_id="run1",
            node_id="node1",
            timestamp=1234567890.0,
            payload=payload,
            visual_metadata={},
        )
