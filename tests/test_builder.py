import pytest

from coreason_manifest.builder import AgentBuilder, NewGraphFlow, NewLinearFlow, NewSwarmFlow
from coreason_manifest.spec.core.governance import Governance, OperationalPolicy
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile
from coreason_manifest.spec.core.tools import MCPServerConfig, MCPTool


def test_linear_builder() -> None:
    builder = NewLinearFlow("MyLinear", version="1.0.0", description="Desc")
    builder.define_profile("default", "role", "persona")

    # Use AgentNode instead of PlaceholderNode to be safe
    node1 = AgentNode(id="step1", type="agent", metadata={}, profile="default", tools=[])
    node2 = AgentNode(id="step2", type="agent", metadata={}, profile="default", tools=[])

    builder.add_step(node1)
    builder.add_step(node2)

    tp = MCPServerConfig(
        kind="MCPServerConfig",
        namespace="test",
        tools=[MCPTool(name="t1", input_schema={})],
        dependencies=[],
        env_vars=[],
    )
    builder.add_mcp_server(tp)

    gov = Governance(rate_limit_rpm=10)
    builder.set_governance(gov)

    flow = builder.build()

    assert flow.kind == "LinearFlow"
    assert flow.metadata.name == "MyLinear"
    assert len(flow.steps) == 2
    assert flow.definitions is not None
    assert len(flow.definitions.mcp_servers) == 1
    assert flow.governance is not None
    assert flow.governance.rate_limit_rpm == 10


def test_graph_builder() -> None:
    builder = NewGraphFlow("MyGraph", version="1.0.0", description="Desc")
    builder.define_profile("default", "role", "persona")

    node1 = AgentNode(id="n1", type="agent", metadata={}, profile="default", tools=[])
    node2 = AgentNode(id="n2", type="agent", metadata={}, profile="default", tools=[])

    builder.add_node(node1)
    builder.add_node(node2)
    builder.connect("n1", "n2", condition="ok")

    tp = MCPServerConfig(
        kind="MCPServerConfig",
        namespace="test",
        tools=[MCPTool(name="t1", input_schema={})],
        dependencies=[],
        env_vars=[],
    )
    builder.add_mcp_server(tp)

    gov = Governance(rate_limit_rpm=10)
    builder.set_governance(gov)

    # Test set_interface and memory
    builder.set_interface(
        inputs={"type": "object", "properties": {"in": {"type": "string"}}},
        outputs={"type": "object", "properties": {"out": {"type": "integer"}}},
    )

    builder.with_memory_tier("working", {"variables": {"var1": None}})
    builder.with_memory_tier("episodic", {"retention_policy": "forever"})

    flow = builder.build()

    assert flow.kind == "GraphFlow"
    assert flow.metadata.name == "MyGraph"
    assert len(flow.graph.nodes) == 2
    assert len(flow.graph.edges) == 1
    assert flow.graph.edges[0].from_node == "n1"
    assert flow.graph.edges[0].to_node == "n2"
    assert flow.graph.edges[0].condition == "ok"
    assert flow.definitions is not None
    assert len(flow.definitions.mcp_servers) == 1
    assert flow.governance is not None
    assert flow.governance.rate_limit_rpm == 10

    # Assert new features
    from coreason_manifest.spec.core.flow import DataSchema
    assert isinstance(flow.interface.inputs, DataSchema)
    assert flow.interface.inputs.json_schema == {"type": "object", "properties": {"in": {"type": "string"}}}
    assert isinstance(flow.interface.outputs, DataSchema)
    assert flow.interface.outputs.json_schema == {"type": "object", "properties": {"out": {"type": "integer"}}}
    assert flow.memory is not None
    assert flow.memory.working is not None
    assert "var1" in flow.memory.working.variables
    assert flow.memory.episodic is not None
    assert flow.memory.episodic.retention_policy == "forever"


def test_swarm_builder() -> None:
    builder = NewSwarmFlow("MySwarm", "1.0.0", "Desc")

    agent = AgentBuilder("agent1").with_identity("worker", "worker").build()
    builder.add_agent(agent)

    builder.set_routing("round_robin")
    # Termination criteria is now a typed object, not a dict
    from coreason_manifest.spec.core.flow import SchemaSatisfiedCriteria

    builder.add_termination(SchemaSatisfiedCriteria(target_variable="result", json_schema={"type": "object"}))

    flow = builder.build()

    assert flow.kind == "IntentFlow"
    assert len(flow.pool) == 1
    assert flow.routing_strategy == "round_robin"
    # termination_criteria can be a list or single object depending on build() logic.
    # NewSwarmFlow.build() takes the first element if length is 1.
    assert isinstance(flow.termination_criteria, SchemaSatisfiedCriteria)
    assert flow.termination_criteria.target_variable == "result"


def test_linear_builder_invalid() -> None:
    # Empty sequence is invalid because FlowBuilder calls validate_flow() which enforces it.
    builder = NewLinearFlow("Invalid")
    with pytest.raises(ValueError, match="Validation failed"):
        builder.build()


