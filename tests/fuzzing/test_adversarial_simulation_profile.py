# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

from typing import Any

import hypothesis.strategies as st
import pytest
from hypothesis import HealthCheck, given, settings
from pydantic import ValidationError

from coreason_manifest.spec.ontology import AdversarialSimulationProfile

# 1. Strategy for generating deeply nested, potentially malformed JSON-RPC-like payloads
# Includes strings that deliberately push past the 100,000 limit, and keys past 255.
malformed_json_rpc_st = st.recursive(
    st.none()
    | st.booleans()
    | st.floats(allow_nan=False, allow_infinity=False)
    | st.integers()
    | st.text(max_size=150000),
    lambda children: (
        st.lists(children, max_size=20) | st.dictionaries(st.text(min_size=1, max_size=300), children, max_size=20)
    ),
    max_leaves=100,
)


@given(payload=malformed_json_rpc_st)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_adversarial_simulation_payload_fuzzing(payload: Any) -> None:
    """
    AGENT INSTRUCTION: Fuzz the AdversarialSimulationProfile with Chaos Engineering vectors.
    Mathematically prove that injecting massive, malformed, or deeply nested JSON-RPC payloads
    triggers the validation layer's hardware guillotines (ValidationError) without causing OOM or C-stack overflows.
    """
    try:
        # Attempt to instantiate the profile with the fuzzed synthetic payload
        profile = AdversarialSimulationProfile(
            simulation_cid="sim-chaos-001",
            target_node_cid="did:coreason:target-node:123",
            attack_vector="tool_poisoning",
            synthetic_payload=payload,
        )

        # If instantiation succeeds, assert the payload successfully fell within the strict hardware boundaries
        if isinstance(profile.synthetic_payload, str):
            assert len(profile.synthetic_payload) <= 100000
        elif isinstance(profile.synthetic_payload, dict):
            # Assert dictionary keys adhere to the 255-char StringConstraints limit
            for key in profile.synthetic_payload:
                assert len(key) <= 255

    except ValidationError:
        # Expected behavior: The validation layer correctly guillotines invalid schema/bounds
        pass


def test_adversarial_simulation_dictionary_bombing() -> None:
    """
    Chaos Engineering: Explicitly test extreme dictionary key limits and depth.
    """
    # Massive key exceeding 255 chars
    massive_key = "a" * 256
    payload: dict[str, Any] = {massive_key: "malicious_injection"}

    with pytest.raises(ValidationError, match="String should have at most 255 characters"):
        AdversarialSimulationProfile(
            simulation_cid="sim-chaos-002",
            target_node_cid="did:coreason:target-node:123",
            attack_vector="semantic_hijacking",
            synthetic_payload=payload,
        )


def test_adversarial_simulation_string_overflow() -> None:
    """
    Chaos Engineering: Throw string payload exceeding 100,000 characters limit.
    """
    massive_string = "a" * 100001

    with pytest.raises(ValidationError, match="Value should have at most 100000 items after validation"):
        AdversarialSimulationProfile(
            simulation_cid="sim-chaos-003",
            target_node_cid="did:coreason:target-node:123",
            attack_vector="data_exfiltration",
            synthetic_payload=massive_string,
        )


def test_adversarial_simulation_invalid_attack_vector() -> None:
    """
    Chaos Engineering: Verify that the Literal automaton traps invalid attack categories.
    """
    with pytest.raises(ValidationError, match="Input should be"):
        AdversarialSimulationProfile(
            simulation_cid="sim-chaos-004",
            target_node_cid="did:coreason:target-node:123",
            attack_vector="invalid_attack_vector",  # type: ignore
            synthetic_payload={"method": "destroy"},
        )
