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

from coreason_manifest.spec.ontology import (
    ActiveInferenceEpoch,
    EpistemicRejectionReceipt,
    TargetTopologyEnum,
    TopologicalProjectionIntent,
)


@given(st.floats(max_value=-0.001) | st.floats(min_value=1.001))
def test_topological_projection_intent_out_of_bounds(v: float) -> None:
    with pytest.raises(ValidationError, match=r"isomorphism_confidence must be between 0\.0 and 1\.0"):
        TopologicalProjectionIntent(
            source_consensus_cid="test-1234",
            target_topology=TargetTopologyEnum.ALGEBRAIC_RING,
            isomorphism_confidence=v,
            lossy_translation_divergence=[],
        )


@given(st.floats(min_value=0.0, max_value=0.84999))
def test_topological_projection_intent_guillotine(v: float) -> None:
    with pytest.raises(ValidationError, match="Isomorphism Guillotine triggered"):
        TopologicalProjectionIntent(
            source_consensus_cid="test-1234",
            target_topology=TargetTopologyEnum.ALGEBRAIC_RING,
            isomorphism_confidence=v,
            lossy_translation_divergence=[],
        )


@given(st.floats(max_value=-0.001) | st.just(float("nan")) | st.just(float("inf")))
def test_kl_divergence_paradox(v: float) -> None:
    with pytest.raises(ValidationError, match="Mathematical paradox:"):
        EpistemicRejectionReceipt(
            failed_projection_cid="test-1234",
            violated_algebraic_constraint="test",
            kl_divergence_to_validity=v,
            stochastic_mutation_gradient="test",
        )


@given(st.floats(max_value=-0.001) | st.just(float("nan")) | st.just(float("inf")))
def test_active_inference_epoch_paradox(v: float) -> None:
    with pytest.raises(ValidationError, match="Mathematical paradox:"):
        ActiveInferenceEpoch(current_free_energy=v, rejection_history=[])
