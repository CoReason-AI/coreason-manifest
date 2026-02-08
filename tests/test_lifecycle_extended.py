import pytest
from pydantic import ValidationError

from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    GraphEdge,
    GraphTopology,
    HumanNode,
    RecipeDefinition,
    RecipeInterface,
    RecipeStatus,
    SemanticRef,
)


def test_transition_draft_to_published_mixed_nodes() -> None:
    """
    Test transition from Draft to Published with a mix of valid (concrete)
    and invalid (semantic) nodes. Should fail.
    """
    concrete_node = AgentNode(id="step-1", agent_ref="concrete-agent")
    semantic_node = AgentNode(id="step-2", agent_ref=SemanticRef(intent="do something"))

    # 1. Start as Draft - Should be Valid
    topology_draft = GraphTopology(
        nodes=[concrete_node, semantic_node],
        edges=[GraphEdge(source="step-1", target="step-2")],
        entry_point="step-1",
        status="draft",  # In draft, we can have semantic refs
    )

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Hybrid Draft"),
        interface=RecipeInterface(),
        topology=topology_draft,
        status=RecipeStatus.DRAFT,
    )
    assert recipe.status == RecipeStatus.DRAFT

    # 2. Try to update to Published - Should Fail due to SemanticRef
    # We simulate this by creating a new RecipeDefinition with the same topology but status=PUBLISHED
    # (Pydantic models are immutable/frozen by default in this codebase, so we create new instances)

    # Note: Even if we set topology.status="valid", the SemanticRef should still block it.
    topology_valid_struct = GraphTopology(
        nodes=[concrete_node, semantic_node],
        edges=[GraphEdge(source="step-1", target="step-2")],
        entry_point="step-1",
        status="valid",
    )

    with pytest.raises(ValidationError) as exc:
        RecipeDefinition(
            metadata=ManifestMetadata(name="Hybrid Published"),
            interface=RecipeInterface(),
            topology=topology_valid_struct,
            status=RecipeStatus.PUBLISHED,
        )
    assert "Resolve all SemanticRefs" in str(exc.value)


def test_semantic_ref_serialization() -> None:
    """Test that SemanticRef serializes and deserializes correctly."""
    ref = SemanticRef(intent="analyze data")
    node = AgentNode(id="step-1", agent_ref=ref)

    # Dump to dict
    data = node.model_dump(mode="json")
    assert data["agent_ref"] == {
        "intent": "analyze data",
        "candidates": [],
        "constraints": [],
        "optimization": None,
    }

    # Load back
    loaded_node = AgentNode.model_validate(data)
    assert isinstance(loaded_node.agent_ref, SemanticRef)
    assert loaded_node.agent_ref.intent == "analyze data"


def test_archived_status_behavior() -> None:
    """Test that ARCHIVED status behaves permissively like DRAFT."""
    semantic_node = AgentNode(id="step-1", agent_ref=SemanticRef(intent="legacy intent"))

    # Even with a broken topology
    topology_broken = GraphTopology(
        nodes=[semantic_node],
        edges=[GraphEdge(source="step-1", target="missing")],
        entry_point="step-1",
        status="draft",
    )

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Archived Recipe"),
        interface=RecipeInterface(),
        topology=topology_broken,
        status=RecipeStatus.ARCHIVED,
    )

    assert recipe.status == RecipeStatus.ARCHIVED
    # Should not raise validation error


def test_large_graph_multiple_semantic_refs() -> None:
    """Test a larger graph with multiple semantic refs in Published mode."""
    nodes = []
    # Create 10 nodes, even ones are semantic
    for i in range(10):
        if i % 2 == 0:
            nodes.append(AgentNode(id=f"step-{i}", agent_ref=SemanticRef(intent=f"intent-{i}")))
        else:
            nodes.append(AgentNode(id=f"step-{i}", agent_ref=f"agent-{i}"))

    # Valid edges linearly
    edges = [GraphEdge(source=f"step-{i}", target=f"step-{i + 1}") for i in range(9)]

    topology = GraphTopology(nodes=nodes, edges=edges, entry_point="step-0", status="valid")

    with pytest.raises(ValidationError) as exc:
        RecipeDefinition(
            metadata=ManifestMetadata(name="Large Invalid"),
            interface=RecipeInterface(),
            topology=topology,
            status=RecipeStatus.PUBLISHED,
        )

    # Verify error message mentions semantic refs
    assert "Resolve all SemanticRefs" in str(exc.value)


def test_structurally_valid_but_semantic_fail() -> None:
    """
    Test a graph that has perfect topology (valid edges/entry) but uses SemanticRef.
    Must fail in PUBLISHED.
    """
    # A graph with 2 nodes, connected properly.
    # But node 2 is semantic.
    node1 = AgentNode(id="start", agent_ref="concrete-1")
    node2 = AgentNode(id="end", agent_ref=SemanticRef(intent="finish"))

    topology = GraphTopology(
        nodes=[node1, node2], edges=[GraphEdge(source="start", target="end")], entry_point="start", status="valid"
    )

    with pytest.raises(ValidationError) as exc:
        RecipeDefinition(
            metadata=ManifestMetadata(name="Structurally Valid Semantic"),
            interface=RecipeInterface(),
            topology=topology,
            status=RecipeStatus.PUBLISHED,
        )

    assert "Resolve all SemanticRefs" in str(exc.value)


def test_structurally_invalid_and_semantic_fail() -> None:
    """
    Test a graph that is BOTH structurally invalid AND has SemanticRef.
    Should fail (order of check determines which error, but must fail).
    """
    # Semantic node
    node1 = AgentNode(id="start", agent_ref=SemanticRef(intent="start"))

    # Invalid edge to nowhere
    topology = GraphTopology(
        nodes=[node1],
        edges=[GraphEdge(source="start", target="void")],
        entry_point="start",
        status="draft",  # Skip internal topology check to let Recipe catch it
    )

    with pytest.raises(ValidationError) as exc:
        RecipeDefinition(
            metadata=ManifestMetadata(name="Double Invalid"),
            interface=RecipeInterface(),
            topology=topology,
            status=RecipeStatus.PUBLISHED,
        )

    err_msg = str(exc.value)
    # Our implementation checks SemanticRefs first (step 1), then Topology (step 2).
    # So we expect the SemanticRef error.
    assert "Resolve all SemanticRefs" in err_msg


def test_mixed_node_types_with_semantic_ref() -> None:
    """
    Test mixed node types (Human, Agent) where Agent uses SemanticRef.
    """
    human_node = HumanNode(id="human-1", prompt="approve")
    agent_node = AgentNode(id="agent-1", agent_ref=SemanticRef(intent="execute"))

    topology = GraphTopology(
        nodes=[human_node, agent_node],
        edges=[GraphEdge(source="human-1", target="agent-1")],
        entry_point="human-1",
        status="valid",
    )

    # Should fail in PUBLISHED
    with pytest.raises(ValidationError) as exc:
        RecipeDefinition(
            metadata=ManifestMetadata(name="Mixed Nodes"),
            interface=RecipeInterface(),
            topology=topology,
            status=RecipeStatus.PUBLISHED,
        )
    assert "Resolve all SemanticRefs" in str(exc.value)
