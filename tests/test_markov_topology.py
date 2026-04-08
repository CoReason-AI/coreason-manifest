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
    CognitiveActionSpaceManifest,
    CyclicEdgeProfile,
    PermissionBoundaryPolicy,
    SideEffectProfile,
    SpatialToolManifest,
    TerminalConditionContract,
    TransitionEdgeProfile,
)


def test_cyclic_edge_infinite_loop_guillotine() -> None:
    # Test that discount_factor=1.0 and max_causal_depth=None raises ValueError
    with pytest.raises(ValidationError, match="Un-haltable infinite loop detected"):
        CyclicEdgeProfile(
            topology_class="cyclic",
            target_node_cid="tool_A",
            probability_weight=1.0,
            compute_weight_magnitude=10,
            discount_factor=1.0,
            terminal_condition=TerminalConditionContract(minimum_budget_magnitude=10),
        )

    # Test valid CyclicEdgeProfile
    CyclicEdgeProfile(
        topology_class="cyclic",
        target_node_cid="tool_A",
        probability_weight=1.0,
        compute_weight_magnitude=10,
        discount_factor=0.9,
        terminal_condition=TerminalConditionContract(minimum_budget_magnitude=10),
    )

    CyclicEdgeProfile(
        topology_class="cyclic",
        target_node_cid="tool_A",
        probability_weight=1.0,
        compute_weight_magnitude=10,
        discount_factor=1.0,
        terminal_condition=TerminalConditionContract(max_causal_depth=10),
    )


def test_action_space_dcg_compilation() -> None:
    tool_a = SpatialToolManifest(
        topology_class="native_tool",
        tool_name="tool_A",
        description="Tool A",
        input_schema={"topology_class": "object", "properties": {"input": {"topology_class": "string"}}},
        side_effects=SideEffectProfile(is_idempotent=True, mutates_state=False),
        permissions=PermissionBoundaryPolicy(network_access=False, file_system_mutation_forbidden=True),
    )

    tool_b = SpatialToolManifest(
        topology_class="native_tool",
        tool_name="tool_B",
        description="Tool B",
        input_schema={"topology_class": "object", "properties": {"input": {"topology_class": "string"}}},
        side_effects=SideEffectProfile(is_idempotent=True, mutates_state=False),
        permissions=PermissionBoundaryPolicy(network_access=False, file_system_mutation_forbidden=True),
    )

    # Coinductive Validation Test (No RecursionError)
    asm = CognitiveActionSpaceManifest(
        action_space_cid="test_dcg",
        entry_point_cid="tool_A",
        capabilities={
            "tool_A": tool_a,
            "tool_B": tool_b,
        },
        transition_matrix={
            "tool_A": [
                TransitionEdgeProfile(
                    topology_class="acyclic",
                    target_node_cid="tool_B",
                    probability_weight=1.0,
                    compute_weight_magnitude=5,
                )
            ],
            "tool_B": [
                CyclicEdgeProfile(
                    topology_class="cyclic",
                    target_node_cid="tool_A",
                    probability_weight=1.0,
                    compute_weight_magnitude=5,
                    discount_factor=0.9,
                    terminal_condition=TerminalConditionContract(max_causal_depth=10),
                )
            ],
        },
    )

    assert asm.entry_point_cid == "tool_A"
    assert "tool_A" in asm.capabilities
    assert "tool_B" in asm.capabilities


def test_action_space_ghost_edge_prevention() -> None:
    tool_a = SpatialToolManifest(
        topology_class="native_tool",
        tool_name="tool_A",
        description="Tool A",
        input_schema={"topology_class": "object", "properties": {"input": {"topology_class": "string"}}},
        side_effects=SideEffectProfile(is_idempotent=True, mutates_state=False),
        permissions=PermissionBoundaryPolicy(network_access=False, file_system_mutation_forbidden=True),
    )

    # Missing tool_C in capabilities
    with pytest.raises(ValidationError, match="not found in capabilities"):
        CognitiveActionSpaceManifest(
            action_space_cid="test_ghost_edge",
            entry_point_cid="tool_A",
            capabilities={"tool_A": tool_a},
            transition_matrix={
                "tool_A": [
                    TransitionEdgeProfile(
                        topology_class="acyclic",
                        target_node_cid="tool_C",
                        probability_weight=1.0,
                        compute_weight_magnitude=5,
                    )
                ]
            },
        )

    # Missing entry_point_cid in capabilities
    with pytest.raises(ValidationError, match="not found in capabilities"):
        CognitiveActionSpaceManifest(
            action_space_cid="test_ghost_edge",
            entry_point_cid="tool_B",
            capabilities={"tool_A": tool_a},
            transition_matrix={"tool_A": []},
        )


def test_discount_factor_bounds() -> None:
    with pytest.raises(ValidationError, match="discount_factor"):
        CyclicEdgeProfile(
            topology_class="cyclic",
            target_node_cid="tool_A",
            probability_weight=1.0,
            compute_weight_magnitude=10,
            discount_factor=1.5,
            terminal_condition=TerminalConditionContract(max_causal_depth=10),
        )
