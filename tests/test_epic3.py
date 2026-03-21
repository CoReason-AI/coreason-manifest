import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    ActionSpaceManifest,
    PermissionBoundaryPolicy,
    SemanticDiscoveryIntent,
    SideEffectProfile,
    ToolManifest,
    TransitionEdgeProfile,
)


def test_transition_edge_xor_validation() -> None:
    # Test valid target_node_id only
    TransitionEdgeProfile(
        edge_type="acyclic", target_node_id="tool_A", probability_weight=1.0, compute_weight_magnitude=5
    )

    # Test valid target_intent only
    intent = SemanticDiscoveryIntent(
        required_structural_types=["ToolManifest"],
        min_isometry_score=0.9,
        query_vector={"vector_base64": "dummy", "dimensionality": 128, "model_name": "test-model"},
    )
    TransitionEdgeProfile(edge_type="acyclic", target_intent=intent, probability_weight=1.0, compute_weight_magnitude=5)

    # Test invalid both
    with pytest.raises(ValidationError, match="Exactly one of target_node_id or target_intent must be populated"):
        TransitionEdgeProfile(
            edge_type="acyclic",
            target_node_id="tool_A",
            target_intent=intent,
            probability_weight=1.0,
            compute_weight_magnitude=5,
        )

    # Test invalid neither
    with pytest.raises(ValidationError, match="Exactly one of target_node_id or target_intent must be populated"):
        TransitionEdgeProfile(edge_type="acyclic", probability_weight=1.0, compute_weight_magnitude=5)


def test_dynamic_ghost_node_and_canonical_sorting() -> None:
    tool_a = ToolManifest(
        type="native_tool",
        tool_name="tool_A",
        description="Tool A",
        input_schema={"type": "object", "properties": {"input": {"type": "string"}}},
        side_effects=SideEffectProfile(is_idempotent=True, mutates_state=False),
        permissions=PermissionBoundaryPolicy(network_access=False, file_system_mutation_forbidden=True),
    )

    # Intent 1 should sort first (min_isometry_score 0.8 < 0.9)
    intent1 = SemanticDiscoveryIntent(
        required_structural_types=["ToolManifest"],
        min_isometry_score=0.8,
        query_vector={"vector_base64": "dummy", "dimensionality": 128, "model_name": "test-model"},
    )
    # Intent 2 should sort second
    intent2 = SemanticDiscoveryIntent(
        required_structural_types=["ToolManifest"],
        min_isometry_score=0.9,
        query_vector={"vector_base64": "dummy", "dimensionality": 128, "model_name": "test-model"},
    )

    edge1 = TransitionEdgeProfile(
        edge_type="acyclic", target_intent=intent2, probability_weight=1.0, compute_weight_magnitude=5
    )
    edge2 = TransitionEdgeProfile(
        edge_type="acyclic", target_intent=intent1, probability_weight=1.0, compute_weight_magnitude=5
    )

    asm = ActionSpaceManifest(
        action_space_id="test_dynamic_edges",
        entry_point_id="tool_A",
        capabilities={"tool_A": tool_a},
        transition_matrix={"tool_A": [edge1, edge2]},
    )

    # Assert that dynamic edges are accepted even if their "target" is not in capabilities
    assert "tool_A" in asm.capabilities

    # Assert canonical sorting worked
    edges = asm.transition_matrix["tool_A"]
    assert edges[0].target_intent.min_isometry_score == 0.8
    assert edges[1].target_intent.min_isometry_score == 0.9
