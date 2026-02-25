

from coreason_manifest.spec.core.flow import (
    DataSchema,
    FlowInterface,
    FlowMetadata,
    Graph,
    GraphFlow,
    LinearFlow,
)
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile
from coreason_manifest.spec.core.resilience import (
    FallbackStrategy,
    SupervisionPolicy,
)
from coreason_manifest.utils.validator import validate_flow


def test_validator_catch_invalid_fallback_ids() -> None:
    # 1. Fallback Strategy
    s = FallbackStrategy(fallback_node_id="missing")
    node = AgentNode(
        id="a1", type="agent", metadata={}, profile=CognitiveProfile(role="r", persona="p"), tools=[], resilience=s
    )
    flow = LinearFlow(
        metadata=FlowMetadata(name="T", version="1.0.0", description="D", tags=[]), steps=[node], definitions=None
    )
    errors = validate_flow(flow)
    assert any(
        e.code == "ERR_RESILIENCE_FALLBACK_MISSING" and e.details.get("fallback_node_id") == "missing" for e in errors
    )

    # 2. Supervision Policy (default strategy)
    p = SupervisionPolicy(handlers=[], default_strategy=s)
    node2 = AgentNode(
        id="a1", type="agent", metadata={}, profile=CognitiveProfile(role="r", persona="p"), tools=[], resilience=p
    )
    flow2 = LinearFlow(
        metadata=FlowMetadata(name="T", version="1.0.0", description="D", tags=[]), steps=[node2], definitions=None
    )
    errors2 = validate_flow(flow2)
    assert any(
        e.code == "ERR_RESILIENCE_FALLBACK_MISSING" and e.details.get("fallback_node_id") == "missing" for e in errors2
    )


def test_fallback_cycle_detection() -> None:
    # A -> Fallback(B)
    # B -> Fallback(A)
    # A -> B -> A cycle via fallbacks

    res_a = FallbackStrategy(fallback_node_id="B")
    res_b = FallbackStrategy(fallback_node_id="A")

    node_a = AgentNode(
        id="A", type="agent", metadata={}, profile=CognitiveProfile(role="r", persona="p"), tools=[], resilience=res_a
    )
    node_b = AgentNode(
        id="B", type="agent", metadata={}, profile=CognitiveProfile(role="r", persona="p"), tools=[], resilience=res_b
    )

    # Use unified validation
    from coreason_manifest.utils.validator import _validate_topology_cycles

    # Need to put them in a flow context
    graph = Graph(nodes={"A": node_a, "B": node_b}, edges=[], entry_point="A")
    flow = GraphFlow(
        metadata=FlowMetadata(name="T", version="1.0.0", description="D", tags=[]),
        interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
        blackboard=None,
        graph=graph,
    )

    errors = _validate_topology_cycles(flow)
    assert any(e.code == "ERR_TOPOLOGY_CYCLE_002" for e in errors)
