from coreason_manifest.core.workflow.nodes import HumanNode, SwitchNode
from coreason_manifest.core.workflow.nodes.visual_oversight import VisualInspectorNode
from coreason_manifest.core.workflow.topologies.sci_vis_flow import get_sota_scivis_topology


def test_sci_vis_flow_serialization_and_structure() -> None:
    # Get the topology
    flow = get_sota_scivis_topology()

    # Verify basic counts
    assert len(flow.graph.nodes) == 6
    assert len(flow.graph.edges) == 8

    # Determine node structure explicitly
    assert "semantic_parser" in flow.graph.nodes
    assert "layout_agent" in flow.graph.nodes
    assert "visual_critic" in flow.graph.nodes
    assert "critique_router" in flow.graph.nodes
    assert "human_expert_review" in flow.graph.nodes
    assert "final_renderer" in flow.graph.nodes

    # Validate visual_critic node
    visual_critic = flow.graph.nodes["visual_critic"]
    assert isinstance(visual_critic, VisualInspectorNode)
    assert visual_critic.target_artifact_key == "rendered_layout_svg"

    # Validate human node
    human_node = flow.graph.nodes["human_expert_review"]
    assert isinstance(human_node, HumanNode)
    assert human_node.options is not None
    assert "approve_to_render" in human_node.options
    assert "reject_to_layout" in human_node.options
    assert "reject_to_planner" in human_node.options

    # Validate the default non-null constraint on router
    router = flow.graph.nodes["critique_router"]
    assert isinstance(router, SwitchNode)
    assert router.default is not None
    assert router.default == "human_expert_review"

    # Validate Pydantic dump doesn't throw errors
    dumped = flow.model_dump()
    assert isinstance(dumped, dict)
    assert "graph" in dumped
    assert "nodes" in dumped["graph"]
