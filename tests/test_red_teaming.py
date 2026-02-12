from pydantic import TypeAdapter

from coreason_manifest.spec.core.engines import (
    ModelCriteria,
    ReasoningConfig,
    RedTeamingReasoning,
)


def test_red_teaming_reasoning_instantiation() -> None:
    # Test defaults
    rt = RedTeamingReasoning(
        model="gpt-4",
        attacker_model="gpt-4-turbo",
        success_criteria="Leakage of PII",
    )
    assert rt.type == "red_teaming"
    assert rt.attack_strategy == "crescendo"
    assert rt.max_turns == 5
    assert rt.target_model is None

    # Test with custom fields
    target_criteria = ModelCriteria(strategy="performance")
    rt = RedTeamingReasoning(
        model="gpt-4",
        attacker_model="claude-3-opus",
        target_model=target_criteria,
        attack_strategy="goat",
        max_turns=10,
        success_criteria="Jailbreak successful",
    )
    assert rt.attacker_model == "claude-3-opus"
    assert isinstance(rt.target_model, ModelCriteria)
    assert rt.target_model.strategy == "performance"
    assert rt.attack_strategy == "goat"
    assert rt.max_turns == 10
    assert rt.success_criteria == "Jailbreak successful"


def test_reasoning_config_union_red_teaming() -> None:
    # Use TypeAdapter to test parsing into the Union
    adapter: TypeAdapter[ReasoningConfig] = TypeAdapter(ReasoningConfig)

    data = {
        "type": "red_teaming",
        "model": "gpt-4",
        "attacker_model": "gpt-4-turbo",
        "success_criteria": "Harmful content generation",
    }
    parsed = adapter.validate_python(data)
    assert isinstance(parsed, RedTeamingReasoning)
    assert parsed.type == "red_teaming"
    assert parsed.attacker_model == "gpt-4-turbo"
