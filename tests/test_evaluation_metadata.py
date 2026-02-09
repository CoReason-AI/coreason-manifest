# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.v2.definitions import AgentDefinition, ManifestV2
from coreason_manifest.spec.v2.evaluation import EvaluationProfile, SuccessCriterion

# --- Basic Tests ---


def test_serialization() -> None:
    criterion = SuccessCriterion(name="accuracy", description="Response accuracy > 95%", threshold=0.95, strict=True)
    profile = EvaluationProfile(
        expected_latency_ms=200,
        golden_dataset_uri="s3://bucket/data.json",
        evaluator_model="gpt-4",
        grading_rubric=[criterion],
    )

    agent_def = AgentDefinition(
        id="test-agent", name="Test Agent", role="Tester", goal="Test things", evaluation=profile
    )

    dumped = agent_def.model_dump(mode='json', by_alias=True, exclude_none=True)
    assert dumped["evaluation"]["expected_latency_ms"] == 200
    assert dumped["evaluation"]["grading_rubric"][0]["name"] == "accuracy"
    assert dumped["evaluation"]["grading_rubric"][0]["threshold"] == 0.95


def test_validation() -> None:
    # Test strict typing enforcement
    with pytest.raises(ValidationError) as excinfo:
        SuccessCriterion(
            name="fail",
            description="fail",
            threshold="not-a-float",  # Should fail
            strict=True,
        )
    assert "Input should be a valid number" in str(excinfo.value)

    # Test immutability (frozen=True)
    criterion = SuccessCriterion(name="ok", description="ok", threshold=0.5, strict=True)
    with pytest.raises(ValidationError):
        criterion.threshold = 0.9  # type: ignore # Should fail due to frozen=True


def test_integration() -> None:
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
                        {"name": "speed", "description": "Fast enough", "threshold": 1.0, "strict": False}
                    ],
                },
            }
        },
        "workflow": {"start": "step1", "steps": {"step1": {"type": "agent", "id": "step1", "agent": "my-agent"}}},
    }

    manifest = ManifestV2.model_validate(data)
    agent = manifest.definitions["my-agent"]
    assert isinstance(agent, AgentDefinition)
    assert agent.evaluation is not None
    assert agent.evaluation.golden_dataset_uri == "http://example.com/data"
    assert agent.evaluation.grading_rubric[0].name == "speed"
    assert agent.evaluation.grading_rubric[0].strict is False


# --- Edge Cases ---


def test_edge_case_empty_rubric() -> None:
    """Test that an empty grading rubric is valid."""
    profile = EvaluationProfile(grading_rubric=[])
    assert profile.grading_rubric == []

    agent = AgentDefinition(id="a1", name="A1", role="R", goal="G", evaluation=profile)
    assert agent.evaluation is not None
    assert agent.evaluation.grading_rubric == []


def test_edge_case_none_optionals() -> None:
    """Test that optional fields accept None."""
    profile = EvaluationProfile(
        expected_latency_ms=None, golden_dataset_uri=None, evaluator_model=None, grading_rubric=[]
    )
    assert profile.expected_latency_ms is None
    assert profile.golden_dataset_uri is None
    assert profile.evaluator_model is None


def test_edge_case_threshold_boundaries() -> None:
    """Test boundary values for threshold (float)."""
    # 0.0 is valid
    c1 = SuccessCriterion(name="n", description="d", threshold=0.0)
    assert c1.threshold == 0.0

    # 1.0 is valid
    c2 = SuccessCriterion(name="n", description="d", threshold=1.0)
    assert c2.threshold == 1.0

    # Negative values (technically valid per schema, just float)
    c3 = SuccessCriterion(name="n", description="d", threshold=-1.5)
    assert c3.threshold == -1.5

    # Large values
    c4 = SuccessCriterion(name="n", description="d", threshold=100.0)
    assert c4.threshold == 100.0


def test_edge_case_long_strings() -> None:
    """Test extremely long strings for description."""
    long_desc = "a" * 10000
    c = SuccessCriterion(name="long", description=long_desc, threshold=0.5)
    assert c.description == long_desc


# --- Complex Cases ---


