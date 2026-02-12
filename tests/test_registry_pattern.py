import pytest

from coreason_manifest.spec.core.flow import (
    FlowDefinitions,
    FlowInterface,
    FlowMetadata,
    Graph,
    GraphFlow,
    LinearFlow,
)
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile


def test_agent_node_brain_string() -> None:
    """Test that AgentNode can accept a string ID for profile."""
    agent = AgentNode(
        id="agent-1",
        metadata={},
        supervision=None,
        type="agent",
        profile="brain-id-123",
        tools=[],
    )
    assert agent.profile == "brain-id-123"


def test_agent_node_brain_object() -> None:
    """Test that AgentNode can still accept a CognitiveProfile object."""
    brain = CognitiveProfile(role="assistant", persona="helpful", reasoning=None, fast_path=None)
    agent = AgentNode(
        id="agent-1",
        metadata={},
        supervision=None,
        type="agent",
        profile=brain,
        tools=[],
    )
    assert isinstance(agent.profile, CognitiveProfile)
    assert agent.profile.role == "assistant"


def test_flow_definitions() -> None:
    """Test FlowDefinitions instantiation."""
    brain = CognitiveProfile(role="assistant", persona="helpful", reasoning=None, fast_path=None)
    definitions = FlowDefinitions(
        profiles={"brain-id-123": brain},
        tool_packs={},
        skills={"skill-1": {"type": "python", "code": "print('hello')"}},
    )
    assert definitions.profiles["brain-id-123"] == brain
    assert definitions.skills["skill-1"]["type"] == "python"


def test_linear_flow_definitions() -> None:
    """Test LinearFlow with definitions."""
    brain = CognitiveProfile(role="assistant", persona="helpful", reasoning=None, fast_path=None)
    definitions = FlowDefinitions(
        profiles={"brain-id-123": brain},
        tool_packs={},
    )
    agent = AgentNode(
        id="agent-1",
        metadata={},
        supervision=None,
        type="agent",
        profile="brain-id-123",
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
    assert flow.definitions.profiles["brain-id-123"] == brain

    first_node = flow.sequence[0]
    assert isinstance(first_node, AgentNode)
    assert first_node.profile == "brain-id-123"


def test_graph_flow_definitions() -> None:
    """Test GraphFlow with definitions."""
    brain = CognitiveProfile(role="assistant", persona="helpful", reasoning=None, fast_path=None)
    definitions = FlowDefinitions(
        profiles={"brain-id-123": brain},
        tool_packs={},
    )
    agent = AgentNode(
        id="agent-1",
        metadata={},
        supervision=None,
        type="agent",
        profile="brain-id-123",
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
    assert flow.definitions.profiles["brain-id-123"] == brain

    agent_node = flow.graph.nodes["agent-1"]
    assert isinstance(agent_node, AgentNode)
    assert agent_node.profile == "brain-id-123"


def test_referential_integrity_failure() -> None:
    """
    SOTA SAFETY CHECK:
    Ensures that referencing a non-existent profile ID raises a validation error.
    This prevents 'dangling pointer' runtime crashes.
    """
    # 1. Define a flow with an AgentNode pointing to "ghost-brain"
    # 2. But DO NOT define "ghost-brain" in the registry

    agent = AgentNode(
        id="bad-agent",
        type="agent",
        profile="ghost-brain",  # <--- This ID does not exist
        tools=[],
        metadata={},
        supervision=None,
    )

    metadata = FlowMetadata(name="broken-flow", version="1.0", description="fail", tags=[])

    # 3. Expect a ValueError during initialization
    with pytest.raises(ValueError, match="references undefined profile ID 'ghost-brain'"):
        LinearFlow(
            kind="LinearFlow",
            metadata=metadata,
            definitions=FlowDefinitions(),  # Empty registry
            sequence=[agent],
        )


def test_tool_integrity_failure() -> None:
    """Ensures that referencing a missing tool raises a validation error."""
    # Define a brain (so that part passes)
    brain = CognitiveProfile(role="assistant", persona="helper", reasoning=None, fast_path=None)
    definitions = FlowDefinitions(
        profiles={"my-brain": brain},
        tool_packs={},  # No tools registered
    )

    agent = AgentNode(
        id="agent-1",
        type="agent",
        profile="my-brain",
        tools=["missing-tool"],  # <--- Violation
        metadata={},
        supervision=None,
    )

    with pytest.raises(ValueError, match="requires missing tool 'missing-tool'"):
        LinearFlow(
            kind="LinearFlow",
            metadata=FlowMetadata(name="fail", version="1", description="", tags=[]),
            definitions=definitions,
            sequence=[agent],
        )


def test_tool_integrity_failure_graph() -> None:
    """Ensures that referencing a missing tool raises a validation error in GraphFlow."""
    brain = CognitiveProfile(role="assistant", persona="helper", reasoning=None, fast_path=None)
    definitions = FlowDefinitions(
        profiles={"my-brain": brain},
        tool_packs={},  # No tools registered
    )

    agent = AgentNode(
        id="agent-1",
        type="agent",
        profile="my-brain",
        tools=["missing-tool"],  # <--- Violation
        metadata={},
        supervision=None,
    )

    graph = Graph(nodes={"agent-1": agent}, edges=[])

    with pytest.raises(ValueError, match="requires missing tool 'missing-tool'"):
        GraphFlow(
            kind="GraphFlow",
            metadata=FlowMetadata(name="fail", version="1", description="", tags=[]),
            definitions=definitions,
            interface=FlowInterface(inputs={}, outputs={}),
            blackboard=None,
            graph=graph,
        )
