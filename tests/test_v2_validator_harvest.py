import pytest

from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    FailureBehavior,
    GraphEdge,
    GraphTopology,
    RecipeDefinition,
    RecipeInterface,
    RecipeStatus,
    RecoveryConfig,
)


def test_valid_topology() -> None:
    """Test a valid topology with correct fallback reference."""
    node_a = AgentNode(
        id="Agent_A",
        agent_ref="agent-1",
        recovery=RecoveryConfig(
            behavior=FailureBehavior.ROUTE_TO_FALLBACK,
            fallback_node_id="Agent_B",
        ),
    )
    node_b = AgentNode(id="Agent_B", agent_ref="agent-2")

    topology = GraphTopology(
        nodes=[node_a, node_b],
        edges=[GraphEdge(source="Agent_A", target="Agent_B")],
        entry_point="Agent_A",
        status="valid",
    )

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Valid Topology"),
        interface=RecipeInterface(),
        topology=topology,
        status=RecipeStatus.DRAFT,
    )

    assert recipe.topology.nodes[0].recovery is not None
    assert recipe.topology.nodes[0].recovery.fallback_node_id == "Agent_B"


def test_broken_link_fallback() -> None:
    """Test a broken link where fallback node does not exist."""
    node_a = AgentNode(
        id="Agent_A",
        agent_ref="agent-1",
        recovery=RecoveryConfig(
            behavior=FailureBehavior.ROUTE_TO_FALLBACK,
            fallback_node_id="Ghost_Node",
        ),
    )

    # Even if GraphTopology is draft, RecipeDefinition should catch this if we add the validator.
    # Note: GraphTopology skips validation if status='draft', so we rely on RecipeDefinition validator.
    topology = GraphTopology(
        nodes=[node_a],
        edges=[],
        entry_point="Agent_A",
        status="draft",
    )

    with pytest.raises(ValueError, match="Ghost_Node"):
        RecipeDefinition(
            metadata=ManifestMetadata(name="Broken Link"),
            interface=RecipeInterface(),
            topology=topology,
            status=RecipeStatus.DRAFT,
        )


def test_self_reference_fallback() -> None:
    """Test a node referencing itself as fallback."""
    node_a = AgentNode(
        id="Agent_A",
        agent_ref="agent-1",
        recovery=RecoveryConfig(
            behavior=FailureBehavior.ROUTE_TO_FALLBACK,
            fallback_node_id="Agent_A",
        ),
    )

    topology = GraphTopology(
        nodes=[node_a],
        edges=[],
        entry_point="Agent_A",
        status="valid",
    )

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Self Reference"),
        interface=RecipeInterface(),
        topology=topology,
        status=RecipeStatus.DRAFT,
    )

    assert recipe.topology.nodes[0].recovery is not None
    assert recipe.topology.nodes[0].recovery.fallback_node_id == "Agent_A"
