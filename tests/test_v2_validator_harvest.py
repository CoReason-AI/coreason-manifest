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


def test_empty_topology() -> None:
    """Test an empty topology to ensure validator handles it gracefully."""
    # GraphTopology requires non-empty nodes list by default due to entry_point validation
    # unless status is draft and we construct it carefully or mock it.
    # However, GraphTopology definition:
    # nodes: list[...] = Field(..., description="List of nodes in the graph.")
    # It doesn't enforce min_length at Pydantic level, but check validation logic.

    # GraphTopology validation:
    # @model_validator(mode="after")
    # def validate_integrity(self) -> "GraphTopology":
    # ...
    # if self.status == "draft": return self

    # So for draft status, we can have empty nodes if we bypass other constraints.
    # But wait, entry_point is required field.

    # Let's try to construct a minimal valid empty topology if possible,
    # or just one that passes Pydantic validation enough to reach our validator.

    # If nodes is empty, entry_point validation will fail in GraphTopology.validate_integrity
    # unless status is draft.

    # But wait, `validate_topology_integrity` in `RecipeDefinition` runs regardless of status.

    topology = GraphTopology(
        nodes=[],
        edges=[],
        entry_point="None",  # Required field
        status="draft",
    )

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Empty Topology"),
        interface=RecipeInterface(),
        topology=topology,
        status=RecipeStatus.DRAFT,
    )

    assert len(recipe.topology.nodes) == 0
