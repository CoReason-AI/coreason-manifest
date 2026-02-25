from typing import Any

import pytest

from coreason_manifest.builder import NewLinearFlow
from coreason_manifest.spec.core.flow import (
    DataSchema,
    FlowDefinitions,
    FlowInterface,
    FlowMetadata,
    Graph,
    GraphFlow,
    LinearFlow,
)
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile, InspectorNode, SwarmNode
from coreason_manifest.spec.core.resilience import EscalationStrategy, FallbackStrategy, ReflexionStrategy
from coreason_manifest.utils.validator import validate_flow


def test_coverage_agent_builder_recovery() -> None:
    # Not testing builder here, but testing the flow produced by it/validator.
    pass


def test_coverage_flow_builder_template() -> None:
    # Not testing validator
    pass


def test_coverage_linear_flow_published() -> None:
    """Test LinearFlow with status='published' to hit validate_integrity."""
    brain = CognitiveProfile(role="assistant", persona="helper", reasoning=None, fast_path=None)
    definitions = FlowDefinitions(profiles={"my-brain": brain})
    agent = AgentNode(
        id="agent-1",
        type="agent",
        profile="my-brain",
        tools=[],
        metadata={},
        resilience=None,
    )

    # Should pass validation
    LinearFlow(
        kind="LinearFlow",
        status="published",
        metadata=FlowMetadata(name="test", version="1.0.0", description="", tags=[]),
        definitions=definitions,
        steps=[agent],
    )


def test_coverage_validator_reflexion_mismatch() -> None:
    """Test ReflexionStrategy on non-supported node type (via bypass)."""
    # Create invalid AgentNode type manually
    node = AgentNode.model_construct(
        id="a1",
        type="invalid_type",  # type: ignore
        resilience=ReflexionStrategy(max_attempts=3, critic_model="gpt-4", critic_prompt="fix", include_trace=True),
        metadata={},
        profile="p",
        tools=[],
    )

    # Run validation logic manually
    from coreason_manifest.utils.validator import _validate_supervision

    errors = _validate_supervision(node, set(), None)
    assert any(e.code == "ERR_RESILIENCE_MISMATCH" for e in errors)


def test_coverage_validator_escalation_empty_queue() -> None:
    """Test EscalationStrategy with empty queue via bypass."""
    # EscalationStrategy model validation prevents empty string if we used min_length=1.
    # So we use model_construct.

    esc = EscalationStrategy.model_construct(
        type="escalate", queue_name="", notification_level="info", timeout_seconds=10
    )

    node = AgentNode(id="a1", metadata={}, type="agent", profile="p", tools=[], resilience=esc)

    from coreason_manifest.utils.validator import _validate_supervision

    errors = _validate_supervision(node, set(), None)
    assert any(e.code == "ERR_RESILIENCE_ESCALATION_INVALID" for e in errors)


def test_supervision_policy_complex_validation() -> None:
    """Test validation of SupervisionPolicy (complex) in resilience field."""
    # Create a complex policy with a fallback strategy that points to a missing node
    from coreason_manifest.spec.core.resilience import ErrorDomain, ErrorHandler, FallbackStrategy, SupervisionPolicy

    complex_policy = SupervisionPolicy(
        handlers=[
            ErrorHandler(
                match_domain=[ErrorDomain.SYSTEM], strategy=FallbackStrategy(fallback_node_id="missing_handler")
            )
        ],
        default_strategy=FallbackStrategy(fallback_node_id="missing_default"),
    )

    node = AgentNode(id="a1", metadata={}, type="agent", profile="p", tools=[], resilience=complex_policy)

    from coreason_manifest.utils.validator import _validate_supervision

    errors = _validate_supervision(node, {"a1"}, None)

    # Should catch both missing IDs
    assert any(e.code == "ERR_RESILIENCE_FALLBACK_MISSING" and e.details.get("fallback_node_id") == "missing_handler" for e in errors)
    assert any(e.code == "ERR_RESILIENCE_FALLBACK_MISSING" and e.details.get("fallback_node_id") == "missing_default" for e in errors)


def test_validator_string_reference_skip() -> None:
    """Test that string references skip validation in _validate_supervision."""
    node = AgentNode(id="a1", metadata={}, type="agent", profile="p", tools=[], resilience="ref:template")
    from coreason_manifest.utils.validator import _validate_supervision

    errors = _validate_supervision(node, set(), None)
    assert len(errors) == 0


