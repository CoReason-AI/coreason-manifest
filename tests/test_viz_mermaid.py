# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest.spec.v2.definitions import ManifestV2
from coreason_manifest.utils.viz import generate_mermaid_graph


def test_mermaid_basic_structure() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Agent",
        "metadata": {"name": "Basic Agent"},
        "interface": {"inputs": {"query": {"type": "string"}}},
        "workflow": {
            "start": "step_1",
            "steps": {
                "step_1": {
                    "type": "agent",
                    "id": "step_1",
                    "agent": "helper-agent",
                    "next": "step_2",
                },
                "step_2": {
                    "type": "logic",
                    "id": "step_2",
                    "code": "return True",
                    "next": None,  # Implicit end
                },
            },
        },
    }
    manifest = ManifestV2.model_validate(data)
    chart = generate_mermaid_graph(manifest)

    assert "graph TD" in chart
    assert "classDef input" in chart
    assert "classDef step" in chart

    # Check Nodes
    assert "START((Start)):::term" in chart
    assert 'INPUTS["Inputs<br/>- query"]:::input' in chart
    assert 'STEP_step_1["step_1<br/>(Call: helper-agent)"]:::step' in chart
    assert 'STEP_step_2["step_2<br/>(Call: Logic)"]:::step' in chart
    assert "END((End)):::term" in chart

    # Check Edges
    assert "START --> INPUTS" in chart
    assert "INPUTS --> STEP_step_1" in chart
    assert "STEP_step_1 --> STEP_step_2" in chart
    assert "STEP_step_2 --> END" in chart


def test_mermaid_sanitization() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Sanitization Test"},
        "workflow": {
            "start": "Step One",
            "steps": {
                "Step One": {
                    "type": "agent",
                    "id": "Step One",
                    "agent": "search_tool",
                    "next": "Step-Two!",
                },
                "Step-Two!": {"type": "logic", "id": "Step-Two!", "code": "x=1"},
            },
        },
    }
    manifest = ManifestV2.model_validate(data)
    chart = generate_mermaid_graph(manifest)

    # Check that IDs are sanitized
    assert "STEP_Step_One" in chart
    assert "STEP_Step_Two_" in chart  # ! becomes _

    # Check that labels are preserved
    assert '["Step One<br/>' in chart
    assert '["Step-Two!<br/>' in chart

    # Check connections
    assert "INPUTS --> STEP_Step_One" in chart
    assert "STEP_Step_One --> STEP_Step_Two_" in chart


def test_mermaid_switch_case() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Switch Test"},
        "workflow": {
            "start": "decide",
            "steps": {
                "decide": {
                    "type": "switch",
                    "id": "decide",
                    "cases": {"x > 5": "step_big", 'status == "ok"': "step_ok"},
                    "default": "step_default",
                },
                "step_big": {"type": "logic", "id": "step_big", "code": "pass"},
                "step_ok": {"type": "logic", "id": "step_ok", "code": "pass"},
                "step_default": {"type": "logic", "id": "step_default", "code": "pass"},
            },
        },
    }
    manifest = ManifestV2.model_validate(data)
    chart = generate_mermaid_graph(manifest)

    # Check node type
    assert "(Call: Switch)" in chart

    # Check edges with labels
    # Quotes in conditions should be safe
    assert 'STEP_decide -- "x > 5" --> STEP_step_big' in chart
    # 'status == "ok"' -> 'status == 'ok''
    assert "STEP_decide -- \"status == 'ok'\" --> STEP_step_ok" in chart
    assert 'STEP_decide -- "default" --> STEP_step_default' in chart


def test_mermaid_council_step() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Council Test"},
        "workflow": {
            "start": "vote",
            "steps": {
                "vote": {
                    "type": "council",
                    "id": "vote",
                    "voters": ["agent1", "agent2"],
                    "strategy": "consensus",
                    "next": None,
                }
            },
        },
    }
    manifest = ManifestV2.model_validate(data)
    chart = generate_mermaid_graph(manifest)

    assert "(Call: Council)" in chart
    assert "STEP_vote --> END" in chart


