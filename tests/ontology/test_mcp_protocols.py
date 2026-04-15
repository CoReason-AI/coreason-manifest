# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

"""Hypothesis property tests for MCP, JSON-RPC, CognitiveActionSpaceManifest, and transport protocol models."""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    CognitiveActionSpaceManifest,
    PermissionBoundaryPolicy,
    SideEffectProfile,
    SpatialToolManifest,
    TargetTopologyProfile,
    TopologicalProjectionIntent,
    TransitionEdgeProfile,
)


def _make_tool(name: str, input_schema: dict | None = None, output_schema: dict | None = None) -> SpatialToolManifest:  # type: ignore[type-arg]
    return SpatialToolManifest(
        tool_name=name,
        description=f"Tool {name}",
        input_schema=input_schema or {"arg": "string"},
        output_schema=output_schema,
        side_effects=SideEffectProfile(is_idempotent=True, mutates_state=False),
        permissions=PermissionBoundaryPolicy(network_access=False, file_system_mutation_forbidden=True),
    )


def _edge(target: str) -> TransitionEdgeProfile:
    return TransitionEdgeProfile(
        target_node_cid=target,
        probability_weight=0.5,
        compute_weight_magnitude=1,
    )


class TestCognitiveActionSpaceManifest:
    """Exercise _enforce_structural_integrity and _prevent_custom_state_management validators."""

    def test_valid_action_space(self) -> None:
        obj = CognitiveActionSpaceManifest(
            action_space_cid="as-1",
            capabilities={"tool-1": _make_tool("tool-1")},
            transition_matrix={"tool-1": [_edge("tool-1")]},
            entry_point_cid="tool-1",
        )
        assert obj.entry_point_cid == "tool-1"

    def test_entry_point_not_in_capabilities(self) -> None:
        with pytest.raises(ValidationError, match="entry_point_cid"):
            CognitiveActionSpaceManifest(
                action_space_cid="as-2",
                capabilities={"tool-1": _make_tool("tool-1")},
                transition_matrix={},
                entry_point_cid="missing",
            )

    def test_source_not_in_capabilities(self) -> None:
        with pytest.raises(ValidationError, match="Source node"):
            CognitiveActionSpaceManifest(
                action_space_cid="as-3",
                capabilities={"tool-1": _make_tool("tool-1")},
                transition_matrix={"missing": [_edge("tool-1")]},
                entry_point_cid="tool-1",
            )

    def test_target_not_in_capabilities(self) -> None:
        with pytest.raises(ValidationError, match="Target node"):
            CognitiveActionSpaceManifest(
                action_space_cid="as-4",
                capabilities={"tool-1": _make_tool("tool-1")},
                transition_matrix={"tool-1": [_edge("missing")]},
                entry_point_cid="tool-1",
            )

    def test_illegal_payload_key_in_input_schema(self) -> None:
        """A native_tool with 'memory' in input_schema properties is rejected."""
        tool = _make_tool("t1", input_schema={"properties": {"memory": "forbidden"}})
        with pytest.raises(ValidationError, match="Framework Violation"):
            CognitiveActionSpaceManifest(
                action_space_cid="as-5",
                capabilities={"t1": tool},
                transition_matrix={},
                entry_point_cid="t1",
            )

    def test_illegal_payload_key_in_output_schema(self) -> None:
        """A native_tool with 'trace_context' in output_schema properties is rejected."""
        tool = _make_tool("t2", output_schema={"properties": {"trace_context": "forbidden"}})
        with pytest.raises(ValidationError, match="Framework Violation"):
            CognitiveActionSpaceManifest(
                action_space_cid="as-6",
                capabilities={"t2": tool},
                transition_matrix={},
                entry_point_cid="t2",
            )


class TestTopologicalProjectionIntent:
    """Exercise enforce_isomorphism_guillotine field_validator."""

    def test_valid_confidence(self) -> None:
        obj = TopologicalProjectionIntent(
            projection_cid="proj-1",
            source_superposition_cid="sp-1",
            target_topology=TargetTopologyProfile.N_DIMENSIONAL_TENSOR,
            isomorphism_confidence=0.95,
            lossy_translation_divergence=[],
        )
        assert obj.isomorphism_confidence == 0.95

    def test_below_threshold_rejected(self) -> None:
        with pytest.raises(ValidationError, match="Isomorphism Guillotine"):
            TopologicalProjectionIntent(
                projection_cid="proj-2",
                source_superposition_cid="sp-2",
                target_topology=TargetTopologyProfile.MARKOV_BLANKET,
                isomorphism_confidence=0.5,
                lossy_translation_divergence=[],
            )

    def test_at_threshold_valid(self) -> None:
        obj = TopologicalProjectionIntent(
            projection_cid="proj-3",
            source_superposition_cid="sp-3",
            target_topology=TargetTopologyProfile.ACYCLIC_DIRECTED_GRAPH,
            isomorphism_confidence=0.85,
            lossy_translation_divergence=[],
        )
        assert obj.isomorphism_confidence == 0.85

    @given(conf=st.floats(min_value=0.85, max_value=1.0, allow_nan=False))
    @settings(max_examples=10, deadline=None)
    def test_above_threshold_always_valid(self, conf: float) -> None:
        obj = TopologicalProjectionIntent(
            projection_cid="proj-gen",
            source_superposition_cid="sp-gen",
            target_topology=TargetTopologyProfile.ALGEBRAIC_RING,
            isomorphism_confidence=conf,
            lossy_translation_divergence=[],
        )
        assert obj.isomorphism_confidence >= 0.85

    def test_lossy_divergence_sorted(self) -> None:
        obj = TopologicalProjectionIntent(
            projection_cid="proj-4",
            source_superposition_cid="sp-4",
            target_topology=TargetTopologyProfile.N_DIMENSIONAL_TENSOR,
            isomorphism_confidence=0.9,
            lossy_translation_divergence=["z-loss", "a-loss", "m-loss"],
        )
        assert obj.lossy_translation_divergence == sorted(obj.lossy_translation_divergence)
