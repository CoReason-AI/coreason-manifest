# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    ActiveInferenceContract,
    CausalDirectedEdge,
    FalsificationContract,
    HypothesisGenerationEvent,
    StructuralCausalModel,
)


def test_hypothesis_generation_event_valid() -> None:
    condition = FalsificationContract(
        condition_id="cond-1",
        description="Must observe HTTP 404.",
        required_tool_name="http_client",
        falsifying_observation_signature="HTTP 404 Not Found",
    )

    hypothesis = HypothesisGenerationEvent(
        event_id="evt-1",
        timestamp=123.456,
        hypothesis_id="hyp-1",
        premise_text="The server is down.",
        bayesian_prior=0.75,
        falsification_conditions=[condition],
        status="active",
    )

    assert hypothesis.type == "hypothesis"
    assert hypothesis.hypothesis_id == "hyp-1"
    assert hypothesis.bayesian_prior == 0.75
    assert len(hypothesis.falsification_conditions) == 1
    assert hypothesis.falsification_conditions[0].condition_id == "cond-1"


def test_hypothesis_causal_model() -> None:
    causal_edge = CausalDirectedEdge(
        source_variable="smoking",
        target_variable="cancer",
        edge_type="direct_cause",
    )
    scm = StructuralCausalModel(
        observed_variables=["smoking", "cancer"],
        latent_variables=["genetics"],
        causal_edges=[causal_edge],
    )
    hypothesis = HypothesisGenerationEvent(
        event_id="evt-2",
        timestamp=123.456,
        hypothesis_id="hyp-2",
        premise_text="Smoking causes cancer.",
        bayesian_prior=0.9,
        falsification_conditions=[
            FalsificationContract(
                condition_id="cond-2",
                description="Must not observe correlation.",
                falsifying_observation_signature="No correlation",
            )
        ],
        status="active",
        causal_model=scm,
    )

    assert hypothesis.causal_model is not None
    assert len(hypothesis.causal_model.causal_edges) == 1
    assert hypothesis.causal_model.causal_edges[0].edge_type == "direct_cause"


def test_hypothesis_bayesian_prior_bounds() -> None:
    condition = FalsificationContract(
        condition_id="cond-1",
        description="test",
        falsifying_observation_signature="test",
    )

    with pytest.raises(ValidationError) as exc:
        HypothesisGenerationEvent(
            event_id="evt-1",
            timestamp=123.456,
            hypothesis_id="hyp-1",
            premise_text="Premise",
            bayesian_prior=-0.1,  # Invalid
            falsification_conditions=[condition],
        )
    assert "Input should be greater than or equal to 0" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        HypothesisGenerationEvent(
            event_id="evt-1",
            timestamp=123.456,
            hypothesis_id="hyp-1",
            premise_text="Premise",
            bayesian_prior=1.1,  # Invalid
            falsification_conditions=[condition],
        )
    assert "Input should be less than or equal to 1" in str(exc.value)


def test_active_inference_contract_expected_information_gain_bounds() -> None:
    with pytest.raises(ValidationError) as exc:
        ActiveInferenceContract(
            task_id="task-1",
            target_hypothesis_id="hyp-1",
            target_condition_id="cond-1",
            selected_tool_name="tool-1",
            expected_information_gain=-0.1,  # Invalid
            execution_cost_budget_magnitude=100,
        )
    assert "Input should be greater than or equal to 0" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        ActiveInferenceContract(
            task_id="task-1",
            target_hypothesis_id="hyp-1",
            target_condition_id="cond-1",
            selected_tool_name="tool-1",
            expected_information_gain=1.1,  # Invalid
            execution_cost_budget_magnitude=100,
        )
    assert "Input should be less than or equal to 1" in str(exc.value)
