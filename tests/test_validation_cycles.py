# tests/test_validation_cycles.py

from collections.abc import Callable

from coreason_manifest.spec.core.flow import (
    Edge,
    FlowDefinitions,
    FlowInterface,
    FlowMetadata,
    Graph,
    GraphFlow,
    LinearFlow,
)
from coreason_manifest.spec.core.governance import CircuitBreaker, Governance
from coreason_manifest.spec.core.nodes import (
    AgentNode,
    SwitchNode,
)
from coreason_manifest.spec.core.resilience import (
    ErrorDomain,
    ErrorHandler,
    FallbackStrategy,
    SupervisionPolicy,
)
from coreason_manifest.utils.validator import validate_flow


def test_simple_execution_cycle(flow_metadata: FlowMetadata, agent_node_factory: Callable[..., AgentNode]) -> None:
    # A -> B -> A
    a = agent_node_factory("A")
    b = agent_node_factory("B")
    graph = Graph(
        nodes={"A": a, "B": b},
        edges=[Edge(from_node="A", to_node="B"), Edge(from_node="B", to_node="A")],
        entry_point="A",
    )
    flow = GraphFlow(metadata=flow_metadata, interface=FlowInterface(), graph=graph)

    errors = validate_flow(flow)
    assert any(e.code == "ERR_TOPOLOGY_CYCLE_002" for e in errors)
    assert any("A" in e.details.get("cycle_nodes", []) for e in errors if e.code == "ERR_TOPOLOGY_CYCLE_002")
    assert any("B" in e.details.get("cycle_nodes", []) for e in errors if e.code == "ERR_TOPOLOGY_CYCLE_002")


def test_self_referencing_node(flow_metadata: FlowMetadata, agent_node_factory: Callable[..., AgentNode]) -> None:
    # A -> A
    a = agent_node_factory("A")
    graph = Graph(nodes={"A": a}, edges=[Edge(from_node="A", to_node="A")], entry_point="A")
    flow = GraphFlow(metadata=flow_metadata, interface=FlowInterface(), graph=graph)

    errors = validate_flow(flow)
    assert any(e.code == "ERR_TOPOLOGY_CYCLE_002" for e in errors)


def test_isolated_cycle(flow_metadata: FlowMetadata, agent_node_factory: Callable[..., AgentNode]) -> None:
    # A (entry)
    # B <-> C (isolated cycle)
    a = agent_node_factory("A")
    b = agent_node_factory("B")
    c = agent_node_factory("C")
    graph = Graph(
        nodes={"A": a, "B": b, "C": c},
        edges=[Edge(from_node="B", to_node="C"), Edge(from_node="C", to_node="B")],
        entry_point="A",
    )
    flow = GraphFlow(metadata=flow_metadata, interface=FlowInterface(), graph=graph)

    errors = validate_flow(flow)
    # Expect validation error for cycle, even if isolated
    assert any(e.code == "ERR_TOPOLOGY_CYCLE_002" for e in errors)
    # Note: B and C are not "orphans" (indegree=0) because they point to each other.
    # Reachability check (BFS from entry) would be needed to flag them as unreachable.


def test_switch_node_cycle(flow_metadata: FlowMetadata, agent_node_factory: Callable[..., AgentNode]) -> None:
    # A -> Switch -> A
    a = agent_node_factory("A")
    switch = SwitchNode(
        id="S",
        type="switch",
        metadata={},
        variable="x",
        cases={"true": "A"},
        default="A",
    )
    graph = Graph(
        nodes={"A": a, "S": switch},
        edges=[Edge(from_node="A", to_node="S")],
        entry_point="A",
    )
    # Mock blackboard for variable
    from coreason_manifest.spec.core.flow import Blackboard, VariableDef

    bb = Blackboard(variables={"x": VariableDef(type="string")})

    flow = GraphFlow(metadata=flow_metadata, interface=FlowInterface(), graph=graph, blackboard=bb)

    errors = validate_flow(flow)
    assert any(e.code == "ERR_TOPOLOGY_CYCLE_002" for e in errors)


def test_linear_flow_cycle(flow_metadata: FlowMetadata, agent_node_factory: Callable[..., AgentNode]) -> None:
    # LinearFlow implicit edges (A -> B).
    # Add fallback B -> A to create cycle.
    a = agent_node_factory("A")
    b = agent_node_factory("B", resilience=FallbackStrategy(fallback_node_id="A"))

    flow = LinearFlow(metadata=flow_metadata, steps=[a, b])

    errors = validate_flow(flow)
    assert any(e.code == "ERR_TOPOLOGY_CYCLE_002" for e in errors)


def test_hybrid_fallback_cycle(flow_metadata: FlowMetadata, agent_node_factory: Callable[..., AgentNode]) -> None:
    # Graph: A -> B
    # Fallback: B -> A
    a = agent_node_factory("A")
    b = agent_node_factory("B", resilience=FallbackStrategy(fallback_node_id="A"))

    graph = Graph(nodes={"A": a, "B": b}, edges=[Edge(from_node="A", to_node="B")], entry_point="A")
    flow = GraphFlow(metadata=flow_metadata, interface=FlowInterface(), graph=graph)

    errors = validate_flow(flow)
    assert any(e.code == "ERR_TOPOLOGY_CYCLE_002" for e in errors)


def test_global_circuit_breaker_cycle(
    flow_metadata: FlowMetadata, agent_node_factory: Callable[..., AgentNode]
) -> None:
    # A -> B
    # Global CB Fallback -> A
    # If B triggers CB, it goes to A -> cycle?
    # B -> Fallback(A). A -> B. Cycle.

    a = agent_node_factory("A")
    b = agent_node_factory("B")  # B implicitly connects to fallback if set

    graph = Graph(nodes={"A": a, "B": b}, edges=[Edge(from_node="A", to_node="B")], entry_point="A")

    gov = Governance(
        circuit_breaker=CircuitBreaker(error_threshold_count=1, reset_timeout_seconds=10, fallback_node_id="A")
    )

    flow = GraphFlow(metadata=flow_metadata, interface=FlowInterface(), graph=graph, governance=gov)

    errors = validate_flow(flow)
    # The adjacency map should include edge from ALL nodes (except fallback itself) to fallback node
    # So B -> A. And A -> B. Cycle.
    assert any(e.code == "ERR_TOPOLOGY_CYCLE_002" for e in errors)


def test_referenced_template_cycle(flow_metadata: FlowMetadata, agent_node_factory: Callable[..., AgentNode]) -> None:
    # A -> B
    # B uses template -> Fallback(A)
    # Cycle.

    strategy = FallbackStrategy(fallback_node_id="A")
    policy = SupervisionPolicy(handlers=[ErrorHandler(match_domain=[ErrorDomain.SYSTEM], strategy=strategy)])
    defs = FlowDefinitions(supervision_templates={"tpl": policy})

    a = agent_node_factory("A")
    b = agent_node_factory("B", resilience="ref:tpl")

    graph = Graph(nodes={"A": a, "B": b}, edges=[Edge(from_node="A", to_node="B")], entry_point="A")
    flow = GraphFlow(metadata=flow_metadata, interface=FlowInterface(), graph=graph, definitions=defs)

    errors = validate_flow(flow)
    assert any(e.code == "ERR_TOPOLOGY_CYCLE_002" for e in errors)
