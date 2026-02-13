import pytest

from coreason_manifest.builder import AgentBuilder, NewGraphFlow, NewLinearFlow
from coreason_manifest.spec.core.flow import VariableDef
from coreason_manifest.spec.core.governance import Governance
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile, PlaceholderNode
from coreason_manifest.spec.core.resilience import EscalationStrategy
from coreason_manifest.spec.core.tools import ToolPack


def test_linear_builder() -> None:
    builder = NewLinearFlow("MyLinear", version="1.0", description="Desc")
    builder.add_step(
        PlaceholderNode(id="step1", type="placeholder", metadata={}, supervision=None, required_capabilities=[])
    )
    builder.add_step(
        PlaceholderNode(id="step2", type="placeholder", metadata={}, supervision=None, required_capabilities=[])
    )

    tp = ToolPack(kind="ToolPack", namespace="test", tools=["t1"], dependencies=[], env_vars=[])
    builder.add_tool_pack(tp)

    gov = Governance(rate_limit_rpm=10)
    builder.set_governance(gov)

    flow = builder.build()

    assert flow.kind == "LinearFlow"
    assert flow.metadata.name == "MyLinear"
    assert len(flow.sequence) == 2
    assert flow.definitions is not None
    assert len(flow.definitions.tool_packs) == 1
    assert flow.governance is not None
    assert flow.governance.rate_limit_rpm == 10


def test_graph_builder() -> None:
    builder = NewGraphFlow("MyGraph", version="1.0", description="Desc")
    builder.add_node(
        PlaceholderNode(id="n1", type="placeholder", metadata={}, supervision=None, required_capabilities=[])
    )
    builder.add_node(
        PlaceholderNode(id="n2", type="placeholder", metadata={}, supervision=None, required_capabilities=[])
    )
    builder.connect("n1", "n2", condition="ok")

    tp = ToolPack(kind="ToolPack", namespace="test", tools=["t1"], dependencies=[], env_vars=[])
    builder.add_tool_pack(tp)

    gov = Governance(rate_limit_rpm=10)
    builder.set_governance(gov)

    # Test set_interface and set_blackboard
    builder.set_interface(inputs={"in": "str"}, outputs={"out": "int"})
    builder.set_blackboard(variables={"var1": VariableDef(type="string", description="test var")}, persistence=True)

    flow = builder.build()

    assert flow.kind == "GraphFlow"
    assert flow.metadata.name == "MyGraph"
    assert len(flow.graph.nodes) == 2
    assert len(flow.graph.edges) == 1
    assert flow.graph.edges[0].source == "n1"
    assert flow.graph.edges[0].target == "n2"
    assert flow.graph.edges[0].condition == "ok"
    assert flow.definitions is not None
    assert len(flow.definitions.tool_packs) == 1
    assert flow.governance is not None
    assert flow.governance.rate_limit_rpm == 10

    # Assert new features
    assert flow.interface.inputs == {"in": "str"}
    assert flow.interface.outputs == {"out": "int"}
    assert flow.blackboard is not None
    assert flow.blackboard.persistence is True
    assert "var1" in flow.blackboard.variables
    assert flow.blackboard.variables["var1"].type == "string"


def test_linear_builder_invalid() -> None:
    # Empty sequence is invalid
    builder = NewLinearFlow("Invalid")
    with pytest.raises(ValueError, match="Validation failed"):
        builder.build()


def test_graph_builder_invalid() -> None:
    # Empty graph is invalid
    builder = NewGraphFlow("Invalid")
    with pytest.raises(ValueError, match="Validation failed"):
        builder.build()


def test_builder_coverage_set_circuit_breaker_with_existing_governance() -> None:
    """Test setting circuit breaker when governance is already set."""
    builder = NewLinearFlow("Test", "1.0", "Desc")
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
    builder = NewLinearFlow("Test", "1.0", "Desc")
    # No governance set

    # This should trigger the `else:` branch in set_circuit_breaker
    builder.set_circuit_breaker(error_threshold=5, reset_timeout=30)

    assert builder.governance is not None
    assert builder.governance.circuit_breaker is not None
    assert builder.governance.circuit_breaker.error_threshold_count == 5


def test_builder_coverage_add_inspector_linear() -> None:
    """Test add_inspector method in NewLinearFlow."""
    builder = NewLinearFlow("Test", "1.0", "Desc")
    builder.add_inspector(node_id="inspector1", target="var1", criteria="criteria1", output="out1")
    assert len(builder.sequence) == 1
    node = builder.sequence[0]
    assert node.id == "inspector1"
    assert node.type == "inspector"


def test_builder_coverage_add_inspector_graph() -> None:
    """Test add_inspector method in NewGraphFlow."""
    builder = NewGraphFlow("Test", "1.0", "Desc")
    builder.add_inspector(node_id="inspector1", target="var1", criteria="criteria1", output="out1")
    assert "inspector1" in builder._nodes
    node = builder._nodes["inspector1"]
    assert node.type == "inspector"


def test_builder_coverage_add_agent_ref_defaults() -> None:
    """Test add_agent_ref with default tools=None."""
    # Linear
    builder_l = NewLinearFlow("Test", "1.0", "Desc")
    builder_l.define_profile("brain1", "role", "persona")
    builder_l.add_agent_ref("agent1", "brain1")  # Default tools=None -> []
    assert len(builder_l.sequence) == 1
    node_l = builder_l.sequence[0]
    assert isinstance(node_l, AgentNode)
    assert node_l.tools == []

    # Graph
    builder_g = NewGraphFlow("Test", "1.0", "Desc")
    builder_g.define_profile("brain1", "role", "persona")
    builder_g.add_agent_ref("agent1", "brain1")  # Default tools=None -> []
    assert "agent1" in builder_g._nodes
    node_g = builder_g._nodes["agent1"]
    assert isinstance(node_g, AgentNode)
    assert node_g.tools == []


def test_builder_coverage_explicit_add_agent() -> None:
    """Explicitly test add_agent to ensure coverage."""
    brain = CognitiveProfile(role="role", persona="persona", reasoning=None, fast_path=None)
    agent = AgentNode(id="agent1", type="agent", profile=brain, tools=[], metadata={}, supervision=None)

    # Linear
    builder_l = NewLinearFlow("Test", "1.0", "Desc")
    builder_l.add_agent(agent)
    assert len(builder_l.sequence) == 1

    # Graph
    builder_g = NewGraphFlow("Test", "1.0", "Desc")
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
    builder.with_supervision(retries=3)

    agent = builder.build()
    assert isinstance(agent.profile, CognitiveProfile)
    assert agent.profile.reasoning is not None
    assert agent.profile.fast_path is not None
    assert agent.tools == ["tool1"]
    assert agent.supervision is not None
    # max_attempts removed from EscalationStrategy
    assert isinstance(agent.supervision.default_strategy, EscalationStrategy)

    # Fail build
    builder = AgentBuilder("agent3")
    with pytest.raises(ValueError, match="Agent identity"):
        builder.build()


def test_agent_builder_fallback_missing_id() -> None:
    """Test AgentBuilder raises error when fallback_id is missing for fallback strategy."""
    builder = AgentBuilder("agent_fallback")
    with pytest.raises(ValueError, match="Fallback strategy requires fallback_id"):
        builder.with_supervision(retries=3, strategy="fallback")
