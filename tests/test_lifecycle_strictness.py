import pytest

from coreason_manifest.spec.core.flow import Edge, FlowInterface, FlowMetadata, Graph, GraphFlow, LinearFlow
from coreason_manifest.spec.core.governance import CircuitBreaker, Governance
from coreason_manifest.spec.core.nodes import AgentNode, PlaceholderNode
from coreason_manifest.spec.interop.exceptions import ManifestError
from coreason_manifest.utils.validator import validate_flow


def test_graph_flow_strictness_accumulated_placeholders() -> None:
    """Test that GraphFlow collects multiple placeholder errors."""
    n1 = PlaceholderNode(id="p1", type="placeholder", metadata={}, required_capabilities=[])
    n2 = PlaceholderNode(id="p2", type="placeholder", metadata={}, required_capabilities=[])
    graph = Graph(nodes={"p1": n1, "p2": n2}, edges=[], entry_point="p1")

    with pytest.raises(ManifestError) as exc:
        GraphFlow(
            kind="GraphFlow",
            status="published",
            metadata=FlowMetadata(name="test", version="1.0.0"),
            interface=FlowInterface(),
            graph=graph,
        )

    msg = exc.value.fault.message
    assert "p1" in msg
    assert "p2" in msg
    assert exc.value.fault.error_code == "CRSN-VAL-LIFECYCLE-PLACEHOLDER"
    # Check context has remediation for both
    assert len(exc.value.fault.context["remediations"]) == 2


def test_graph_flow_strictness_dangling_edges() -> None:
    """Test that GraphFlow detects edges pointing to non-existent nodes."""
    n1 = AgentNode(id="a1", type="agent", metadata={}, profile="p1", tools=[])

    # Edge points to "missing"
    graph = Graph(nodes={"a1": n1}, edges=[Edge(from_node="a1", to_node="missing")], entry_point="a1")

    with pytest.raises(ManifestError) as exc:
        GraphFlow(
            kind="GraphFlow",
            status="published",
            metadata=FlowMetadata(name="test", version="1.0.0"),
            interface=FlowInterface(),
            graph=graph,
        )

    assert exc.value.fault.error_code == "CRSN-VAL-LIFECYCLE-DANGLING-EDGE"
    assert "missing" in exc.value.fault.message


def test_graph_flow_entry_point_remediation() -> None:
    """Test that GraphFlow missing entry point suggests valid nodes."""
    n1 = AgentNode(id="a1", type="agent", metadata={}, profile="p1", tools=[])

    # Missing entry_point
    graph = Graph(nodes={"a1": n1}, edges=[], entry_point=None)

    with pytest.raises(ManifestError) as exc:
        GraphFlow(
            kind="GraphFlow",
            status="published",
            metadata=FlowMetadata(name="test", version="1.0.0"),
            interface=FlowInterface(),
            graph=graph,
        )

    assert exc.value.fault.error_code == "CRSN-VAL-LIFECYCLE-ENTRYPOINT"
    # Check context for suggestion
    assert "a1" in str(exc.value.fault.context)


def test_graph_flow_entry_point_invalid() -> None:
    """Test that GraphFlow invalid entry point raises error."""
    n1 = AgentNode(id="a1", type="agent", metadata={}, profile="p1", tools=[])

    # Invalid entry_point
    graph = Graph(nodes={"a1": n1}, edges=[], entry_point="invalid_ep")

    with pytest.raises(ManifestError) as exc:
        GraphFlow(
            kind="GraphFlow",
            status="published",
            metadata=FlowMetadata(name="test", version="1.0.0"),
            interface=FlowInterface(),
            graph=graph,
        )

    assert exc.value.fault.error_code == "CRSN-VAL-LIFECYCLE-ENTRYPOINT"


def test_graph_flow_fallback_validation() -> None:
    """Test that GraphFlow validates fallback node ID exists."""
    n1 = AgentNode(id="a1", type="agent", metadata={}, profile="p1", tools=[])
    graph = Graph(nodes={"a1": n1}, edges=[], entry_point="a1")

    gov = Governance(
        circuit_breaker=CircuitBreaker(
            error_threshold_count=5, reset_timeout_seconds=60, fallback_node_id="missing_fallback"
        )
    )

    with pytest.raises(ManifestError) as exc:
        GraphFlow(
            kind="GraphFlow",
            status="published",
            metadata=FlowMetadata(name="test", version="1.0.0"),
            interface=FlowInterface(),
            graph=graph,
            governance=gov,
        )

    assert exc.value.fault.error_code == "CRSN-VAL-LIFECYCLE-DANGLING-FALLBACK"
    assert "missing_fallback" in exc.value.fault.message


