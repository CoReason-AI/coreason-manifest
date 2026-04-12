# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

from typing import Any, cast

import hypothesis.strategies as st
import pytest
from hypothesis import HealthCheck, given, settings
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    JsonPrimitiveState,
    StateHydrationManifest,
    _validate_payload_bounds,
)

# 1. Define the Valid Mathematical Space
valid_json_st = st.recursive(
    st.none()
    | st.booleans()
    | st.floats(allow_nan=False, allow_infinity=False)
    | st.integers()
    | st.text(max_size=9999),
    lambda children: (
        st.lists(children, max_size=999) | st.dictionaries(st.text(min_size=1, max_size=9999), children, max_size=99)
    ),
    max_leaves=50,
)


@given(payload=valid_json_st)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_payload_bounds_fuzz_valid_space(payload: Any) -> None:
    """
    AGENT INSTRUCTION: Fuzz the valid structural space using hypothesis.
    Mathematically prove that any permutation falling UNDER the tripwires is strictly accepted.
    """
    # 1. Direct Function Fuzzing
    result = _validate_payload_bounds(payload)
    assert result == payload

    # 2. Pydantic Manifest Projection
    if isinstance(payload, dict):
        manifest = StateHydrationManifest(
            epistemic_coordinate="session-123",
            crystallized_ledger_cids=["a" * 64],
            working_context_variables=payload,
            max_retained_tokens=4000,
        )
        assert manifest.working_context_variables == payload


def test_payload_bounds_recursion_depth_exceeded() -> None:
    # Create a nested dictionary of depth 11 (max is 10)
    nested_payload: Any = "leaf"
    for _ in range(11):
        nested_payload = {"key": nested_payload}

    with pytest.raises(ValueError, match="Payload exceeds maximum recursion depth of 10"):
        _validate_payload_bounds(nested_payload)


def test_payload_bounds_dict_keys_exceeded() -> None:
    # Create a dictionary with 10001 keys to exceed the 10000 node volume limit
    large_dict: dict[str, Any] = {f"key_{i}": i for i in range(10001)}

    with pytest.raises(ValueError, match="Payload volume exceeds absolute hardware limit of 10000 nodes"):
        _validate_payload_bounds(cast("JsonPrimitiveState", large_dict))


def test_payload_bounds_list_items_exceeded() -> None:
    # Create a list with 10001 items to exceed the 10000 node volume limit
    large_list: list[Any] = list(range(10001))

    with pytest.raises(ValueError, match="Payload volume exceeds absolute hardware limit of 10000 nodes"):
        _validate_payload_bounds(cast("JsonPrimitiveState", large_list))


def test_payload_bounds_string_length_exceeded() -> None:
    # Create a string of length 10001 (max is 10000)
    large_string = "a" * 10001

    with pytest.raises(ValueError, match="String exceeds max length of 10000"):
        _validate_payload_bounds(large_string)


def test_payload_bounds_dict_key_length_exceeded() -> None:
    # Create a dictionary with a key of length 10001 (max string length is 10000)
    large_key = "a" * 10001
    bad_dict: dict[str, Any] = {large_key: "value"}

    with pytest.raises(ValueError, match="Dictionary key exceeds max string length of 10000"):
        _validate_payload_bounds(cast("JsonPrimitiveState", bad_dict))


def test_payload_bounds_dict_key_not_string() -> None:
    # JSON standard allows only string keys for dictionaries
    bad_dict: dict[Any, Any] = {42: "value"}

    with pytest.raises(ValueError, match="Dictionary keys must be strings"):
        _validate_payload_bounds(cast("JsonPrimitiveState", bad_dict))


def test_payload_bounds_invalid_type() -> None:
    # A non-JSON primitive object should fail validation
    class CustomObj:
        pass

    with pytest.raises(ValueError, match="Payload value must be a valid JSON primitive, got CustomObj"):
        _validate_payload_bounds(CustomObj())  # type: ignore


