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
from pydantic import ValidationError

from coreason_manifest.definitions.topology import (
    ConditionalEdge,
    Edge,
    GraphTopology,
    LogicNode,
    MapNode,
    RecipeNode,
    StateDefinition,
)


def test_state_schema_creation() -> None:
    """Test creating a valid StateDefinition."""
    schema_def = {"type": "object", "properties": {"messages": {"type": "array"}}}
    state = StateDefinition(schema_=schema_def, persistence="ephemeral")
    assert state.schema_ == schema_def
    assert state.persistence == "ephemeral"


def test_state_schema_validation_types() -> None:
    """Test validation fails for invalid types."""
    with pytest.raises(ValidationError):
        StateDefinition(schema_="not-a-dict", persistence="ephemeral")


def test_state_schema_missing_fields() -> None:
    """Test validation fails for missing required fields."""
    with pytest.raises(ValidationError) as excinfo:
        StateDefinition(persistence="ephemeral")  # type: ignore[call-arg]
    assert "Field required" in str(excinfo.value)
    assert "schema" in str(excinfo.value)


def test_state_schema_extra_forbid() -> None:
    """Test that extra fields are forbidden."""
    schema_def = {"type": "object"}
    with pytest.raises(ValidationError) as excinfo:
        StateDefinition(schema_=schema_def, persistence="ephemeral", extra_field="fail")  # type: ignore[call-arg]
    assert "Extra inputs are not permitted" in str(excinfo.value)


def test_graph_topology_with_state_schema() -> None:
    """Test integrating StateDefinition into GraphTopology."""
    schema_def = {"type": "object", "properties": {"messages": {"type": "array"}}}
    state = StateDefinition(schema_=schema_def, persistence="ephemeral")
    topology = GraphTopology(nodes=[], edges=[], state_schema=state)
    assert topology.state_schema == state
    assert topology.state_schema.persistence == "ephemeral"


def test_conditional_edge_creation() -> None:
    """Test creating a valid ConditionalEdge."""
    edge = ConditionalEdge(source_node_id="start", router_logic="routers.logic", mapping={"a": "node_a", "b": "node_b"})
    assert edge.source_node_id == "start"
    assert edge.mapping["a"] == "node_a"


def test_conditional_edge_missing_fields() -> None:
    """Test validation fails for missing required fields in ConditionalEdge."""
    with pytest.raises(ValidationError) as excinfo:
        ConditionalEdge(source_node_id="start")  # type: ignore[call-arg]
    assert "Field required" in str(excinfo.value)
    assert "router_logic" in str(excinfo.value)


def test_topology_mixed_edges() -> None:
    """Test GraphTopology accepts both Edge and ConditionalEdge."""
    # Create dummy nodes to satisfy validation
    nodes = [
        LogicNode(id="a", code="pass"),
        LogicNode(id="b", code="pass"),
        LogicNode(id="c", code="pass"),
    ]
    edge1 = Edge(source_node_id="a", target_node_id="b")
    edge2 = ConditionalEdge(source_node_id="b", router_logic="routers.logic", mapping={"res": "c"})
    topology = GraphTopology(nodes=nodes, edges=[edge1, edge2])
    assert len(topology.edges) == 2
    assert isinstance(topology.edges[0], Edge)
    assert isinstance(topology.edges[1], ConditionalEdge)


def test_conditional_edge_extra_forbid() -> None:
    """Test that extra fields are forbidden in ConditionalEdge."""
    with pytest.raises(ValidationError):
        ConditionalEdge(source_node_id="a", router_logic="l", mapping={"x": "y"}, extra="fail")  # type: ignore[call-arg]


def test_recipe_node_creation() -> None:
    """Test creating a valid RecipeNode."""
    node = RecipeNode(
        id="sub_recipe",
        type="recipe",
        recipe_id="another_recipe_v1",
        input_mapping={"parent_var": "child_input"},
        output_mapping={"child_output": "parent_var"},
    )
    assert node.recipe_id == "another_recipe_v1"
    assert node.input_mapping["parent_var"] == "child_input"


def test_recipe_node_missing_fields() -> None:
    """Test validation fails for missing required fields in RecipeNode."""
    with pytest.raises(ValidationError) as excinfo:
        RecipeNode(id="r1", type="recipe", recipe_id="r")  # type: ignore[call-arg]
    assert "Field required" in str(excinfo.value)
    assert "input_mapping" in str(excinfo.value)


def test_graph_topology_with_recipe_node() -> None:
    """Test GraphTopology includes RecipeNode in polymorphism."""
    node = RecipeNode(id="sub", type="recipe", recipe_id="r", input_mapping={}, output_mapping={})
    topology = GraphTopology(nodes=[node], edges=[])
    assert isinstance(topology.nodes[0], RecipeNode)


def test_recipe_node_extra_forbid() -> None:
    """Test extra fields forbidden in RecipeNode."""
    with pytest.raises(ValidationError):
        RecipeNode(id="r", type="recipe", recipe_id="r", input_mapping={}, output_mapping={}, extra="fail")  # type: ignore[call-arg]


def test_map_node_creation() -> None:
    """Test creating a valid MapNode."""
    node = MapNode(
        id="map1", type="map", items_path="state.items", processor_node_id="process_item_node", concurrency_limit=5
    )
    assert node.items_path == "state.items"
    assert node.concurrency_limit == 5


def test_map_node_missing_fields() -> None:
    """Test validation fails for missing required fields in MapNode."""
    with pytest.raises(ValidationError) as excinfo:
        MapNode(id="map1", type="map", items_path="p")  # type: ignore[call-arg]
    assert "Field required" in str(excinfo.value)
    assert "processor_node_id" in str(excinfo.value)


def test_graph_topology_with_map_node() -> None:
    """Test GraphTopology includes MapNode in polymorphism."""
    node = MapNode(id="map1", type="map", items_path="p", processor_node_id="proc", concurrency_limit=1)
    topology = GraphTopology(nodes=[node], edges=[])
    assert isinstance(topology.nodes[0], MapNode)


def test_map_node_extra_forbid() -> None:
    """Test extra fields forbidden in MapNode."""
    with pytest.raises(ValidationError):
        MapNode(id="m", type="map", items_path="p", processor_node_id="n", concurrency_limit=1, extra="fail")  # type: ignore[call-arg]