def test_linear_flow_strictness_accumulated_placeholders() -> None:
    """Test that LinearFlow collects multiple placeholder errors."""
    n1 = PlaceholderNode(id="p1", type="placeholder", metadata={}, required_capabilities=[])
    n2 = PlaceholderNode(id="p2", type="placeholder", metadata={}, required_capabilities=[])

    with pytest.raises(ManifestError) as exc:
        LinearFlow(
            kind="LinearFlow", status="published", metadata=FlowMetadata(name="test", version="1.0.0"), steps=[n1, n2]
        )

    msg = exc.value.fault.message
    assert "p1" in msg
    assert "p2" in msg
    assert exc.value.fault.error_code == "CRSN-VAL-LIFECYCLE-PLACEHOLDER"


def test_linear_flow_fallback_validation() -> None:
    """Test that LinearFlow validates fallback node ID exists."""
    n1 = AgentNode(id="a1", type="agent", metadata={}, profile="p1", tools=[])

    gov = Governance(
        circuit_breaker=CircuitBreaker(
            error_threshold_count=5, reset_timeout_seconds=60, fallback_node_id="missing_fallback"
        )
    )

    with pytest.raises(ManifestError) as exc:
        LinearFlow(
            kind="LinearFlow",
            status="published",
            metadata=FlowMetadata(name="test", version="1.0.0"),
            steps=[n1],
            governance=gov,
        )

    assert exc.value.fault.error_code == "CRSN-VAL-LIFECYCLE-DANGLING-FALLBACK"


def test_validator_dangling_edge_draft() -> None:
    """
    Test validator.py dangling edge detection on a DRAFT flow.
    This covers validator.py line 240 (missed in published strict check).
    """
    n1 = AgentNode(id="a1", type="agent", metadata={}, profile="p1", tools=[])
    graph = Graph(
        nodes={"a1": n1},
        # Dangling edge from a1 to missing
        edges=[Edge(from_node="a1", to_node="missing"), Edge(from_node="missing_source", to_node="a1")],
        entry_point="a1",
    )

    flow = GraphFlow(
        kind="GraphFlow",
        status="draft",  # Draft allows creation, but validate_flow should report it
        metadata=FlowMetadata(name="test", version="1.0.0"),
        interface=FlowInterface(),
        graph=graph,
    )

    errors = validate_flow(flow)
    assert any("Dangling Edge Error" in e for e in errors)
    assert any("Target 'missing'" in e for e in errors)
    assert any("Source 'missing_source'" in e for e in errors)


def test_validator_governance_fallback() -> None:
    """
    Test validator.py governance fallback logic.
    Ensures validator.py line 240 is covered.
    """
    node = AgentNode(id="start", type="agent", profile="p1", tools=[])
    graph = Graph(nodes={"start": node}, edges=[], entry_point="start")
    gov = Governance(
        circuit_breaker=CircuitBreaker(
            fallback_node_id="missing_node", error_threshold_count=3, reset_timeout_seconds=10
        )
    )
    flow = GraphFlow(
        metadata=FlowMetadata(name="t", version="1"), interface=FlowInterface(), graph=graph, governance=gov
    )
    # validate_flow calls _validate_governance
    errors = validate_flow(flow)
    assert any("Circuit Breaker Error" in e for e in errors)
    assert any("missing_node" in e for e in errors)


def test_graph_flow_strictness_dangling_edge_source() -> None:
    """
    Test that GraphFlow detects edges coming from non-existent nodes.
    Covers flow.py line 334 (missing source).
    """
    node = AgentNode(id="start", type="agent", profile="p1", tools=[])
    graph = Graph(
        nodes={"start": node},
        # "missing" is not in nodes
        edges=[Edge(from_node="missing", to_node="start")],
        entry_point="start",
    )

    with pytest.raises(ManifestError) as excinfo:
        GraphFlow(
            metadata=FlowMetadata(name="t", version="1"), interface=FlowInterface(), graph=graph, status="published"
        )

    assert "CRSN-VAL-LIFECYCLE-DANGLING-EDGE" in str(excinfo.value)
    assert "missing" in str(excinfo.value)
