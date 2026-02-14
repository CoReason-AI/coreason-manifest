from coreason_manifest.spec.core.flow import (
    DataSchema,
    Edge,
    FlowDefinitions,
    FlowInterface,
    FlowMetadata,
    Graph,
    GraphFlow,
)
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile, SwarmNode
from coreason_manifest.utils.diff import ChangeType, ManifestDiff
from coreason_manifest.utils.mock import MockFactory


def test_swarm_simulation_expansion() -> None:
    # 1. Setup Flow with SwarmNode
    swarm = SwarmNode(
        id="swarm-1",
        metadata={},
        supervision=None,
        worker_profile="worker-p",
        workload_variable="items",
        distribution_strategy="sharded",
        max_concurrency=3,
        failure_tolerance_percent=0.0,
        reducer_function="concat",
        output_variable="result",
    )

    nodes = {"swarm-1": swarm}
    edges: list[Edge] = []

    # We need a dummy definitions for profile check because GraphFlow validation enforces referential integrity.
    definitions = FlowDefinitions(
        profiles={"worker-p": CognitiveProfile(role="worker", persona="w", reasoning=None, fast_path=None)}
    )

    flow = GraphFlow(
        kind="GraphFlow",
        metadata=FlowMetadata(name="SwarmTest", version="1.0", description="T", tags=[]),
        interface=FlowInterface(
            inputs=DataSchema(fields={}, required=[]),
            outputs=DataSchema(fields={}, required=[]),
        ),
        blackboard=None,
        definitions=definitions,
        graph=Graph(nodes=nodes, edges=edges),  # type: ignore[arg-type]
    )

    # 2. Simulate
    factory = MockFactory()
    trace = factory.simulate_trace(flow, max_steps=10)

    # 3. Verify
    # Should have 3 workers + 1 aggregator
    workers = [t for t in trace if t.attributes.get("worker")]
    aggregators = [t for t in trace if t.attributes.get("role") == "aggregator"]

    assert len(workers) == 3
    assert len(aggregators) == 1

    agg = aggregators[0]
    worker_hashes = {w.execution_hash for w in workers}

    # Check dependencies: Aggregator must depend on all workers
    assert set(agg.previous_hashes) == worker_hashes


def test_deep_diff_granularity() -> None:
    # 1. Base Flow
    profile_a = CognitiveProfile(role="assistant", persona="helpful", reasoning=None, fast_path=None)
    node_a = AgentNode(id="a", metadata={}, supervision=None, profile=profile_a, tools=[])

    flow_1 = GraphFlow(
        kind="GraphFlow",
        metadata=FlowMetadata(name="DiffTest", version="1.0", description="T", tags=[]),
        interface=FlowInterface(
            inputs=DataSchema(fields={}, required=[]),
            outputs=DataSchema(fields={}, required=[]),
        ),
        blackboard=None,
        graph=Graph(nodes={"a": node_a}, edges=[]),
    )

    # 2. Modified Flow
    profile_b = profile_a.model_copy(update={"persona": "grumpy"})
    node_b = node_a.model_copy(update={"profile": profile_b})

    flow_2 = flow_1.model_copy()
    # Deep copy graph to modify node
    new_graph = Graph(nodes={"a": node_b}, edges=[])
    flow_2 = flow_2.model_copy(update={"graph": new_graph})

    # 3. Diff
    diffs = ManifestDiff.compare(flow_1, flow_2)

    # 4. Verify
    # Should be BEHAVIORAL change on 'profile.persona'
    # We might get other diffs if Pydantic model dump includes defaults that changed?
    # But here we explicitly changed persona.

    persona_diff = next((d for d in diffs if d.field == "profile.persona"), None)
    assert persona_diff is not None
    assert persona_diff.type == ChangeType.BEHAVIORAL
    assert persona_diff.old_value == "helpful"
    assert persona_diff.new_value == "grumpy"
