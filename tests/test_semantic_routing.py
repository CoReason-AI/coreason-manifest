import pytest
from pydantic import ValidationError

from coreason_manifest.spec.core.engines import (
    CouncilReasoning,
    ModelCriteria,
    Reflex,
    StandardReasoning,
    Supervision,
    TreeSearchReasoning,
)


def test_model_criteria_instantiation() -> None:
    # Test valid criteria
    criteria = ModelCriteria(
        strategy="lowest_cost",
        min_context=8192,
        capabilities=["vision", "json_mode"],
        compliance=["gdpr"],
        max_cost_per_m_tokens=10.0,
        provider_whitelist=["azure"],
    )
    assert criteria.strategy == "lowest_cost"
    assert criteria.min_context == 8192

    # Test invalid strategy
    with pytest.raises(ValidationError):
        ModelCriteria(strategy="invalid_strategy")  # type: ignore


def test_semantic_routing_in_reasoning() -> None:
    # 1. StandardReasoning with String (Legacy)
    legacy = StandardReasoning(model="gpt-4", thoughts_max=5)
    assert legacy.model == "gpt-4"

    # 2. StandardReasoning with Criteria
    criteria = ModelCriteria(strategy="performance")
    advanced = StandardReasoning(model=criteria, thoughts_max=5)
    assert isinstance(advanced.model, ModelCriteria)
    assert advanced.model.strategy == "performance"


def test_tree_search_evaluator_routing() -> None:
    # Evaluator model can be a criteria
    lats = TreeSearchReasoning(
        model="gpt-4",
        depth=3,
        branching_factor=2,
        simulations=5,
        evaluator_model=ModelCriteria(strategy="balanced"),
    )
    assert isinstance(lats.evaluator_model, ModelCriteria)
    assert lats.evaluator_model.strategy == "balanced"


def test_reflex_routing() -> None:
    criteria = ModelCriteria(strategy="lowest_latency")
    reflex = Reflex(model=criteria, timeout_ms=500)
    assert isinstance(reflex.model, ModelCriteria)
    assert reflex.model.strategy == "lowest_latency"


def test_supervision_critic_routing() -> None:
    criteria = ModelCriteria(capabilities=["coding"])
    sup = Supervision(
        strategy="adversarial",
        max_retries=3,
        fallback=None,
        critic_model=criteria,
    )
    assert isinstance(sup.critic_model, ModelCriteria)
    assert sup.critic_model.capabilities == ["coding"]


def test_council_tie_breaker_routing() -> None:
    criteria = ModelCriteria(strategy="performance")
    council = CouncilReasoning(
        model="gpt-4",
        personas=["A", "B"],
        tie_breaker_model=criteria,
    )
    assert isinstance(council.tie_breaker_model, ModelCriteria)
    assert council.tie_breaker_model.strategy == "performance"