def test_complex_serialization_cycle() -> None:
    """Test round-trip serialization (Load -> Dump -> Load)."""
    original_data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Agent",
        "metadata": {"name": "Complex Agent"},
        "definitions": {
            "complex-agent": {
                "type": "agent",
                "id": "complex-agent",
                "name": "Complex Agent",
                "role": "Worker",
                "goal": "Work",
                "evaluation": {
                    "expected_latency_ms": 150,
                    "golden_dataset_uri": "http://data.com/set",
                    "evaluator_model": "judge-model",
                    "grading_rubric": [
                        {"name": "c1", "description": "d1", "threshold": 0.9, "strict": True},
                        {"name": "c2", "description": "d2", "threshold": 0.5, "strict": False},
                    ],
                },
            }
        },
        "workflow": {"start": "s", "steps": {"s": {"type": "agent", "id": "s", "agent": "complex-agent"}}},
    }

    # Load
    manifest = ManifestV2.model_validate(original_data)

    # Dump
    dumped = manifest.model_dump(mode='json', by_alias=True, exclude_none=True)

    # Load again
    manifest_reloaded = ManifestV2.model_validate(dumped)

    # Compare deeply
    agent_orig = manifest.definitions["complex-agent"]
    agent_reload = manifest_reloaded.definitions["complex-agent"]

    assert isinstance(agent_orig, AgentDefinition)
    assert isinstance(agent_reload, AgentDefinition)
    assert agent_orig.evaluation is not None
    assert agent_reload.evaluation is not None

    assert agent_orig.evaluation.grading_rubric[0].name == agent_reload.evaluation.grading_rubric[0].name
    assert agent_orig.evaluation.grading_rubric[1].strict == agent_reload.evaluation.grading_rubric[1].strict
    # Compare the objects directly, not the raw dictionaries, because loading fills defaults.
    assert manifest == manifest_reloaded


def test_complex_multiple_agents_varying_profiles() -> None:
    """Test multiple agents with different or missing evaluation profiles."""
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Agent",
        "metadata": {"name": "Multi Agent"},
        "definitions": {
            "agent-strict": {
                "type": "agent",
                "id": "agent-strict",
                "name": "A1",
                "role": "R",
                "goal": "G",
                "evaluation": {
                    "grading_rubric": [{"name": "must-pass", "description": "d", "threshold": 1.0, "strict": True}]
                },
            },
            "agent-lax": {
                "type": "agent",
                "id": "agent-lax",
                "name": "A2",
                "role": "R",
                "goal": "G",
                "evaluation": {
                    "grading_rubric": [{"name": "nice-to-have", "description": "d", "threshold": 0.5, "strict": False}]
                },
            },
            "agent-none": {
                "type": "agent",
                "id": "agent-none",
                "name": "A3",
                "role": "R",
                "goal": "G",
                # evaluation is missing (None)
            },
        },
        "workflow": {"start": "s", "steps": {"s": {"type": "agent", "id": "s", "agent": "agent-strict"}}},
    }

    manifest = ManifestV2.model_validate(data)

    agent_strict = manifest.definitions["agent-strict"]
    agent_lax = manifest.definitions["agent-lax"]
    agent_none = manifest.definitions["agent-none"]

    assert isinstance(agent_strict, AgentDefinition)
    assert isinstance(agent_lax, AgentDefinition)
    assert isinstance(agent_none, AgentDefinition)

    assert agent_strict.evaluation is not None
    assert agent_lax.evaluation is not None

    assert agent_strict.evaluation.grading_rubric[0].strict is True
    assert agent_lax.evaluation.grading_rubric[0].strict is False
    assert agent_none.evaluation is None


def test_complex_partial_update_attempt() -> None:
    """Test that we cannot partially update the frozen model via copy or similar standard methods if they were mutable.

    This ensures that the model correctly supports Pydantic's functional update pattern while remaining immutable.
    """
    # Since it's frozen, model_copy(update={...}) is the way to 'change' it by creating a new one.

    criterion = SuccessCriterion(name="old", description="old", threshold=0.1)

    # Valid functional update
    new_criterion = criterion.model_copy(update={"threshold": 0.9})
    assert criterion.threshold == 0.1
    assert new_criterion.threshold == 0.9
    assert new_criterion.name == "old"
