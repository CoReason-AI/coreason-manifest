import pytest
from pydantic import ValidationError

from coreason_manifest.builder import NewGraphFlow, NewLinearFlow, create_supervision
from coreason_manifest.spec.core.engines import ModelCriteria
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


def test_create_supervision_fallback_missing_id() -> None:
    """Test create_supervision raises error when fallback_id is missing for fallback strategy."""
    with pytest.raises(ValidationError):
        create_supervision(retries=3, strategy="fallback", fallback_id=None)


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
            match_domain=None, match_pattern=None, match_error_code=None, strategy=RetryStrategy(max_attempts=3)
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
        output_schema={"type": "object"},
    )

    gf = NewGraphFlow(name="Planner Flow")
    gf.add_node(planner)

    # Should not raise validation error
    flow = gf.build()
    assert flow.graph.nodes["planner1"].supervision is not None


def test_resource_error_domain() -> None:
    """Test using the RESOURCE error domain."""
    handler = ErrorHandler(match_domain=[ErrorDomain.RESOURCE], strategy=RetryStrategy(max_attempts=3))
    assert handler.match_domain is not None
    assert ErrorDomain.RESOURCE in handler.match_domain


def test_reflexion_structured_output() -> None:
    """Test that ReflexionStrategy accepts a JSON schema."""
    strategy = ReflexionStrategy(
        max_attempts=3,
        critic_model="gpt-4",
        critic_prompt="Fix",
        include_trace=True,
        critic_schema={"type": "object", "properties": {"fix": {"type": "string"}}},
    )
    assert strategy.critic_schema is not None
    assert strategy.critic_schema["properties"]["fix"]["type"] == "string"


def test_error_handler_integer_codes() -> None:
    """Test that ErrorHandler accepts integer error codes."""
    handler = ErrorHandler(
        match_error_code=[429, 503, "rate_limit"],  # type: ignore
        strategy=RetryStrategy(max_attempts=3),
    )
    # Codes should be normalized to strings
    assert handler.match_error_code == ["429", "503", "rate_limit"]


def test_error_handler_single_value_codes() -> None:
    """Test that ErrorHandler accepts single value error codes."""
    # Single int
    handler1 = ErrorHandler(
        match_error_code=404,  # type: ignore
        strategy=RetryStrategy(max_attempts=3),
    )
    assert handler1.match_error_code == ["404"]

    # Single str
    handler2 = ErrorHandler(
        match_error_code="not_found",  # type: ignore
        strategy=RetryStrategy(max_attempts=3),
    )
    assert handler2.match_error_code == ["not_found"]


def test_error_handler_invalid_codes() -> None:
    """Test that ErrorHandler raises validation error for invalid code types."""
    # Dict is not handled by normalizer, should fall through and fail pydantic validation
    with pytest.raises(ValidationError):
        ErrorHandler(
            match_error_code={"code": 400},  # type: ignore
            strategy=RetryStrategy(max_attempts=3),
        )


def test_escalation_template_syntax() -> None:
    """Test EscalationStrategy template validation."""
    # Template with jinja syntax
    s1 = EscalationStrategy(
        queue_name="q",
        notification_level="info",
        timeout_seconds=10,
        template="Error: {{ error }}",
    )
    assert s1.template == "Error: {{ error }}"

    # Template without jinja syntax (should pass with warning/note internally)
    s2 = EscalationStrategy(
        queue_name="q",
        notification_level="info",
        timeout_seconds=10,
        template="Static error message",
    )
    assert s2.template == "Static error message"


def test_escalation_template() -> None:
    """Test that EscalationStrategy accepts a template."""
    strategy = EscalationStrategy(
        queue_name="human-review",
        notification_level="warning",
        timeout_seconds=600,
        template="Agent failed at step {{step_id}}: {{error}}",
    )
    assert strategy.template == "Agent failed at step {{step_id}}: {{error}}"


def test_reflexion_max_trace_turns() -> None:
    """Test that ReflexionStrategy has max_trace_turns."""
    strategy = ReflexionStrategy(
        max_attempts=3,
        critic_model="gpt-4",
        critic_prompt="Fix",
        include_trace=True,
        max_trace_turns=5,
    )
    assert strategy.max_trace_turns == 5


def test_retry_max_delay_seconds() -> None:
    """Test that RetryStrategy has max_delay_seconds."""
    strategy = RetryStrategy(
        max_attempts=3,
        backoff_factor=2.0,
        initial_delay_seconds=1.0,
        max_delay_seconds=30.0,
    )
    assert strategy.max_delay_seconds == 30.0


def test_supervision_optional_default_strategy() -> None:
    """Test that SupervisionPolicy default_strategy is optional."""
    policy = SupervisionPolicy(
        handlers=[ErrorHandler(match_domain=[ErrorDomain.SYSTEM], strategy=RetryStrategy(max_attempts=3))],
        default_strategy=None,
    )
    assert policy.default_strategy is None


