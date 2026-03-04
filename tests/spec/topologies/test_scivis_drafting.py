from coreason_manifest.spec.topologies.scivis_drafting import (
    SciVisCriticNode,
    SciVisDraftingBlackboard,
    SciVisDraftingFlow,
    SciVisLayoutAgentNode,
    SciVisPlannerNode,
)


def test_scivis_drafting_flow_initialization() -> None:
    flow = SciVisDraftingFlow()

    assert "metadata" in flow.model_dump()
    assert flow.metadata.name == "SciVisDraftingTopology"
    assert flow.metadata.version == "1.0.0"

    # Assert nodes presence and type
    assert "planner" in flow.topology.nodes
    assert isinstance(flow.topology.nodes["planner"], SciVisPlannerNode)
    assert flow.topology.nodes["planner"].id == "planner"

    assert "drafter" in flow.topology.nodes
    assert isinstance(flow.topology.nodes["drafter"], SciVisLayoutAgentNode)
    assert flow.topology.nodes["drafter"].id == "drafter"

    assert "critic" in flow.topology.nodes
    assert isinstance(flow.topology.nodes["critic"], SciVisCriticNode)
    assert flow.topology.nodes["critic"].id == "critic"

    # Assert entry point
    assert getattr(flow.topology, "entry_point", None) == "planner"

    # Assert strictly 2 edges for the DAG (planner -> drafter, drafter -> critic)
    edges = getattr(flow.topology, "edges", [])
    assert len(edges) == 2

    planner_drafter_edge = next((e for e in edges if e.from_node == "planner" and e.to_node == "drafter"), None)
    assert planner_drafter_edge is not None

    drafter_critic_edge = next((e for e in edges if e.from_node == "drafter" and e.to_node == "critic"), None)
    assert drafter_critic_edge is not None


def test_scivis_drafting_blackboard_initialization() -> None:
    from coreason_manifest.presentation.scivis.scientific_vis import SciVisIntent, VisInformationType

    intent = SciVisIntent(
        vis_type=VisInformationType.QUALITATIVE_SCHEMATIC, requires_code_execution=False, requires_vector_layout=True
    )
    bb = SciVisDraftingBlackboard(intent=intent)

    assert bb.intent == intent
    assert bb.current_blueprint is None
    assert bb.critic_feedback is None
    assert bb.iteration_count == 0
