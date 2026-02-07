import pytest
from pydantic import ValidationError

from coreason_manifest.spec.v2.definitions import AgentStep, ManifestV2


def test_manifest_v2_validation() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Test Workflow", "x-design": {"x": 0, "y": 0}},
        "definitions": {
            "test-agent": {
                "type": "agent",
                "id": "test-agent",
                "name": "Test Agent",
                "role": "Tester",
                "goal": "Test",
            }
        },
        "workflow": {
            "start": "step-1",
            "steps": {
                "step-1": {"type": "agent", "id": "step-1", "agent": "test-agent", "next": "step-2"},
                "step-2": {"type": "switch", "id": "step-2", "cases": {"cond": "step-3"}, "default": "step-3"},
                "step-3": {"type": "logic", "id": "step-3", "code": "pass"},
            },
        },
    }

    manifest = ManifestV2.model_validate(data)
    assert manifest.metadata.name == "Test Workflow"
    assert manifest.metadata.design_metadata is not None
    assert manifest.metadata.design_metadata.x == 0
    assert len(manifest.workflow.steps) == 3

    step1 = manifest.workflow.steps["step-1"]
    assert isinstance(step1, AgentStep)  # direct check might fail if pydantic wraps it? No, should be fine.
    # Actually step1 is of type Step (Union), so checking isinstance against AgentStep is correct if instantiated.
    # Since it's a discriminated union, pydantic instantiates the specific class.

    assert step1.type == "agent"
    assert step1.next == "step-2"


def test_invalid_manifest() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Bad"},
        "workflow": {
            "start": "step-1",
            "steps": {
                "step-1": {
                    "type": "agent",
                    "id": "step-1",
                    # missing agent
                }
            },
        },
    }
    with pytest.raises(ValidationError):
        ManifestV2.model_validate(data)


def test_manifest_metadata_tested_models() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {
            "name": "Test Workflow",
            "tested_models": ["gpt-4", "claude-3-opus"]
        },
        "workflow": {
            "start": "step-1",
            "steps": {
                "step-1": {"type": "logic", "id": "step-1", "code": "pass"}
            },
        },
    }
    manifest = ManifestV2.model_validate(data)
    assert manifest.metadata.tested_models == ["gpt-4", "claude-3-opus"]
