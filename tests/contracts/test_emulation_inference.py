# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

"""
Strict behavioral contract tests for the Epic 8 Emulation & Inference Frontier classes:
KinematicNoiseProfile, EnvironmentalSpoofingProfile, AdversarialEmulationProfile,
LatentSchemaInferenceIntent, IntentClassificationReceipt, and AgentNodeProfile emulation integration.
"""

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    AdversarialEmulationProfile,
    AgentNodeProfile,
    EnvironmentalSpoofingProfile,
    IntentClassificationReceipt,
    KinematicNoiseProfile,
    LatentSchemaInferenceIntent,
)

# ---------------------------------------------------------------------------
# 1. KinematicNoiseProfile — Stochastic Trajectory Perturbation Bounds
# ---------------------------------------------------------------------------


class TestKinematicNoiseProfile:
    """Mathematical boundary proofs for pointer trajectory noise injection."""

    def test_valid_instantiation(self) -> None:
        profile = KinematicNoiseProfile(
            noise_type="pink",
            pink_noise_amplitude=0.5,
            frequency_exponent=1.0,
        )
        assert profile.noise_type == "pink"
        assert profile.pink_noise_amplitude == 0.5
        assert profile.frequency_exponent == 1.0
        assert profile.velocity_profile == "minimum_jerk"
        assert profile.target_overshoot_radius_pixels == 0
        assert profile.hick_hyman_dwell_time_ms == 0

    def test_valid_brownian_noise(self) -> None:
        profile = KinematicNoiseProfile(
            noise_type="brownian",
            pink_noise_amplitude=0.0,
            frequency_exponent=2.0,
        )
        assert profile.noise_type == "brownian"

    def test_valid_gaussian_noise(self) -> None:
        profile = KinematicNoiseProfile(
            noise_type="gaussian",
            pink_noise_amplitude=1.0,
            frequency_exponent=0.0,
        )
        assert profile.noise_type == "gaussian"

    def test_pink_noise_amplitude_rejects_above_1(self) -> None:
        with pytest.raises(ValidationError, match=r"Input should be less than or equal to 1"):
            KinematicNoiseProfile(
                noise_type="pink",
                pink_noise_amplitude=1.1,
                frequency_exponent=1.0,
            )

    def test_pink_noise_amplitude_rejects_below_0(self) -> None:
        with pytest.raises(ValidationError, match=r"Input should be greater than or equal to 0"):
            KinematicNoiseProfile(
                noise_type="pink",
                pink_noise_amplitude=-0.1,
                frequency_exponent=1.0,
            )

    def test_frequency_exponent_rejects_above_5(self) -> None:
        with pytest.raises(ValidationError, match=r"Input should be less than or equal to 5"):
            KinematicNoiseProfile(
                noise_type="pink",
                pink_noise_amplitude=0.5,
                frequency_exponent=5.1,
            )

    def test_frequency_exponent_rejects_below_0(self) -> None:
        with pytest.raises(ValidationError, match=r"Input should be greater than or equal to 0"):
            KinematicNoiseProfile(
                noise_type="pink",
                pink_noise_amplitude=0.5,
                frequency_exponent=-0.1,
            )

    def test_invalid_noise_type_rejected(self) -> None:
        with pytest.raises(ValidationError, match=r"Input should be"):
            KinematicNoiseProfile(
                noise_type="white",  # type: ignore[arg-type]
                pink_noise_amplitude=0.5,
                frequency_exponent=1.0,
            )

    def test_boundary_values_accepted(self) -> None:
        """Prove edge cases at exact mathematical boundaries are accepted."""
        profile = KinematicNoiseProfile(
            noise_type="pink",
            pink_noise_amplitude=0.0,
            frequency_exponent=5.0,
        )
        assert profile.pink_noise_amplitude == 0.0
        assert profile.frequency_exponent == 5.0

    def test_velocity_profile_accepts_valid_literals(self) -> None:
        for vp in ("minimum_jerk", "constant", "fractional_brownian"):
            profile = KinematicNoiseProfile(
                noise_type="pink",
                pink_noise_amplitude=0.5,
                frequency_exponent=1.0,
                velocity_profile=vp,
            )
            assert profile.velocity_profile == vp

    def test_velocity_profile_rejects_invalid(self) -> None:
        with pytest.raises(ValidationError, match=r"Input should be"):
            KinematicNoiseProfile(
                noise_type="pink",
                pink_noise_amplitude=0.5,
                frequency_exponent=1.0,
                velocity_profile="linear",  # type: ignore[arg-type]
            )

    def test_target_overshoot_rejects_below_0(self) -> None:
        with pytest.raises(ValidationError, match=r"Input should be greater than or equal to 0"):
            KinematicNoiseProfile(
                noise_type="pink",
                pink_noise_amplitude=0.5,
                frequency_exponent=1.0,
                target_overshoot_radius_pixels=-1,
            )

    def test_target_overshoot_rejects_above_5000(self) -> None:
        with pytest.raises(ValidationError, match=r"Input should be less than or equal to 5000"):
            KinematicNoiseProfile(
                noise_type="pink",
                pink_noise_amplitude=0.5,
                frequency_exponent=1.0,
                target_overshoot_radius_pixels=5001,
            )

    def test_target_overshoot_boundary_values(self) -> None:
        p0 = KinematicNoiseProfile(
            noise_type="pink",
            pink_noise_amplitude=0.5,
            frequency_exponent=1.0,
            target_overshoot_radius_pixels=0,
        )
        assert p0.target_overshoot_radius_pixels == 0

        p5k = KinematicNoiseProfile(
            noise_type="pink",
            pink_noise_amplitude=0.5,
            frequency_exponent=1.0,
            target_overshoot_radius_pixels=5000,
        )
        assert p5k.target_overshoot_radius_pixels == 5000

    def test_hick_hyman_dwell_time_rejects_below_0(self) -> None:
        with pytest.raises(ValidationError, match=r"Input should be greater than or equal to 0"):
            KinematicNoiseProfile(
                noise_type="pink",
                pink_noise_amplitude=0.5,
                frequency_exponent=1.0,
                hick_hyman_dwell_time_ms=-1,
            )

    def test_hick_hyman_dwell_time_rejects_above_86400000(self) -> None:
        with pytest.raises(ValidationError, match=r"Input should be less than or equal to 86400000"):
            KinematicNoiseProfile(
                noise_type="pink",
                pink_noise_amplitude=0.5,
                frequency_exponent=1.0,
                hick_hyman_dwell_time_ms=86400001,
            )

    def test_hick_hyman_dwell_time_boundary_values(self) -> None:
        p0 = KinematicNoiseProfile(
            noise_type="pink",
            pink_noise_amplitude=0.5,
            frequency_exponent=1.0,
            hick_hyman_dwell_time_ms=0,
        )
        assert p0.hick_hyman_dwell_time_ms == 0

        p_max = KinematicNoiseProfile(
            noise_type="pink",
            pink_noise_amplitude=0.5,
            frequency_exponent=1.0,
            hick_hyman_dwell_time_ms=86400000,
        )
        assert p_max.hick_hyman_dwell_time_ms == 86400000


