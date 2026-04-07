# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

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
    # Test valid target_node_cid only
    TransitionEdgeProfile(
        topology_class="acyclic", target_node_cid="tool_A", probability_weight=1.0, compute_weight_magnitude=5
    )

    # Test valid target_intent only
    intent = SemanticDiscoveryIntent(
        required_structural_manifold_categorys=["ToolManifest"],
        min_isometry_score=0.9,
        query_vector={"vector_base64": "dummy", "dimensionality": 128, "model_name": "test-model"},  # type: ignore[arg-type]
    )
    TransitionEdgeProfile(
        topology_class="acyclic", target_intent=intent, probability_weight=1.0, compute_weight_magnitude=5
    )

    # Test invalid both
    with pytest.raises(ValidationError, match="Exactly one of target_node_cid or target_intent must be populated"):
        TransitionEdgeProfile(
            topology_class="acyclic",
            target_node_cid="tool_A",
            target_intent=intent,
            probability_weight=1.0,
            compute_weight_magnitude=5,
        )

    # Test invalid neither
    with pytest.raises(ValidationError, match="Exactly one of target_node_cid or target_intent must be populated"):
        TransitionEdgeProfile(topology_class="acyclic", probability_weight=1.0, compute_weight_magnitude=5)


def test_dynamic_ghost_node_and_canonical_sorting() -> None:
    tool_a = ToolManifest(
        manifold_category="native_tool",
        tool_name="tool_A",
        description="Tool A",
        input_schema={"type": "object", "properties": {"input": {"type": "string"}}},
        side_effects=SideEffectProfile(is_idempotent=True, mutates_state=False),
        permissions=PermissionBoundaryPolicy(network_access=False, file_system_mutation_forbidden=True),
    )

    # Intent 1 should sort first (min_isometry_score 0.8 < 0.9)
    intent1 = SemanticDiscoveryIntent(
        required_structural_manifold_categorys=["ToolManifest"],
        min_isometry_score=0.8,
        query_vector={"vector_base64": "dummy", "dimensionality": 128, "model_name": "test-model"},  # type: ignore[arg-type]
    )
    # Intent 2 should sort second
    intent2 = SemanticDiscoveryIntent(
        required_structural_manifold_categorys=["ToolManifest"],
        min_isometry_score=0.9,
        query_vector={"vector_base64": "dummy", "dimensionality": 128, "model_name": "test-model"},  # type: ignore[arg-type]
    )

    edge1 = TransitionEdgeProfile(
        topology_class="acyclic", target_intent=intent2, probability_weight=1.0, compute_weight_magnitude=5
    )
    edge2 = TransitionEdgeProfile(
        topology_class="acyclic", target_intent=intent1, probability_weight=1.0, compute_weight_magnitude=5
    )

    asm = ActionSpaceManifest(
        action_space_cid="test_dynamic_edges",
        entry_point_cid="tool_A",
        capabilities={"tool_A": tool_a},
        transition_matrix={"tool_A": [edge1, edge2]},
    )

    # Assert that dynamic edges are accepted even if their "target" is not in capabilities
    assert "tool_A" in asm.capabilities

    # Assert canonical sorting worked
    edges = asm.transition_matrix["tool_A"]
    assert edges[0].target_intent is not None
    assert edges[1].target_intent is not None
    assert edges[0].target_intent.min_isometry_score == 0.8
    assert edges[1].target_intent.min_isometry_score == 0.9
