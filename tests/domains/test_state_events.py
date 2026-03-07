# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

import pytest
from pydantic import ValidationError

from coreason_manifest.state.events import NeuralAuditAttestation, SaeFeatureActivation


def test_sae_feature_activation_valid() -> None:
    activation = SaeFeatureActivation(
        feature_index=1024,
        activation_magnitude=5.7,
        interpretability_label="sycophancy",
    )
    assert activation.feature_index == 1024
    assert activation.activation_magnitude == 5.7
    assert activation.interpretability_label == "sycophancy"


def test_sae_feature_activation_invalid_negative_index() -> None:
    with pytest.raises(ValidationError, match="Input should be greater than or equal to 0"):
        SaeFeatureActivation(
            feature_index=-1,
            activation_magnitude=5.7,
        )


def test_neural_audit_attestation_valid() -> None:
    attestation = NeuralAuditAttestation(
        audit_id="audit_42",
        layer_activations={
            12: [
                SaeFeatureActivation(feature_index=1, activation_magnitude=1.0),
                SaeFeatureActivation(feature_index=2, activation_magnitude=0.5),
            ]
        },
        causal_scrubbing_applied=True,
    )
    assert attestation.audit_id == "audit_42"
    assert attestation.causal_scrubbing_applied is True
    assert 12 in attestation.layer_activations
    assert len(attestation.layer_activations[12]) == 2


def test_neural_audit_attestation_invalid_empty_id() -> None:
    with pytest.raises(ValidationError, match="String should have at least 1 character"):
        NeuralAuditAttestation(
            audit_id="",
            layer_activations={},
        )
