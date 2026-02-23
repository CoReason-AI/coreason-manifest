import pytest
from pydantic import ValidationError

from coreason_manifest.spec.core.flow import (
    AnyNode,
    Blackboard,
    DataSchema,
    FlowInterface,
    FlowMetadata,
    Graph,
    GraphFlow,
)
from coreason_manifest.spec.core.nodes import HumanNode
from coreason_manifest.spec.interop.compliance import ErrorCatalog
from coreason_manifest.spec.interop.exceptions import ManifestError
from coreason_manifest.utils.gatekeeper import validate_policy


def test_human_node_mutual_exclusion() -> None:
    """Fix 4: Enforce temporal isolation."""

    # 1. Shadow mode with timeout_seconds -> Error
    with pytest.raises((ValidationError, ManifestError)) as excinfo:
        HumanNode(
            id="h1",
            metadata={},
            type="human",
            prompt="test",
            interaction_mode="shadow",
            shadow_timeout_seconds=300,
            timeout_seconds=300,  # Invalid
        )
    assert "must not have 'timeout_seconds'" in str(excinfo.value)

    # 2. Blocking mode with shadow_timeout_seconds -> Error
    with pytest.raises((ValidationError, ManifestError)) as excinfo:
        HumanNode(
            id="h2",
            metadata={},
            type="human",
            prompt="test",
            interaction_mode="blocking",
            timeout_seconds=300,
            shadow_timeout_seconds=300,  # Invalid
        )
    assert "must not have 'shadow_timeout_seconds'" in str(excinfo.value)


def test_domain_validation_error_remediation() -> None:
    """Directive 4: DomainValidationError should contain remediation."""
    with pytest.raises((ValidationError, ManifestError)) as excinfo:
        HumanNode(
            id="h1",
            metadata={},
            type="human",
            prompt="test",
            timeout_seconds=None,
            interaction_mode="shadow",
            shadow_timeout_seconds=None,  # Missing required field
        )

    e = excinfo.value
    msg = str(e)
    assert "HumanNode in 'shadow' mode requires 'shadow_timeout_seconds'" in msg

    if isinstance(e, ManifestError):
        assert e.fault.context.get("remediation") is not None


def test_healing_ingestion_stub() -> None:
    """Directive 3: Invalid schema should raise ManifestError with repair attempt context."""
    invalid_schema = {"type": "unknown_type"}

    # Fix: DataSchema requires id and schema
    with pytest.raises((ValidationError, ManifestError)) as excinfo:
        DataSchema(id="test_id", json_schema=invalid_schema)
    assert "Invalid JSON Schema" in str(excinfo.value)


def test_topology_tolerance_and_gatekeeper() -> None:
    """Directive 2: GraphFlow should allow islands, Gatekeeper should flag them."""
    nodes: dict[str, AnyNode] = {
        "n1": HumanNode(id="n1", metadata={}, type="human", prompt="entry", timeout_seconds=10),
        "n2": HumanNode(id="n2", metadata={}, type="human", prompt="island", timeout_seconds=10),
    }

    graph = Graph(nodes=nodes, edges=[], entry_point="n1")

    # Fix: DataSchema instantiation and Blackboard
    flow = GraphFlow(
        kind="GraphFlow",
        status="published",
        metadata=FlowMetadata(name="test", version="1.0.0", description="test", tags=[]),
        interface=FlowInterface(
            inputs=DataSchema(id="in", json_schema={"type": "object"}),
            outputs=DataSchema(id="out", json_schema={"type": "object"}),
        ),
        blackboard=Blackboard(),
        graph=graph,
    )

    assert flow.status == "published"

    reports = validate_policy(flow)

    orphan_reports = [r for r in reports if r.code == ErrorCatalog.ERR_TOPOLOGY_ORPHAN_001]
    assert len(orphan_reports) == 1

    assert "n2" in orphan_reports[0].details["node_ids"]
    assert orphan_reports[0].severity == "warning"
    assert orphan_reports[0].remediation is not None
    assert orphan_reports[0].remediation.type == "prune_node"
    assert isinstance(orphan_reports[0].remediation.patch_data, list)
    assert orphan_reports[0].remediation.patch_data[0]["op"] == "remove"
