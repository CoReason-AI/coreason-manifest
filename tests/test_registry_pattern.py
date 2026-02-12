from coreason_manifest.spec.core.flow import (
    FlowDefinitions,
    FlowInterface,
    FlowMetadata,
    Graph,
    GraphFlow,
    LinearFlow,
)
from coreason_manifest.spec.core.nodes import AgentNode, Brain
import pytest


def test_agent_node_brain_string() -> None:
    """Test that AgentNode can accept a string ID for brain."""
    agent = AgentNode(
        id="agent-1",
        metadata={},
        supervision=None,
        type="agent",
        brain="brain-id-123",
        tools=[],
    )
    assert agent.brain == "brain-id-123"


def test_agent_node_brain_object() -> None:
    """Test that AgentNode can still accept a Brain object."""
    brain = Brain(role="assistant", persona="helpful", reasoning=None, reflex=None)
    agent = AgentNode(
        id="agent-1",
        metadata={},
        supervision=None,
        type="agent",
        brain=brain,
        tools=[],
    )
    assert isinstance(agent.brain, Brain)
    assert agent.brain.role == "assistant"


def test_flow_definitions() -> None:
    """Test FlowDefinitions instantiation."""
    brain = Brain(role="assistant", persona="helpful", reasoning=None, reflex=None)
    definitions = FlowDefinitions(
        brains={"brain-id-123": brain},
        tool_packs={},
        skills={"skill-1": {"type": "python", "code": "print('hello')"}},
    )
    assert definitions.brains["brain-id-123"] == brain
    assert definitions.skills["skill-1"]["type"] == "python"


def test_linear_flow_definitions() -> None:
    """Test LinearFlow with definitions."""
    brain = Brain(role="assistant", persona="helpful", reasoning=None, reflex=None)
    definitions = FlowDefinitions(
        brains={"brain-id-123": brain},
        tool_packs={},
    )
    agent = AgentNode(
        id="agent-1",
        metadata={},
        supervision=None,
        type="agent",
        brain="brain-id-123",
        tools=[],
    )

    metadata = FlowMetadata(name="test-linear", version="1.0", description="test", tags=[])
    flow = LinearFlow(
        kind="LinearFlow",
        metadata=metadata,
        definitions=definitions,
        sequence=[agent],
    )

    assert flow.definitions is not None
    assert flow.definitions.brains["brain-id-123"] == brain

    first_node = flow.sequence[0]
    assert isinstance(first_node, AgentNode)
    assert first_node.brain == "brain-id-123"


def test_graph_flow_definitions() -> None:
    """Test GraphFlow with definitions."""
    brain = Brain(role="assistant", persona="helpful", reasoning=None, reflex=None)
    definitions = FlowDefinitions(
        brains={"brain-id-123": brain},
        tool_packs={},
    )
    agent = AgentNode(
        id="agent-1",
        metadata={},
        supervision=None,
        type="agent",
        brain="brain-id-123",
        tools=[],
    )

    metadata = FlowMetadata(name="test-graph", version="1.0", description="test", tags=[])
    interface = FlowInterface(inputs={}, outputs={})
    graph = Graph(nodes={"agent-1": agent}, edges=[])

    flow = GraphFlow(
        kind="GraphFlow",
        metadata=metadata,
        definitions=definitions,
        interface=interface,
        blackboard=None,
        graph=graph,
    )

    assert flow.definitions is not None
    assert flow.definitions.brains["brain-id-123"] == brain

    agent_node = flow.graph.nodes["agent-1"]
    assert isinstance(agent_node, AgentNode)
    assert agent_node.brain == "brain-id-123"


def test_referential_integrity_failure() -> None:
    """
    SOTA SAFETY CHECK:
    Ensures that referencing a non-existent brain ID raises a validation error.
    This prevents 'dangling pointer' runtime crashes.
    """
    # 1. Define a flow with an AgentNode pointing to "ghost-brain"
    # 2. But DO NOT define "ghost-brain" in the registry

    agent = AgentNode(
        id="bad-agent",
        type="agent",
        brain="ghost-brain", # <--- This ID does not exist
        tools=[],
        metadata={},
        supervision=None
    )

    metadata = FlowMetadata(name="broken-flow", version="1.0", description="fail", tags=[])

    # 3. Expect a ValueError during initialization
    with pytest.raises(ValueError) as excinfo:
        LinearFlow(
            kind="LinearFlow",
            metadata=metadata,
            definitions=FlowDefinitions(), # Empty registry
            sequence=[agent],
        )

    # 4. Verify the error message is helpful
    assert "references undefined brain ID 'ghost-brain'" in str(excinfo.value)
