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
