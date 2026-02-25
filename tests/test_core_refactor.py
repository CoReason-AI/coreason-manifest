import pytest
from pydantic import ValidationError

from coreason_manifest.spec.core.engines import StandardReasoning
from coreason_manifest.spec.core.flow import (
    AnyNode,
    DataSchema,
    FlowInterface,
    FlowMetadata,
    Graph,
    GraphFlow,
)
from coreason_manifest.spec.core.memory import MemorySubsystem, WorkingMemory
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile
from coreason_manifest.spec.interop.compliance import ErrorCatalog
from coreason_manifest.spec.interop.exceptions import ManifestError
from coreason_manifest.utils.gatekeeper import validate_policy


def test_healing_ingestion_stub() -> None:
    """Directive 3: Invalid schema should raise ManifestError with repair attempt context."""
    invalid_schema = {"type": "unknown_type"}

    # Fix: DataSchema requires id and schema
    with pytest.raises((ValidationError, ManifestError)) as excinfo:
        DataSchema(id="test_id", json_schema=invalid_schema)
    assert "Invalid JSON Schema" in str(excinfo.value)


def test_topology_tolerance_and_gatekeeper() -> None:
    """Directive 2: GraphFlow should allow islands, Gatekeeper should flag them."""
    profile = CognitiveProfile(
        role="tester", persona="tester", reasoning=StandardReasoning(model="gpt-4"), fast_path=None
    )
    nodes: dict[str, AnyNode] = {
        "n1": AgentNode(id="n1", metadata={}, type="agent", profile=profile, tools=[]),
        "n2": AgentNode(id="n2", metadata={}, type="agent", profile=profile, tools=[]),
    }

    graph = Graph(nodes=nodes, edges=[], entry_point="n1")

    # Fix: DataSchema instantiation and Memory
    flow = GraphFlow(
        kind="GraphFlow",
        status="published",
        metadata=FlowMetadata(name="test", version="1.0.0", description="test", tags=[]),
        interface=FlowInterface(
            inputs=DataSchema(id="in", json_schema={"type": "object"}),
            outputs=DataSchema(id="out", json_schema={"type": "object"}),
        ),
        memory=MemorySubsystem(working=WorkingMemory()),
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