# ---------------------------------------------------------------------------
# 2. EnvironmentalSpoofingProfile — Browser Fingerprint Entropy Bounds
# ---------------------------------------------------------------------------


class TestEnvironmentalSpoofingProfile:
    """Mathematical boundary proofs for browser fingerprint spoofing geometry."""

    def test_valid_instantiation(self) -> None:
        profile = EnvironmentalSpoofingProfile(
            webgl_entropy_seed_hash="abc123",
            user_agent_template="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            timezone_offset_minutes=-300,
            screen_resolution_width=1920,
            screen_resolution_height=1080,
        )
        assert profile.webgl_entropy_seed_hash == "abc123"
        assert profile.timezone_offset_minutes == -300
        assert profile.screen_resolution_width == 1920
        assert profile.screen_resolution_height == 1080
        assert profile.tls_cipher_permutation == "chrome_windows"
        assert profile.hardware_concurrency_mask == 8

    def test_timezone_offset_rejects_below_negative_720(self) -> None:
        with pytest.raises(ValidationError, match=r"Input should be greater than or equal to -720"):
            EnvironmentalSpoofingProfile(
                webgl_entropy_seed_hash="abc123",
                user_agent_template="Mozilla/5.0",
                timezone_offset_minutes=-721,
                screen_resolution_width=1920,
                screen_resolution_height=1080,
            )

    def test_timezone_offset_rejects_above_840(self) -> None:
        with pytest.raises(ValidationError, match=r"Input should be less than or equal to 840"):
            EnvironmentalSpoofingProfile(
                webgl_entropy_seed_hash="abc123",
                user_agent_template="Mozilla/5.0",
                timezone_offset_minutes=841,
                screen_resolution_width=1920,
                screen_resolution_height=1080,
            )

    def test_webgl_hash_pattern_rejects_invalid_chars(self) -> None:
        with pytest.raises(ValidationError, match=r"String should match pattern"):
            EnvironmentalSpoofingProfile(
                webgl_entropy_seed_hash="invalid hash with spaces!",
                user_agent_template="Mozilla/5.0",
                timezone_offset_minutes=0,
                screen_resolution_width=1920,
                screen_resolution_height=1080,
            )

    def test_webgl_hash_rejects_empty(self) -> None:
        with pytest.raises(ValidationError):
            EnvironmentalSpoofingProfile(
                webgl_entropy_seed_hash="",
                user_agent_template="Mozilla/5.0",
                timezone_offset_minutes=0,
                screen_resolution_width=1920,
                screen_resolution_height=1080,
            )

    def test_screen_resolution_rejects_zero(self) -> None:
        with pytest.raises(ValidationError, match=r"Input should be greater than or equal to 1"):
            EnvironmentalSpoofingProfile(
                webgl_entropy_seed_hash="abc123",
                user_agent_template="Mozilla/5.0",
                timezone_offset_minutes=0,
                screen_resolution_width=0,
                screen_resolution_height=1080,
            )

    def test_screen_resolution_rejects_above_15360(self) -> None:
        with pytest.raises(ValidationError, match=r"Input should be less than or equal to 15360"):
            EnvironmentalSpoofingProfile(
                webgl_entropy_seed_hash="abc123",
                user_agent_template="Mozilla/5.0",
                timezone_offset_minutes=0,
                screen_resolution_width=1920,
                screen_resolution_height=15361,
            )

    def test_boundary_timezone_values(self) -> None:
        """Prove exact boundary values are accepted."""
        profile_min = EnvironmentalSpoofingProfile(
            webgl_entropy_seed_hash="abc123",
            user_agent_template="Mozilla/5.0",
            timezone_offset_minutes=-720,
            screen_resolution_width=1,
            screen_resolution_height=1,
        )
        assert profile_min.timezone_offset_minutes == -720

        profile_max = EnvironmentalSpoofingProfile(
            webgl_entropy_seed_hash="abc123",
            user_agent_template="Mozilla/5.0",
            timezone_offset_minutes=840,
            screen_resolution_width=15360,
            screen_resolution_height=15360,
        )
        assert profile_max.timezone_offset_minutes == 840

    def test_tls_cipher_permutation_accepts_valid_literals(self) -> None:
        for cipher in ("chrome_windows", "safari_macos", "firefox_macos", "android_webview"):
            profile = EnvironmentalSpoofingProfile(
                webgl_entropy_seed_hash="abc123",
                user_agent_template="Mozilla/5.0",
                timezone_offset_minutes=0,
                screen_resolution_width=1920,
                screen_resolution_height=1080,
                tls_cipher_permutation=cipher,
            )
            assert profile.tls_cipher_permutation == cipher

    def test_tls_cipher_permutation_rejects_invalid(self) -> None:
        with pytest.raises(ValidationError, match=r"Input should be"):
            EnvironmentalSpoofingProfile(
                webgl_entropy_seed_hash="abc123",
                user_agent_template="Mozilla/5.0",
                timezone_offset_minutes=0,
                screen_resolution_width=1920,
                screen_resolution_height=1080,
                tls_cipher_permutation="edge_windows",  # type: ignore[arg-type]
            )

    def test_hardware_concurrency_rejects_zero(self) -> None:
        with pytest.raises(ValidationError, match=r"Input should be greater than 0"):
            EnvironmentalSpoofingProfile(
                webgl_entropy_seed_hash="abc123",
                user_agent_template="Mozilla/5.0",
                timezone_offset_minutes=0,
                screen_resolution_width=1920,
                screen_resolution_height=1080,
                hardware_concurrency_mask=0,
            )

    def test_hardware_concurrency_rejects_above_256(self) -> None:
        with pytest.raises(ValidationError, match=r"Input should be less than or equal to 256"):
            EnvironmentalSpoofingProfile(
                webgl_entropy_seed_hash="abc123",
                user_agent_template="Mozilla/5.0",
                timezone_offset_minutes=0,
                screen_resolution_width=1920,
                screen_resolution_height=1080,
                hardware_concurrency_mask=257,
            )

    def test_hardware_concurrency_boundary_values(self) -> None:
        p1 = EnvironmentalSpoofingProfile(
            webgl_entropy_seed_hash="abc123",
            user_agent_template="Mozilla/5.0",
            timezone_offset_minutes=0,
            screen_resolution_width=1920,
            screen_resolution_height=1080,
            hardware_concurrency_mask=1,
        )
        assert p1.hardware_concurrency_mask == 1

        p256 = EnvironmentalSpoofingProfile(
            webgl_entropy_seed_hash="abc123",
            user_agent_template="Mozilla/5.0",
            timezone_offset_minutes=0,
            screen_resolution_width=1920,
            screen_resolution_height=1080,
            hardware_concurrency_mask=256,
        )
        assert p256.hardware_concurrency_mask == 256


