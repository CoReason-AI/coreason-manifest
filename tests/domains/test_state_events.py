# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

import pytest
from pydantic import TypeAdapter, ValidationError

from coreason_manifest.state.events import (
    ActiveInferenceYield,
    AnyStateEvent,
    EpistemicPromotionEvent,
    NeuralAuditAttestation,
    NormativeDriftEvent,
    SaeFeatureActivation,
)


def test_active_inference_yield_valid() -> None:
    """Prove baseline instantiation of epistemic exhaustion receipt."""
    event = ActiveInferenceYield(
        event_id="evt_123",
        timestamp=1710000000.0,
        target_variable_urn="urn:coreason:variable:user_intent",
        epistemic_confidence_delta=0.85,
        canonical_projection="Need user to clarify intent.",
        temporal_escalation_bound=3600,
    )
    assert event.type == "active_inference_yield"
    assert event.epistemic_confidence_delta == 0.85


def test_active_inference_yield_invalid_confidence() -> None:
    """Enforce mathematical bounds on epistemic confidence."""
    with pytest.raises(ValidationError):
        ActiveInferenceYield(
            event_id="evt_123",
            timestamp=1710000000.0,
            target_variable_urn="urn:coreason:variable:user_intent",
            epistemic_confidence_delta=1.5,  # Invalid: > 1.0
            canonical_projection="Need user to clarify intent.",
            temporal_escalation_bound=3600,
        )


def test_active_inference_yield_invalid_temporal() -> None:
    """Enforce physical bounds on temporal escalation."""
    with pytest.raises(ValidationError):
        ActiveInferenceYield(
            event_id="evt_123",
            timestamp=1710000000.0,
            target_variable_urn="urn:coreason:variable:user_intent",
            epistemic_confidence_delta=0.5,
            canonical_projection="Need user to clarify intent.",
            temporal_escalation_bound=0,  # Invalid: <= 0
        )


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


def test_epistemic_promotion_event_routing() -> None:
    event_data = {
        "type": "epistemic_promotion",
        "event_id": "promo_123",
        "timestamp": 1234567890.0,
        "source_episodic_event_ids": ["obs_1", "obs_2", "obs_3"],
        "crystallized_semantic_node_id": "sem_node_42",
        "compression_ratio": 5.0,
    }

    adapter: TypeAdapter[AnyStateEvent] = TypeAdapter(AnyStateEvent)
    parsed_event = adapter.validate_python(event_data)

    assert isinstance(parsed_event, EpistemicPromotionEvent)
    assert parsed_event.event_id == "promo_123"
    assert parsed_event.source_episodic_event_ids == ["obs_1", "obs_2", "obs_3"]
    assert parsed_event.crystallized_semantic_node_id == "sem_node_42"
    assert parsed_event.compression_ratio == 5.0


def test_normative_drift_event_routing() -> None:
    event_data = {
        "type": "normative_drift",
        "event_id": "drift_456",
        "timestamp": 1234567890.0,
        "tripped_rule_id": "rule_789",
        "measured_semantic_drift": 0.95,
        "contradiction_proof_hash": "proof_hash_abc",
    }

    adapter: TypeAdapter[AnyStateEvent] = TypeAdapter(AnyStateEvent)
    parsed_event = adapter.validate_python(event_data)

    assert isinstance(parsed_event, NormativeDriftEvent)
    assert parsed_event.event_id == "drift_456"
    assert parsed_event.tripped_rule_id == "rule_789"
    assert parsed_event.measured_semantic_drift == 0.95
    assert parsed_event.contradiction_proof_hash == "proof_hash_abc"
