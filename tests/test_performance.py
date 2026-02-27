# tests/test_performance.py

import pytest
from coreason_manifest.spec.core.flow import GraphFlow, FlowMetadata, FlowInterface, Graph, Edge
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile
from coreason_manifest.utils.validator import validate_flow
from coreason_manifest.utils.integrity import compute_hash

@pytest.fixture
def massive_flow() -> GraphFlow:
    """Generates a massive graph flow with 100 nodes and linear edges."""
    node_count = 100
    nodes = {}
    edges = []

    # Create simple profile
    profile = CognitiveProfile(role="worker", persona="perf", reasoning=None)

    for i in range(node_count):
        node_id = f"node_{i}"
        nodes[node_id] = AgentNode(
            id=node_id,
            type="agent",
            profile=profile,
            tools=[],
            metadata={"index": str(i)}
        )
        if i > 0:
            edges.append(Edge(from_node=f"node_{i-1}", to_node=node_id))

    return GraphFlow(
        kind="GraphFlow",
        metadata=FlowMetadata(name="Perf Test", version="1.0"),
        interface=FlowInterface(),
        graph=Graph(
            nodes=nodes,
            edges=edges,
            entry_point="node_0"
        )
    )

def test_benchmark_validation(benchmark, massive_flow) -> None:  # type: ignore[no-untyped-def]
    """Benchmarks the full semantic validation of a 100-node flow."""
    # We benchmark the validate_flow function
    result = benchmark(validate_flow, massive_flow)
    assert isinstance(result, list)

def test_benchmark_hashing(benchmark, massive_flow) -> None:  # type: ignore[no-untyped-def]
    """Benchmarks the Merkle hash computation of a 100-node flow."""
    # We benchmark compute_hash
    result = benchmark(compute_hash, massive_flow)
    assert isinstance(result, str)
    assert len(result) == 64