# ---------------------------------------------------------------------------
# 3. AdversarialEmulationProfile — Composite Emulation Geometry Bounds
# ---------------------------------------------------------------------------


class TestAdversarialEmulationProfile:
    """Mathematical boundary proofs for the composite emulation manifold."""

    def test_valid_with_all_subprofiles(self) -> None:
        noise = KinematicNoiseProfile(
            noise_type="pink",
            pink_noise_amplitude=0.3,
            frequency_exponent=1.0,
        )
        spoofing = EnvironmentalSpoofingProfile(
            webgl_entropy_seed_hash="seed123",
            user_agent_template="Mozilla/5.0",
            timezone_offset_minutes=0,
            screen_resolution_width=1920,
            screen_resolution_height=1080,
        )
        profile = AdversarialEmulationProfile(
            kinematic_noise=noise,
            environmental_spoofing=spoofing,
            emulation_fidelity_target=0.95,
        )
        assert profile.kinematic_noise is not None
        assert profile.environmental_spoofing is not None
        assert profile.emulation_fidelity_target == 0.95

    def test_valid_with_none_subprofiles(self) -> None:
        profile = AdversarialEmulationProfile(
            emulation_fidelity_target=0.5,
        )
        assert profile.kinematic_noise is None
        assert profile.environmental_spoofing is None
        assert profile.generative_persona == "fast_expert"

    def test_emulation_fidelity_target_rejects_above_1(self) -> None:
        with pytest.raises(ValidationError, match=r"Input should be less than or equal to 1"):
            AdversarialEmulationProfile(emulation_fidelity_target=1.1)

    def test_emulation_fidelity_target_rejects_below_0(self) -> None:
        with pytest.raises(ValidationError, match=r"Input should be greater than or equal to 0"):
            AdversarialEmulationProfile(emulation_fidelity_target=-0.1)

    def test_boundary_fidelity_values(self) -> None:
        profile_zero = AdversarialEmulationProfile(emulation_fidelity_target=0.0)
        assert profile_zero.emulation_fidelity_target == 0.0

        profile_one = AdversarialEmulationProfile(emulation_fidelity_target=1.0)
        assert profile_one.emulation_fidelity_target == 1.0

    def test_generative_persona_accepts_valid_literals(self) -> None:
        for persona in ("hesitant_novice", "fast_expert", "distracted_browser"):
            profile = AdversarialEmulationProfile(
                emulation_fidelity_target=0.5,
                generative_persona=persona,
            )
            assert profile.generative_persona == persona

    def test_generative_persona_rejects_invalid(self) -> None:
        with pytest.raises(ValidationError, match=r"Input should be"):
            AdversarialEmulationProfile(
                emulation_fidelity_target=0.5,
                generative_persona="casual_user",  # type: ignore[arg-type]
            )


