import pytest
from pydantic import ValidationError

from coreason_manifest import (
    AgentNode,
    Edge,
    GraphTopology,
    HumanNode,
    LogicNode,
    RecipeManifest,
)


def test_invalid_node_discriminator() -> None:
    """Test that an invalid discriminator value raises a ValidationError."""
    raw_data = {
        "nodes": [
            {"id": "n1", "type": "alien", "agent_name": "A1"}
        ],
        "edges": []
    }
    with pytest.raises(ValidationError) as excinfo:
        GraphTopology(**raw_data)

    # Error should mention the discriminator 'type' or input value
    assert "type" in str(excinfo.value) or "alien" in str(excinfo.value)


def test_strict_schema_extra_fields() -> None:
    """Test that extra fields are forbidden."""
    # Test on Node
    with pytest.raises(ValidationError) as excinfo:
        AgentNode(
            id="n1",
            type="agent",
            agent_name="A1",
            extra_field="should_fail"
        )
    assert "Extra inputs are not permitted" in str(excinfo.value)

    # Test on Manifest
    with pytest.raises(ValidationError) as excinfo:
        RecipeManifest(
            id="r1", version="1.0.0", name="N",
            inputs={},
            graph=GraphTopology(nodes=[], edges=[]),
            extra_thing="bad"
        )
    assert "Extra inputs are not permitted" in str(excinfo.value)


def test_missing_required_fields() -> None:
    """Test that missing required fields raises ValidationError."""
    # AgentNode requires 'agent_name'
    with pytest.raises(ValidationError) as excinfo:
        AgentNode(id="n1", type="agent")
    assert "Field required" in str(excinfo.value)
    assert "agent_name" in str(excinfo.value)


def test_recursive_version_normalization() -> None:
    """Test recursive stripping of 'v' prefixes."""
    manifest = RecipeManifest(
        id="r1",
        version="vVv1.5.0",
        name="Test",
        inputs={},
        graph=GraphTopology(nodes=[], edges=[])
    )
    assert manifest.version == "1.5.0"


def test_complex_inputs_structure() -> None:
    """Test that 'inputs' can handle arbitrary complex nested structures."""
    complex_inputs = {
        "user": {
            "name": "Alice",
            "roles": ["admin", "editor"],
            "meta": {"login_count": 42}
        },
        "config": [
            {"key": "k1", "value": 1.5},
            {"key": "k2", "value": None}
        ]
    }

    manifest = RecipeManifest(
        id="r1",
        version="1.0.0",
        name="Test",
        inputs=complex_inputs,
        graph=GraphTopology(nodes=[], edges=[])
    )

    assert manifest.inputs["user"]["name"] == "Alice"
    assert manifest.inputs["config"][0]["value"] == 1.5


def test_large_topology_serialization() -> None:
    """Test serialization/deserialization of a larger graph."""
    nodes = []
    edges = []
    count = 100

    for i in range(count):
        nodes.append(LogicNode(
            id=f"node_{i}",
            type="logic",
            code=f"x = {i}"
        ))
        if i > 0:
            edges.append(Edge(
                source_node_id=f"node_{i-1}",
                target_node_id=f"node_{i}"
            ))

    topology = GraphTopology(nodes=nodes, edges=edges)

    manifest = RecipeManifest(
        id="large_recipe",
        version="1.0.0",
        name="Large Recipe",
        inputs={},
        graph=topology
    )

    # Dump
    json_str = manifest.model_dump_json()

    # Load back
    loaded = RecipeManifest.model_validate_json(json_str)

    assert len(loaded.graph.nodes) == count
    assert len(loaded.graph.edges) == count - 1
    assert loaded.graph.nodes[99].id == "node_99"
    assert isinstance(loaded.graph.nodes[0], LogicNode)


def test_polymorphic_list_parsing() -> None:
    """Test parsing a mixed list of node types from raw dictionaries."""
    raw_nodes = [
        {"id": "a1", "type": "agent", "agent_name": "A"},
        {"id": "h1", "type": "human", "timeout_seconds": 10},
        {"id": "l1", "type": "logic", "code": "pass"},
    ]

    topo = GraphTopology(nodes=raw_nodes, edges=[])

    assert isinstance(topo.nodes[0], AgentNode)
    assert isinstance(topo.nodes[1], HumanNode)
    assert isinstance(topo.nodes[2], LogicNode)
