import pytest
from pydantic import ValidationError

from coreason_manifest.spec.v2.agent import (
    CognitiveProfile,
    ComponentPriority,
    ContextDependency,
)
from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    PolicyConfig,
)


def test_inline_cognitive_profile() -> None:
    """Test creating an AgentNode with an inline cognitive profile."""
    construct = CognitiveProfile(
        role="analyst",
        reasoning_mode="chain_of_thought",
        knowledge_contexts=[ContextDependency(name="financial_data", priority=ComponentPriority.HIGH)],
    )

    agent = AgentNode(
        id="agent_1",
        construct=construct,
        # agent_ref is None by default
    )

    assert agent.agent_ref is None
    assert agent.construct is not None
    assert agent.construct.role == "analyst"
    assert agent.construct.reasoning_mode == "chain_of_thought"
    assert len(agent.construct.knowledge_contexts) == 1
    assert agent.construct.knowledge_contexts[0].name == "financial_data"
    assert agent.construct.knowledge_contexts[0].priority == ComponentPriority.HIGH


def test_validation_failure() -> None:
    """Test validation failure when neither agent_ref nor construct is provided."""
    with pytest.raises(ValidationError) as excinfo:
        AgentNode(id="agent_fail")

    # Check that the error message contains the expected string
    assert "AgentNode must provide either 'agent_ref' (catalog) or 'construct' (inline)." in str(excinfo.value)


def test_token_budget() -> None:
    """Test PolicyConfig with token_budget."""
    policy = PolicyConfig(token_budget=8000, budget_cap_usd=0.50)

    assert policy.token_budget == 8000
    assert policy.budget_cap_usd == 0.50


def test_context_dependency_defaults() -> None:
    """Test ContextDependency defaults."""
    ctx = ContextDependency(name="default_ctx")
    assert ctx.priority == ComponentPriority.MEDIUM
    assert ctx.parameters == {}