# ---------------------------------------------------------------------------
# 4. LatentSchemaInferenceIntent — Schema Depth & Properties Bounds
# ---------------------------------------------------------------------------


class TestLatentSchemaInferenceIntent:
    """Mathematical boundary proofs for unstructured payload schema deduction."""

    def test_valid_instantiation(self) -> None:
        intent = LatentSchemaInferenceIntent(
            target_buffer_id="buffer.001",
            max_schema_depth=5,
            max_properties=100,
        )
        assert intent.type == "latent_schema_inference"
        assert intent.max_schema_depth == 5
        assert intent.max_properties == 100
        assert intent.require_strict_validation is True

    def test_max_schema_depth_rejects_above_10(self) -> None:
        with pytest.raises(ValidationError, match=r"Input should be less than or equal to 10"):
            LatentSchemaInferenceIntent(
                target_buffer_id="buffer.001",
                max_schema_depth=11,
                max_properties=100,
            )

    def test_max_schema_depth_rejects_below_1(self) -> None:
        with pytest.raises(ValidationError, match=r"Input should be greater than or equal to 1"):
            LatentSchemaInferenceIntent(
                target_buffer_id="buffer.001",
                max_schema_depth=0,
                max_properties=100,
            )

    def test_max_properties_rejects_above_1000(self) -> None:
        with pytest.raises(ValidationError, match=r"Input should be less than or equal to 1000"):
            LatentSchemaInferenceIntent(
                target_buffer_id="buffer.001",
                max_schema_depth=5,
                max_properties=1001,
            )

    def test_max_properties_rejects_below_1(self) -> None:
        with pytest.raises(ValidationError, match=r"Input should be greater than or equal to 1"):
            LatentSchemaInferenceIntent(
                target_buffer_id="buffer.001",
                max_schema_depth=5,
                max_properties=0,
            )

    def test_boundary_values_accepted(self) -> None:
        intent = LatentSchemaInferenceIntent(
            target_buffer_id="buffer.001",
            max_schema_depth=10,
            max_properties=1000,
        )
        assert intent.max_schema_depth == 10
        assert intent.max_properties == 1000

        intent_min = LatentSchemaInferenceIntent(
            target_buffer_id="buffer.001",
            max_schema_depth=1,
            max_properties=1,
        )
        assert intent_min.max_schema_depth == 1
        assert intent_min.max_properties == 1

    def test_target_buffer_id_rejects_invalid_pattern(self) -> None:
        with pytest.raises(ValidationError, match=r"String should match pattern"):
            LatentSchemaInferenceIntent(
                target_buffer_id="invalid buffer id!",
                max_schema_depth=5,
                max_properties=100,
            )