def test_payload_bounds_invalid_type_nested() -> None:
    # A non-JSON primitive object deeply nested should fail validation
    class CustomObj:
        pass

    payload = {"valid": 1, "invalid": [1, 2, CustomObj()]}

    with pytest.raises(ValueError, match="Payload value must be a valid JSON primitive, got CustomObj"):
        _validate_payload_bounds(payload)  # type: ignore


def test_state_vector_memory_bounds() -> None:
    import pytest

    from coreason_manifest.spec.ontology import StateVectorProfile

    s = StateVectorProfile(mutable_matrix={"test": "abc"}, immutable_matrix={"rules": "abc"})
    assert s.mutable_matrix == {"test": "abc"}
    assert s.immutable_matrix == {"rules": "abc"}

    huge_dict: dict[str, Any] = {}
    for i in range(10001):
        huge_dict[f"key_{i}"] = i

    with pytest.raises(ValidationError) as exc_info:
        StateVectorProfile(mutable_matrix=huge_dict)
    assert "Payload volume exceeds absolute hardware limit" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        StateVectorProfile(immutable_matrix=huge_dict)
    assert "Payload volume exceeds absolute hardware limit" in str(exc_info.value)


def test_neurosymbolic_inference_request_requires_contextualized_entity() -> None:
    import pytest

    from coreason_manifest.spec.ontology import NeurosymbolicInferenceIntent

    # Instantiating with bare string instead of ContextualizedSourceState
    with pytest.raises(ValidationError) as exc_info:
        NeurosymbolicInferenceIntent(
            source_entity="Amoxicillin 500mg",  # type: ignore
            fidelity_receipt={  # type: ignore
                "contextual_completeness_score": 0.9,
                "surrounding_token_density": 10,
            },
            uncertainty_profile={  # type: ignore
                "aleatoric_noise_ratio": 0.05,
                "epistemic_knowledge_gap": 0.2,
                "semantic_consistency_score": 0.9,
                "requires_abductive_escalation": False,
            },
            sla={  # type: ignore
                "strict_probability_retention": True,
                "max_allowed_entropy_loss": 0.5,
                "required_grounding_density": "dense",
                "minimum_fidelity_threshold": 0.5,
            },
        )
    assert "Input should be a valid dictionary or instance of ContextualizedSourceState" in str(exc_info.value)


def test_constitutional_amendment_intent_payload_bounds() -> None:
    from coreason_manifest.spec.ontology import ConstitutionalAmendmentIntent

    # Valid payload
    intent = ConstitutionalAmendmentIntent(
        drift_event_cid="drift:123",
        proposed_patch={"op": "add", "path": "/policy", "value": "updated"},
        justification="Valid patch justification",
    )
    assert intent.proposed_patch == {"op": "add", "path": "/policy", "value": "updated"}

    # Invalid payload (exceeds depth)
    nested_payload: Any = "leaf"
    for _ in range(11):
        nested_payload = {"key": nested_payload}

    with pytest.raises(ValidationError) as exc_info:
        ConstitutionalAmendmentIntent(
            drift_event_cid="drift:123", proposed_patch=nested_payload, justification="Valid patch justification"
        )
    assert "Payload exceeds maximum recursion depth of 10" in str(exc_info.value)


def test_span_event_payload_bounds() -> None:
    from coreason_manifest.spec.ontology import SpanEvent

    # Valid payload
    event = SpanEvent(name="test_event", timestamp_unix_nano=1678888888000000000, attributes={"key": "value"})
    assert event.attributes == {"key": "value"}

    # Invalid payload (exceeds depth)
    nested_payload: Any = "leaf"
    for _ in range(11):
        nested_payload = {"key": nested_payload}

    with pytest.raises(ValidationError) as exc_info:
        SpanEvent(name="test_event", timestamp_unix_nano=1678888888000000000, attributes=nested_payload)
    assert "Payload exceeds maximum recursion depth of 10" in str(exc_info.value)


