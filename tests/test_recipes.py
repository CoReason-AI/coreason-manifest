import pytest
from pydantic import ValidationError

from coreason_manifest import Edge, RecipeManifest
from coreason_manifest import Topology as GraphTopology
from coreason_manifest.definitions.topology import AgentNode, HumanNode, LogicNode
from coreason_manifest.recipes import RecipeInterface, StateDefinition


def test_recipe_manifest_creation() -> None:
    """Test creating a valid RecipeManifest."""
    node1 = AgentNode(id="node1", type="agent", agent_name="TestAgent")
    node2 = HumanNode(id="node2", type="human", timeout_seconds=60)
    edge = Edge(source_node_id="node1", target_node_id="node2")

    topology = GraphTopology(nodes=[node1, node2], edges=[edge])

    manifest = RecipeManifest(
        id="recipe1",
        version="1.0.0",
        name="Test Recipe",
        description="A test recipe",
        interface=RecipeInterface(inputs={"param1": "value1"}, outputs={}),
        state=StateDefinition(schema={}, persistence="ephemeral"),
        parameters={},
        graph=topology,
    )

    assert manifest.id == "recipe1"
    assert manifest.version == "1.0.0"
    assert len(manifest.graph.nodes) == 2
    assert isinstance(manifest.graph.nodes[0], AgentNode)
    assert isinstance(manifest.graph.nodes[1], HumanNode)


def test_version_validation() -> None:
    """Test strict version validation."""
    interface = RecipeInterface(inputs={}, outputs={})
    state = StateDefinition(schema={}, persistence="ephemeral")
    params = {}

    # Valid versions (normalized)
    m = RecipeManifest(
        id="r1",
        version="v1.0.0",
        name="n",
        interface=interface,
        state=state,
        parameters=params,
        graph=GraphTopology(nodes=[], edges=[]),
    )
    assert m.version == "1.0.0"

    m = RecipeManifest(
        id="r1",
        version="V2.0.0",
        name="n",
        interface=interface,
        state=state,
        parameters=params,
        graph=GraphTopology(nodes=[], edges=[]),
    )
    assert m.version == "2.0.0"

    # Invalid version
    with pytest.raises(ValidationError):
        RecipeManifest(
            id="r1",
            version="invalid",
            name="n",
            interface=interface,
            state=state,
            parameters=params,
            graph=GraphTopology(nodes=[], edges=[]),
        )


def test_node_polymorphism() -> None:
    """Test that nodes are correctly deserialized into their specific types."""
    data = {
        "nodes": [
            {"id": "n1", "type": "agent", "agent_name": "A1"},
            {"id": "n2", "type": "human", "timeout_seconds": 30},
            {"id": "n3", "type": "logic", "code": "print('hello')"},
        ],
        "edges": [],
    }

    topology = GraphTopology(**data)

    assert isinstance(topology.nodes[0], AgentNode)
    assert topology.nodes[0].agent_name == "A1"

    assert isinstance(topology.nodes[1], HumanNode)
    assert topology.nodes[1].timeout_seconds == 30

    assert isinstance(topology.nodes[2], LogicNode)
    assert topology.nodes[2].code == "print('hello')"


def test_serialization() -> None:
    """Test JSON serialization."""
    node = LogicNode(id="n1", type="logic", code="x=1")
    manifest = RecipeManifest(
        id="r1",
        version="1.0.0",
        name="n",
        interface=RecipeInterface(inputs={}, outputs={}),
        state=StateDefinition(schema={}, persistence="ephemeral"),
        parameters={},
        graph=GraphTopology(nodes=[node], edges=[]),
    )

    json_output = manifest.model_dump_json()
    assert '"type":"logic"' in json_output
    assert '"code":"x=1"' in json_output
