# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    CounterfactualReceipt,
    DefeasibleCascadeEvent,
    InterventionalTaskIntent,
    StructuralCausalGraphProfile,
)


def test_interventional_task_intent_ssrf_rejection():
    # Attempt to use a loopback URI which should trigger SSRF quarantine
    with pytest.raises(ValidationError, match="SSRF restricted IP detected"):
        InterventionalTaskIntent(
            task_cid="task-123",
            target_hypothesis_cid="hypo-456",
            structural_causal_model=StructuralCausalGraphProfile(
                causal_edges=[
                    {
                        "source_variable": "A",
                        "target_variable": "B",
                        "edge_class": "direct_cause",
                        "predicate_curie": "test:test",
                        "belief_vector": {
                            "lexical_confidence": 1.0,
                            "semantic_distance": 0.0,
                            "structural_graph_confidence": 1.0,
                            "epistemic_conflict_mass": 0.0,
                        },
                    }
                ],
                observed_variables=["A", "B"],
                latent_variables=[],
            ),
            treatment_variables=["A"],
            outcome_variables=["B"],
            refutation_tests=["random_common_cause"],
            empirical_data_uri="http://127.0.0.1/data.csv",
        )


def test_interventional_task_intent_array_sorting():
    intent = InterventionalTaskIntent(
        task_cid="task-123",
        target_hypothesis_cid="hypo-456",
        structural_causal_model=StructuralCausalGraphProfile(
            causal_edges=[
                {
                    "source_variable": "A",
                    "target_variable": "B",
                    "edge_class": "direct_cause",
                    "predicate_curie": "test:test",
                    "belief_vector": {
                        "lexical_confidence": 1.0,
                        "semantic_distance": 0.0,
                        "structural_graph_confidence": 1.0,
                        "epistemic_conflict_mass": 0.0,
                    },
                }
            ],
            observed_variables=["A", "B"],
            latent_variables=[],
        ),
        treatment_variables=["Z", "A", "C"],
        outcome_variables=["Y", "X"],
        refutation_tests=["placebo_treatment", "random_common_cause", "data_subset"],
        empirical_data_uri="https://example.com/data.csv",
    )

    assert intent.treatment_variables == ["A", "C", "Z"]
    assert intent.outcome_variables == ["X", "Y"]
    assert intent.refutation_tests == ["data_subset", "placebo_treatment", "random_common_cause"]


def test_counterfactual_receipt_enforce_cascade_on_refutation():
    # Test that ValueError is raised when refutation_passed is False and cascade_event is None
    with pytest.raises(
        ValidationError, match=r"Mathematical Contradiction: A falsified SCM must trigger a cascade event."
    ):
        CounterfactualReceipt(
            event_cid="receipt-789",
            timestamp=1620000000.0,
            receipt_cid="receipt-789",
            task_cid="task-123",
            causal_estimate_value=0.5,
            refutation_passed=False,
            p_values={"random_common_cause": 0.01},
            cascade_event=None,
        )

    # Test that ValueError is raised when refutation_passed is True and cascade_event is not None
    with pytest.raises(
        ValidationError, match=r"Mathematical Contradiction: A verified SCM cannot trigger a cascade event."
    ):
        CounterfactualReceipt(
            event_cid="receipt-789",
            timestamp=1620000000.0,
            receipt_cid="receipt-789",
            task_cid="task-123",
            causal_estimate_value=0.5,
            refutation_passed=True,
            p_values={"random_common_cause": 0.5},
            cascade_event=DefeasibleCascadeEvent(
                cascade_cid="cascade-1",
                root_falsified_event_cid="event-1",
                propagated_decay_factor=0.5,
                quarantined_event_cids=["event-2"],
            ),
        )
