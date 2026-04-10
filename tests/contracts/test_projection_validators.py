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

@given(st.floats(min_value=0.0, max_value=0.84999), st.uuids().map(str), st.uuids().map(str), st.sampled_from(TargetTopologyEnum))
def test_isomorphism_guillotine(confidence: float, projection_cid: str, source_cid: str, topology: TargetTopologyEnum) -> None:
    with pytest.raises(ValidationError) as exc_info:
        TopologicalProjectionIntent(
            projection_cid=projection_cid,
            source_superposition_cid=source_cid,
            target_topology=topology,
            isomorphism_confidence=confidence,
            lossy_translation_divergence=["semantic loss 1"],
        )
    assert "Isomorphism Guillotine triggered" in str(exc_info.value)

@given(st.floats(min_value=0.85, max_value=1.0), st.uuids().map(str), st.uuids().map(str), st.sampled_from(TargetTopologyEnum))
def test_valid_projection_space(confidence: float, projection_cid: str, source_cid: str, topology: TargetTopologyEnum) -> None:
    intent = TopologicalProjectionIntent(
        projection_cid=projection_cid,
        source_superposition_cid=source_cid,
        target_topology=topology,
        isomorphism_confidence=confidence,
        lossy_translation_divergence=["minor nuance dropped"],
    )
    assert intent.isomorphism_confidence == confidence
    assert intent.source_superposition_cid == source_cid
    assert intent.target_topology == topology

@given(
    st.floats(min_value=0.85, max_value=1.0),
    st.uuids().map(str),
    st.uuids().map(str),
    st.sampled_from(TargetTopologyEnum),
    st.sampled_from(["executed", "collapsed"]),
)
def test_immutability_of_status(
    confidence: float, projection_cid: str, source_cid: str, topology: TargetTopologyEnum, invalid_status: str
) -> None:
    intent = TopologicalProjectionIntent(
        projection_cid=projection_cid,
        source_superposition_cid=source_cid,
        target_topology=topology,
        isomorphism_confidence=confidence,
        lossy_translation_divergence=[],
    )
    with pytest.raises(ValidationError):
        TopologicalProjectionIntent(
            projection_cid=projection_cid,
            source_superposition_cid=source_cid,
            target_topology=topology,
            isomorphism_confidence=confidence,
            lossy_translation_divergence=[],
            epistemic_status=invalid_status,  # type: ignore
        )
    with pytest.raises(ValidationError):
        intent.epistemic_status = invalid_status  # type: ignore
