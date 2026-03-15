import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    BargeInInterruptEvent,
    DifferentiableLogicConstraint,
    EpistemicAxiomState,
    IntentClassificationReceipt,
    TaxonomicRoutingPolicy,
)
from coreason_manifest.utils.algebra import ManifestSemanticRegistry


def test_taxonomic_routing_policy_extensions() -> None:
    # Test valid core string
    p1 = TaxonomicRoutingPolicy(
        policy_id="p1",
        intent_to_heuristic_matrix={"informational_inform": "chronological"},
        fallback_heuristic="chronological",
    )
    assert p1.intent_to_heuristic_matrix["informational_inform"] == "chronological"

    # Test invalid extension without context
    with pytest.raises(ValidationError) as exc:
        TaxonomicRoutingPolicy(
            policy_id="p2",
            intent_to_heuristic_matrix={"ext:custom_intent": "chronological"},
            fallback_heuristic="chronological",
        )
    assert "Unauthorized domain extension string" in str(exc.value)

    # Test valid extension with context
    p3 = TaxonomicRoutingPolicy.model_validate(
        {
            "policy_id": "p3",
            "intent_to_heuristic_matrix": {"ext:custom_intent": "chronological"},
            "fallback_heuristic": "chronological",
        },
        context={"allowed_ext_intents": {"ext:custom_intent"}},
    )
    assert "ext:custom_intent" in p3.intent_to_heuristic_matrix


def test_differentiable_logic_constraint_extensions() -> None:
    with pytest.raises(ValidationError):
        DifferentiableLogicConstraint(
            constraint_id="c1",
            formal_syntax_smt="(assert (= x y))",
            relaxation_epsilon=0.1,
            anomaly_classification="ext:custom_anomaly",
            solver_status="unknown",
        )

    c2 = DifferentiableLogicConstraint.model_validate(
        {
            "constraint_id": "c2",
            "formal_syntax_smt": "(assert (= x y))",
            "relaxation_epsilon": 0.1,
            "anomaly_classification": "ext:custom_anomaly",
            "solver_status": "ext:custom_solver_status",
        },
        context={"allowed_ext_intents": {"ext:custom_anomaly", "ext:custom_solver_status"}},
    )
    assert c2.anomaly_classification == "ext:custom_anomaly"
    assert c2.solver_status == "ext:custom_solver_status"


def test_barge_in_interrupt_event_extensions() -> None:
    with pytest.raises(ValidationError):
        BargeInInterruptEvent(
            event_id="e1",
            timestamp=100.0,
            target_event_id="t1",
            epistemic_disposition="discard",
            disfluency_type="ext:custom_disfluency",
            evicted_token_count=5,
        )

    e2 = BargeInInterruptEvent.model_validate(
        {
            "event_id": "e2",
            "timestamp": 100.0,
            "target_event_id": "t2",
            "epistemic_disposition": "discard",
            "disfluency_type": "ext:custom_disfluency",
            "evicted_token_count": 5,
        },
        context={"allowed_ext_intents": {"ext:custom_disfluency"}},
    )
    assert e2.disfluency_type == "ext:custom_disfluency"


def test_epistemic_axiom_state_extensions() -> None:
    with pytest.raises(ValidationError):
        EpistemicAxiomState(source_concept_id="s1", directed_edge_type="ext:custom_edge", target_concept_id="t1")

    a2 = EpistemicAxiomState.model_validate(
        {"source_concept_id": "s2", "directed_edge_type": "ext:custom_edge", "target_concept_id": "t2"},
        context={"allowed_ext_intents": {"ext:custom_edge"}},
    )
    assert a2.directed_edge_type == "ext:custom_edge"


def test_intent_classification_receipt_sorting() -> None:
    # Test sort_concurrent_intents
    receipt = IntentClassificationReceipt(
        primary_intent="informational_inform",
        concurrent_intents={"taxonomic_restructure": 0.5, "directive_instruct": 0.8, "informational_inform": 0.2},
    )

    expected_order = ["directive_instruct", "informational_inform", "taxonomic_restructure"]
    assert list(receipt.concurrent_intents.keys()) == expected_order


