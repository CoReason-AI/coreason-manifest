import pytest
from coreason_manifest.spec.v2.recipe import (
    RecipeDefinition,
    AgentNode,
    GraphTopology,
    GraphEdge,
    RecipeInterface,
    RecipeStatus,
    RecoveryConfig,
    FailureBehavior,
)
from coreason_manifest.spec.v2.definitions import ManifestMetadata

def test_valid_topology():
    """Test a valid topology with correct fallback reference."""
    node_a = AgentNode(
        id="Agent_A",
        agent_ref="agent-1",
        recovery=RecoveryConfig(
            behavior=FailureBehavior.ROUTE_TO_FALLBACK,
            fallback_node_id="Agent_B"
        )
    )
    node_b = AgentNode(id="Agent_B", agent_ref="agent-2")

    topology = GraphTopology(
        nodes=[node_a, node_b],
        edges=[GraphEdge(source="Agent_A", target="Agent_B")],
        entry_point="Agent_A",
        status="valid"
    )

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Valid Topology"),
        interface=RecipeInterface(),
        topology=topology,
        status=RecipeStatus.DRAFT
    )

    assert recipe.topology.nodes[0].recovery.fallback_node_id == "Agent_B"

def test_broken_link_fallback():
    """Test a broken link where fallback node does not exist."""
    node_a = AgentNode(
        id="Agent_A",
        agent_ref="agent-1",
        recovery=RecoveryConfig(
            behavior=FailureBehavior.ROUTE_TO_FALLBACK,
            fallback_node_id="Ghost_Node"
        )
    )

    # Even if GraphTopology is draft, RecipeDefinition should catch this if we add the validator.
    # Note: GraphTopology skips validation if status='draft', so we rely on RecipeDefinition validator.
    topology = GraphTopology(
        nodes=[node_a],
        edges=[],
        entry_point="Agent_A",
        status="draft"
    )

    with pytest.raises(ValueError) as excinfo:
        RecipeDefinition(
            metadata=ManifestMetadata(name="Broken Link"),
            interface=RecipeInterface(),
            topology=topology,
            status=RecipeStatus.DRAFT
        )

    assert "Ghost_Node" in str(excinfo.value)
    assert "fallback_node_id" in str(excinfo.value)

def test_self_reference_fallback():
    """Test a node referencing itself as fallback."""
    node_a = AgentNode(
        id="Agent_A",
        agent_ref="agent-1",
        recovery=RecoveryConfig(
            behavior=FailureBehavior.ROUTE_TO_FALLBACK,
            fallback_node_id="Agent_A"
        )
    )

    topology = GraphTopology(
        nodes=[node_a],
        edges=[],
        entry_point="Agent_A",
        status="valid"
    )

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Self Reference"),
        interface=RecipeInterface(),
        topology=topology,
        status=RecipeStatus.DRAFT
    )

    assert recipe.topology.nodes[0].recovery.fallback_node_id == "Agent_A"
