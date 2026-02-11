import pytest

from coreason_manifest.builder import NewGraphFlow, NewLinearFlow, create_supervision
from coreason_manifest.spec.core.engines import Supervision
from coreason_manifest.spec.core.nodes import AgentNode, Brain


def test_builder_integration_circuit_breaker() -> None:
    # Linear Flow
    lf = NewLinearFlow(name="Test Linear")
    lf.set_circuit_breaker(error_threshold=5, reset_timeout=30)

    # Add a dummy node to pass sequence cannot be empty check
    node = AgentNode(
        id="dummy_linear",
        metadata={},
        supervision=None,
        brain=Brain(role="dummy", persona="dummy", reasoning=None, reflex=None),
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
        brain=Brain(role="dummy", persona="dummy", reasoning=None, reflex=None),
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
    sup = Supervision(
        strategy="degrade",
        max_retries=3,
        fallback=None,
        retry_delay_seconds=1.5,
        backoff_factor=2.5,
        default_payload={"status": "mock"},
    )

    assert sup.strategy == "degrade"
    assert sup.max_retries == 3
    assert sup.retry_delay_seconds == 1.5
    assert sup.backoff_factor == 2.5
    assert sup.default_payload == {"status": "mock"}

    # Helper creation
    sup2 = create_supervision(retries=2, strategy="escalate", backoff=3.0, delay=0.5, default=None)
    assert sup2.strategy == "escalate"
    assert sup2.max_retries == 2
    assert sup2.backoff_factor == 3.0
    assert sup2.retry_delay_seconds == 0.5
    assert sup2.default_payload is None


def test_validator_catch_degrade_missing_payload() -> None:
    sup = Supervision(
        strategy="degrade",
        max_retries=3,
        fallback=None,
        default_payload=None,  # Invalid for degrade
    )

    node = AgentNode(
        id="node1",
        metadata={},
        supervision=sup,
        brain=Brain(role="tester", persona="tester", reasoning=None, reflex=None),
        tools=[],
    )

    lf = NewLinearFlow(name="Invalid Flow")
    lf.add_step(node)

    # Validation is called in build()
    with pytest.raises(ValueError, match=r"Node 'node1' is set to 'degrade' but missing 'default_payload'\."):
        lf.build()


def test_validator_catch_invalid_backoff() -> None:
    sup = Supervision(
        strategy="restart",
        max_retries=3,
        fallback=None,
        backoff_factor=0.5,  # Invalid < 1.0
    )

    node = AgentNode(
        id="node2",
        metadata={},
        supervision=sup,
        brain=Brain(role="tester", persona="tester", reasoning=None, reflex=None),
        tools=[],
    )

    lf = NewLinearFlow(name="Invalid Flow Backoff")
    lf.add_step(node)

    with pytest.raises(ValueError, match=r"backoff_factor must be >= 1\.0"):
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
        brain=Brain(role="dummy", persona="dummy", reasoning=None, reflex=None),
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
        brain=Brain(role="dummy", persona="dummy", reasoning=None, reflex=None),
        tools=[],
    )
    lf.add_step(node)

    with pytest.raises(
        ValueError, match="Circuit Breaker Error: 'fallback_node_id' points to missing ID 'missing_node'"
    ):
        lf.build()

    # 2. Invalid Supervision Fallback
    sup = Supervision(
        strategy="escalate",
        max_retries=3,
        fallback="missing_sup_node",
        retry_delay_seconds=1.0,
        backoff_factor=2.0,
    )

    lf2 = NewLinearFlow(name="Invalid Sup Fallback")
    node2 = AgentNode(
        id="node2",
        metadata={},
        supervision=sup,
        brain=Brain(role="dummy", persona="dummy", reasoning=None, reflex=None),
        tools=[],
    )
    lf2.add_step(node2)

    with pytest.raises(
        ValueError, match="Supervision Error: Node 'node2' fallback points to missing ID 'missing_sup_node'"
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
        input_schema={"type": "object", "properties": {"reason": {"type": "string"}}}
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
