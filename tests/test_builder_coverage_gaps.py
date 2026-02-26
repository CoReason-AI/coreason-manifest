
import pytest
from coreason_manifest.builder import NewLinearFlow, NewGraphFlow, AgentBuilder, create_resilience
from coreason_manifest.spec.core.nodes import AgentNode
from coreason_manifest.spec.core.governance import Governance, CircuitBreaker, OperationalPolicy, FinancialLimits, ComputeLimits, DataLimits
from coreason_manifest.spec.core.tools import ToolPack
from coreason_manifest.spec.core.resilience import SupervisionPolicy, RetryStrategy, FallbackStrategy, EscalationStrategy

def test_flow_builder_operational_policy():
    flow = NewLinearFlow("test-flow")

    # Test setting operational policy
    flow.set_operational_policy(
        max_cost_usd=10.0,
        max_tokens=1000,
        fallback_model="gpt-3.5-turbo",
        max_steps=50,
        max_execution_time_seconds=600,
        max_concurrent_agents=5,
        max_rows_per_query=100,
        max_payload_bytes=1024,
        max_search_results=10
    )

    assert flow.governance is not None
    assert flow.governance.operational_policy is not None
    op = flow.governance.operational_policy
    assert op.financial.max_cost_usd == 10.0
    assert op.compute.max_cognitive_steps == 50
    assert op.data.max_rows_per_query == 100

    # Test updating existing governance
    flow.set_operational_policy(max_cost_usd=20.0)
    assert flow.governance.operational_policy.financial.max_cost_usd == 20.0

    # Explicitly test partial updates to trigger all if branches
    flow_partial = NewLinearFlow("test-partial")

    # Only financial
    flow_partial.set_operational_policy(max_cost_usd=5.0)
    assert flow_partial.governance.operational_policy.financial.max_cost_usd == 5.0
    assert flow_partial.governance.operational_policy.compute is None
    assert flow_partial.governance.operational_policy.data is None

    # Only compute
    flow_partial_compute = NewLinearFlow("test-partial-compute")
    flow_partial_compute.set_operational_policy(max_steps=10)
    assert flow_partial_compute.governance.operational_policy.financial is None
    assert flow_partial_compute.governance.operational_policy.compute.max_cognitive_steps == 10
    assert flow_partial_compute.governance.operational_policy.data is None

    # Only data
    flow_partial_data = NewLinearFlow("test-partial-data")
    flow_partial_data.set_operational_policy(max_rows_per_query=10)
    assert flow_partial_data.governance.operational_policy.financial is None
    assert flow_partial_data.governance.operational_policy.compute is None
    assert flow_partial_data.governance.operational_policy.data.max_rows_per_query == 10

def test_flow_builder_circuit_breaker():
    flow = NewLinearFlow("test-flow")

    # Test setting circuit breaker
    flow.set_circuit_breaker(error_threshold=5, reset_timeout=30, fallback_node="fallback-agent")

    assert flow.governance is not None
    assert flow.governance.circuit_breaker is not None
    cb = flow.governance.circuit_breaker
    assert cb.error_threshold_count == 5
    assert cb.reset_timeout_seconds == 30
    assert cb.fallback_node_id == "fallback-agent"

    # Test updating existing governance
    flow.set_circuit_breaker(error_threshold=10, reset_timeout=60)
    assert flow.governance.circuit_breaker.error_threshold_count == 10

def test_flow_builder_add_agent_ref():
    flow = NewLinearFlow("test-flow")
    flow.define_profile("researcher", "researcher", "You verify facts")

    flow.add_agent_ref("agent-1", "researcher", tools=["web-search"])

    assert len(flow.steps) == 1
    node = flow.steps[0]
    assert isinstance(node, AgentNode)
    assert node.id == "agent-1"
    assert node.profile == "researcher"
    assert "web-search" in node.tools

def test_flow_builder_add_shadow_node():
    flow = NewLinearFlow("test-flow")

    flow.add_shadow_node("shadow-1", "Approve this plan?", shadow_timeout=120)

    assert len(flow.steps) == 1
    node = flow.steps[0]
    assert node.type == "human"
    assert node.id == "shadow-1"
    assert node.prompt == "Approve this plan?"
    assert node.interaction_mode == "shadow"
    assert node.escalation.timeout_seconds == 120

