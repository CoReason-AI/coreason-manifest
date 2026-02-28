from coreason_manifest.spec.core.oversight.governance import (
    ComputeLimits,
    FinancialLimits,
    Governance,
    OperationalPolicy,
)
from coreason_manifest.spec.core.workflow.flow import Edge, FlowInterface, FlowMetadata, Graph, GraphFlow
from coreason_manifest.spec.core.workflow.nodes import AgentNode
from coreason_manifest.utils.validator import _validate_budget_constraints


def test_financial_budget_within_limits() -> None:
    nodes = {
        "n1": AgentNode(id="n1", profile="p1", operational_policy=None),
        "n2": AgentNode(id="n2", profile="p2", operational_policy=None),
        "n3": AgentNode(id="n3", profile="p3", operational_policy=None),
    }
    edges = [
        Edge(from_node="n1", to_node="n2", cost_weight=0.1, latency_weight_ms=100.0),
        Edge(from_node="n2", to_node="n3", cost_weight=0.2, latency_weight_ms=200.0),
    ]
    graph = Graph(nodes=nodes, edges=edges)

    from coreason_manifest.spec.core.rebuild import rebuild_manifest

    rebuild_manifest()

    flow = GraphFlow(
        metadata=FlowMetadata(name="f", version="1"),
        interface=FlowInterface(),
        graph=graph,
        governance=Governance(
            operational_policy=OperationalPolicy(
                financial=FinancialLimits(max_cost_usd=0.5),
                compute=ComputeLimits(max_execution_time_seconds=1),  # 1000ms
            )
        ),
    )

    errors = _validate_budget_constraints(flow)
    assert not errors  # noqa: S101


def test_financial_budget_exceeded() -> None:
    nodes = {
        "n1": AgentNode(id="n1", profile="p1", operational_policy=None),
        "n2": AgentNode(id="n2", profile="p2", operational_policy=None),
        "n3": AgentNode(id="n3", profile="p3", operational_policy=None),
    }
    edges = [
        Edge(from_node="n1", to_node="n2", cost_weight=0.1, latency_weight_ms=500.0),
        Edge(from_node="n2", to_node="n3", cost_weight=0.2, latency_weight_ms=600.0),
    ]
    graph = Graph(nodes=nodes, edges=edges)

    from coreason_manifest.spec.core.rebuild import rebuild_manifest

    rebuild_manifest()

    flow = GraphFlow(
        metadata=FlowMetadata(name="f", version="1"),
        interface=FlowInterface(),
        graph=graph,
        governance=Governance(
            operational_policy=OperationalPolicy(
                financial=FinancialLimits(max_cost_usd=0.25), compute=ComputeLimits(max_execution_time_seconds=1)
            )
        ),
    )

    errors = _validate_budget_constraints(flow)
    assert len(errors) == 2  # noqa: S101
    assert "ERR_GOV_INVALID_CONFIG" in [e.code for e in errors]  # noqa: S101
