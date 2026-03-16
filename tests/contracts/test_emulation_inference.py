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
    SpatialCoordinateProfile,
    SpatialKinematicActionIntent,
)
from coreason_manifest.utils.algebra import extract_webgl_entropy_seed


def test_kinematic_noise_profile_bounds():
    # Valid
    p = KinematicNoiseProfile(pink_noise_amplitude=0.5, fitts_law_variance_ms=100)
    assert p.pink_noise_amplitude == 0.5

    # Invalid amplitude (too high)
    with pytest.raises(ValidationError):
        KinematicNoiseProfile(pink_noise_amplitude=1.5, fitts_law_variance_ms=100)

    # Invalid amplitude (too low)
    with pytest.raises(ValidationError):
        KinematicNoiseProfile(pink_noise_amplitude=-0.1, fitts_law_variance_ms=100)

    # Invalid variance (too high)
    with pytest.raises(ValidationError):
        KinematicNoiseProfile(pink_noise_amplitude=0.5, fitts_law_variance_ms=10001)


def test_environmental_spoofing_profile_bounds():
    # Valid
    p = EnvironmentalSpoofingProfile(
        screen_resolution=(1920, 1080),
        user_agent_override="Mozilla/5.0",
        webgl_entropy_seed_hash="a" * 64,
    )
    assert p.screen_resolution == (1920, 1080)

    # Invalid hash length
    with pytest.raises(ValidationError):
        EnvironmentalSpoofingProfile(
            screen_resolution=(1920, 1080), user_agent_override="Mozilla", webgl_entropy_seed_hash="short"
        )


def test_adversarial_emulation_profile():
    p = AdversarialEmulationProfile(
        kinematic_noise=KinematicNoiseProfile(pink_noise_amplitude=0.5, fitts_law_variance_ms=100),
        environmental_spoof=EnvironmentalSpoofingProfile(
            screen_resolution=(1920, 1080),
            user_agent_override="Mozilla/5.0",
        ),
        rotation_ttl_seconds=3600,
    )
    assert p.rotation_ttl_seconds == 3600

    # Invalid TTL
    with pytest.raises(ValidationError):
        AdversarialEmulationProfile(rotation_ttl_seconds=86401)


def test_latent_schema_inference_intent():
    i = LatentSchemaInferenceIntent(
        target_buffer_id="buffer-1",
        max_schema_depth=5,
        max_properties=100,
    )
    assert i.max_schema_depth == 5

    with pytest.raises(ValidationError):
        LatentSchemaInferenceIntent(
            target_buffer_id="buffer-1",
            max_schema_depth=11,  # exceeds 10
            max_properties=100,
        )

    with pytest.raises(ValidationError):
        LatentSchemaInferenceIntent(
            target_buffer_id="buffer-1",
            max_schema_depth=5,
            max_properties=1001,  # exceeds 1000
        )


def test_intent_classification_receipt():
    r = IntentClassificationReceipt(
        event_id="receipt-1",
        timestamp=123.0,
        raw_input_string="hello world",
        classified_intent="greeting",
        confidence_score=0.95,
    )
    assert r.confidence_score == 0.95

    with pytest.raises(ValidationError):
        IntentClassificationReceipt(
            event_id="receipt-1",
            timestamp=123.0,
            raw_input_string="hello world",
            classified_intent="greeting",
            confidence_score=1.1,  # exceeds 1.0
        )


def test_extract_webgl_entropy_seed():
    agent = AgentNodeProfile(
        description="Test Agent",
        adversarial_emulation=AdversarialEmulationProfile(
            rotation_ttl_seconds=3600,
            environmental_spoof=EnvironmentalSpoofingProfile(
                screen_resolution=(1920, 1080), user_agent_override="Mozilla", webgl_entropy_seed_hash="b" * 64
            ),
        ),
    )
    assert extract_webgl_entropy_seed(agent) == "b" * 64

    agent2 = AgentNodeProfile(description="Test Agent 2")
    assert extract_webgl_entropy_seed(agent2) is None


def test_spatial_kinematic_action_intent_noise():
    i = SpatialKinematicActionIntent(
        action_type="click",
        target_coordinate=SpatialCoordinateProfile(x=0.5, y=0.5),
        noise_override=KinematicNoiseProfile(pink_noise_amplitude=0.1, fitts_law_variance_ms=50),
    )
    assert i.noise_override is not None
    assert i.noise_override.pink_noise_amplitude == 0.1