def test_strategy_name() -> None:
    """Test that ResilienceStrategy has a name field."""
    strategy = RetryStrategy(max_attempts=3, name="my-retry-strategy")
    assert strategy.name == "my-retry-strategy"


def test_supervision_max_cumulative_actions() -> None:
    """Test that SupervisionPolicy has max_cumulative_actions."""
    policy = SupervisionPolicy(
        handlers=[],
        default_strategy=RetryStrategy(max_attempts=3),
        max_cumulative_actions=20,
    )
    assert policy.max_cumulative_actions == 20


def test_timeout_error_domain() -> None:
    """Test using the TIMEOUT error domain."""
    handler = ErrorHandler(
        match_domain=[ErrorDomain.TIMEOUT],
        strategy=RetryStrategy(max_attempts=3),
    )
    assert handler.match_domain is not None
    assert ErrorDomain.TIMEOUT in handler.match_domain


def test_reflexion_invalid_schema() -> None:
    """Test that ReflexionStrategy validates JSON schema."""
    with pytest.raises(ValidationError, match="valid JSON Schema"):
        ReflexionStrategy(
            max_attempts=3,
            critic_model="gpt-4",
            critic_prompt="Fix",
            include_trace=True,
            critic_schema={"invalid": "schema"},  # Missing type/properties/$ref
        )


def test_retry_backoff_ge_1() -> None:
    """Test that RetryStrategy backoff_factor must be >= 1.0."""
    with pytest.raises(ValidationError, match="backoff_factor"):
        RetryStrategy(max_attempts=3, backoff_factor=0.5)


def test_reflexion_zombie_config() -> None:
    """Test that max_trace_turns is cleared if include_trace is False."""
    strategy = ReflexionStrategy(
        max_attempts=3,
        critic_model="gpt-4",
        critic_prompt="Fix",
        include_trace=False,
        max_trace_turns=10,
    )
    assert strategy.max_trace_turns is None


def test_supervision_limits_conflict() -> None:
    """Test that SupervisionPolicy raises error if strategy limit > global limit."""
    with pytest.raises(ValidationError, match="SupervisionPolicy global limit"):
        SupervisionPolicy(
            handlers=[],
            default_strategy=RetryStrategy(max_attempts=20),
            max_cumulative_actions=10,
        )


def test_reflexion_capability_requirement() -> None:
    """Test that ReflexionStrategy enforces json_mode capability if critic_schema is present."""
    # Case 1: Missing json_mode
    model_without_json = ModelCriteria(capabilities=["vision"])
    with pytest.raises(ValidationError, match="does not explicitly require 'json_mode'"):
        ReflexionStrategy(
            max_attempts=3,
            critic_model=model_without_json,
            critic_prompt="Fix",
            critic_schema={"type": "object", "properties": {"fix": {"type": "string"}}},
        )

    # Case 2: Has json_mode
    model_with_json = ModelCriteria(capabilities=["json_mode"])
    strategy = ReflexionStrategy(
        max_attempts=3,
        critic_model=model_with_json,
        critic_prompt="Fix",
        critic_schema={"type": "object", "properties": {"fix": {"type": "string"}}},
    )
    assert strategy.critic_model == model_with_json


def test_security_retry_forbidden() -> None:
    """Test that SECURITY domain cannot use RetryStrategy."""
    with pytest.raises(ValidationError, match="Security Policy Violation"):
        ErrorHandler(
            match_domain=[ErrorDomain.SECURITY],
            strategy=RetryStrategy(max_attempts=3),
        )


def test_strategy_name_slug() -> None:
    """Test that strategy names must be slug-formatted."""
    # Valid name
    RetryStrategy(max_attempts=3, name="valid_name")
    RetryStrategy(max_attempts=3, name="valid-name-123")

    # Invalid names
    with pytest.raises(ValidationError, match="metric-safe"):
        RetryStrategy(max_attempts=3, name="Invalid Name")
    with pytest.raises(ValidationError, match="metric-safe"):
        RetryStrategy(max_attempts=3, name="invalid/name")


def test_reflexion_schema_object_properties() -> None:
    """Test that object type schemas require properties."""
    # Valid schema
    ReflexionStrategy(
        max_attempts=3,
        critic_model="gpt-4",
        critic_prompt="Fix",
        include_trace=True,
        critic_schema={"type": "object", "properties": {"fix": {"type": "string"}}},
    )

    # Invalid schema (missing properties for object)
    with pytest.raises(ValidationError, match="properties' are required"):
        ReflexionStrategy(
            max_attempts=3,
            critic_model="gpt-4",
            critic_prompt="Fix",
            include_trace=True,
            critic_schema={"type": "object"},
        )
