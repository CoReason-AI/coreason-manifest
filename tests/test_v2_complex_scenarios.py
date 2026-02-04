import pytest
from pydantic import ValidationError

from coreason_manifest.common import ToolRiskLevel
from coreason_manifest.v2.spec.definitions import (
    AgentDefinition,
    AgentStep,
    CouncilStep,
    GenericDefinition,
    LogicStep,
    ManifestV2,
    SwitchStep,
    ToolDefinition,
)


# Test 1: Complex Workflow with Cycles
def test_complex_workflow_with_cycles() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Cyclic Workflow"},
        "workflow": {
            "start": "start-switch",
            "steps": {
                "start-switch": {
                    "type": "switch",
                    "id": "start-switch",
                    "cases": {"cond1": "process-agent"},
                    "default": "end-logic",
                },
                "process-agent": {
                    "type": "agent",
                    "id": "process-agent",
                    "agent": "worker-1",
                    "next": "check-result",
                },
                "check-result": {
                    "type": "switch",
                    "id": "check-result",
                    "cases": {"retry": "process-agent"},  # Cycle back
                    "default": "end-logic",
                },
                "end-logic": {
                    "type": "logic",
                    "id": "end-logic",
                    "code": "print('Done')",
                },
            },
        },
        "definitions": {
            "worker-1": {
                "type": "agent",
                "id": "worker-1",
                "name": "Worker",
                "role": "worker",
                "goal": "work",
            }
        },
    }
    manifest = ManifestV2.model_validate(data)
    assert manifest.workflow.start == "start-switch"
    steps = manifest.workflow.steps
    assert isinstance(steps["start-switch"], SwitchStep)
    assert isinstance(steps["process-agent"], AgentStep)

    check_result = steps["check-result"]
    assert isinstance(check_result, SwitchStep)
    assert check_result.cases["retry"] == "process-agent"


# Test 2: All Step Types
def test_all_step_types_usage() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "All Steps"},
        "workflow": {
            "start": "agent-step",
            "steps": {
                "agent-step": {
                    "type": "agent",
                    "id": "agent-step",
                    "agent": "agent-1",
                    "next": "council-step",
                },
                "council-step": {
                    "type": "council",
                    "id": "council-step",
                    "voters": ["agent-1", "agent-2"],
                    "strategy": "consensus",
                    "next": "logic-step",
                },
                "logic-step": {
                    "type": "logic",
                    "id": "logic-step",
                    "code": "result = True",
                    "next": "switch-step",
                },
                "switch-step": {
                    "type": "switch",
                    "id": "switch-step",
                    "cases": {"result": "agent-step"},
                    "default": "logic-step",
                },
            },
        },
    }
    manifest = ManifestV2.model_validate(data)
    assert len(manifest.workflow.steps) == 4
    assert isinstance(manifest.workflow.steps["council-step"], CouncilStep)
    assert manifest.workflow.steps["council-step"].strategy == "consensus"


# Test 3: Full Policy and State
def test_full_policy_and_state() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Policy State"},
        "policy": {
            "max_steps": 100,
            "max_retries": 5,
            "timeout": 3600,
            "human_in_the_loop": True,
        },
        "state": {
            "schema": {
                "type": "object",
                "properties": {"counter": {"type": "integer"}},
            },
            "backend": "redis",
        },
        "workflow": {"start": "s1", "steps": {"s1": {"type": "logic", "id": "s1", "code": "pass"}}},
    }
    manifest = ManifestV2.model_validate(data)
    assert manifest.policy.max_steps == 100
    assert manifest.policy.human_in_the_loop is True
    assert manifest.state.backend == "redis"
    assert manifest.state.schema_["properties"]["counter"]["type"] == "integer"


# Test 4: Design Metadata
def test_metadata_and_design_completeness() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {
            "name": "Design Demo",
            "x-design": {
                "x": 100.5,
                "y": 200.0,
                "icon": "flow-chart",
                "color": "#FF5733",
                "label": "Main Flow",
                "zoom": 1.2,
                "collapsed": False,
            },
        },
        "workflow": {
            "start": "s1",
            "steps": {
                "s1": {
                    "type": "logic",
                    "id": "s1",
                    "code": "pass",
                    "x-design": {"x": 10, "y": 20, "collapsed": True},
                }
            },
        },
    }
    manifest = ManifestV2.model_validate(data)
    design = manifest.metadata.design_metadata
    assert design is not None
    assert design.x == 100.5
    assert design.color == "#FF5733"

    step_design = manifest.workflow.steps["s1"].design_metadata
    assert step_design is not None
    assert step_design.x == 10
    assert step_design.collapsed is True


