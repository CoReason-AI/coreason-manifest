
from coreason_manifest.core.workflow.nodes import SwitchNode
from coreason_manifest.core.workflow.topologies.sci_vis_flow import get_sota_scivis_topology


def test_sci_vis_flow_serialization_and_structure() -> None:
    # Get the topology
    flow = get_sota_scivis_topology()

    # Verify basic counts
    assert len(flow.graph.nodes) == 5
    assert len(flow.graph.edges) == 5

    # Determine node structure explicitly
    assert "semantic_parser" in flow.graph.nodes
    assert "layout_agent" in flow.graph.nodes
    assert "visual_critic" in flow.graph.nodes
    assert "critique_router" in flow.graph.nodes
    assert "final_renderer" in flow.graph.nodes

    # Validate the default non-null constraint on router
    router = flow.graph.nodes["critique_router"]
    assert isinstance(router, SwitchNode)
    assert router.default is not None
    assert router.default == "final_renderer"

    # Validate Pydantic dump doesn't throw errors
    dumped = flow.model_dump()
    assert isinstance(dumped, dict)
    assert "graph" in dumped
    assert "nodes" in dumped["graph"]
