from coreason_manifest.definitions.agent import VersionStr
from coreason_manifest.definitions.topology import AgentNode, GraphTopology, StateDefinition
from coreason_manifest.recipes import RecipeInterface, RecipeManifest


def test_agent_node_v0_10_0_features() -> None:
    """Test new optional fields in AgentNode."""
    # Test valid instantiation with new fields
    node = AgentNode(
        id="agent_1",
        agent_name="optimizer_agent",
        system_prompt="You are a helpful assistant.",
        config={"temperature": 0.7, "model": "gpt-4"},
    )
    assert node.system_prompt == "You are a helpful assistant."
    assert node.config == {"temperature": 0.7, "model": "gpt-4"}

    # Test valid instantiation without new fields (defaults)
    node_defaults = AgentNode(id="agent_2", agent_name="standard_agent")
    assert node_defaults.system_prompt is None
    assert node_defaults.config is None


def test_recipe_manifest_v0_10_0_features() -> None:
    """Test new optional fields in RecipeManifest."""
    interface = RecipeInterface(inputs={}, outputs={})
    state = StateDefinition(schema_={}, persistence="ephemeral")
    topology = GraphTopology(nodes=[], edges=[])

    # Test valid instantiation with new fields
    manifest = RecipeManifest(
        id="recipe_1",
        version=VersionStr("1.0.0"),
        name="Test Recipe",
        interface=interface,
        state=state,
        parameters={},
        topology=topology,
        integrity_hash="sha256:1234567890abcdef",
        metadata={"ui_layout": {"x": 100, "y": 200}, "draft": True},
    )
    assert manifest.integrity_hash == "sha256:1234567890abcdef"
    assert manifest.metadata == {"ui_layout": {"x": 100, "y": 200}, "draft": True}

    # Test valid instantiation without new fields (defaults)
    manifest_defaults = RecipeManifest(
        id="recipe_2",
        version=VersionStr("1.0.0"),
        name="Default Recipe",
        interface=interface,
        state=state,
        parameters={},
        topology=topology,
    )
    assert manifest_defaults.integrity_hash is None
    assert manifest_defaults.metadata == {}


def test_graph_topology_state_schema_optional() -> None:
    """Test that state_schema is optional in GraphTopology."""
    # This was already verified to be optional, but good to have a test for regression.
    topology = GraphTopology(nodes=[], edges=[])
    assert topology.state_schema is None

    # Also verify we can provide it
    from coreason_manifest.definitions.topology import StateDefinition

    schema = StateDefinition(schema_={}, persistence="ephemeral")
    topology_with_schema = GraphTopology(nodes=[], edges=[], state_schema=schema)
    assert topology_with_schema.state_schema == schema


def test_agent_node_serialization() -> None:
    """Test serialization of AgentNode with new fields."""
    node = AgentNode(id="agent_1", agent_name="optimizer_agent", system_prompt="Prompt", config={"key": "value"})
    data = node.model_dump()
    assert data["system_prompt"] == "Prompt"
    assert data["config"] == {"key": "value"}


def test_recipe_manifest_serialization() -> None:
    """Test serialization of RecipeManifest with new fields."""
    interface = RecipeInterface(inputs={}, outputs={})
    state = StateDefinition(schema_={}, persistence="ephemeral")
    topology = GraphTopology(nodes=[], edges=[])

    manifest = RecipeManifest(
        id="recipe_1",
        version=VersionStr("1.0.0"),
        name="Test Recipe",
        interface=interface,
        state=state,
        parameters={},
        topology=topology,
        integrity_hash="hash_123",
        metadata={"key": "value"},
    )

    # Use by_alias=True because StateDefinition has an alias
    data = manifest.model_dump(by_alias=True)
    assert data["integrity_hash"] == "hash_123"
    assert data["metadata"] == {"key": "value"}
