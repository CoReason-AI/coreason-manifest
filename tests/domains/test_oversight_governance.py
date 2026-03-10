# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    AdjudicationRubric,
    BoundedInterventionScope,
    ConsensusPolicy,
    ConstitutionalPolicy,
    FallbackSLA,
    GradingCriteria,
    InterventionIntent,
    PredictionMarketPolicy,
    QuorumPolicy,
)


@given(
    weight=st.floats(max_value=-0.000001, allow_nan=False, allow_infinity=False),
    threshold=st.floats(max_value=-0.000001, allow_nan=False, allow_infinity=False),
)
def test_adjudication_rubric_rejects_negative_bounds(weight: float, threshold: float) -> None:
    with pytest.raises(ValidationError):
        GradingCriteria(
            criterion_id="test-criterion",
            description="test description",
            weight=weight,
        )

    with pytest.raises(ValidationError):
        AdjudicationRubric(
            rubric_id="test-rubric",
            criteria=[],
            passing_threshold=threshold,
        )


@given(
    timeout_seconds=st.integers(max_value=0),
)
def test_fallback_sla_rejects_non_positive_timeout(timeout_seconds: int) -> None:
    with pytest.raises(ValidationError):
        FallbackSLA(
            timeout_seconds=timeout_seconds,
            timeout_action="fail_safe",
        )


@given(forbidden_intents=st.lists(st.just(""), min_size=1))
def test_constitutional_rule_rejects_empty_strings(forbidden_intents: list[str]) -> None:
    with pytest.raises(ValidationError):
        ConstitutionalPolicy.model_validate(
            {
                "rule_id": "rule-1",
                "description": "desc",
                "severity": "critical",
                "forbidden_intents": forbidden_intents,
            }
        )


@given(forbidden_intents=st.lists(st.text(min_size=1), min_size=2).filter(lambda x: len(set(x)) < len(x)))
def test_constitutional_rule_deduplicates_or_rejects_duplicate_strings(forbidden_intents: list[str]) -> None:
    # If using set, Pydantic should deduplicate or raise error if list has duplicates.
    # We test that it's structurally impossible to have duplicates in the model.
    try:
        rule = ConstitutionalPolicy.model_validate(
            {
                "rule_id": "rule-2",
                "description": "desc",
                "severity": "critical",
                "forbidden_intents": forbidden_intents,
            }
        )
        # If it succeeds, it MUST be deduplicated by Pydantic (converted to set)
        assert len(rule.forbidden_intents) == len(set(forbidden_intents))
        assert len(rule.forbidden_intents) < len(forbidden_intents)
    except ValidationError:
        pass  # Also acceptable if it rejects lists with duplicates (depending on strict mode)


def test_prediction_market_policy_bounds() -> None:
    # Test valid bounds
    policy = PredictionMarketPolicy(
        staking_function="quadratic", min_liquidity_magnitude=0, convergence_delta_threshold=0.5
    )
    assert policy.staking_function == "quadratic"

    # Test invalid min_liquidity_magnitude
    with pytest.raises(ValidationError) as exc_info:
        PredictionMarketPolicy(
            staking_function="quadratic", min_liquidity_magnitude=-1, convergence_delta_threshold=0.5
        )
    assert "ge" in str(exc_info.value) or "greater than or equal" in str(exc_info.value)

    # Test invalid convergence_delta_threshold
    with pytest.raises(ValidationError) as exc_info2:
        PredictionMarketPolicy(staking_function="linear", min_liquidity_magnitude=100, convergence_delta_threshold=-0.1)
    assert "ge" in str(exc_info2.value) or "greater than or equal" in str(exc_info2.value)

    with pytest.raises(ValidationError) as exc_info3:
        PredictionMarketPolicy(staking_function="linear", min_liquidity_magnitude=100, convergence_delta_threshold=1.1)
    assert "le" in str(exc_info3.value) or "less than or equal" in str(exc_info3.value)


def test_quorum_policy_enforce_bft_math() -> None:
    # Valid quorum
    QuorumPolicy(
        max_tolerable_faults=1,
        min_quorum_size=4,
        state_validation_metric="ledger_hash",
        byzantine_action="quarantine",
    )

    # Invalid quorum: 3 * 1 + 1 = 4, but min_quorum_size is 3
    with pytest.raises(
        ValidationError,
        match=r"Byzantine Fault Tolerance requires min_quorum_size \(N\) >= 3f \+ 1\.",
    ):
        QuorumPolicy(
            max_tolerable_faults=1,
            min_quorum_size=3,
            state_validation_metric="ledger_hash",
            byzantine_action="quarantine",
        )


def test_consensus_policy_validate_pbft_requirements() -> None:
    # Valid consensus policy with pbft
    quorum = QuorumPolicy(
        max_tolerable_faults=1,
        min_quorum_size=4,
        state_validation_metric="ledger_hash",
        byzantine_action="quarantine",
    )
    ConsensusPolicy(
        strategy="pbft",
        quorum_rules=quorum,
    )

    # Invalid consensus policy with pbft but missing quorum_rules
    with pytest.raises(ValidationError, match=r"quorum_rules must be provided when strategy is 'pbft'\."):
        ConsensusPolicy(
            strategy="pbft",
            quorum_rules=None,
        )


@given(
    allowed_fields=st.lists(st.text()),
    json_schema_whitelist=st.dictionaries(st.text(), st.integers()),  # Simple dict
    timeout_seconds=st.integers(min_value=1, max_value=1000000),
    context_summary=st.text(),
    proposed_action=st.dictionaries(st.text(), st.integers()),
    adjudication_deadline=st.floats(min_value=0.0, allow_nan=False, allow_infinity=False),
    escalation_target_node_id=st.one_of(st.none(), st.from_regex(r"^did:[a-z0-9]+:[a-zA-Z0-9.\-_:]+$", fullmatch=True)),
)
def test_sandbox_success_massive_configs(
    allowed_fields: list[str],
    json_schema_whitelist: dict[str, int],
    timeout_seconds: int,
    context_summary: str,
    proposed_action: dict[str, int],
    adjudication_deadline: float,
    escalation_target_node_id: str | None,
) -> None:
    scope = BoundedInterventionScope(
        allowed_fields=allowed_fields,
        json_schema_whitelist=json_schema_whitelist,  # type: ignore
    )
    sla = FallbackSLA(
        timeout_seconds=timeout_seconds,
        timeout_action="fail_safe",
        escalation_target_node_id=escalation_target_node_id,
    )
    req = InterventionIntent(
        intervention_scope=scope,
        fallback_sla=sla,
        target_node_id="did:web:node-1",
        context_summary=context_summary,
        proposed_action=proposed_action,  # type: ignore
        adjudication_deadline=adjudication_deadline,
    )
    assert req.intervention_scope is not None
    assert req.fallback_sla is not None