def test_manifest_semantic_registry() -> None:
    resources = ManifestSemanticRegistry.list_resources()
    assert len(resources) > 0
    assert resources[0].uri.startswith("mcp://")

    # Read specific resource
    resource = ManifestSemanticRegistry.read_resource("mcp://coreason/semantics/routing")
    assert resource is not None
    assert resource.name == "Core Routing Intents"

    # Read invalid resource
    invalid = ManifestSemanticRegistry.read_resource("mcp://invalid")
    assert invalid is None


def test_taxonomic_routing_policy_dict_validation() -> None:
    # Test valid extension dictionary value with context
    with pytest.raises(ValidationError):
        TaxonomicRoutingPolicy.model_validate(
            {
                "policy_id": "p4",
                "intent_to_heuristic_matrix": {"ext:custom_intent": "chronological"},
                "fallback_heuristic": "chronological",
                "some_other_dict": {"k": "ext:invalid_value"},
            },
            context={"allowed_ext_intents": {"ext:custom_intent"}},
        )


def test_taxonomic_routing_policy_dict_validation_key() -> None:
    with pytest.raises(ValidationError):
        TaxonomicRoutingPolicy.model_validate(
            {
                "policy_id": "p5",
                "intent_to_heuristic_matrix": {"ext:custom_intent": "chronological"},
                "fallback_heuristic": "chronological",
                "some_other_dict": {"ext:invalid_key": "v"},
            },
            context={"allowed_ext_intents": {"ext:custom_intent"}},
        )


def test_dict_validation_in_barge_in_event() -> None:
    # Invalid key
    with pytest.raises(ValidationError) as exc:
        BargeInInterruptEvent.model_validate(
            {
                "event_id": "e3",
                "timestamp": 100.0,
                "target_event_id": "t3",
                "epistemic_disposition": "discard",
                "disfluency_type": "repair",
                "retained_partial_payload": {"ext:invalid_key": "v"},
            },
            context={"allowed_ext_intents": set()},
        )
    assert "Unauthorized domain extension string detected: 'ext:invalid_key'" in str(exc.value)

    # Invalid value
    with pytest.raises(ValidationError) as exc:
        BargeInInterruptEvent.model_validate(
            {
                "event_id": "e4",
                "timestamp": 100.0,
                "target_event_id": "t4",
                "epistemic_disposition": "discard",
                "disfluency_type": "repair",
                "retained_partial_payload": {"k": "ext:invalid_val"},
            },
            context={"allowed_ext_intents": set()},
        )


def test_dict_validation_in_taxonomic_routing_policy() -> None:
    # intent_to_heuristic_matrix has keys as ValidRoutingIntent
    # Values are Literals. Values cannot be extensions.
    # Wait, if pydantic catches it first, the custom validator won't run for the value.
    # But it WILL run for the key because the key is ValidRoutingIntent.

    with pytest.raises(ValidationError) as exc:
        TaxonomicRoutingPolicy.model_validate(
            {
                "policy_id": "p6",
                "intent_to_heuristic_matrix": {"ext:invalid_key": "chronological"},
                "fallback_heuristic": "chronological",
            },
            context={"allowed_ext_intents": set()},
        )
    assert "Unauthorized domain extension string detected: 'ext:invalid_key'" in str(exc.value)

    # List extension tests
    with pytest.raises(ValidationError) as exc:
        BargeInInterruptEvent.model_validate(
            {
                "event_id": "e5",
                "timestamp": 100.0,
                "target_event_id": "t5",
                "epistemic_disposition": "discard",
                "disfluency_type": "repair",
                "retained_partial_payload": {"k": ["ext:invalid_list_val"]},
            },
            context={"allowed_ext_intents": set()},
        )
    assert "Unauthorized domain extension string detected: 'ext:invalid_list_val'" in str(exc.value)
