# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest.spec.common.presentation import (
    GraphTheme,
    NodePresentation,
    NodeStatus,
    RuntimeStateSnapshot,
)
from coreason_manifest.spec.v2.agent import CognitiveProfile
from coreason_manifest.spec.v2.definitions import (
    AgentStep,
    CouncilStep,
    ManifestMetadata,
    ManifestV2,
    SwitchStep,
    Workflow,
)
from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    GraphEdge,
    GraphTopology,
    HumanNode,
    InteractionConfig,
    RecipeDefinition,
    RecipeInterface,
    RouterNode,
    TransparencyLevel,
)
from coreason_manifest.utils.viz import generate_mermaid_graph, to_graph_json


def test_viz_theme_application() -> None:
    nodes = [AgentNode(id="step1", agent_ref="agent1")]
    edges: list[GraphEdge] = []
    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="ThemeTest"),
        interface=RecipeInterface(),
        topology=GraphTopology(nodes=nodes, edges=edges, entry_point="step1"),
    )

    theme = GraphTheme(
        orientation="LR",
        node_styles={"agent": "fill:#000000,stroke:#ffffff"},
    )

    chart = generate_mermaid_graph(recipe, theme=theme)

    assert "graph LR" in chart
    assert "classDef agent fill:#000000,stroke:#ffffff;" in chart


def test_viz_runtime_state_overlay() -> None:
    nodes = [
        AgentNode(id="step1", agent_ref="agent1"),
        AgentNode(id="step2", agent_ref="agent2"),
    ]
    edges: list[GraphEdge] = [GraphEdge(source="step1", target="step2")]
    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="StateTest"),
        interface=RecipeInterface(),
        topology=GraphTopology(nodes=nodes, edges=edges, entry_point="step1"),
    )

    state = RuntimeStateSnapshot(node_states={"step1": NodeStatus.COMPLETED, "step2": NodeStatus.RUNNING})

    chart = generate_mermaid_graph(recipe, state=state)

    assert "class step1 completed;" in chart
    assert "class step2 running;" in chart


def test_viz_interaction_binding() -> None:
    nodes = [
        AgentNode(
            id="step1",
            agent_ref="agent1",
            interaction=InteractionConfig(transparency=TransparencyLevel.INTERACTIVE),
        )
    ]
    edges: list[GraphEdge] = []
    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="InteractionTest"),
        interface=RecipeInterface(),
        topology=GraphTopology(nodes=nodes, edges=edges, entry_point="step1"),
    )

    chart = generate_mermaid_graph(recipe)

    assert 'click step1 call_interaction_handler "Interact with step1"' in chart


def test_viz_nested_graph() -> None:
    profile = CognitiveProfile(role="Researcher", reasoning_mode="standard")
    nodes = [
        AgentNode(
            id="complex_agent",
            cognitive_profile=profile,
        )
    ]
    edges: list[GraphEdge] = []
    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="NestedTest"),
        interface=RecipeInterface(),
        topology=GraphTopology(nodes=nodes, edges=edges, entry_point="complex_agent"),
    )

    chart = generate_mermaid_graph(recipe)

    assert 'subgraph cluster_complex_agent ["complex_agent (Cognitive Profile)"]' in chart
    assert "direction TD" in chart
    assert 'complex_agent["Role: Researcher<br/>Mode: standard"]:::agent' in chart


def test_viz_json_export() -> None:
    nodes = [
        AgentNode(id="step1", agent_ref="agent1"),
        AgentNode(id="step2", agent_ref="agent2"),
    ]
    edges: list[GraphEdge] = [GraphEdge(source="step1", target="step2", condition="success")]
    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="JsonTest"),
        interface=RecipeInterface(inputs={"q": {"type": "string"}}),
        topology=GraphTopology(nodes=nodes, edges=edges, entry_point="step1"),
    )

    data = to_graph_json(recipe)

    assert "nodes" in data
    assert "edges" in data
    assert "theme" in data
    assert data["theme"]["orientation"] == "TD"  # Default theme check

    # Check Inputs Node
    assert data["nodes"][0]["id"] == "INPUTS"
    assert data["nodes"][0]["type"] == "input"
    assert "q" in data["nodes"][0]["config"]["inputs"]

    # Check Nodes
    step1 = next(n for n in data["nodes"] if n["id"] == "step1")
    assert step1["type"] == "agent"
    assert step1["original_id"] == "step1"

    # Check Edges
    edge = next(e for e in data["edges"] if e["source"] == "step1" and e["target"] == "step2")
    assert edge["label"] == "success"

    # Check Implicit Edge
    implicit = next(e for e in data["edges"] if e["source"] == "INPUTS" and e["target"] == "step1")
    assert implicit["type"] == "implicit"


