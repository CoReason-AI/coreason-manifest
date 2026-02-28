import pytest

from coreason_manifest.core.workflow.flow import DataSchema, FlowInterface, FlowMetadata, Graph, GraphFlow, LinearFlow
from coreason_manifest.core.workflow.nodes import AgentNode, PlaceholderNode


def test_placeholder_node():
    node = PlaceholderNode(id="placeholder_1", required_capabilities=["search"])
    assert node.type == "placeholder"
    assert node.required_capabilities == ["search"]


def create_mock_flow_metadata():
    return FlowMetadata(name="test", version="1", description="test")


def create_mock_flow_interface():
    return FlowInterface(inputs=DataSchema(), outputs=DataSchema())


def test_linear_flow_validation():
    # Test draft flow with placeholder
    placeholder = PlaceholderNode(id="placeholder_1", required_capabilities=["search"])
    flow = LinearFlow(status="draft", metadata=create_mock_flow_metadata(), steps=[placeholder])
    assert flow.status == "draft"

    # Test published flow with placeholder
    with pytest.raises(ValueError, match="Cannot publish a flow with placeholder nodes"):
        LinearFlow(status="published", metadata=create_mock_flow_metadata(), steps=[placeholder])


def test_graph_flow_validation():
    # Test published flow without entry point
    agent = AgentNode(id="agent_1", profile="test_profile")
    with pytest.raises(ValueError, match="Cannot publish a GraphFlow without an entry point"):
        GraphFlow(
            status="published",
            metadata=create_mock_flow_metadata(),
            interface=create_mock_flow_interface(),
            graph=Graph(nodes={"agent_1": agent}, edges=[]),
        )
