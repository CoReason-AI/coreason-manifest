from coreason_manifest.spec.core.engines import (
    ModelCriteria,
    StandardReasoning,
    TreeSearchReasoning,
    Reflex,
    Supervision,
    CouncilReasoning
)
import pytest
from pydantic import ValidationError

def test_model_criteria_instantiation():
    # Test valid criteria
    criteria = ModelCriteria(
        strategy="lowest_cost",
        min_context=8192,
        capabilities=["vision", "json_mode"],
        compliance=["gdpr"],
        max_cost_per_m_tokens=10.0,
        provider_whitelist=["azure"]
    )
    assert criteria.strategy == "lowest_cost"
    assert criteria.min_context == 8192

    # Test invalid strategy
    with pytest.raises(ValidationError):
        ModelCriteria(strategy="invalid_strategy")

def test_semantic_routing_in_reasoning():
    # 1. StandardReasoning with String (Legacy)
    legacy = StandardReasoning(
        model="gpt-4",
        thoughts_max=5
    )
    assert legacy.model == "gpt-4"

    # 2. StandardReasoning with Criteria
    criteria = ModelCriteria(strategy="performance")
    advanced = StandardReasoning(
        model=criteria,
        thoughts_max=5
    )
    assert isinstance(advanced.model, ModelCriteria)
    assert advanced.model.strategy == "performance"

def test_tree_search_evaluator_routing():
    # Evaluator model can be a criteria
    lats = TreeSearchReasoning(
        model="gpt-4",
        depth=3,
        branching_factor=2,
        simulations=5,
        evaluator_model=ModelCriteria(strategy="balanced")
    )
    assert isinstance(lats.evaluator_model, ModelCriteria)
    assert lats.evaluator_model.strategy == "balanced"

def test_reflex_routing():
    criteria = ModelCriteria(strategy="lowest_latency")
    reflex = Reflex(
        model=criteria,
        timeout_ms=500
    )
    assert reflex.model.strategy == "lowest_latency"

def test_supervision_critic_routing():
    criteria = ModelCriteria(capabilities=["coding"])
    sup = Supervision(
        strategy="adversarial",
        max_retries=3,
        fallback=None,
        critic_model=criteria
    )
    assert sup.critic_model.capabilities == ["coding"]

def test_council_tie_breaker_routing():
    criteria = ModelCriteria(strategy="performance")
    council = CouncilReasoning(
        model="gpt-4",
        personas=["A", "B"],
        tie_breaker_model=criteria
    )
    assert council.tie_breaker_model.strategy == "performance"