def test_viz_council_step_shape() -> None:
    manifest = ManifestV2(
        kind="Agent",
        metadata=ManifestMetadata(name="CouncilTest"),
        workflow=Workflow(
            start="vote",
            steps={"vote": CouncilStep(id="vote", voters=["a", "b"], next=None)},
        ),
    )

    chart = generate_mermaid_graph(manifest)

    # Check for Council Shape [[ ]]
    # STEP_vote[["vote<br/>(Call: Council)"]]:::council
    assert 'STEP_vote[["vote<br/>(Call: Council)"]]:::council' in chart


def test_to_graph_json_with_presentation() -> None:
    nodes = [
        AgentNode(
            id="step1",
            agent_ref="agent1",
            presentation=NodePresentation(x=100, y=200),
        )
    ]
    edges: list[GraphEdge] = []
    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="JsonPresTest"),
        interface=RecipeInterface(),
        topology=GraphTopology(nodes=nodes, edges=edges, entry_point="step1"),
    )

    data = to_graph_json(recipe)
    step1 = next(n for n in data["nodes"] if n["id"] == "step1")
    assert step1["x"] == 100
    assert step1["y"] == 200


def test_manifest_v2_advanced_viz() -> None:
    # Covers SwitchStep and Next logic in ManifestV2
    manifest = ManifestV2(
        kind="Agent",
        metadata=ManifestMetadata(name="AdvTest"),
        workflow=Workflow(
            start="start_step",
            steps={
                "start_step": AgentStep(id="start_step", agent="agent1", next="decision"),
                "decision": SwitchStep(id="decision", cases={"x>1": "end_ok", "x<0": "end_fail"}, default="end_ok"),
                "end_ok": AgentStep(id="end_ok", agent="agent1", next=None),
                "end_fail": AgentStep(id="end_fail", agent="agent1", next=None),
            },
        ),
    )

    state = RuntimeStateSnapshot(node_states={"start_step": NodeStatus.COMPLETED, "decision": NodeStatus.RUNNING})

    chart = generate_mermaid_graph(manifest, state=state)

    # Check edges
    assert "STEP_start_step --> STEP_decision" in chart
    assert 'STEP_decision -- "x>1" --> STEP_end_ok' in chart
    assert 'STEP_decision -- "default" --> STEP_end_ok' in chart

    # Check state overlay logic was executed
    assert "class STEP_start_step completed;" in chart
    assert "class STEP_decision running;" in chart


def test_to_graph_json_coverage() -> None:
    # Test RouterNode and HumanNode to cover logic branches in to_graph_json
    profile = CognitiveProfile(role="Researcher", reasoning_mode="standard")
    nodes = [
        AgentNode(id="agent1", cognitive_profile=profile),
        RouterNode(
            id="router1",
            input_key="classification",
            routes={"A": "agent1"},
            default_route="agent1",
        ),
        HumanNode(id="human1", prompt="Approve?"),
    ]
    edges: list[GraphEdge] = [GraphEdge(source="router1", target="agent1", condition="A")]
    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="CoverageTest"),
        interface=RecipeInterface(),
        topology=GraphTopology(nodes=nodes, edges=edges, entry_point="router1"),
    )

    data = to_graph_json(recipe)

    agent_node = next(n for n in data["nodes"] if n["id"] == "agent1")
    assert "Profile: Researcher" in agent_node["label"]

    router_node = next(n for n in data["nodes"] if n["id"] == "router1")
    assert "(Router: classification)" in router_node["label"]

    human_node = next(n for n in data["nodes"] if n["id"] == "human1")
    assert "(human)" in human_node["label"]


def test_manifest_v2_with_theme() -> None:
    manifest = ManifestV2(
        kind="Agent",
        metadata=ManifestMetadata(name="ThemeV2Test"),
        workflow=Workflow(start="step1", steps={"step1": AgentStep(id="step1", agent="agent1", next=None)}),
    )
    theme = GraphTheme(orientation="LR", node_styles={"step": "fill:red"})
    chart = generate_mermaid_graph(manifest, theme=theme)
    assert "graph LR" in chart
    assert "classDef step fill:red;" in chart


def test_to_graph_json_with_theme() -> None:
    nodes = [AgentNode(id="step1", agent_ref="agent1")]
    edges: list[GraphEdge] = []
    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="JsonThemeTest"),
        interface=RecipeInterface(),
        topology=GraphTopology(nodes=nodes, edges=edges, entry_point="step1"),
    )
    theme = GraphTheme(primary_color="#FF0000")
    data = to_graph_json(recipe, theme=theme)
    assert data["theme"]["primary_color"] == "#FF0000"