def test_mermaid_invalid_start_step() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Invalid Start Test"},
        "workflow": {
            "start": "non_existent_step",
            "steps": {
                "step1": {"type": "logic", "id": "step1", "code": "pass"},
            },
        },
    }
    manifest = ManifestV2.model_validate(data)
    chart = generate_mermaid_graph(manifest)

    # Should fallback to linking Inputs to End
    assert "INPUTS --> END" in chart


def test_mermaid_cyclic_workflow() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Cyclic"},
        "workflow": {
            "start": "A",
            "steps": {
                "A": {"type": "agent", "id": "A", "agent": "worker", "next": "B"},
                "B": {"type": "agent", "id": "B", "agent": "worker", "next": "A"},  # Loop back
            },
        },
    }
    manifest = ManifestV2.model_validate(data)
    chart = generate_mermaid_graph(manifest)

    assert "STEP_A --> STEP_B" in chart
    assert "STEP_B --> STEP_A" in chart


def test_mermaid_disconnected_nodes() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Disconnected"},
        "workflow": {
            "start": "main",
            "steps": {
                "main": {"type": "logic", "id": "main", "code": "pass", "next": None},
                "orphan": {"type": "logic", "id": "orphan", "code": "pass"},  # Not linked
            },
        },
    }
    manifest = ManifestV2.model_validate(data)
    chart = generate_mermaid_graph(manifest)

    # Orphan node should still be defined
    assert 'STEP_orphan["orphan<br/>(Call: Logic)"]:::step' in chart
    # But likely not connected from anywhere (unless Inputs connected it, but Start->Inputs->main)
    # Just checking existence validates it's visualized.


def test_mermaid_complex_switch_routing() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Complex Switch"},
        "workflow": {
            "start": "root",
            "steps": {
                "root": {
                    "type": "switch",
                    "id": "root",
                    "cases": {
                        "c1": "target_a",
                        "c2": "target_a",  # Multi-path to same node
                    },
                    "default": "root",  # Self-loop default
                },
                "target_a": {"type": "logic", "id": "target_a", "code": "pass"},
            },
        },
    }
    manifest = ManifestV2.model_validate(data)
    chart = generate_mermaid_graph(manifest)

    assert 'STEP_root -- "c1" --> STEP_target_a' in chart
    assert 'STEP_root -- "c2" --> STEP_target_a' in chart
    assert 'STEP_root -- "default" --> STEP_root' in chart


def test_mermaid_special_characters_heavy() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Special Chars"},
        "workflow": {
            "start": "start@node",
            "steps": {
                "start@node": {
                    "type": "agent",
                    "id": "start@node",
                    "agent": "tool/v1",
                    "next": "end w/ space & symbol!",
                },
                "end w/ space & symbol!": {
                    "type": "logic",
                    "id": "end w/ space & symbol!",
                    "code": "pass",
                },
            },
        },
    }
    manifest = ManifestV2.model_validate(data)
    chart = generate_mermaid_graph(manifest)

    # Verify ID sanitization
    assert "STEP_start_node" in chart
    assert "STEP_end_w__space___symbol_" in chart
    # Verify Labels preserved
    assert '["start@node<br/>' in chart
    assert '["end w/ space & symbol!<br/>' in chart


def test_mermaid_empty_inputs() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Agent",
        "metadata": {"name": "No Inputs"},
        "interface": {"inputs": {}},  # Empty inputs
        "workflow": {
            "start": "s1",
            "steps": {"s1": {"type": "logic", "id": "s1", "code": "pass"}},
        },
    }
    manifest = ManifestV2.model_validate(data)
    chart = generate_mermaid_graph(manifest)

    # Should just be "Inputs" without bullet points
    assert 'INPUTS["Inputs"]:::input' in chart