def test_ontology_discovery_intent_payload_bounds() -> None:
    from coreason_manifest.spec.ontology import OntologyDiscoveryIntent

    # Valid payload
    intent = OntologyDiscoveryIntent(
        jsonrpc="2.0",
        method="query_registry",
        id="req-123",
        target_registry_uri="https://www.ebi.ac.uk/ols4/api",  # type: ignore
        query_concept_cid="SCTID:12345",
        expected_response_schema={"type": "object"},
    )
    assert intent.expected_response_schema == {"type": "object"}

    # Null payload
    intent_null = OntologyDiscoveryIntent(
        jsonrpc="2.0",
        method="query_registry",
        id="req-123",
        target_registry_uri="https://www.ebi.ac.uk/ols4/api",  # type: ignore
        query_concept_cid="SCTID:12345",
        expected_response_schema=None,
    )
    assert intent_null.expected_response_schema is None

    # Invalid payload (exceeds depth)
    nested_payload: Any = "leaf"
    for _ in range(11):
        nested_payload = {"key": nested_payload}

    with pytest.raises(ValidationError) as exc_info:
        OntologyDiscoveryIntent(
            method="query_registry",
            id="req-123",
            target_registry_uri="https://www.ebi.ac.uk/ols4/api",  # type: ignore
            query_concept_cid="SCTID:12345",
            expected_response_schema=nested_payload,
        )
    assert "Payload exceeds maximum recursion depth of 10" in str(exc_info.value)


def test_semantic_mapping_heuristic_proposal_payload_bounds() -> None:
    from coreason_manifest.spec.ontology import SemanticMappingHeuristicIntent

    # Valid payload
    proposal = SemanticMappingHeuristicIntent(
        proposal_cid="prop-123",
        source_ontology_namespace="ICD-10",
        target_ontology_namespace="SNOMED-CT",
        formal_logic_clauses="SWRL_EXPRESSION",
        justification_evidence_cids=["did:example:node_B", "did:example:node_A"],
    )
    assert proposal.formal_logic_clauses == "SWRL_EXPRESSION"
    # Verify canonical sorting
    assert proposal.justification_evidence_cids == ["did:example:node_A", "did:example:node_B"]

    # Invalid payload (exceeds length constraint)
    large_string = "a" * 65537

    with pytest.raises(ValidationError) as exc_info:
        SemanticMappingHeuristicIntent(
            proposal_cid="prop-123",
            source_ontology_namespace="ICD-10",
            target_ontology_namespace="SNOMED-CT",
            formal_logic_clauses=large_string,
            justification_evidence_cids=["did:example:node_A"],
        )
    assert "String should have at most 65536 characters" in str(exc_info.value)


def test_epistemic_logic_premise_bounds() -> None:
    from pydantic import ValidationError
    from coreason_manifest.spec.ontology import EpistemicLogicPremise

    # Valid payload
    premise = EpistemicLogicPremise(
        ontology_node_id="did:example:node_123",
        asp_program="a :- b.",
        max_models=5
    )
    assert premise.asp_program == "a :- b."

    # Invalid payload (exceeds length constraint 65536)
    large_string = "a" * 65537

    with pytest.raises(ValidationError) as exc_info:
        EpistemicLogicPremise(
            ontology_node_id="did:example:node_123",
            asp_program=large_string,
            max_models=5
        )
    assert "String should have at most 65536 characters" in str(exc_info.value)


def test_epistemic_lean4_premise_bounds() -> None:
    from pydantic import ValidationError
    from coreason_manifest.spec.ontology import EpistemicLean4Premise

    # Valid payload
    premise = EpistemicLean4Premise(
        ontology_node_id="did:example:node_123",
        formal_statement="theorem test : True := by trivial",
        tactic_proof="trivial"
    )
    assert premise.tactic_proof == "trivial"

    # Invalid payload (exceeds length constraint 100000)
    large_string = "a" * 100001

    with pytest.raises(ValidationError) as exc_info:
        EpistemicLean4Premise(
            ontology_node_id="did:example:node_123",
            formal_statement="theorem test : True := by trivial",
            tactic_proof=large_string
        )
    assert "String should have at most 100000 characters" in str(exc_info.value)