def test_fallback_cycle_complex_policy() -> None:
    """Test cycle detection with SupervisionPolicy (complex)."""
    from coreason_manifest.spec.core.resilience import ErrorDomain, ErrorHandler, FallbackStrategy, SupervisionPolicy

    policy_a = SupervisionPolicy(handlers=[], default_strategy=FallbackStrategy(fallback_node_id="b"))

    policy_b = SupervisionPolicy(
        handlers=[ErrorHandler(match_domain=[ErrorDomain.SYSTEM], strategy=FallbackStrategy(fallback_node_id="a"))],
        default_strategy=None,
    )

    node_a = AgentNode(id="a", metadata={}, type="agent", profile="p", tools=[], resilience=policy_a)
    node_b = AgentNode(id="b", metadata={}, type="agent", profile="p", tools=[], resilience=policy_b)

    # Use unified cycle validation
    from coreason_manifest.spec.core.flow import DataSchema, FlowInterface, FlowMetadata, Graph, GraphFlow
    from coreason_manifest.utils.validator import _validate_topology_cycles

    dummy_graph = Graph(nodes={"a": node_a, "b": node_b}, edges=[], entry_point="a")
    flow = GraphFlow(
        kind="GraphFlow",
        status="published",
        metadata=FlowMetadata(name="test", version="1.0.0", description="", tags=[]),
        interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
        blackboard=None,
        graph=dummy_graph,
        definitions=None,
    )
    errors = _validate_topology_cycles(flow)

    assert any(e.code == "ERR_TOPOLOGY_CYCLE_002" for e in errors)


def test_validator_definitions_profile_scanning() -> None:
    """Verify that the validator scans profiles stored in definitions."""
    from coreason_manifest.spec.core.flow import (
        Blackboard,
        DataSchema,
        FlowDefinitions,
        FlowInterface,
        FlowMetadata,
        Graph,
        GraphFlow,
    )
    from coreason_manifest.utils.validator import validate_flow

    # Define a profile with a variable
    definitions = FlowDefinitions(
        profiles={
            "my-profile": CognitiveProfile(
                role="Role {{ role_var }}",
                persona="Persona",
                reasoning=None,
                fast_path=None,
            )
        }
    )

    # Agent referencing that profile
    agent = AgentNode(
        id="a1",
        type="agent",
        metadata={},
        resilience=None,
        profile="my-profile",
        tools=[],
    )

    # Flow with empty blackboard (so role_var is missing)
    blackboard = Blackboard(variables={}, persistence=False)
    graph = Graph(nodes={"a1": agent}, edges=[], entry_point="a1")

    flow = GraphFlow(
        kind="GraphFlow",
        metadata=FlowMetadata(name="T", version="1.0.0", description="D", tags=[]),
        interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
        blackboard=blackboard,
        graph=graph,
        definitions=definitions,
    )

    errors = validate_flow(flow)
    assert any(e.code == "ERR_CAP_MISSING_VAR" and e.details.get("variable") == "role_var" for e in errors)


def test_jinja2_filter_validation() -> None:
    """
    Test that Jinja2 filters in templates are correctly handled by the validator.
    The validator should strip filters and only check the variable name.
    """
    from coreason_manifest.spec.core.flow import (
        Blackboard,
        DataSchema,
        FlowInterface,
        FlowMetadata,
        Graph,
        GraphFlow,
        VariableDef,
    )
    from coreason_manifest.utils.validator import validate_flow

    agent = AgentNode(
        id="n1",
        type="agent",
        metadata={"desc": "Hello {{ user_name | upper }}"},
        resilience=None,
        profile=CognitiveProfile(
            role="Role",
            persona="Persona",
            reasoning=None,
            fast_path=None,
        ),
        tools=[],
    )

    # Define 'user_name' in blackboard
    blackboard = Blackboard(variables={"user_name": VariableDef(type="string")}, persistence=False)

    graph = Graph(nodes={"n1": agent}, edges=[], entry_point="n1")
    flow = GraphFlow(
        kind="GraphFlow",
        metadata=FlowMetadata(name="T", version="1.0.0", description="D", tags=[]),
        interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
        blackboard=blackboard,
        graph=graph,
    )

    # Should pass validation
    errors = validate_flow(flow)
    assert not errors

    # Now verify failure if variable is missing
    agent_fail = AgentNode(
        id="n1",
        type="agent",
        metadata={"desc": "Hello {{ missing | upper }}"},
        resilience=None,
        profile=CognitiveProfile(role="R", persona="P", reasoning=None, fast_path=None),
        tools=[],
    )
    graph_fail = Graph(nodes={"n1": agent_fail}, edges=[], entry_point="n1")
    flow_fail = GraphFlow(
        kind="GraphFlow",
        metadata=FlowMetadata(name="T", version="1.0.0", description="D", tags=[]),
        interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
        blackboard=blackboard,
        graph=graph_fail,
    )

    errors_fail = validate_flow(flow_fail)
    assert any(e.code == "ERR_CAP_MISSING_VAR" and e.details.get("variable") == "missing" for e in errors_fail)


