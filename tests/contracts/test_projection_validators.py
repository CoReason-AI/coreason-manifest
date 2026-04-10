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
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.ontology import TargetTopologyEnum, TopologicalProjectionIntent


@given(st.floats(min_value=0.0, max_value=0.84999), st.uuids().map(str), st.sampled_from(TargetTopologyEnum))
def test_isomorphism_guillotine(confidence: float, source_cid: str, topology: TargetTopologyEnum) -> None:
    """Test 1: The Isomorphism Guillotine"""
    with pytest.raises(ValidationError) as exc_info:
        TopologicalProjectionIntent(
            source_consensus_cid=source_cid,
            target_topology=topology,
            isomorphism_confidence=confidence,
            lossy_translation_divergence=["semantic loss 1"],
        )
    assert "Isomorphism Guillotine triggered" in str(exc_info.value)


@given(st.floats(min_value=0.85, max_value=1.0), st.uuids().map(str), st.sampled_from(TargetTopologyEnum))
def test_valid_projection_space(confidence: float, source_cid: str, topology: TargetTopologyEnum) -> None:
    """Test 2: Valid Projection Space"""
    intent = TopologicalProjectionIntent(
        source_consensus_cid=source_cid,
        target_topology=topology,
        isomorphism_confidence=confidence,
        lossy_translation_divergence=["minor nuance dropped"],
    )
    assert intent.isomorphism_confidence == confidence
    assert intent.source_consensus_cid == source_cid
    assert intent.target_topology == topology


@given(
    st.floats(min_value=0.85, max_value=1.0),
    st.uuids().map(str),
    st.sampled_from(TargetTopologyEnum),
    st.sampled_from(["executed", "collapsed"]),
)
def test_immutability_of_status(
    confidence: float, source_cid: str, topology: TargetTopologyEnum, invalid_status: str
) -> None:
    """Test 3: Immutability of Status"""
    intent = TopologicalProjectionIntent(
        source_consensus_cid=source_cid,
        target_topology=topology,
        isomorphism_confidence=confidence,
        lossy_translation_divergence=[],
    )

    with pytest.raises(ValidationError):
        # We need to bypass the frozen check or use mutation that violates epistemic_status
        # The assignment itself is blocked by frozen=True and strict epistemic_status
        # The test specifically mentioned "attempting to mutate epistemic_status to 'executed' or 'collapsed' results in a ValidationError"
        # Since it's a CoreasonBaseState with frozen=True, we check using model_validate

        # Another way to attempt mutation is to create with it
        TopologicalProjectionIntent(
            source_consensus_cid=source_cid,
            target_topology=topology,
            isomorphism_confidence=confidence,
            lossy_translation_divergence=[],
            epistemic_status=invalid_status,  # type: ignore
        )

    # To specifically test the mutation on the existing intent:
    with pytest.raises(ValidationError):
        # Direct mutation is caught by frozen=True configuration
        intent.epistemic_status = invalid_status  # type: ignore
