import pytest

from coreason_manifest.builder import NewGraphFlow, NewLinearFlow, create_supervision
from coreason_manifest.spec.core.resilience import (
    EscalationStrategy,
    FallbackStrategy,
    ReflexionStrategy,
    RetryStrategy,
    SupervisionPolicy,
)
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile, SwitchNode


def test_builder_integration_circuit_breaker() -> None:
    # Linear Flow
    lf = NewLinearFlow(name="Test Linear")
    lf.set_circuit_breaker(error_threshold=5, reset_timeout=30)

    # Add a dummy node to pass sequence cannot be empty check
    node = AgentNode(
        id="dummy_linear",
        metadata={},
        supervision=None,
        profile=CognitiveProfile(role="dummy", persona="dummy", reasoning=None, fast_path=None),
        tools=[],
    )
    lf.add_step(node)

    flow = lf.build()

    assert flow.governance is not None
    assert flow.governance.circuit_breaker is not None
    assert flow.governance.circuit_breaker.error_threshold_count == 5
    assert flow.governance.circuit_breaker.reset_timeout_seconds == 30
    assert flow.governance.circuit_breaker.fallback_node_id is None

    # Graph Flow
    gf = NewGraphFlow(name="Test Graph")
    gf.set_circuit_breaker(error_threshold=10, reset_timeout=60, fallback_node="dummy")
    # Add a dummy node so build() passes validation "Graph must contain at least one node"
    node_g = AgentNode(
        id="dummy",
        metadata={},
        supervision=None,
        profile=CognitiveProfile(role="dummy", persona="dummy", reasoning=None, fast_path=None),
        tools=[],
    )
    gf.add_node(node_g)

    flow_g = gf.build()
    assert flow_g.governance is not None
    assert flow_g.governance.circuit_breaker is not None
    assert flow_g.governance.circuit_breaker.error_threshold_count == 10
    assert flow_g.governance.circuit_breaker.reset_timeout_seconds == 60
    assert flow_g.governance.circuit_breaker.fallback_node_id == "dummy"


def test_supervision_logic() -> None:
    # Manual creation
    policy = SupervisionPolicy(
        handlers=[],
        default_strategy=RetryStrategy(max_attempts=3, backoff_factor=2.5, initial_delay_seconds=1.5)
    )

    strategy = policy.default_strategy
    assert isinstance(strategy, RetryStrategy)
    assert strategy.max_attempts == 3
    assert strategy.backoff_factor == 2.5
    assert strategy.initial_delay_seconds == 1.5

    # Helper creation
    policy2 = create_supervision(retries=2, strategy="retry", backoff=3.0, delay=0.5)
    assert isinstance(policy2.default_strategy, RetryStrategy)
    assert policy2.default_strategy.max_attempts == 2
    assert policy2.default_strategy.backoff_factor == 3.0
    assert policy2.default_strategy.initial_delay_seconds == 0.5


def test_validator_catch_reflexion_type_mismatch() -> None:
    # Reflexion is only for Agents/Inspectors. Try putting it on a SwitchNode.
    policy = SupervisionPolicy(
        handlers=[],
        default_strategy=ReflexionStrategy(
            max_attempts=3,
            critic_model="gpt-4",
            critic_prompt="Fix it",
            include_trace=True
        )
    )

    node = SwitchNode(
        id="switch1",
        metadata={},
        supervision=policy,
        variable="x",
        cases={},
        default="next"
    )

    lf = NewLinearFlow(name="Invalid Flow")
    lf.add_step(node)

    # SwitchNode integrity requires target IDs to exist
    lf.add_agent_ref("next", "profile1")
    lf.define_profile("profile1", "role", "persona")

    with pytest.raises(ValueError, match=r"uses ReflexionStrategy but is of type 'switch'"):
        lf.build()


def test_validator_catch_escalation_empty_queue() -> None:
    policy = SupervisionPolicy(
        handlers=[],
        default_strategy=EscalationStrategy(
            max_attempts=3,
            queue_name="", # Invalid empty
            notification_level="warning",
            timeout_seconds=10
        )
    )

    node = AgentNode(
        id="node_esc",
        metadata={},
        supervision=policy,
        profile=CognitiveProfile(role="dummy", persona="dummy", reasoning=None, fast_path=None),
        tools=[],
    )

    lf = NewLinearFlow(name="Invalid Escalation")
    lf.add_step(node)

    with pytest.raises(ValueError, match="uses EscalationStrategy with empty queue_name"):
        lf.build()


