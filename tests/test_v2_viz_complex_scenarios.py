# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest


from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    CollaborationConfig,
    CollaborationMode,
    EvaluatorNode,
    GraphEdge,
    GraphTopology,
    HumanNode,
    NodePresentation,
    PresentationHints,
    RecipeDefinition,
    RecipeInterface,
    RouterNode,
    VisualizationStyle,
)
from coreason_manifest.utils.viz import generate_recipe_mermaid


def test_complex_full_stack_recipe() -> None:
    """
    Test a full-stack recipe with multiple node types, all having distinct
    visualization (hints) and presentation (layout) settings.
    """
    # 1. Router Node (Entry)
    router = RouterNode(
        id="router",
        input_key="intent",
        routes={"research": "researcher", "write": "writer"},
        default_route="writer",
        presentation=NodePresentation(x=100, y=100, color="#FFCC00"),
        visualization=PresentationHints(style=VisualizationStyle.CHAT, display_title="Intent Router"),
    )

    # 2. Agent Node (Researcher) - Tree Style + Layout
    researcher = AgentNode(
        id="researcher",
        agent_ref="agent-research-v1",
        presentation=NodePresentation(x=50, y=200, color="#00CCFF"),
        visualization=PresentationHints(style=VisualizationStyle.TREE, icon="lucide:search"),
        collaboration=CollaborationConfig(mode=CollaborationMode.INTERACTIVE),
    )

    # 3. Agent Node (Writer) - Document Style + Layout
    writer = AgentNode(
        id="writer",
        agent_ref="agent-writer-v1",
        presentation=NodePresentation(x=150, y=200, color="#00FFCC"),
        visualization=PresentationHints(style=VisualizationStyle.DOCUMENT, hidden_fields=["scratchpad"]),
        collaboration=CollaborationConfig(mode=CollaborationMode.CO_EDIT),
    )

    # 4. Human Node (Review) - Layout only
    reviewer = HumanNode(
        id="reviewer",
        prompt="Review the draft.",
        presentation=NodePresentation(x=100, y=300, color="#FF00FF"),
        # No visualization hints provided (should default)
    )

    # 5. Evaluator Node (Score) - Viz only
    evaluator = EvaluatorNode(
        id="scorer",
        target_variable="output",
        evaluator_agent_ref="judge-v1",
        evaluation_profile="standard",
        pass_threshold=0.8,
        max_refinements=1,
        pass_route="reviewer",
        fail_route="writer",
        feedback_variable="critique",
        visualization=PresentationHints(display_title="Quality Gate"),
        # No layout provided (should be None)
    )

    # Build Topology
    edges = [
        GraphEdge(source="router", target="researcher"),
        GraphEdge(source="router", target="writer"),
        GraphEdge(source="researcher", target="scorer"),
        GraphEdge(source="writer", target="scorer"),
        GraphEdge(source="reviewer", target="writer"),  # Feedback loop
    ]

    topology = GraphTopology(
        nodes=[router, researcher, writer, reviewer, evaluator],
        edges=edges,
        entry_point="router",
    )

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Complex Viz Recipe"),
        interface=RecipeInterface(),
        topology=topology,
    )

    # Verify Logic
    assert len(recipe.topology.nodes) == 5

    # Check serialization round-trip
    dumped = recipe.model_dump(mode="json")
    reloaded = RecipeDefinition.model_validate(dumped)

    assert reloaded.metadata.name == "Complex Viz Recipe"
    assert len(reloaded.topology.nodes) == 5

    # Check specific fields survived
    node_map = {node.id: node for node in reloaded.topology.nodes}

    # Router
    assert node_map["router"].presentation is not None
    assert node_map["router"].presentation.color == "#FFCC00"
    assert node_map["router"].visualization is not None
    assert node_map["router"].visualization.display_title == "Intent Router"

    # Researcher
    assert node_map["researcher"].visualization is not None
    assert node_map["researcher"].visualization.style == VisualizationStyle.TREE
    assert node_map["researcher"].collaboration is not None
    assert node_map["researcher"].collaboration.mode == CollaborationMode.INTERACTIVE

    # Writer
    assert node_map["writer"].visualization is not None
    assert node_map["writer"].visualization.style == VisualizationStyle.DOCUMENT
    assert node_map["writer"].collaboration is not None
    assert node_map["writer"].collaboration.mode == CollaborationMode.CO_EDIT

    # Reviewer
    assert node_map["reviewer"].presentation is not None
    assert node_map["reviewer"].presentation.color == "#FF00FF"
    assert node_map["reviewer"].visualization is None  # Was not set

    # Evaluator
    assert node_map["scorer"].presentation is None  # Was not set
    assert node_map["scorer"].visualization is not None
    assert node_map["scorer"].visualization.display_title == "Quality Gate"


def test_complex_mermaid_generation() -> None:
    """
    Generate a Mermaid graph for the complex recipe and verify
    visual attributes (styles, labels) are correctly rendered.
    """
    # Re-use setup logic or build a minimal complex graph for viz testing
    node1 = AgentNode(
        id="n1",
        agent_ref="a1",
        presentation=NodePresentation(x=0, y=0, color="#FF0000"),
        visualization=PresentationHints(display_title="Red Node"),
    )
    node2 = AgentNode(
        id="n2",
        agent_ref="a2",
        presentation=NodePresentation(x=10, y=10, color="#00FF00"),
        visualization=PresentationHints(display_title="Green Node"),
    )

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="VizTest"),
        interface=RecipeInterface(),
        topology=GraphTopology(nodes=[node1, node2], edges=[GraphEdge(source="n1", target="n2")], entry_point="n1"),
    )

    mermaid = generate_recipe_mermaid(recipe)

    # Check Node Labels from Visualization Hints
    assert 'n1["Red Node"]' in mermaid
    assert 'n2["Green Node"]' in mermaid

    # Check Styles from Presentation Layout
    assert "style n1 fill:#FF0000" in mermaid
    assert "style n2 fill:#00FF00" in mermaid

    # Check Connections
    assert "n1 --> n2" in mermaid
