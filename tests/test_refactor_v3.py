# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import TypeAdapter, ValidationError

from coreason_manifest.definitions.events import (
    EdgeTraversed,
    GraphEvent,
    GraphEventEdgeActive,
    GraphEventNodeDone,
    GraphEventNodeInit,
    GraphEventNodeStart,
    GraphEventNodeStream,
    NodeInit,
    StandardizedNodeCompleted,
    StandardizedNodeStarted,
    StandardizedNodeStream,
    migrate_graph_event_to_cloud_event,
)
from coreason_manifest.definitions.simulation import SimulationStep
from coreason_manifest.definitions.topology import (
    ConditionalEdge,
    DataMapping,
    DataMappingStrategy,
    RecipeNode,
    RouterExpression,
)


def test_topology_security_router_ref_valid() -> None:
    """Test valid router references."""
    edge = ConditionalEdge(
        source_node_id="start", router_logic="routers.approval.check_score", mapping={"approve": "end"}
    )
    assert edge.router_logic == "routers.approval.check_score"


def test_topology_security_router_ref_invalid() -> None:
    """Test invalid router references (RCE attempt)."""
    invalid_paths = [
        "os.system('rm -rf')",
        "__import__('os')",
        "foo()",
        "foo+bar",
    ]
    for path in invalid_paths:
        with pytest.raises(ValidationError):
            ConditionalEdge(source_node_id="start", router_logic=path, mapping={"approve": "end"})


def test_topology_security_router_expression() -> None:
    """Test router expression (structured)."""
    expr = RouterExpression(operator="eq", args=["$input.score", 100])
    edge = ConditionalEdge(source_node_id="start", router_logic=expr, mapping={"approve": "end"})
    assert isinstance(edge.router_logic, RouterExpression)
    assert edge.router_logic.operator == "eq"


def test_recipe_mapping_mixed() -> None:
    """Test mixing strings and DataMapping in RecipeNode."""
    node = RecipeNode(
        id="recipe1",
        recipe_id="sub_recipe",
        input_mapping={
            "direct_key": "parent_key",
            "complex_key": DataMapping(source="$.foo.bar", strategy=DataMappingStrategy.JSONPATH),
        },
        output_mapping={"out_key": DataMapping(source="result", strategy="direct")},
    )
    assert node.input_mapping["direct_key"] == "parent_key"
    assert isinstance(node.input_mapping["complex_key"], DataMapping)
    assert node.input_mapping["complex_key"].strategy == DataMappingStrategy.JSONPATH


def test_simulation_snapshot() -> None:
    """Test SimulationStep has snapshot field."""
    step = SimulationStep(
        step_id=uuid4(),
        timestamp=datetime.now(),
        node_id="node1",
        inputs={"a": 1},
        thought="thinking",
        action={},
        observation={},
        snapshot={"full_state": "here"},
    )
    assert step.snapshot == {"full_state": "here"}

    # Test default
    step_default = SimulationStep(
        step_id=uuid4(), timestamp=datetime.now(), node_id="node1", inputs={}, thought="", action={}, observation={}
    )
    assert step_default.snapshot == {}


def test_event_polymorphism_node_start() -> None:
    """Test migration of NODE_START event."""
    event = GraphEventNodeStart(
        event_type="NODE_START",
        run_id="run1",
        node_id="node1",
        timestamp=1234567890.0,
        payload={
            "timestamp": 1234567890.0,
            "status": "RUNNING",
            "input_tokens": 100,
            "model": "gpt-4",
            "system": "you are a bot",
            "node_id": "node1",
        },
        visual_metadata={},
    )

    ce = migrate_graph_event_to_cloud_event(event)
    assert ce.type == "ai.coreason.node.started"
    assert isinstance(ce.data, StandardizedNodeStarted)
    assert ce.data.gen_ai is not None
    assert ce.data.gen_ai.usage is not None
    assert ce.data.gen_ai.usage.input_tokens == 100
    assert ce.data.gen_ai.request is not None
    assert ce.data.gen_ai.request.model == "gpt-4"
    assert ce.data.gen_ai.system == "you are a bot"


def test_event_polymorphism_node_stream() -> None:
    """Test migration of NODE_STREAM event."""
    event = GraphEventNodeStream(
        event_type="NODE_STREAM",
        run_id="run1",
        node_id="node1",
        timestamp=1234567890.0,
        payload={"chunk": "hello", "model": "gpt-4", "node_id": "node1"},
        visual_metadata={},
    )

    ce = migrate_graph_event_to_cloud_event(event)
    assert ce.type == "ai.coreason.node.stream"
    assert isinstance(ce.data, StandardizedNodeStream)
    assert ce.data.gen_ai is not None
    assert ce.data.gen_ai.completion is not None
    assert ce.data.gen_ai.completion.chunk == "hello"
    assert ce.data.gen_ai.request is not None
    assert ce.data.gen_ai.request.model == "gpt-4"


