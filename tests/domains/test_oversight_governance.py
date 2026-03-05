import pytest
from hypothesis import given, strategies as st
from pydantic import ValidationError

from coreason_manifest.oversight.adjudication import AdjudicationRubric, GradingCriteria
from coreason_manifest.oversight.intervention import FallbackSLA, InterventionRequest, BoundedInterventionScope
from coreason_manifest.oversight.governance import ConstitutionalRule


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


@given(
    forbidden_intents=st.lists(st.just(""), min_size=1)
)
def test_constitutional_rule_rejects_empty_strings(forbidden_intents: list[str]) -> None:
    with pytest.raises(ValidationError):
        ConstitutionalRule(
            rule_id="rule-1",
            description="desc",
            severity="critical",
            forbidden_intents=forbidden_intents,
        )


@given(
    forbidden_intents=st.lists(st.text(min_size=1), min_size=2).filter(lambda x: len(set(x)) < len(x))
)
def test_constitutional_rule_deduplicates_or_rejects_duplicate_strings(forbidden_intents: list[str]) -> None:
    # If using set, Pydantic should deduplicate or raise error if list has duplicates.
    # We test that it's structurally impossible to have duplicates in the model.
    try:
        rule = ConstitutionalRule(
            rule_id="rule-2",
            description="desc",
            severity="critical",
            forbidden_intents=forbidden_intents,
        )
        # If it succeeds, it MUST be deduplicated by Pydantic (converted to set)
        assert len(rule.forbidden_intents) == len(set(forbidden_intents))
        assert len(rule.forbidden_intents) < len(forbidden_intents)
    except ValidationError:
        pass  # Also acceptable if it rejects lists with duplicates (depending on strict mode)


@given(
    allowed_fields=st.lists(st.text()),
    json_schema_whitelist=st.dictionaries(st.text(), st.integers()),  # Simple dict
    timeout_seconds=st.integers(min_value=1, max_value=1000000),
    context_summary=st.text(),
    proposed_action=st.dictionaries(st.text(), st.integers()),
    adjudication_deadline=st.floats(min_value=0.0, allow_nan=False, allow_infinity=False),
)
def test_sandbox_success_massive_configs(
    allowed_fields: list[str],
    json_schema_whitelist: dict[str, int],
    timeout_seconds: int,
    context_summary: str,
    proposed_action: dict[str, int],
    adjudication_deadline: float,
) -> None:
    scope = BoundedInterventionScope(
        allowed_fields=allowed_fields,
        json_schema_whitelist=json_schema_whitelist, # type: ignore
    )
    sla = FallbackSLA(
        timeout_seconds=timeout_seconds,
        timeout_action="fail_safe",
    )
    req = InterventionRequest(
        intervention_scope=scope,
        fallback_sla=sla,
        target_node_id="node-1",
        context_summary=context_summary,
        proposed_action=proposed_action, # type: ignore
        adjudication_deadline=adjudication_deadline,
    )
    assert req.intervention_scope is not None
    assert req.fallback_sla is not None