# ---------------------------------------------------------------------------
# 5. IntentClassificationReceipt — Confidence Score Bounds
# ---------------------------------------------------------------------------


class TestIntentClassificationReceipt:
    """Mathematical boundary proofs for intent classification receipts."""

    def test_valid_instantiation(self) -> None:
        receipt = IntentClassificationReceipt(
            event_id="evt_001",
            timestamp=1234567890.0,
            raw_input_string="Please summarize this document.",
            classified_intent="summarization",
            confidence_score=0.95,
        )
        assert receipt.type == "intent_classification"
        assert receipt.classified_intent == "summarization"
        assert receipt.confidence_score == 0.95
        assert receipt.routing_policy_id is None

    def test_confidence_score_rejects_above_1(self) -> None:
        with pytest.raises(ValidationError, match=r"Input should be less than or equal to 1"):
            IntentClassificationReceipt(
                event_id="evt_001",
                timestamp=1234567890.0,
                raw_input_string="test",
                classified_intent="test",
                confidence_score=1.1,
            )

    def test_confidence_score_rejects_below_0(self) -> None:
        with pytest.raises(ValidationError, match=r"Input should be greater than or equal to 0"):
            IntentClassificationReceipt(
                event_id="evt_001",
                timestamp=1234567890.0,
                raw_input_string="test",
                classified_intent="test",
                confidence_score=-0.1,
            )

    def test_boundary_confidence_values(self) -> None:
        receipt_zero = IntentClassificationReceipt(
            event_id="evt_001",
            timestamp=1234567890.0,
            raw_input_string="test",
            classified_intent="test",
            confidence_score=0.0,
        )
        assert receipt_zero.confidence_score == 0.0

        receipt_one = IntentClassificationReceipt(
            event_id="evt_002",
            timestamp=1234567890.0,
            raw_input_string="test",
            classified_intent="test",
            confidence_score=1.0,
        )
        assert receipt_one.confidence_score == 1.0

    def test_with_routing_policy_id(self) -> None:
        receipt = IntentClassificationReceipt(
            event_id="evt_001",
            timestamp=1234567890.0,
            raw_input_string="test input",
            classified_intent="code_generation",
            confidence_score=0.85,
            routing_policy_id="policy.001",
        )
        assert receipt.routing_policy_id == "policy.001"


# ---------------------------------------------------------------------------
# 6. AgentNodeProfile — Emulation Field Integration
# ---------------------------------------------------------------------------


class TestAgentNodeProfileEmulation:
    """Prove the emulation_profile field integrates correctly into AgentNodeProfile."""

    def test_emulation_profile_default_none(self) -> None:
        agent = AgentNodeProfile(description="Test agent node")
        assert agent.emulation_profile is None

    def test_emulation_profile_accepts_adversarial_emulation(self) -> None:
        noise = KinematicNoiseProfile(
            noise_type="brownian",
            pink_noise_amplitude=0.7,
            frequency_exponent=2.0,
        )
        emulation = AdversarialEmulationProfile(
            kinematic_noise=noise,
            emulation_fidelity_target=0.9,
        )
        agent = AgentNodeProfile(
            description="Agent with emulation",
            emulation_profile=emulation,
        )
        assert agent.emulation_profile is not None
        assert agent.emulation_profile.kinematic_noise is not None
        assert agent.emulation_profile.kinematic_noise.noise_type == "brownian"
        assert agent.emulation_profile.emulation_fidelity_target == 0.9
