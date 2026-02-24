from coreason_manifest.builder import NewGraphFlow
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile
from coreason_manifest.spec.core.flow import GraphFlow, Graph, FlowMetadata, FlowInterface
from coreason_manifest.spec.core.engines import ComputerUseReasoning
from coreason_manifest.utils.gatekeeper import validate_policy
from coreason_manifest.spec.interop.compliance import ErrorCatalog

def test_builder_set_entry_point():
    """Cover builder.py set_entry_point method."""
    builder = NewGraphFlow("test", "1.0.0", "desc")
    builder.add_agent(AgentNode(id="node1", profile=CognitiveProfile(role="r", persona="p")))

    # Call the method to cover it
    builder.set_entry_point("node1")

    flow = builder.build()
    assert flow.graph.entry_point == "node1"

def test_gatekeeper_published_dangerous_unreachable():
    """Cover gatekeeper.py published mode with dangerous unreachable nodes."""
    # Create a flow manually to ensure status="published" and dangerous node
    nodes = {
        "node1": AgentNode(id="node1", profile=CognitiveProfile(role="assistant", persona="p")),
        "node2": AgentNode(
            id="node2",
            profile=CognitiveProfile(
                role="hacker",
                persona="p",
                reasoning=ComputerUseReasoning(
                    model="gpt-4",
                    interaction_mode="native_os",
                    coordinate_system="normalized_0_1"
                )
            )
        )
    }

    flow = GraphFlow(
        status="published",
        metadata=FlowMetadata(name="Test Flow", version="1.0.0"),
        interface=FlowInterface(),
        graph=Graph(
            nodes=nodes,
            edges=[],
            entry_point="node1"
        )
    )

    reports = validate_policy(flow)

    # Verify we hit the published dangerous block
    risk_reports = [r for r in reports if r.code == ErrorCatalog.ERR_TOPOLOGY_UNREACHABLE_RISK_003]
    assert len(risk_reports) > 0
    assert risk_reports[0].severity == "violation"