def test_flow_builder_add_inspector():
    flow = NewLinearFlow("test-flow")

    flow.add_inspector("inspector-1", "output_var", "is valid", "validation_result", pass_threshold=0.8)

    assert len(flow.steps) == 1
    node = flow.steps[0]
    assert node.type == "inspector"
    assert node.id == "inspector-1"
    assert node.target_variable == "output_var"
    assert node.pass_threshold == 0.8

def test_new_linear_flow_methods():
    flow = NewLinearFlow("test-flow")
    agent = AgentBuilder("agent-1").with_identity("helper", "You help").build()

    flow.add_agent(agent)
    # The duplicate ID caused validation failure in previous run.
    agent2 = AgentBuilder("agent-2").with_identity("helper", "You help").build()
    flow.add_step(agent2)

    assert len(flow.steps) == 2
    assert flow.steps[0].id == "agent-1"

    built_flow = flow.build()
    assert built_flow.kind == "LinearFlow"
    assert len(built_flow.steps) == 2

def test_new_graph_flow_methods():
    flow = NewGraphFlow("test-graph")
    agent1 = AgentBuilder("start").with_identity("starter", "You start").build()
    agent2 = AgentBuilder("end").with_identity("ender", "You end").build()

    flow.add_node(agent1)
    flow.add_agent(agent2)

    flow.connect("start", "end")

    flow.set_entry_point("start")

    flow.set_interface(inputs={"in": "string"}, outputs={"out": "string"})

    flow.set_blackboard({"var1": {"type": "string", "description": "test var"}})

    built_flow = flow.build()

    assert built_flow.kind == "GraphFlow"
    assert len(built_flow.graph.nodes) == 2
    assert len(built_flow.graph.edges) == 1
    assert built_flow.graph.entry_point == "start"
    assert built_flow.interface.inputs.json_schema == {"in": "string"}
    assert built_flow.blackboard.variables["var1"]["type"] == "string"

def test_agent_builder_human_steering():
    # Case 1: No previous resilience
    builder = AgentBuilder("agent-1")
    builder.with_human_steering(timeout=600, fallback_id="human-agent")
    assert builder.resilience.timeout_seconds == 600
    assert builder.resilience.fallback_node_id == "human-agent"

    # Case 2: Upgrade existing resilience (RetryStrategy) to SupervisionPolicy
    builder = AgentBuilder("agent-2")
    builder.with_resilience(retries=3, strategy="retry")
    builder.with_human_steering(timeout=300)
    assert isinstance(builder.resilience, SupervisionPolicy)
    # Check if max_cumulative_actions is calculated correctly: max(10, retries + 1) -> max(10, 4) = 10
    assert builder.resilience.max_cumulative_actions == 10

    # Case 3: Upgrade existing resilience with high retries
    builder = AgentBuilder("agent-3")
    builder.with_resilience(retries=15, strategy="retry")
    builder.with_human_steering(timeout=300)
    assert isinstance(builder.resilience, SupervisionPolicy)
    # max(10, 15 + 1) = 16
    assert builder.resilience.max_cumulative_actions == 16

    # Case 4: Already a SupervisionPolicy
    builder = AgentBuilder("agent-4")
    # First setup a supervision policy indirectly via case 2 logic or manually
    builder.with_resilience(retries=3, strategy="retry")
    builder.with_human_steering(timeout=300) # Now it is SupervisionPolicy
    # Add another steering, should append handler
    initial_handlers = len(builder.resilience.handlers)
    builder.with_human_steering(timeout=600)
    assert len(builder.resilience.handlers) == initial_handlers + 1

def test_agent_builder_build_validation():
    builder = AgentBuilder("agent-1")
    # Missing identity
    with pytest.raises(ValueError, match="Agent identity"):
        builder.build()

    builder.with_identity("role", "persona")
    # Should pass now
    builder.build()

def test_create_resilience_coverage():
    # Test retry
    res = create_resilience(retries=3, strategy="retry")
    assert isinstance(res, RetryStrategy)
    assert res.max_attempts == 3

    # Test fallback success
    res = create_resilience(retries=3, strategy="fallback", fallback_id="backup")
    assert isinstance(res, FallbackStrategy)
    assert res.fallback_node_id == "backup"

    # Test fallback failure
    with pytest.raises(ValueError, match="fallback_id is required"):
        create_resilience(retries=3, strategy="fallback")

    # Test escalate (default)
    res = create_resilience(retries=3, strategy="escalate", queue_name="custom")
    assert isinstance(res, EscalationStrategy)
    assert res.queue_name == "custom"
