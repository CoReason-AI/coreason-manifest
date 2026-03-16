# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import coreason_manifest.utils.algebra as algebra


def test_algebra_placeholder() -> None:
    assert True


def test_extract_webgl_entropy_seed_hash() -> None:
    from coreason_manifest.spec.ontology import (
        AdversarialEmulationProfile,
        AgentNodeProfile,
        EnvironmentalSpoofingProfile,
    )

    hash_str = "b" * 64
    spoofing = EnvironmentalSpoofingProfile(webgl_entropy_seed_hash=hash_str, canvas_noise_seed="seed")
    adv = AdversarialEmulationProfile(environmental_spoofing=spoofing)
    profile = AgentNodeProfile(description="test", adversarial_emulation=adv)

    res = algebra.extract_webgl_entropy_seed_hash(profile)
    assert res == hash_str

    empty_profile = AgentNodeProfile(description="test")
    assert algebra.extract_webgl_entropy_seed_hash(empty_profile) is None


def test_algebra_validate_payload() -> None:
    import json

    from coreason_manifest.spec.ontology import IntentClassificationReceipt, LatentSchemaInferenceIntent

    # Test valid schema inference
    payload = json.dumps({"target_buffer_id": "abc", "max_schema_depth": 5, "max_properties": 100})
    res = algebra.validate_payload("schema_inference", payload.encode())
    assert isinstance(res, LatentSchemaInferenceIntent)
    assert res.target_buffer_id == "abc"

    # Test valid intent classification
    payload2 = json.dumps(
        {
            "event_id": "chain-xyz",
            "timestamp": 123.4,
            "raw_input_string": "do something",
            "classified_intent": "task_intent",
            "confidence_score": 0.9,
        }
    )
    res2 = algebra.validate_payload("intent_classification", payload2.encode())
    assert isinstance(res2, IntentClassificationReceipt)
    assert res2.classified_intent == "task_intent"
