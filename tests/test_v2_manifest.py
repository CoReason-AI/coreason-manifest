import pytest
from pydantic import ValidationError
from coreason_manifest.v2.spec.definitions import ManifestV2, Step, AgentStep

def test_manifest_v2_validation():
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {
            "name": "Test Workflow",
            "x-design": {"x": 0, "y": 0}
        },
        "workflow": {
            "start": "step-1",
            "steps": {
                "step-1": {
                    "type": "agent",
                    "id": "step-1",
                    "agent": "test-agent",
                    "next": "step-2"
                },
                "step-2": {
                    "type": "switch",
                    "id": "step-2",
                    "cases": {"cond": "step-3"},
                    "default": "step-3"
                },
                "step-3": {
                    "type": "logic",
                    "id": "step-3",
                    "code": "pass"
                }
            }
        }
    }

    manifest = ManifestV2.model_validate(data)
    assert manifest.metadata.name == "Test Workflow"
    assert manifest.metadata.design_metadata.x == 0
    assert len(manifest.workflow.steps) == 3

    step1 = manifest.workflow.steps["step-1"]
    assert isinstance(step1, AgentStep) # direct check might fail if pydantic wraps it? No, should be fine.
    # Actually step1 is of type Step (Union), so checking isinstance against AgentStep is correct if instantiated.
    # Since it's a discriminated union, pydantic instantiates the specific class.

    assert step1.type == "agent"
    assert step1.next == "step-2"

def test_invalid_manifest():
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Bad"},
        "workflow": {
            "start": "step-1",
            "steps": {
                "step-1": {
                    "type": "agent",
                    "id": "step-1"
                    # missing agent
                }
            }
        }
    }
    with pytest.raises(ValidationError):
        ManifestV2.model_validate(data)
