# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

import pytest
from pydantic import ValidationError

from coreason_manifest.compute.neuromodulation import ActivationSteeringContract, CognitiveRoutingDirective


def test_activation_steering_contract_valid() -> None:
    contract = ActivationSteeringContract(
        steering_vector_hash="a" * 64,
        injection_layers=[1, 2, 3],
        scaling_factor=1.5,
        vector_modality="additive",
    )
    assert contract.scaling_factor == 1.5


def test_activation_steering_contract_invalid_hash() -> None:
    with pytest.raises(ValidationError):
        ActivationSteeringContract(
            steering_vector_hash="invalid_hash",
            injection_layers=[1, 2, 3],
            scaling_factor=1.5,
            vector_modality="additive",
        )


def test_activation_steering_contract_invalid_layers() -> None:
    with pytest.raises(ValidationError):
        ActivationSteeringContract(
            steering_vector_hash="a" * 64,
            injection_layers=[],
            scaling_factor=1.5,
            vector_modality="additive",
        )


def test_activation_steering_contract_invalid_modality() -> None:
    with pytest.raises(ValidationError):
        ActivationSteeringContract(
            steering_vector_hash="a" * 64,
            injection_layers=[1, 2, 3],
            scaling_factor=1.5,
            vector_modality="invalid_modality",  # type: ignore[arg-type]
        )


def test_cognitive_routing_directive_valid() -> None:
    directive = CognitiveRoutingDirective(
        dynamic_top_k=2,
        routing_temperature=0.5,
        expert_logit_biases={"falsifier": 2.0},
        enforce_functional_isolation=True,
    )
    assert directive.dynamic_top_k == 2


def test_cognitive_routing_directive_invalid_top_k() -> None:
    with pytest.raises(ValidationError):
        CognitiveRoutingDirective(
            dynamic_top_k=0,
            routing_temperature=0.5,
            expert_logit_biases={"falsifier": 2.0},
            enforce_functional_isolation=True,
        )


def test_cognitive_routing_directive_invalid_temperature() -> None:
    with pytest.raises(ValidationError):
        CognitiveRoutingDirective(
            dynamic_top_k=2,
            routing_temperature=-0.1,
            expert_logit_biases={"falsifier": 2.0},
            enforce_functional_isolation=True,
        )