def test_graph_builder_invalid() -> None:
    from coreason_manifest.spec.interop.exceptions import ManifestError

    # Empty graph is invalid
    builder = NewGraphFlow("Invalid")

    with pytest.raises(ManifestError, match="CRSN-VAL-ENTRY-POINT-MISSING") as exc:
        builder.build()
    assert "CRSN-VAL-ENTRY-POINT-MISSING" in str(exc.value)


def test_builder_coverage_set_circuit_breaker_with_existing_governance() -> None:
    """Test setting circuit breaker when governance is already set."""
    builder = NewLinearFlow("Test", "1.0.0", "Desc")
    gov = Governance(rate_limit_rpm=10)
    builder.set_governance(gov)

    # This should trigger the `if self.governance:` branch in set_circuit_breaker
    builder.set_circuit_breaker(error_threshold=5, reset_timeout=30)

    assert builder.governance is not None
    assert builder.governance.rate_limit_rpm == 10
    assert builder.governance.circuit_breaker is not None
    assert builder.governance.circuit_breaker.error_threshold_count == 5


def test_builder_coverage_set_circuit_breaker_without_governance() -> None:
    """Test setting circuit breaker when governance is NOT set."""
    builder = NewLinearFlow("Test", "1.0.0", "Desc")
    # No governance set

    # This should trigger the `else:` branch in set_circuit_breaker
    builder.set_circuit_breaker(error_threshold=5, reset_timeout=30)

    assert builder.governance is not None
    assert builder.governance.circuit_breaker is not None
    assert builder.governance.circuit_breaker.error_threshold_count == 5


def test_builder_coverage_set_operational_policy_with_existing_governance() -> None:
    """Test setting operational policy when governance is already set."""
    builder = NewLinearFlow("Test", "1.0.0", "Desc")
    gov = Governance(rate_limit_rpm=10)
    builder.set_governance(gov)

    policy = OperationalPolicy(retry_counts={"default": 3})
    builder.set_operational_policy(policy)

    assert builder.governance is not None
    assert builder.governance.rate_limit_rpm == 10
    assert builder.governance.operational_policy is not None
    assert builder.governance.operational_policy.retry_counts["default"] == 3


def test_builder_coverage_set_operational_policy_without_governance() -> None:
    """Test setting operational policy when governance is NOT set."""
    builder = NewLinearFlow("Test", "1.0.0", "Desc")
    # No governance set

    policy = OperationalPolicy(retry_counts={"default": 3})
    builder.set_operational_policy(policy)

    assert builder.governance is not None
    assert builder.governance.operational_policy is not None
    assert builder.governance.operational_policy.retry_counts["default"] == 3


def test_builder_coverage_add_inspector_linear() -> None:
    """Test add_inspector method in NewLinearFlow."""
    builder = NewLinearFlow("Test", "1.0.0", "Desc")
    builder.add_inspector(node_id="inspector1", target="var1", criteria="criteria1", output="out1")
    assert len(builder.steps) == 1
    node = builder.steps[0]
    assert node.id == "inspector1"
    assert node.type == "inspector"


def test_builder_coverage_add_inspector_graph() -> None:
    """Test add_inspector method in NewGraphFlow."""
    builder = NewGraphFlow("Test", "1.0.0", "Desc")
    builder.add_inspector(node_id="inspector1", target="var1", criteria="criteria1", output="out1")
    assert "inspector1" in builder._nodes
    node = builder._nodes["inspector1"]
    assert node.type == "inspector"


def test_builder_coverage_add_agent_ref_defaults() -> None:
    """Test add_agent_ref with default tools=None."""
    # Linear
    builder_l = NewLinearFlow("Test", "1.0.0", "Desc")
    builder_l.define_profile("brain1", "role", "persona")
    builder_l.add_agent_ref("agent1", "brain1")  # Default tools=None -> []
    assert len(builder_l.steps) == 1
    node_l = builder_l.steps[0]
    assert isinstance(node_l, AgentNode)
    assert node_l.tools == []

    # Graph
    builder_g = NewGraphFlow("Test", "1.0.0", "Desc")
    builder_g.define_profile("brain1", "role", "persona")
    builder_g.add_agent_ref("agent1", "brain1")  # Default tools=None -> []
    assert "agent1" in builder_g._nodes
    node_g = builder_g._nodes["agent1"]
    assert isinstance(node_g, AgentNode)
    assert node_g.tools == []


def test_builder_coverage_explicit_add_agent() -> None:
    """Explicitly test add_agent to ensure coverage."""
    brain = CognitiveProfile(role="role", persona="persona", reasoning=None, fast_path=None)
    # AgentNode needs profile to be a valid ID or object.
    agent = AgentNode(id="agent1", type="agent", profile=brain, tools=[], metadata={}, resilience=None)

    # Linear
    builder_l = NewLinearFlow("Test", "1.0.0", "Desc")
    builder_l.add_agent(agent)
    assert len(builder_l.steps) == 1

    # Graph
    builder_g = NewGraphFlow("Test", "1.0.0", "Desc")
    builder_g.add_agent(agent)
    assert "agent1" in builder_g._nodes


