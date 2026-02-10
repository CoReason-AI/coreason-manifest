# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    EvaluatorNode,
    GenerativeNode,
    GraphEdge,
    GraphTopology,
    HumanNode,
    RecipeDefinition,
    RecipeInterface,
    RouterNode,
    SemanticRef,
    SolverConfig,
)
from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.utils.viz import generate_mermaid_graph


def test_recipe_mermaid_agent_node() -> None:
    nodes = [AgentNode(id="step1", agent_ref="agent1")]
    edges = []
    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="TestRecipe"),
        interface=RecipeInterface(),
        topology=GraphTopology(
            nodes=nodes,
            edges=edges,
            entry_point="step1"
        )
    )

    chart = generate_mermaid_graph(recipe)

    assert "graph TD" in chart
    assert "classDef agent" in chart
    assert 'step1["step1<br/>(Agent: agent1)"]:::agent' in chart
    assert "START --> INPUTS" in chart
    assert "INPUTS --> step1" in chart

def test_recipe_mermaid_semantic_ref() -> None:
    nodes = [AgentNode(id="step1", agent_ref=SemanticRef(intent="Do something"))]
    edges = []
    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="TestRecipe"),
        interface=RecipeInterface(),
        topology=GraphTopology(
            nodes=nodes,
            edges=edges,
            entry_point="step1"
        )
    )

    chart = generate_mermaid_graph(recipe)

    assert 'step1["step1<br/>(Agent: Draft: Do something)"]:::agent' in chart

def test_recipe_mermaid_human_node() -> None:
    nodes = [HumanNode(id="human1", prompt="Approve?")]
    edges = []
    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="TestRecipe"),
        interface=RecipeInterface(),
        topology=GraphTopology(
            nodes=nodes,
            edges=edges,
            entry_point="human1"
        )
    )

    chart = generate_mermaid_graph(recipe)

    assert "classDef human" in chart
    assert 'human1{{"human1<br/>(Human Input)"}}:::human' in chart

def test_recipe_mermaid_router_node() -> None:
    nodes = [
        RouterNode(
            id="router1",
            input_key="classification",
            routes={"A": "stepA"},
            default_route="stepA"
        ),
        AgentNode(id="stepA", agent_ref="agentA")
    ]
    edges = [
        GraphEdge(source="router1", target="stepA", condition="A"),
        GraphEdge(source="router1", target="stepA", condition="default")
    ]
    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="TestRecipe"),
        interface=RecipeInterface(),
        topology=GraphTopology(
            nodes=nodes,
            edges=edges,
            entry_point="router1"
        )
    )

    chart = generate_mermaid_graph(recipe)

    assert "classDef router" in chart
    assert 'router1{"router1<br/>(Router: classification)"}:::router' in chart
    assert 'router1 -- "A" --> stepA' in chart
    # Unlabeled edge for default is usually handled by not having a condition in edge definition if we strictly follow GraphEdge.
    # But here we added condition="default" manually to the edge.
    assert 'router1 -- "default" --> stepA' in chart

def test_recipe_mermaid_evaluator_node() -> None:
    nodes = [
        EvaluatorNode(
            id="eval1",
            target_variable="output",
            evaluator_agent_ref="judge",
            evaluation_profile="standard",
            pass_threshold=0.8,
            max_refinements=3,
            pass_route="pass",
            fail_route="fail",
            feedback_variable="critique"
        ),
        AgentNode(id="pass", agent_ref="agentP"),
        AgentNode(id="fail", agent_ref="agentF")
    ]
    edges = [
        GraphEdge(source="eval1", target="pass"),
        GraphEdge(source="eval1", target="fail")
    ]
    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="TestRecipe"),
        interface=RecipeInterface(),
        topology=GraphTopology(
            nodes=nodes,
            edges=edges,
            entry_point="eval1"
        )
    )

    chart = generate_mermaid_graph(recipe)

    assert "classDef evaluator" in chart
    assert 'eval1(["eval1<br/>(Evaluator)"]):::evaluator' in chart
    assert "eval1 --> pass" in chart
    assert "eval1 --> fail" in chart

def test_recipe_mermaid_generative_node() -> None:
    nodes = [
        GenerativeNode(
            id="gen1",
            goal="Solve world hunger",
            output_schema={"type": "string"}
        )
    ]
    edges = []
    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="TestRecipe"),
        interface=RecipeInterface(),
        topology=GraphTopology(
            nodes=nodes,
            edges=edges,
            entry_point="gen1"
        )
    )

    chart = generate_mermaid_graph(recipe)

    assert "classDef generative" in chart
    assert 'gen1[["gen1<br/>(Generative)"]]:::generative' in chart

def test_recipe_mermaid_inputs() -> None:
    nodes = [AgentNode(id="step1", agent_ref="agent1")]
    edges = []
    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="TestRecipe"),
        interface=RecipeInterface(inputs={"q": {"type": "string"}, "n": {"type": "int"}}),
        topology=GraphTopology(
            nodes=nodes,
            edges=edges,
            entry_point="step1"
        )
    )

    chart = generate_mermaid_graph(recipe)

    assert 'INPUTS["Inputs<br/>- q<br/>- n"]:::input' in chart

def test_recipe_mermaid_sanitization() -> None:
    nodes = [AgentNode(id="step 1!", agent_ref="agent1")]
    edges = []
    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="TestRecipe"),
        interface=RecipeInterface(),
        topology=GraphTopology(
            nodes=nodes,
            edges=edges,
            entry_point="step 1!"
        )
    )

    chart = generate_mermaid_graph(recipe)

    assert 'step_1_["step 1!<br/>(Agent: agent1)"]:::agent' in chart
    assert "INPUTS --> step_1_" in chart

def test_recipe_mermaid_no_entry_point_fallback() -> None:
    # Use model_construct to bypass validation and simulate a missing entry point
    nodes = [AgentNode(id="A", agent_ref="a")]
    topology = GraphTopology.model_construct(
        nodes=nodes,
        edges=[],
        entry_point=""  # Simulate missing entry point
    )
    recipe = RecipeDefinition.model_construct(
        apiVersion="coreason.ai/v2",
        kind="Recipe",
        metadata=ManifestMetadata(name="TestRecipe"),
        interface=RecipeInterface(),
        topology=topology
    )

    chart = generate_mermaid_graph(recipe)
    assert "INPUTS --> END" in chart

def test_recipe_mermaid_edges() -> None:
    nodes = [AgentNode(id="A", agent_ref="a"), AgentNode(id="B", agent_ref="b")]
    edges = [GraphEdge(source="A", target="B")]
    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="TestRecipe"),
        interface=RecipeInterface(),
        topology=GraphTopology(
            nodes=nodes,
            edges=edges,
            entry_point="A"
        )
    )
    chart = generate_mermaid_graph(recipe)
    assert "A --> B" in chart

    # Ensure quotes are sanitized in condition
    edges[0] = GraphEdge(source="A", target="B", condition='foo "bar"')
    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="TestRecipe"),
        interface=RecipeInterface(),
        topology=GraphTopology(
            nodes=nodes,
            edges=edges,
            entry_point="A"
        )
    )
    chart = generate_mermaid_graph(recipe)
    assert "A -- \"foo 'bar'\" --> B" in chart
