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

from coreason_manifest.compute.neuromodulation import ActivationSteeringContract, CognitiveRoutingDirective
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


@st.composite
def draw_activation_steering_contract(draw: st.DrawFn) -> ActivationSteeringContract:
    return ActivationSteeringContract(
        steering_vector_hash=draw(st.from_regex(r"^[a-f0-9]{64}$", fullmatch=True)),
        injection_layers=draw(st.lists(st.integers(), min_size=1)),
        scaling_factor=draw(st.floats(allow_nan=False, allow_infinity=False)),
        vector_modality=draw(st.sampled_from(["additive", "ablation", "clamping"])),
    )


@st.composite
def draw_cognitive_routing_directive(draw: st.DrawFn) -> CognitiveRoutingDirective:
    return CognitiveRoutingDirective(
        dynamic_top_k=draw(st.integers(min_value=1)),
        routing_temperature=draw(st.floats(min_value=0.0, allow_nan=False, allow_infinity=False)),
        expert_logit_biases=draw(st.dictionaries(st.text(), st.floats(allow_nan=False, allow_infinity=False))),
        enforce_functional_isolation=draw(st.booleans()),
    )


@given(
    urgency_index=st.floats(min_value=0.0, max_value=1.0),
    caution_index=st.floats(min_value=0.0, max_value=1.0),
    divergence_tolerance=st.floats(min_value=0.0, max_value=1.0),
    activation_steering=st.one_of(st.none(), draw_activation_steering_contract()),
    moe_routing_directive=st.one_of(st.none(), draw_cognitive_routing_directive()),
)
def test_cognitive_state_profile_fuzzing(
    urgency_index: float,
    caution_index: float,
    divergence_tolerance: float,
    activation_steering: ActivationSteeringContract | None,
    moe_routing_directive: CognitiveRoutingDirective | None,
) -> None:
    profile = CognitiveStateProfile(
        urgency_index=urgency_index,
        caution_index=caution_index,
        divergence_tolerance=divergence_tolerance,
        activation_steering=activation_steering,
        moe_routing_directive=moe_routing_directive,
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

    # Test invalid steering contract values indirectly
    with pytest.raises(ValidationError):
        ActivationSteeringContract(
            steering_vector_hash="invalidhash", injection_layers=[1], scaling_factor=1.0, vector_modality="additive"
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

    steering_dict = {
        "steering_vector_hash": "a" * 64,
        "injection_layers": [1],
        "scaling_factor": 1.0,
        "vector_modality": "additive",
    }

    routing_dict = {
        "dynamic_top_k": 2,
        "routing_temperature": 0.5,
        "expert_logit_biases": {},
        "enforce_functional_isolation": False,
    }

    kwargs3: dict[str, Any] = {
        "urgency_index": 0.5,
        "caution_index": 0.5,
        "divergence_tolerance": 0.5,
        "activation_steering": steering_dict,
        "moe_routing_directive": routing_dict,
    }

    kwargs4: dict[str, Any] = {
        "moe_routing_directive": routing_dict,
        "activation_steering": steering_dict,
        "divergence_tolerance": 0.5,
        "caution_index": 0.5,
        "urgency_index": 0.5,
    }

    profile3 = CognitiveStateProfile(**kwargs3)
    profile4 = CognitiveStateProfile(**kwargs4)

    assert profile3.model_dump_canonical() == profile4.model_dump_canonical()
    assert hash(profile3) == hash(profile4)