def test_agent_builder() -> None:
    """Test the AgentBuilder fluent API."""
    # Basic build
    builder = AgentBuilder("agent1")
    builder.with_identity("role1", "persona1")
    agent = builder.build()
    assert agent.id == "agent1"
    assert isinstance(agent.profile, CognitiveProfile)
    assert agent.profile.role == "role1"
    assert agent.profile.persona == "persona1"

    # Full build
    builder = AgentBuilder("agent2")
    builder.with_identity("role2", "persona2")
    builder.with_reasoning(model="gpt-4")
    builder.with_fast_path(model="gpt-3.5")
    builder.with_tools(["tool1"])
    # with_supervision deprecated/removed, assume replaced or removed from builder tests for now
    # builder.with_supervision(retries=3)

    agent = builder.build()
    assert isinstance(agent.profile, CognitiveProfile)
    assert agent.profile.reasoning is not None
    assert agent.profile.fast_path is not None
    assert agent.tools == ["tool1"]
    # assert isinstance(agent.supervision, SupervisionPolicy)
    # assert isinstance(agent.supervision.default_strategy, EscalationStrategy)

    # Fail build
    builder = AgentBuilder("agent3")
    with pytest.raises(ValueError, match="Agent identity"):
        builder.build()


# def test_agent_builder_fallback_missing_id() -> None:
#     """Test AgentBuilder raises error when fallback_id is missing for fallback strategy."""
#     builder = AgentBuilder("agent_fallback")
#     with pytest.raises(ValidationError):
#         builder.with_supervision(retries=3, strategy="fallback")


def test_builder_validation_failure() -> None:
    """Cover NewLinearFlow.build() failure (lines 297-298)."""
    from coreason_manifest.spec.core.resilience import FallbackStrategy

    # Create builder
    builder = NewLinearFlow("Invalid Flow")

    # Define a valid profile so construction passes integrity check
    builder.define_profile("p1", "role", "persona")

    # Add agent with valid profile but invalid resilience fallback
    # Resilience fallback_node_id points to "missing_node"
    # AgentNode needs profile to be a valid ID or object.

    node = AgentNode(
        id="a1",
        metadata={},
        type="agent",
        profile="p1",
        tools=[],
        resilience=FallbackStrategy(fallback_node_id="missing_node"),
    )
    builder.add_step(node)

    # Build should raise ValueError because of validate_flow finding missing fallback node
    with pytest.raises(ValueError, match="Validation failed") as exc:
        builder.build()

    assert "missing ID 'missing_node'" in str(exc.value)


def test_builder_graph_entry_point_coverage() -> None:
    """Cover NewGraphFlow.set_entry_point (lines 297-298)."""
    from coreason_manifest.builder import NewGraphFlow
    from coreason_manifest.spec.core.nodes import AgentNode

    builder = NewGraphFlow("Graph Flow")
    builder.define_profile("p1", "role", "persona")

    node = AgentNode(id="start", metadata={}, profile="p1", tools=[], type="agent")
    builder.add_node(node)

    # Use set_entry_point
    builder.set_entry_point("start")

    flow = builder.build()
    assert flow.graph.entry_point == "start"


def test_builder_graph_auto_entry_point() -> None:
    """Cover NewGraphFlow.build() auto entry point (line 368)."""
    from coreason_manifest.builder import NewGraphFlow
    from coreason_manifest.spec.core.nodes import AgentNode

    builder = NewGraphFlow("Auto Entry")
    builder.define_profile("p1", "role", "persona")

    # Add one node
    node = AgentNode(id="auto_start", metadata={}, profile="p1", tools=[], type="agent")
    builder.add_node(node)

    # Do NOT call set_entry_point

    flow = builder.build()
    assert flow.graph.entry_point == "auto_start"


def test_builder_graph_missing_entry_point() -> None:
    """Cover NewGraphFlow.build() missing entry point logic."""
    from coreason_manifest.builder import NewGraphFlow
    from coreason_manifest.spec.interop.exceptions import ManifestError

    builder = NewGraphFlow("Empty Graph")
    # No nodes added

    with pytest.raises(ManifestError, match="CRSN-VAL-ENTRY-POINT-MISSING") as exc:
        builder.build()
    assert "CRSN-VAL-ENTRY-POINT-MISSING" in str(exc.value)


def test_builder_graph_validation_failure() -> None:
    """Cover NewGraphFlow.build() failure (line 385)."""
    from coreason_manifest.builder import NewGraphFlow
    from coreason_manifest.spec.core.resilience import FallbackStrategy

    builder = NewGraphFlow("Invalid Graph")

    # Define valid profile
    builder.define_profile("p1", "role", "persona")

    # Add agent with valid profile but invalid resilience
    node = AgentNode(
        id="a1",
        metadata={},
        type="agent",
        profile="p1",
        tools=[],
        resilience=FallbackStrategy(fallback_node_id="missing_node"),
    )
    builder.add_node(node)
    builder.set_entry_point("a1")

    with pytest.raises(ValueError, match="Validation failed") as exc:
        builder.build()

    assert "missing ID 'missing_node'" in str(exc.value)
