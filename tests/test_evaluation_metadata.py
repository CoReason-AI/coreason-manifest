import pytest
from pydantic import ValidationError

from coreason_manifest.spec.v2.evaluation import EvaluationProfile, SuccessCriterion
from coreason_manifest.spec.v2.definitions import AgentDefinition, ManifestV2


def test_serialization():
    criterion = SuccessCriterion(
        name="accuracy",
        description="Response accuracy > 95%",
        threshold=0.95,
        strict=True
    )
    profile = EvaluationProfile(
        expected_latency_ms=200,
        golden_dataset_uri="s3://bucket/data.json",
        evaluator_model="gpt-4",
        grading_rubric=[criterion]
    )

    agent_def = AgentDefinition(
        id="test-agent",
        name="Test Agent",
        role="Tester",
        goal="Test things",
        evaluation=profile
    )

    dumped = agent_def.dump()
    assert dumped["evaluation"]["expected_latency_ms"] == 200
    assert dumped["evaluation"]["grading_rubric"][0]["name"] == "accuracy"
    assert dumped["evaluation"]["grading_rubric"][0]["threshold"] == 0.95


def test_validation():
    # Test strict typing enforcement
    with pytest.raises(ValidationError) as excinfo:
        SuccessCriterion(
            name="fail",
            description="fail",
            threshold="not-a-float", # Should fail
            strict=True
        )
    assert "Input should be a valid number" in str(excinfo.value)

    # Test immutability (frozen=True)
    criterion = SuccessCriterion(
        name="ok",
        description="ok",
        threshold=0.5,
        strict=True
    )
    with pytest.raises(ValidationError):
        criterion.threshold = 0.9  # Should fail due to frozen=True


def test_integration():
    # Test full manifest integration using model_validate
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Agent",
        "metadata": {"name": "Evaluated Agent"},
        "definitions": {
            "my-agent": {
                "type": "agent",
                "id": "my-agent",
                "name": "My Agent",
                "role": "Worker",
                "goal": "Work",
                "evaluation": {
                    "expected_latency_ms": 500,
                    "golden_dataset_uri": "http://example.com/data",
                    "grading_rubric": [
                        {
                            "name": "speed",
                            "description": "Fast enough",
                            "threshold": 1.0,
                            "strict": False
                        }
                    ]
                }
            }
        },
        "workflow": {
            "start": "step1",
            "steps": {
                "step1": {
                    "type": "agent",
                    "id": "step1",
                    "agent": "my-agent"
                }
            }
        }
    }

    manifest = ManifestV2.model_validate(data)
    agent = manifest.definitions["my-agent"]
    assert isinstance(agent, AgentDefinition)
    assert agent.evaluation.golden_dataset_uri == "http://example.com/data"
    assert agent.evaluation.grading_rubric[0].name == "speed"
    assert agent.evaluation.grading_rubric[0].strict is False
