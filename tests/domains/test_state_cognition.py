# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.state.cognition import CognitiveStateProfile, CognitiveUncertaintyProfile


@given(
    aleatoric_entropy=st.floats(min_value=0.0, max_value=1.0),
    epistemic_uncertainty=st.floats(min_value=0.0, max_value=1.0),
    semantic_consistency_score=st.floats(min_value=0.0, max_value=1.0),
    requires_abductive_escalation=st.booleans(),
)
def test_cognitive_uncertainty_profile_fuzzing(
    aleatoric_entropy: float,
    epistemic_uncertainty: float,
    semantic_consistency_score: float,
    requires_abductive_escalation: bool,
) -> None:
    profile = CognitiveUncertaintyProfile(
        aleatoric_entropy=aleatoric_entropy,
        epistemic_uncertainty=epistemic_uncertainty,
        semantic_consistency_score=semantic_consistency_score,
        requires_abductive_escalation=requires_abductive_escalation,
    )
    assert profile.aleatoric_entropy == aleatoric_entropy
    assert profile.epistemic_uncertainty == epistemic_uncertainty


@given(
    urgency_index=st.floats(min_value=0.0, max_value=1.0),
    caution_index=st.floats(min_value=0.0, max_value=1.0),
    divergence_tolerance=st.floats(min_value=0.0, max_value=1.0),
    active_steering_vector_hash=st.one_of(st.none(), st.from_regex(r"^[a-f0-9]{64}$", fullmatch=True)),
)
def test_cognitive_state_profile_fuzzing(
    urgency_index: float, caution_index: float, divergence_tolerance: float, active_steering_vector_hash: str | None
) -> None:
    profile = CognitiveStateProfile(
        urgency_index=urgency_index,
        caution_index=caution_index,
        divergence_tolerance=divergence_tolerance,
        active_steering_vector_hash=active_steering_vector_hash,
    )
    assert profile.urgency_index == urgency_index


def test_invalid_bounds_rejected() -> None:
    # Test negative floats
    with pytest.raises(ValidationError):
        CognitiveUncertaintyProfile(
            aleatoric_entropy=-0.1,
            epistemic_uncertainty=0.5,
            semantic_consistency_score=0.5,
            requires_abductive_escalation=False,
        )

    # Test floats > 1.0
    with pytest.raises(ValidationError):
        CognitiveUncertaintyProfile(
            aleatoric_entropy=1.1,
            epistemic_uncertainty=0.5,
            semantic_consistency_score=0.5,
            requires_abductive_escalation=False,
        )

    # Test invalid SHA-256 hash
    with pytest.raises(ValidationError):
        CognitiveStateProfile(
            urgency_index=0.5, caution_index=0.5, divergence_tolerance=0.5, active_steering_vector_hash="invalidhash"
        )


def test_canonical_hashing_determinism() -> None:
    from typing import Any
    kwargs1: dict[str, Any] = {
        "aleatoric_entropy": 0.5,
        "epistemic_uncertainty": 0.2,
        "semantic_consistency_score": 0.8,
        "requires_abductive_escalation": False,
    }

    kwargs2: dict[str, Any] = {
        "requires_abductive_escalation": False,
        "semantic_consistency_score": 0.8,
        "epistemic_uncertainty": 0.2,
        "aleatoric_entropy": 0.5,
    }

    profile1 = CognitiveUncertaintyProfile(**kwargs1)
    profile2 = CognitiveUncertaintyProfile(**kwargs2)

    assert profile1.model_dump_canonical() == profile2.model_dump_canonical()
    assert hash(profile1) == hash(profile2)

    kwargs3: dict[str, Any] = {
        "urgency_index": 0.5,
        "caution_index": 0.5,
        "divergence_tolerance": 0.5,
        "active_steering_vector_hash": "a" * 64,
    }

    kwargs4: dict[str, Any] = {
        "active_steering_vector_hash": "a" * 64,
        "divergence_tolerance": 0.5,
        "caution_index": 0.5,
        "urgency_index": 0.5,
    }

    profile3 = CognitiveStateProfile(**kwargs3)
    profile4 = CognitiveStateProfile(**kwargs4)

    assert profile3.model_dump_canonical() == profile4.model_dump_canonical()
    assert hash(profile3) == hash(profile4)
