import pytest
from pydantic import ValidationError

from coreason_manifest.spec.core.flow import (
    AnyNode,
    DataSchema,
    FlowInterface,
    FlowMetadata,
    Graph,
    GraphFlow,
)
from coreason_manifest.spec.core.nodes import HumanNode, SwarmNode
from coreason_manifest.spec.interop.compliance import ErrorCatalog
from coreason_manifest.utils.gatekeeper import validate_policy


def test_magic_number_coercion_human_node() -> None:
    """Directive 1: -1 should be coerced to 'infinite'."""
    node = HumanNode(
        id="h1",
        metadata={},
        type="human",
        prompt="test",
        timeout_seconds=-1,
        interaction_mode="blocking",
    )
    assert node.timeout_seconds == "infinite"

    node_shadow = HumanNode(
        id="h2",
        metadata={},
        type="human",
        prompt="test",
        timeout_seconds=None,  # SOTA Fix: Must be None for shadow mode
        interaction_mode="shadow",
        shadow_timeout_seconds=-1,
    )
    assert node_shadow.shadow_timeout_seconds == "infinite"


def test_human_node_mutual_exclusion() -> None:
    """Fix 4: Enforce temporal isolation."""

    # 1. Shadow mode with timeout_seconds -> Error
    with pytest.raises(ValidationError, match="must not have 'timeout_seconds'"):
        HumanNode(
            id="h1",
            metadata={},
            type="human",
            prompt="test",
            interaction_mode="shadow",
            shadow_timeout_seconds=300,
            timeout_seconds=300,  # Invalid
        )

    # 2. Blocking mode with shadow_timeout_seconds -> Error
    with pytest.raises(ValidationError, match="must not have 'shadow_timeout_seconds'"):
        HumanNode(
            id="h2",
            metadata={},
            type="human",
            prompt="test",
            interaction_mode="blocking",
            timeout_seconds=300,
            shadow_timeout_seconds=300,  # Invalid
        )


def test_magic_number_coercion_swarm_node() -> None:
    """Directive 1: -1 should be coerced to 'infinite' in SwarmNode."""
    node = SwarmNode(
        id="s1",
        metadata={},
        type="swarm",
        worker_profile="profile_1",
        workload_variable="tasks",
        distribution_strategy="sharded",
        max_concurrency=-1,
        reducer_function="concat",
        output_variable="results",
    )
    assert node.max_concurrency == "infinite"


def test_domain_validation_error_remediation() -> None:
    """Directive 4: DomainValidationError should contain remediation."""
    # When validating during model creation, Pydantic wraps custom exceptions in ValidationError.
    # We need to catch ValidationError and inspect the underlying error.
    with pytest.raises(ValidationError) as excinfo:
        HumanNode(
            id="h1",
            metadata={},
            type="human",
            prompt="test",
            timeout_seconds=None,  # Valid for shadow
            interaction_mode="shadow",
            shadow_timeout_seconds=None,  # Missing required field for shadow mode
        )

    errors = excinfo.value.errors()
    assert len(errors) == 1
    err = errors[0]

    # Actually, for the purpose of this test, verifying the message contains remediation description is good.
    assert "HumanNode in 'shadow' mode requires 'shadow_timeout_seconds'" in err["msg"]
    assert "[Remediation:" in err["msg"]
    assert "[Payload:" in err["msg"]
    # Check that paths are relative
    assert '"path": "/shadow_timeout_seconds"' in err["msg"]


def test_healing_ingestion_stub() -> None:
    """Directive 3: Invalid schema should raise DomainValidationError with repair attempt context."""
    invalid_schema = {"type": "unknown_type"}

    with pytest.raises(ValidationError) as excinfo:
        DataSchema(json_schema=invalid_schema)

    errors = excinfo.value.errors()
    assert len(errors) == 1
    err = errors[0]

    # Check message for healing/invalid schema
    assert "Invalid JSON Schema" in err["msg"]


def test_topology_tolerance_and_gatekeeper() -> None:
    """Directive 2: GraphFlow should allow islands, Gatekeeper should flag them."""
    # Create a graph with an unreachable node (island)
    # Entry point is 'n1', 'n2' is isolated.

    nodes: dict[str, AnyNode] = {
        "n1": HumanNode(id="n1", metadata={}, type="human", prompt="entry", timeout_seconds=10),
        "n2": HumanNode(id="n2", metadata={}, type="human", prompt="island", timeout_seconds=10),
    }

    graph = Graph(nodes=nodes, edges=[], entry_point="n1")

    flow = GraphFlow(
        kind="GraphFlow",
        status="published",
        metadata=FlowMetadata(name="test", version="1.0", description="test", tags=[]),
        interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
        blackboard=None,
        graph=graph,
    )

    # Validation should PASS (no ValueError raised by GraphFlow validation)
    assert flow.status == "published"

    # Now run Gatekeeper
    reports = validate_policy(flow)

    # Check for orphan warning
    orphan_reports = [r for r in reports if r.code == ErrorCatalog.ERR_TOPOLOGY_ORPHAN_001]
    assert len(orphan_reports) == 1

    # Bulk remediation reports do not set single node_id, but detail the list
    assert "n2" in orphan_reports[0].details["node_ids"]
    assert orphan_reports[0].severity == "warning"
    assert orphan_reports[0].remediation is not None
    assert orphan_reports[0].remediation.type == "prune_node"
    # Ensure patch data is a list (list of patches for node + edges)
    assert isinstance(orphan_reports[0].remediation.patch_data, list)
    assert orphan_reports[0].remediation.patch_data[0]["op"] == "remove"