def test_event_polymorphism_fallback() -> None:
    """Test fallback for edge events."""
    event = GraphEventEdgeActive(
        event_type="EDGE_ACTIVE",
        run_id="run1",
        node_id="node1",
        timestamp=1234567890.0,
        payload={"source": "start", "target": "end"},
        visual_metadata={},
    )

    ce = migrate_graph_event_to_cloud_event(event)
    assert isinstance(ce.data, EdgeTraversed)
    assert ce.data.source == "start"


def test_unknown_event_type() -> None:
    """Test unknown event type validation error."""
    # Strict validation prevents unknown event types via Union
    data = {
        "event_type": "UNKNOWN_TYPE",
        "run_id": "run1",
        "node_id": "node1",
        "timestamp": 1234567890.0,
        "payload": {"foo": "bar"},
        "visual_metadata": {},
    }
    with pytest.raises(ValidationError):
        TypeAdapter(GraphEvent).validate_python(data)


def test_instantiation_failure() -> None:
    """Test validation error when payload instantiation fails."""
    # NODE_START requires status="RUNNING".
    with pytest.raises(ValidationError):
        GraphEventNodeStart(
            event_type="NODE_START",
            run_id="run1",
            node_id="node1",
            timestamp=1234567890.0,
            payload={"status": "FAILED", "node_id": "node1", "timestamp": 1234567890.0},  # Invalid status
            visual_metadata={},
        )


def test_empty_cue_filtering() -> None:
    """Test filtering of empty string extensions."""
    event = GraphEventNodeInit(
        event_type="NODE_INIT",
        run_id="run1",
        node_id="node1",
        timestamp=1234567890.0,
        payload={"visual_cue": "", "node_id": "node1"},  # Empty cue
        visual_metadata={"animation": ""},  # Empty animation
    )
    ce = migrate_graph_event_to_cloud_event(event)
    dump = ce.model_dump()
    assert "com_coreason_ui_cue" not in dump


def test_event_polymorphism_node_completed() -> None:
    """Test migration of NODE_DONE event."""
    event = GraphEventNodeDone(
        event_type="NODE_DONE",
        run_id="run1",
        node_id="node1",
        timestamp=1234567890.0,
        payload={"output_summary": "done", "model": "gpt-4", "node_id": "node1"},
        visual_metadata={},
    )
    ce = migrate_graph_event_to_cloud_event(event)
    assert isinstance(ce.data, StandardizedNodeCompleted)
    assert ce.data.output_summary == "done"
    assert ce.data.gen_ai is not None
    assert ce.data.gen_ai.request is not None
    assert ce.data.gen_ai.request.model == "gpt-4"


def test_event_polymorphism_base_implementation() -> None:
    """Test migration using base implementation (e.g. NodeInit)."""
    event = GraphEventNodeInit(
        event_type="NODE_INIT",
        run_id="run1",
        node_id="node1",
        timestamp=1234567890.0,
        payload={"type": "start", "node_id": "node1"},
        visual_metadata={},
    )
    ce = migrate_graph_event_to_cloud_event(event)
    # Should return NodeInit object
    assert isinstance(ce.data, NodeInit)


def test_extension_filtering() -> None:
    """Test UI metadata filtering."""
    # Case 1: All empty values -> Extension dropped
    event_empty = GraphEventNodeInit(
        event_type="NODE_INIT",
        run_id="run1",
        node_id="node1",
        timestamp=1234567890.0,
        payload={"type": "start", "node_id": "node1"},
        visual_metadata={
            "empty": "",
        },
    )
    ce = migrate_graph_event_to_cloud_event(event_empty)
    assert "com_coreason_ui_metadata" not in ce.model_dump()

    # Case 2: Mixed -> Extension kept (as is)
    event_mixed = GraphEventNodeInit(
        event_type="NODE_INIT",
        run_id="run1",
        node_id="node1",
        timestamp=1234567890.0,
        payload={"type": "start", "node_id": "node1"},
        visual_metadata={"valid": "value", "empty": ""},
    )
    ce_mixed = migrate_graph_event_to_cloud_event(event_mixed)
    dump = ce_mixed.model_dump()
    assert "com_coreason_ui_metadata" in dump
    assert dump["com_coreason_ui_metadata"] == {"valid": "value", "empty": ""}
