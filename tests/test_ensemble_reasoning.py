from pydantic import TypeAdapter

from coreason_manifest.spec.core.engines import (
    EnsembleReasoning,
    ModelCriteria,
    ReasoningConfig,
    StandardReasoning,
)


def test_model_criteria_routing_fields() -> None:
    # Test routing_mode default
    criteria = ModelCriteria(strategy="balanced")
    assert criteria.routing_mode == "single"
    assert criteria.specific_models is None

    # Test explicit routing_mode and specific_models
    criteria = ModelCriteria(
        strategy="performance",
        routing_mode="fallback",
        specific_models=["gpt-4", "claude-3-opus"],
    )
    assert criteria.routing_mode == "fallback"
    assert criteria.specific_models == ["gpt-4", "claude-3-opus"]


def test_ensemble_reasoning_instantiation() -> None:
    # Test EnsembleReasoning defaults
    # Since model is ModelRef = Union[str, ModelCriteria], we can pass "gpt-4"
    ensemble = EnsembleReasoning(model="gpt-4")
    assert ensemble.type == "ensemble"
    assert ensemble.aggregation == "majority_vote"
    assert ensemble.semantic_similarity_threshold == 0.85
    assert ensemble.similarity_model is None
    assert ensemble.judge_model is None

    # Test with custom fields
    ensemble = EnsembleReasoning(
        model=ModelCriteria(strategy="balanced", routing_mode="broadcast"),
        aggregation="strongest_judge",
        semantic_similarity_threshold=None,
        similarity_model="gpt-4",
        judge_model="gpt-4-turbo",
    )
    # mypy complains about accessing routing_mode on str | ModelCriteria
    # so we assert it is ModelCriteria first
    assert isinstance(ensemble.model, ModelCriteria)
    assert ensemble.model.routing_mode == "broadcast"
    assert ensemble.aggregation == "strongest_judge"
    assert ensemble.semantic_similarity_threshold is None
    assert ensemble.similarity_model == "gpt-4"
    assert ensemble.judge_model == "gpt-4-turbo"


def test_reasoning_config_union() -> None:
    # Use TypeAdapter to test parsing into the Union
    adapter: TypeAdapter[ReasoningConfig] = TypeAdapter(ReasoningConfig)

    # 1. EnsembleReasoning
    data_ensemble = {
        "type": "ensemble",
        "model": "gpt-4",
        "aggregation": "majority_vote",
    }
    ensemble = adapter.validate_python(data_ensemble)
    assert isinstance(ensemble, EnsembleReasoning)
    assert ensemble.aggregation == "majority_vote"

    # 2. StandardReasoning
    data_standard = {
        "type": "standard",
        "model": "gpt-3.5",
        "thoughts_max": 5,
    }
    standard = adapter.validate_python(data_standard)
    assert isinstance(standard, StandardReasoning)
    assert standard.thoughts_max == 5
