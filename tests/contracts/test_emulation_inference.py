# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    AdversarialEmulationProfile,
    AgentNodeProfile,
    EnvironmentalSpoofingProfile,
    IntentClassificationReceipt,
    KinematicNoiseProfile,
    LatentSchemaInferenceIntent,
    RoutingFrontierPolicy,
    SpatialCoordinateProfile,
    SpatialKinematicActionIntent,
)


def test_latent_schema_inference_intent() -> None:
    intent = LatentSchemaInferenceIntent(target_buffer_id="abc-123", max_schema_depth=5, max_properties=100)
    assert intent.target_buffer_id == "abc-123"
    assert intent.max_schema_depth == 5
    assert intent.max_properties == 100

    with pytest.raises(ValidationError):
        LatentSchemaInferenceIntent(
            target_buffer_id="abc-123",
            max_schema_depth=11,  # out of bounds (> 10)
            max_properties=100,
        )


def test_intent_classification_receipt() -> None:
    receipt = IntentClassificationReceipt(
        event_id="chain-xyz",
        timestamp=123.4,
        raw_input_string="do something",
        classified_intent="task_intent",
        confidence_score=0.9,
    )
    assert receipt.classified_intent == "task_intent"

    with pytest.raises(ValidationError):
        IntentClassificationReceipt(
            event_id="chain-xyz",
            timestamp=123.4,
            raw_input_string="do something",
            classified_intent="task_intent",
            confidence_score=1.5,  # out of bounds (> 1.0)
        )


def test_kinematic_noise_profile() -> None:
    profile = KinematicNoiseProfile(pink_noise_amplitude=0.5, frequency_hz=60.0)
    assert profile.pink_noise_amplitude == 0.5

    with pytest.raises(ValidationError):
        KinematicNoiseProfile(pink_noise_amplitude=1.5, frequency_hz=60.0)


def test_environmental_spoofing_profile() -> None:
    hash_str = "a" * 64
    profile = EnvironmentalSpoofingProfile(webgl_entropy_seed_hash=hash_str, canvas_noise_seed="seed1")
    assert profile.webgl_entropy_seed_hash == hash_str

    with pytest.raises(ValidationError):
        EnvironmentalSpoofingProfile(webgl_entropy_seed_hash="invalid-hash", canvas_noise_seed="seed1")


def test_adversarial_emulation_profile() -> None:
    noise = KinematicNoiseProfile(pink_noise_amplitude=0.5, frequency_hz=60.0)
    spoofing = EnvironmentalSpoofingProfile(webgl_entropy_seed_hash="a" * 64, canvas_noise_seed="seed1")
    profile = AdversarialEmulationProfile(kinematic_noise=noise, environmental_spoofing=spoofing)
    assert profile.kinematic_noise is not None
    assert profile.environmental_spoofing is not None


def test_spatial_kinematic_action_intent() -> None:
    coord = SpatialCoordinateProfile(x=0.5, y=0.5)
    noise = KinematicNoiseProfile(pink_noise_amplitude=0.5, frequency_hz=60.0)
    intent = SpatialKinematicActionIntent(
        action_type="click",
        target_coordinate=coord,
        trajectory_duration_ms=1000,
        bezier_control_points=[coord, coord],
        expected_visual_concept="button",
        noise_profile=noise,
    )
    assert intent.action_type == "click"
    assert intent.noise_profile is not None


def test_agent_node_profile() -> None:
    compute_frontier = RoutingFrontierPolicy(
        max_latency_ms=1000,
        max_cost_magnitude_per_token=10,
        min_capability_score=0.8,
        tradeoff_preference="latency_optimized",
    )
    noise = KinematicNoiseProfile(pink_noise_amplitude=0.5, frequency_hz=60.0)
    spoofing = EnvironmentalSpoofingProfile(webgl_entropy_seed_hash="a" * 64, canvas_noise_seed="seed1")
    adversarial = AdversarialEmulationProfile(kinematic_noise=noise, environmental_spoofing=spoofing)
    profile = AgentNodeProfile(
        description="A test agent profile", compute_frontier=compute_frontier, adversarial_emulation=adversarial
    )
    assert profile.type == "agent"
    assert profile.adversarial_emulation is not None
