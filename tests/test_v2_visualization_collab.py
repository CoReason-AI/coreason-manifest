from coreason_manifest.spec.common.presentation import NodePresentation
from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    CollaborationConfig,
    CollaborationMode,
    GenerativeNode,
    PresentationHints,
    VisualizationStyle,
)


def test_sota_tree_search_configuration() -> None:
    node = GenerativeNode(
        id="node-1",
        goal="Solve the problem",
        output_schema={"type": "string"},
        visualization=PresentationHints(
            style=VisualizationStyle.TREE,
            display_title="Reasoning Tree",
        ),
        collaboration=CollaborationConfig(
            mode=CollaborationMode.INTERACTIVE,
            supported_commands=["/prune"],
        ),
    )

    data = node.dump()
    assert data["visualization"]["style"] == "tree"
    assert data["visualization"]["display_title"] == "Reasoning Tree"
    assert data["collaboration"]["mode"] == "interactive"
    assert data["collaboration"]["supported_commands"] == ["/prune"]


def test_co_edit_agent() -> None:
    node = AgentNode(
        id="agent-1",
        agent_ref="agent-ref-1",
        visualization=PresentationHints(style=VisualizationStyle.DOCUMENT),
        collaboration=CollaborationConfig(mode=CollaborationMode.CO_EDIT),
    )

    assert node.visualization is not None
    assert node.visualization.style == VisualizationStyle.DOCUMENT
    assert node.collaboration is not None
    assert node.collaboration.mode == CollaborationMode.CO_EDIT


def test_conflict_avoidance() -> None:
    node = AgentNode(
        id="agent-1",
        agent_ref="agent-ref-1",
        presentation=NodePresentation(x=100, y=200, color="#0000FF"),
        visualization=PresentationHints(style=VisualizationStyle.CHAT),
    )

    data = node.dump()

    # Check that both fields exist and are correct
    assert data["presentation"]["x"] == 100
    assert data["presentation"]["y"] == 200
    assert data["visualization"]["style"] == "chat"
