import pytest

from coreason_manifest.builder import AgentBuilder, NewGraphFlow
from coreason_manifest.spec.core.engines import StandardReasoning
from coreason_manifest.spec.core.nodes import Brain


def test_fluent_agent_construction() -> None:
    """Test building an AgentNode using the fluent builder."""
    agent = (
        AgentBuilder("research-bot")
        .with_identity("Researcher", "You are strictly factual.")
        .with_reasoning(model="gpt-4o")
        .with_reflex(model="gpt-3.5-turbo", timeout_ms=500)
        .with_tools(["web_search"])
        .with_supervision(retries=3)
        .build()
    )

    # 2. Assertions
    # Verify ID
    assert agent.id == "research-bot"

    # Verify Identity
    assert isinstance(agent.brain, Brain)
    assert agent.brain.role == "Researcher"
    assert agent.brain.persona == "You are strictly factual."

    # Verify Reasoning
    assert agent.brain.reasoning is not None
    assert isinstance(agent.brain.reasoning, StandardReasoning)
    assert agent.brain.reasoning.model == "gpt-4o"
    assert agent.brain.reasoning.thoughts_max == 5  # default

    # Verify Reflex
    assert agent.brain.reflex is not None
    assert agent.brain.reflex.model == "gpt-3.5-turbo"
    assert agent.brain.reflex.timeout_ms == 500
    assert agent.brain.reflex.caching is True  # default

    # Verify Tools
    assert agent.tools == ["web_search"]

    # Verify Supervision
    assert agent.supervision is not None
    assert agent.supervision.max_retries == 3
    assert agent.supervision.strategy == "escalate"  # default


def test_agent_builder_missing_identity() -> None:
    """Test that missing identity raises ValueError."""
    builder = AgentBuilder("incomplete-bot")
    with pytest.raises(ValueError, match="Agent identity"):
        builder.build()


def test_flow_integration() -> None:
    """Test adding a built agent to a GraphFlow and building it."""
    # 1. Build Agent (without tools to avoid validation errors about missing tool packs)
    agent = (
        AgentBuilder("writer-bot").with_identity("Writer", "You are creative.").with_reasoning(model="gpt-4o").build()
    )

    # 2. Add to Flow
    flow_builder = NewGraphFlow("content-creation-flow")

    # Add agent using the new method
    flow_builder.add_agent(agent)

    # Verify it was added to the internal dict
    assert "writer-bot" in flow_builder._nodes
    assert flow_builder._nodes["writer-bot"] == agent

    # 3. Build Flow
    # This triggers validate_flow
    flow = flow_builder.build()

    assert flow is not None
    assert "writer-bot" in flow.graph.nodes


def test_linear_flow_integration() -> None:
    """Test adding a built agent to a LinearFlow and building it."""
    # 1. Build Agent
    agent = (
        AgentBuilder("sequential-bot").with_identity("TaskDoer", "You do tasks.").with_reasoning(model="gpt-4o").build()
    )

    # 2. Add to Linear Flow
    from coreason_manifest.builder import NewLinearFlow

    flow_builder = NewLinearFlow("simple-sequence")

    flow_builder.add_agent(agent)

    # Verify it was added to sequence
    assert agent in flow_builder.sequence

    # 3. Build Flow
    flow = flow_builder.build()

    assert flow is not None
    assert flow.sequence[0] == agent
