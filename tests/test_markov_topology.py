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
    AlgebraicEffectProfile,
    ComputationalMonadProfile,
    CyclicEdgeProfile,
    PermissionBoundaryPolicy,
    TerminalConditionContract,
    ToolManifest,
    TransitionEdgeProfile,
)


def test_cyclic_edge_infinite_loop_guillotine() -> None:
    # Test that discount_factor=1.0 and max_causal_depth=None raises ValueError
    with pytest.raises(ValidationError, match="Un-haltable infinite loop detected"):
        CyclicEdgeProfile(
            edge_type="cyclic",
            target_node_id="tool_A",
            probability_weight=1.0,
            compute_weight_magnitude=10,
            discount_factor=1.0,
            terminal_condition=TerminalConditionContract(minimum_budget_magnitude=10),
        )

    # Test valid CyclicEdgeProfile
    CyclicEdgeProfile(
        edge_type="cyclic",
        target_node_id="tool_A",
        probability_weight=1.0,
        compute_weight_magnitude=10,
        discount_factor=0.9,
        terminal_condition=TerminalConditionContract(minimum_budget_magnitude=10),
    )

    CyclicEdgeProfile(
        edge_type="cyclic",
        target_node_id="tool_A",
        probability_weight=1.0,
        compute_weight_magnitude=10,
        discount_factor=1.0,
        terminal_condition=TerminalConditionContract(max_causal_depth=10),
    )


def test_action_space_dcg_compilation() -> None:
    tool_a = ToolManifest(
        type="native_tool",
        tool_name="tool_A",
        description="Tool A",
        input_schema={"type": "object", "properties": {"input": {"type": "string"}}},
        algebraic_effects=AlgebraicEffectProfile(permitted_monads=[ComputationalMonadProfile.READER], is_referentially_transparent=True, thermodynamic_variance_bound=0.0),
        permissions=PermissionBoundaryPolicy(network_access=False, file_system_mutation_forbidden=True),
    )

    tool_b = ToolManifest(
        type="native_tool",
        tool_name="tool_B",
        description="Tool B",
        input_schema={"type": "object", "properties": {"input": {"type": "string"}}},
        algebraic_effects=AlgebraicEffectProfile(permitted_monads=[ComputationalMonadProfile.READER], is_referentially_transparent=True, thermodynamic_variance_bound=0.0),
        permissions=PermissionBoundaryPolicy(network_access=False, file_system_mutation_forbidden=True),
    )

    # Coinductive Validation Test (No RecursionError)
    asm = ActionSpaceManifest(
        action_space_id="test_dcg",
        entry_point_id="tool_A",
        capabilities={
            "tool_A": tool_a,
            "tool_B": tool_b,
        },
        transition_matrix={
            "tool_A": [
                TransitionEdgeProfile(
                    edge_type="acyclic", target_node_id="tool_B", probability_weight=1.0, compute_weight_magnitude=5
                )
            ],
            "tool_B": [
                CyclicEdgeProfile(
                    edge_type="cyclic",
                    target_node_id="tool_A",
                    probability_weight=1.0,
                    compute_weight_magnitude=5,
                    discount_factor=0.9,
                    terminal_condition=TerminalConditionContract(max_causal_depth=10),
                )
            ],
        },
    )

    assert asm.entry_point_id == "tool_A"
    assert "tool_A" in asm.capabilities
    assert "tool_B" in asm.capabilities


def test_action_space_ghost_edge_prevention() -> None:
    tool_a = ToolManifest(
        type="native_tool",
        tool_name="tool_A",
        description="Tool A",
        input_schema={"type": "object", "properties": {"input": {"type": "string"}}},
        algebraic_effects=AlgebraicEffectProfile(permitted_monads=[ComputationalMonadProfile.READER], is_referentially_transparent=True, thermodynamic_variance_bound=0.0),
        permissions=PermissionBoundaryPolicy(network_access=False, file_system_mutation_forbidden=True),
    )

    # Missing tool_C in capabilities
    with pytest.raises(ValidationError, match="not found in capabilities"):
        ActionSpaceManifest(
            action_space_id="test_ghost_edge",
            entry_point_id="tool_A",
            capabilities={"tool_A": tool_a},
            transition_matrix={
                "tool_A": [
                    TransitionEdgeProfile(
                        edge_type="acyclic", target_node_id="tool_C", probability_weight=1.0, compute_weight_magnitude=5
                    )
                ]
            },
        )

    # Missing entry_point_id in capabilities
    with pytest.raises(ValidationError, match="not found in capabilities"):
        ActionSpaceManifest(
            action_space_id="test_ghost_edge",
            entry_point_id="tool_B",
            capabilities={"tool_A": tool_a},
            transition_matrix={"tool_A": []},
        )


def test_discount_factor_bounds() -> None:
    with pytest.raises(ValidationError, match="discount_factor"):
        CyclicEdgeProfile(
            edge_type="cyclic",
            target_node_id="tool_A",
            probability_weight=1.0,
            compute_weight_magnitude=10,
            discount_factor=1.5,
            terminal_condition=TerminalConditionContract(max_causal_depth=10),
        )
