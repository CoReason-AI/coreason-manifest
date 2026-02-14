import pytest
from coreason_manifest.spec.core.resilience import DiagnosisReasoning, ResilienceConfig, ErrorHandler, ErrorDomain
from pydantic import TypeAdapter

def test_diagnosis_reasoning_instantiation() -> None:
    strategy = DiagnosisReasoning(
        diagnostic_model="gpt-4",
        fix_strategies=["schema_repair", "context_pruning"]
    )
    assert strategy.type == "diagnosis"
    assert strategy.diagnostic_model == "gpt-4"
    assert strategy.fix_strategies == ["schema_repair", "context_pruning"]

def test_diagnosis_reasoning_deserialization() -> None:
    data = {
        "type": "diagnosis",
        "diagnostic_model": "gpt-3.5",
        "fix_strategies": ["parameter_tuning"]
    }

    adapter: TypeAdapter[ResilienceConfig] = TypeAdapter(ResilienceConfig)
    strategy = adapter.validate_python(data)

    assert isinstance(strategy, DiagnosisReasoning)
    assert strategy.fix_strategies == ["parameter_tuning"]

def test_error_handler_integration() -> None:
    data = {
        "match_domain": [ErrorDomain.LLM],
        "strategy": {
            "type": "diagnosis",
            "diagnostic_model": "gpt-4",
            "fix_strategies": ["schema_repair"]
        }
    }

    handler = ErrorHandler.model_validate(data)
    assert isinstance(handler.strategy, DiagnosisReasoning)
