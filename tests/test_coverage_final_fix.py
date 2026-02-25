import pytest

from coreason_manifest.builder import NewGraphFlow
from coreason_manifest.spec.core.flow import FlowDefinitions, FlowInterface, FlowMetadata, Graph, GraphFlow
from coreason_manifest.spec.core.governance import CircuitBreaker, Governance
from coreason_manifest.spec.core.nodes import AgentNode
from coreason_manifest.spec.interop.exceptions import ManifestError


def test_builder_no_nodes_entry_point_fallback():
    """
    Test NewGraphFlow.build() when there are no nodes and no explicit entry point.
    This should hit the 'else' branch in builder.py where ep = "missing_entry_point".
    """
    builder = NewGraphFlow("EmptyFlow", "0.0.1", "Testing empty flow")

    # We expect ManifestError because "missing_entry_point" won't be in the (empty) nodes map.
    with pytest.raises(ManifestError) as excinfo:
        builder.build()

    # Verify the cause is indeed the missing entry point error from validate_topology
    assert "Entry point 'missing_entry_point' not found" in str(excinfo.value)


def test_builder_explicit_entry_point():
    """
    Test NewGraphFlow.set_entry_point() to cover the explicit entry point setter.
    """
    builder = NewGraphFlow("ExplicitFlow", "0.0.1", "Testing explicit entry point")

    # Define a profile so validation passes
    builder.define_profile("default", role="tester", persona="helper")

    node = AgentNode(id="agent1", type="agent", profile="default", tools=[])
    builder.add_node(node)

    # Call set_entry_point explicitly
    builder.set_entry_point("agent1")

    # Also set status to published to ensure we pass lifecycle checks
    builder.set_status("published")

    flow = builder.build()
    assert flow.graph.entry_point == "agent1"
    assert flow.status == "published"


def test_published_flow_missing_entry_point_suggestion():
    """
    Test GraphFlow.enforce_lifecycle_constraints when status is 'published',
    entry_point is missing, BUT nodes exist.
    This triggers the logic to suggest an existing node as entry point.
    """
    node = AgentNode(id="agent1", type="agent", profile="default", tools=[])

    # Note: validate_topology passes if entry_point is None.
    # enforce_lifecycle_constraints runs next and catches the missing entry_point.

    with pytest.raises(ManifestError) as excinfo:
        GraphFlow(
            metadata=FlowMetadata(name="Test", version="1.0.0"),
            interface=FlowInterface(),
            graph=Graph(
                nodes={"agent1": node},
                edges=[],
                entry_point=None,  # Explicitly missing
            ),
            status="published",
            definitions=FlowDefinitions(),
        )

    err = excinfo.value
    assert "Published flow MUST have a defined entry_point" in str(err)

    # Verify the suggestion logic was executed
    assert "remediation" in err.fault.context
    patch_data = err.fault.context["remediation"]["patch_data"]
    assert patch_data[0]["value"] == "agent1"


def test_graph_flow_fallback_missing():
    """
    Test GraphFlow.validate_topology when circuit breaker fallback node is missing.
    This covers the validation logic for CRSN-VAL-FALLBACK-MISSING.
    """
    node = AgentNode(id="agent1", type="agent", profile="default", tools=[])

    # Governance with fallback to non-existent node
    gov = Governance(
        circuit_breaker=CircuitBreaker(
            error_threshold_count=5, reset_timeout_seconds=60, fallback_node_id="missing_fallback"
        )
    )

    with pytest.raises(ManifestError) as excinfo:
        GraphFlow(
            metadata=FlowMetadata(name="Test", version="1.0.0"),
            interface=FlowInterface(),
            graph=Graph(nodes={"agent1": node}, edges=[], entry_point="agent1"),
            status="draft",  # Status doesn't matter for this check
            definitions=FlowDefinitions(),
            governance=gov,
        )

    assert "Circuit breaker fallback 'missing_fallback' not found in nodes" in str(excinfo.value)
