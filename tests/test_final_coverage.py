from datetime import datetime
from typing import Any

from coreason_manifest.spec.common.presentation import PresentationHints
from coreason_manifest.spec.core.flow import Edge, FlowInterface, FlowMetadata, Graph, GraphFlow, LinearFlow
from coreason_manifest.spec.core.governance import CircuitBreaker, Governance
from coreason_manifest.spec.core.nodes import PlaceholderNode
from coreason_manifest.spec.interop.compliance import ErrorCatalog
from coreason_manifest.spec.interop.telemetry import NodeExecution, NodeState
from coreason_manifest.utils.integrity import compute_hash
from coreason_manifest.utils.validator import _validate_kill_switch, validate_flow
from coreason_manifest.utils.visualizer import to_mermaid, to_react_flow


def test_telemetry_implicit_parent_hashes() -> None:
    # Cover telemetry.py line 92: data["parent_hashes"] = [p_hash]
    ne = NodeExecution(
        node_id="n1",
        state=NodeState.COMPLETED,
        inputs={},
        outputs={},
        timestamp=datetime.now(),
        duration_ms=100,
        parent_hash="abc",
        # parent_hashes omitted
    )
    assert ne.parent_hashes == ["abc"]


def test_integrity_duck_typed_model_dump() -> None:
    # Cover integrity.py line 91
    class DuckModel:
        # Prefix unused args with _ to satisfy ARG002
        def model_dump(self, **_kwargs: Any) -> dict[str, Any]:
            return {"a": 1}

    # Must use canonical strategy directly or via compute_hash which uses it
    h = compute_hash(DuckModel())
    assert h == compute_hash({"a": 1})


def test_validator_bad_circuit_breaker() -> None:
    # Cover validator.py line 350-355
    gov = Governance(
        circuit_breaker=CircuitBreaker(
            error_threshold_count=3, reset_timeout_seconds=60, fallback_node_id="missing_node"
        )
    )
    flow = LinearFlow.model_construct(
        kind="LinearFlow", metadata=FlowMetadata(name="t", version="1"), governance=gov, steps=[]
    )
    reports = validate_flow(flow)
    assert any(r.code == ErrorCatalog.ERR_GOV_CIRCUIT_FALLBACK_MISSING for r in reports)


def test_validator_kill_switch_no_gov() -> None:
    # Cover validator.py line 773
    flow = LinearFlow.model_construct(
        kind="LinearFlow", metadata=FlowMetadata(name="t", version="1"), governance=None, steps=[]
    )
    # validate_flow won't call it if no gov, so call directly
    errors = _validate_kill_switch(flow)
    assert len(errors) == 0


def test_visualizer_mermaid_conditional() -> None:
    # Cover visualizer.py line 129
    n1 = PlaceholderNode(id="n1", type="placeholder", required_capabilities=[])
    n2 = PlaceholderNode(id="n2", type="placeholder", required_capabilities=[])

    graph = Graph(
        nodes={"n1": n1, "n2": n2}, edges=[Edge(from_node="n1", to_node="n2", condition="x>1")], entry_point="n1"
    )
    flow = GraphFlow.model_construct(
        kind="GraphFlow",
        metadata=FlowMetadata(name="t", version="1"),
        interface=FlowInterface(),  # Added required field
        graph=graph,
    )
    diagram = to_mermaid(flow)
    assert "|x&gt;1|" in diagram  # HTML escaped


def test_visualizer_react_flow_presentation() -> None:
    # Cover visualizer.py lines 253-255
    n1 = PlaceholderNode(
        id="n1",
        type="placeholder",
        required_capabilities=[],
        presentation=PresentationHints(label="My Node", group="G1"),
    )
    flow = LinearFlow.model_construct(kind="LinearFlow", metadata=FlowMetadata(name="t", version="1"), steps=[n1])
    rf = to_react_flow(flow)
    node_data = rf["nodes"][0]["data"]
    assert "presentation" in node_data
    assert node_data["label"] == "My Node"
