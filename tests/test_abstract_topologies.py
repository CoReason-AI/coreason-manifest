import pytest

from coreason_manifest.core.common.semantic import OptimizationIntent, SemanticRef
from coreason_manifest.core.workflow.flow import FlowInterface, FlowMetadata, Graph, GraphFlow
from coreason_manifest.core.workflow.nodes.agent import AgentNode


def create_metadata() -> FlowMetadata:
    return FlowMetadata(name="test_flow", version="1.0.0", description="Test flow metadata")


def test_agent_node_with_semantic_ref() -> None:
    # 1. Pydantic successfully parses an AgentNode constructed with a SemanticRef for both profile and tools.
    ref = SemanticRef(
        intent="Research and summarize the topic",
        constraints=["latency < 200ms"],
        optimization=OptimizationIntent(
            improvement_goal="Reduce hallucinations", metric_name="faithfulness", teacher_model="gpt-4"
        ),
    )
    node = AgentNode(id="agent_1", profile=ref, tools=ref, operational_policy=None)

    assert isinstance(node.profile, SemanticRef)
    assert node.profile.intent == "Research and summarize the topic"
    assert isinstance(node.tools, SemanticRef)
    assert node.tools.intent == "Research and summarize the topic"


def test_graph_flow_draft_with_semantic_ref() -> None:
    # 2. Constructing a GraphFlow with status="draft" containing SemanticRef nodes passes validation successfully.
    ref = SemanticRef(intent="Research", constraints=[])
    node = AgentNode(id="agent_1", profile=ref, tools=ref, operational_policy=None)
    graph = Graph(nodes={"agent_1": node}, edges=[], entry_point="agent_1")

    flow = GraphFlow(status="draft", metadata=create_metadata(), interface=FlowInterface(), graph=graph)
    assert flow.status == "draft"


def test_graph_flow_published_with_semantic_ref_raises() -> None:
    # 3. Constructing or mutating a GraphFlow to status="published" containing
    # SemanticRef nodes raises the correct Lifecycle Violation exception.
    ref = SemanticRef(intent="Research", constraints=[])
    node = AgentNode(id="agent_1", profile=ref, tools=ref, operational_policy=None)
    graph = Graph(nodes={"agent_1": node}, edges=[], entry_point="agent_1")

    expected_msg = (
        "Lifecycle Violation: Cannot publish graph. Nodes [agent_1] "
        "contain unresolved SemanticRefs. A Weaver must compile this graph into "
        "concrete profiles before publication."
    )

    with pytest.raises(ValueError, match=expected_msg.replace("[", r"\[").replace("]", r"\]")):
        GraphFlow(status="published", metadata=create_metadata(), interface=FlowInterface(), graph=graph)


def test_graph_flow_published_concrete() -> None:
    # 4. Constructing a GraphFlow with status="published" where all nodes
    # use concrete strings/profiles passes successfully.
    node = AgentNode(id="agent_1", profile="profile_1", tools=["tool_1", "tool_2"], operational_policy=None)
    graph = Graph(nodes={"agent_1": node}, edges=[], entry_point="agent_1")

    flow = GraphFlow(status="published", metadata=create_metadata(), interface=FlowInterface(), graph=graph)
    assert flow.status == "published"