def test_swarm_type_safety() -> None:
    """Test MVP type safety for SwarmNode."""
    from coreason_manifest.spec.core.flow import (
        Blackboard,
        DataSchema,
        FlowInterface,
        FlowMetadata,
        Graph,
        GraphFlow,
        VariableDef,
    )
    from coreason_manifest.utils.validator import validate_flow

    blackboard = Blackboard(variables={"text_var": VariableDef(type="string")}, persistence=False)

    swarm = SwarmNode(
        id="s1",
        type="swarm",
        metadata={},
        resilience=None,
        worker_profile="p1",
        workload_variable="text_var",
        distribution_strategy="sharded",
        max_concurrency=1,
        reducer_function="concat",
        output_variable="out",
    )

    graph = Graph(nodes={"s1": swarm}, edges=[], entry_point="s1")
    flow = GraphFlow(
        kind="GraphFlow",
        metadata=FlowMetadata(name="T", version="1.0.0", description="D", tags=[]),
        interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
        blackboard=blackboard,
        graph=graph,
    )

    errors = validate_flow(flow)
    assert any(e.code == "ERR_CAP_TYPE_MISMATCH" and "expects a list" in e.message for e in errors)


def test_inspector_regex_warning() -> None:
    """Test warning when InspectorNode uses regex mode on complex types."""
    from coreason_manifest.spec.core.flow import (
        Blackboard,
        DataSchema,
        FlowInterface,
        FlowMetadata,
        Graph,
        GraphFlow,
        VariableDef,
    )
    from coreason_manifest.spec.core.nodes import InspectorNode
    from coreason_manifest.utils.validator import validate_flow

    blackboard = Blackboard(variables={"obj_var": VariableDef(type="object")}, persistence=False)

    inspector = InspectorNode(
        id="i1",
        type="inspector",
        metadata={},
        resilience=None,
        target_variable="obj_var",
        criteria="regex:.*",
        mode="programmatic",
        pass_threshold=0.5,
        output_variable="out",
    )

    graph = Graph(nodes={"i1": inspector}, edges=[], entry_point="i1")
    flow = GraphFlow(
        kind="GraphFlow",
        metadata=FlowMetadata(name="T", version="1.0.0", description="D", tags=[]),
        interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
        blackboard=blackboard,
        graph=graph,
    )

    errors = validate_flow(flow)
    assert any(e.code == "ERR_CAP_TYPE_MISMATCH" and e.severity == "warning" for e in errors)


def test_validator_union_type_normalization() -> None:
    """Test that union types (list) in input schema are normalized in symbol table."""
    from coreason_manifest.spec.core.flow import (
        DataSchema,
        FlowInterface,
        FlowMetadata,
        Graph,
        GraphFlow,
    )
    from coreason_manifest.spec.core.nodes import SwarmNode
    from coreason_manifest.utils.validator import validate_flow

    inputs = DataSchema(
        json_schema={
            "type": "object",
            "properties": {
                "union_var": {"type": ["string", "null"]},
                "null_var": {"type": ["null"]},
            },
        }
    )

    swarm = SwarmNode(
        id="s1",
        type="swarm",
        metadata={},
        resilience=None,
        worker_profile="p1",
        workload_variable="union_var",
        distribution_strategy="sharded",
        max_concurrency=1,
        reducer_function="concat",
        output_variable="out",
    )

    graph = Graph(nodes={"s1": swarm}, edges=[], entry_point="s1")
    flow = GraphFlow.model_construct(
        type="graph",
        kind="GraphFlow",
        status="draft",
        metadata=FlowMetadata(name="T", version="1.0.0", description="D", tags=[]),
        interface=FlowInterface(inputs=inputs, outputs=DataSchema()),
        blackboard=None,
        graph=graph,
        definitions=None,
    )

    errors = validate_flow(flow)
    assert any(e.code == "ERR_CAP_TYPE_MISMATCH" and "expects a list" in e.message for e in errors)


def test_graph_flow_draft_mode() -> None:
    # Create invalid graph (missing tool)
    brain = CognitiveProfile(role="assistant", persona="helper", reasoning=None, fast_path=None)
    definitions = FlowDefinitions(profiles={"my-brain": brain})
    agent = AgentNode(
        id="agent-1",
        type="agent",
        profile="my-brain",
        tools=["missing-tool"],
        metadata={},
        resilience=None,
    )
    graph = Graph(nodes={"agent-1": agent}, edges=[], entry_point="agent-1")

    # Draft mode (default) should pass validation - wait, validate_flow is stateless regarding 'status'.
    # validate_flow returns errors regardless of status.
    # The caller (Builder) decides whether to raise exception based on status or usage context.
    # But checking if GraphFlow model itself raises on instantiation for draft... it shouldn't.
    flow = GraphFlow(
        kind="GraphFlow",
        # status="draft", # default
        metadata=FlowMetadata(name="test", version="1.0.0", description="", tags=[]),
        definitions=definitions,
        interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
        blackboard=None,
        graph=graph,
    )
    assert flow.status == "draft"

    # Published mode should fail validation (when called manually or via builder)
    flow_pub = GraphFlow(
        kind="GraphFlow",
        status="published",
        metadata=FlowMetadata(name="test", version="1.0.0", description="", tags=[]),
        definitions=definitions,
        interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
        blackboard=None,
        graph=graph,
    )
    from coreason_manifest.utils.validator import validate_flow

    errors = validate_flow(flow_pub)
    assert any(e.code == "ERR_CAP_MISSING_TOOL_001" and e.details.get("tool") == "missing-tool" for e in errors)