def test_builder_integration_governance_update() -> None:
    # Test setting circuit breaker when governance already exists
    from coreason_manifest.spec.core.governance import Governance

    lf = NewLinearFlow(name="Test Update")
    lf.set_governance(Governance(rate_limit_rpm=100))
    lf.set_circuit_breaker(error_threshold=5, reset_timeout=30)

    # Add dummy node
    node = AgentNode(
        id="dummy_update",
        metadata={},
        supervision=None,
        profile=CognitiveProfile(role="dummy", persona="dummy", reasoning=None, fast_path=None),
        tools=[],
    )
    lf.add_step(node)

    flow = lf.build()

    assert flow.governance is not None
    assert flow.governance.rate_limit_rpm == 100
    assert flow.governance.circuit_breaker is not None
    assert flow.governance.circuit_breaker.error_threshold_count == 5

    # Same for GraphFlow
    gf = NewGraphFlow(name="Test Graph Update")
    gf.set_governance(Governance(timeout_seconds=60))
    gf.set_circuit_breaker(error_threshold=2, reset_timeout=10)

    gf.add_node(node)  # Use same dummy node

    flow_g = gf.build()
    assert flow_g.governance is not None
    assert flow_g.governance.timeout_seconds == 60
    assert flow_g.governance.circuit_breaker is not None
    assert flow_g.governance.circuit_breaker.error_threshold_count == 2


def test_validator_catch_invalid_fallback_ids() -> None:
    # 1. Invalid Circuit Breaker Fallback
    lf = NewLinearFlow(name="Invalid CB Fallback")
    lf.set_circuit_breaker(error_threshold=5, reset_timeout=30, fallback_node="missing_node")

    node = AgentNode(
        id="node1",
        metadata={},
        supervision=None,
        profile=CognitiveProfile(role="dummy", persona="dummy", reasoning=None, fast_path=None),
        tools=[],
    )
    lf.add_step(node)

    with pytest.raises(
        ValueError, match="Circuit Breaker Error: 'fallback_node_id' points to missing ID 'missing_node'"
    ):
        lf.build()

    # 2. Invalid Supervision Fallback
    policy = SupervisionPolicy(
        handlers=[],
        default_strategy=FallbackStrategy(max_attempts=3, fallback_node_id="missing_sup_node")
    )

    lf2 = NewLinearFlow(name="Invalid Sup Fallback")
    node2 = AgentNode(
        id="node2",
        metadata={},
        supervision=policy,
        profile=CognitiveProfile(role="dummy", persona="dummy", reasoning=None, fast_path=None),
        tools=[],
    )
    lf2.add_step(node2)

    with pytest.raises(
        ValueError, match="Resilience Error: Node 'node2' fallback points to missing ID 'missing_sup_node'"
    ):
        lf2.build()


def test_human_node_options_and_visualizer() -> None:
    from coreason_manifest.spec.core.nodes import HumanNode
    from coreason_manifest.utils.visualizer import to_mermaid

    # Test HumanNode instantiation with options
    human = HumanNode(
        id="human_decision",
        metadata={},
        supervision=None,
        prompt="Approve or Reject?",
        timeout_seconds=600,
        options=["Approve", "Reject"],
        input_schema={"type": "object", "properties": {"reason": {"type": "string"}}},
    )

    assert human.options == ["Approve", "Reject"]
    assert human.input_schema is not None

    # Test Visualizer rendering
    lf = NewLinearFlow(name="Human Flow")
    lf.add_step(human)
    flow = lf.build()

    mermaid_code = to_mermaid(flow)

    # Check if options are present in the mermaid code
    assert "[Approve, Reject]" in mermaid_code
    assert "(Human)" in mermaid_code
    assert "human_decision" in mermaid_code


def test_circuit_breaker_export() -> None:
    # Test that CircuitBreaker is exported from spec.core
    from coreason_manifest.spec.core import CircuitBreaker

    assert CircuitBreaker is not None
