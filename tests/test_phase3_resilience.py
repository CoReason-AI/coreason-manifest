import pytest
from pydantic import ValidationError

from coreason_manifest.builder import NewGraphFlow, NewLinearFlow, create_supervision
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile, PlannerNode, SwarmNode, SwitchNode
from coreason_manifest.spec.core.resilience import (
    ErrorDomain,
    ErrorHandler,
    EscalationStrategy,
    FallbackStrategy,
    ReflexionStrategy,
    RetryStrategy,
    SupervisionPolicy,
)


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
        handlers=[], default_strategy=RetryStrategy(max_attempts=3, backoff_factor=2.5, initial_delay_seconds=1.5)
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
    # Reflexion is only for Agents/Inspectors/Swarms/Planners. Try putting it on a SwitchNode.
    policy = SupervisionPolicy(
        handlers=[],
        default_strategy=ReflexionStrategy(
            max_attempts=3, critic_model="gpt-4", critic_prompt="Fix it", include_trace=True
        ),
    )

    node = SwitchNode(id="switch1", metadata={}, supervision=policy, variable="x", cases={}, default="next")

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
            # max_attempts removed
            queue_name="",  # Invalid empty
            notification_level="warning",
            timeout_seconds=10,
        ),
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
    policy = SupervisionPolicy(handlers=[], default_strategy=FallbackStrategy(fallback_node_id="missing_sup_node"))

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


def test_error_handler_regex_validation() -> None:
    """Test that ErrorHandler validates regex patterns."""
    # Valid regex
    ErrorHandler(
        match_domain=[ErrorDomain.SYSTEM], match_pattern=r"^Error \d+$", strategy=RetryStrategy(max_attempts=3)
    )

    # Invalid regex
    with pytest.raises(ValidationError, match="Invalid regex pattern"):
        ErrorHandler(
            match_domain=[ErrorDomain.SYSTEM], match_pattern="[unclosed group", strategy=RetryStrategy(max_attempts=3)
        )


def test_swarm_reflexion_support() -> None:
    """Test that SwarmNode supports ReflexionStrategy."""
    policy = SupervisionPolicy(
        handlers=[],
        default_strategy=ReflexionStrategy(
            max_attempts=3, critic_model="gpt-4", critic_prompt="Fix", include_trace=True
        ),
    )

    # Swarm node
    swarm = SwarmNode(
        id="swarm1",
        type="swarm",
        metadata={},
        supervision=policy,
        worker_profile="worker",
        workload_variable="tasks",
        distribution_strategy="sharded",
        max_concurrency=5,
        failure_tolerance_percent=0.2,
        reducer_function="concat",
        output_variable="results",
        aggregator_model=None,
    )

    gf = NewGraphFlow(name="Swarm Flow")
    gf.add_node(swarm)

    # Add dummy worker profile to pass integrity check
    gf.define_profile("worker", "role", "persona")

    # Should not raise validation error
    flow = gf.build()
    assert flow.graph.nodes["swarm1"].supervision is not None


def test_fallback_cycle_detection() -> None:
    """Test detection of fallback cycles."""
    # Node A -> Node B
    policy_a = SupervisionPolicy(handlers=[], default_strategy=FallbackStrategy(fallback_node_id="node_b"))

    # Node B -> Node A
    policy_b = SupervisionPolicy(handlers=[], default_strategy=FallbackStrategy(fallback_node_id="node_a"))

    node_a = AgentNode(id="node_a", metadata={}, supervision=policy_a, profile="p", tools=[], type="agent")

    node_b = AgentNode(id="node_b", metadata={}, supervision=policy_b, profile="p", tools=[], type="agent")

    gf = NewGraphFlow(name="Cycle Flow")
    gf.add_node(node_a).add_node(node_b)
    gf.define_profile("p", "r", "p")

    with pytest.raises(ValueError, match="Fallback cycle detected"):
        gf.build()


def test_error_handler_criteria_existence() -> None:
    """Test that ErrorHandler requires at least one criterion."""
    with pytest.raises(ValueError, match="ErrorHandler must specify at least one matching criterion"):
        ErrorHandler(
            match_domain=None,
            match_pattern=None,
            match_error_code=None,
            strategy=RetryStrategy(max_attempts=3)
        )


def test_planner_reflexion_support() -> None:
    """Test that PlannerNode supports ReflexionStrategy."""
    policy = SupervisionPolicy(
        handlers=[],
        default_strategy=ReflexionStrategy(
            max_attempts=3, critic_model="gpt-4", critic_prompt="Fix", include_trace=True
        ),
    )

    planner = PlannerNode(
        id="planner1",
        type="planner",
        metadata={},
        supervision=policy,
        goal="make plan",
        optimizer=None,
        output_schema={"type": "object"}
    )

    gf = NewGraphFlow(name="Planner Flow")
    gf.add_node(planner)

    # Should not raise validation error
    flow = gf.build()
    assert flow.graph.nodes["planner1"].supervision is not None


def test_resource_error_domain() -> None:
    """Test using the RESOURCE error domain."""
    handler = ErrorHandler(
        match_domain=[ErrorDomain.RESOURCE],
        strategy=RetryStrategy(max_attempts=3)
    )
    assert handler.match_domain is not None
    assert ErrorDomain.RESOURCE in handler.match_domain