# Test 5: Agent Definition Spec
def test_agent_definition_full_spec() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Agent",
        "metadata": {"name": "Full Agent"},
        "definitions": {
            "super-agent": {
                "type": "agent",
                "id": "super-agent",
                "name": "007",
                "role": "Secret Agent",
                "goal": "Save the world",
                "backstory": "Classified",
                "model": "gpt-4-turbo",
                "tools": ["tool-1"],
                "knowledge": ["docs/top_secret.pdf"],
            }
        },
        "workflow": {"start": "s1", "steps": {"s1": {"type": "logic", "id": "s1", "code": "pass"}}},
    }
    manifest = ManifestV2.model_validate(data)
    agent = manifest.definitions["super-agent"]
    assert isinstance(agent, AgentDefinition)
    assert agent.role == "Secret Agent"
    assert agent.knowledge == ["docs/top_secret.pdf"]
    assert agent.tools == ["tool-1"]


# Test 6: Tool Definition Spec
def test_tool_definition_full_spec() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Tool Test"},
        "definitions": {
            "search-tool": {
                "type": "tool",
                "id": "search-tool",
                "name": "Google Search",
                "uri": "https://api.google.com/search",
                "risk_level": "standard",
                "description": "Search the web",
            }
        },
        "workflow": {"start": "s1", "steps": {"s1": {"type": "logic", "id": "s1", "code": "pass"}}},
    }
    manifest = ManifestV2.model_validate(data)
    tool = manifest.definitions["search-tool"]
    assert isinstance(tool, ToolDefinition)
    assert str(tool.uri) == "https://api.google.com/search"
    assert tool.risk_level == ToolRiskLevel.STANDARD


# Test 7: Generic Definition Fallback
def test_generic_definition_fallback() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Generic Fallback"},
        "definitions": {
            "unknown-thing": {
                "type": "alien-tech",  # Not agent or tool
                "id": "unknown-1",
                "properties": {"power": 9000},
            }
        },
        "workflow": {"start": "s1", "steps": {"s1": {"type": "logic", "id": "s1", "code": "pass"}}},
    }
    manifest = ManifestV2.model_validate(data)
    definition = manifest.definitions["unknown-thing"]
    assert isinstance(definition, GenericDefinition)
    # GenericDefinition allows extra fields
    # In Pydantic V2 with extra='allow', fields are in model_extra
    assert definition.model_extra is not None
    assert definition.model_extra["type"] == "alien-tech"
    assert definition.model_extra["id"] == "unknown-1"


# Test 8: Invalid References
# Note: Schema validation only checks structure, not referential integrity across IDs usually, unless validator exists.
# If existing validation doesn't check integrity, this test checks if structure is valid at least.
# Based on current knowledge, I don't see a referential integrity validator in definitions.py.
# But I can test that invalid structure raises ValidationError.
# Let's verify missing mandatory fields in steps.
def test_invalid_missing_fields_in_steps() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Invalid"},
        "workflow": {
            "start": "s1",
            "steps": {
                "s1": {
                    "type": "agent",
                    "id": "s1",
                    # Missing 'agent' field
                }
            },
        },
    }
    with pytest.raises(ValidationError) as excinfo:
        ManifestV2.model_validate(data)
    assert "Field required" in str(excinfo.value)
    assert "agent" in str(excinfo.value)


# Test 9: Invalid Discriminated Union
def test_invalid_discriminated_union() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Invalid Type"},
        "workflow": {
            "start": "s1",
            "steps": {
                "s1": {
                    "type": "invalid-type",  # Not one of agent, logic, council, switch
                    "id": "s1",
                }
            },
        },
    }
    with pytest.raises(ValidationError) as excinfo:
        ManifestV2.model_validate(data)
    # Pydantic V2 error for discriminated union mismatch
    assert "Input tag 'invalid-type' found using 'type' does not match any of the expected tags" in str(excinfo.value)


# Test 10: Large Workflow Scalability
def test_large_workflow_scalability() -> None:
    steps = {}
    count = 50
    for i in range(count):
        step_id = f"step-{i}"
        next_id = f"step-{i + 1}" if i < count - 1 else None
        steps[step_id] = {
            "type": "logic",
            "id": step_id,
            "code": f"print({i})",
            "next": next_id,
        }

    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Large Workflow"},
        "workflow": {
            "start": "step-0",
            "steps": steps,
        },
    }

    manifest = ManifestV2.model_validate(data)
    assert len(manifest.workflow.steps) == count

    last_step = manifest.workflow.steps["step-49"]
    assert isinstance(last_step, LogicStep)
    assert last_step.next is None

    first_step = manifest.workflow.steps["step-0"]
    assert isinstance(first_step, LogicStep)
    assert first_step.next == "step-1"
