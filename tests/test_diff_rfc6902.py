from coreason_manifest.spec.core.flow import (
    AnyNode,
    Edge,
    FlowMetadata,
    Graph,
    GraphFlow,
    LinearFlow,
)
from coreason_manifest.spec.core.nodes import AgentNode
from coreason_manifest.utils.diff import GovernanceMutation, ResourceMutation, TopologyMutation, compare_flows


def create_flow(name: str = "test", nodes: list[AnyNode] | None = None) -> LinearFlow:
    return LinearFlow(
        kind="LinearFlow",
        metadata=FlowMetadata(name=name, version="1.0.0", description="desc", tags=[]),
        sequence=nodes or [],
    )


def test_diff_metadata_resource() -> None:
    f1 = create_flow(name="A")
    f2 = create_flow(name="B")

    report = compare_flows(f1, f2)
    diff = report.changes
    assert len(diff) == 1
    op = diff[0]
    assert isinstance(op, ResourceMutation)
    assert op.op == "replace"
    assert op.path == "/metadata/name"
    assert op.value == "B"
    # SOTA check
    # Metadata name change is arguably not breaking topology/governance, depending on policy.
    assert report.has_breaking is False
    # But currently category defaults to FEATURE for resource changes unless mapped otherwise.
    # _determine_category returns RESOURCE for resource domain.
    # And has_breaking checks for "BREAKING".
    assert op.category == "RESOURCE"


def test_diff_topology_add_node() -> None:
    n1 = AgentNode(id="a1", type="agent", metadata={}, profile="p1", tools=[])
    f1 = create_flow(nodes=[])
    f2 = create_flow(nodes=[n1])

    report = compare_flows(f1, f2)
    diff = report.changes
    assert len(diff) == 1
    op = diff[0]
    assert isinstance(op, TopologyMutation)  # /sequence/0 -> Topology?
    assert op.op == "add"
    assert op.path == "/sequence/0"
    assert op.value["id"] == "a1"

    # Topology ADD is FEATURE
    assert op.category == "FEATURE"


def test_diff_governance() -> None:
    # Helper to add governance
    f1 = create_flow()
    # Pydantic models are immutable (frozen), so we rely on constructor
    # But compare_flows takes validated models.
    # We can use model_copy(update={...}) or construct new ones.

    from coreason_manifest.spec.core.governance import Governance

    gov1 = Governance(allowed_domains=["example.com"])
    gov2 = Governance(allowed_domains=["example.com", "foo.com"])

    f1_gov = f1.model_copy(update={"governance": gov1})
    f2_gov = f1.model_copy(update={"governance": gov2})

    report = compare_flows(f1_gov, f2_gov)
    diff = report.changes
    assert len(diff) == 1
    op = diff[0]
    assert isinstance(op, GovernanceMutation)
    assert op.op == "add"
    assert op.path == "/governance/allowed_domains/1"
    assert op.value == "foo.com"

    assert op.category == "GOVERNANCE"


def test_diff_list_replace() -> None:
    # List: [A, B] -> [A, C]
    # Expect: replace /1
    # Logic in _generate_diff handles list elements recursively if index matches.
    # So index 1 differs.

    n1 = AgentNode(id="a1", type="agent", metadata={}, profile="p1", tools=[])
    n2 = AgentNode(id="a2", type="agent", metadata={}, profile="p1", tools=[])

    f1 = create_flow(nodes=[n1, n1])
    f2 = create_flow(nodes=[n1, n2])

    report = compare_flows(f1, f2)
    diff = report.changes
    assert len(diff) > 0
    # It might be multiple ops if node fields differ
    # id changed: a1 -> a2.
    # path: /sequence/1/id

    op = diff[0]
    assert op.path == "/sequence/1/id"
    assert op.op == "replace"
    assert op.value == "a2"
    # Should be classed as Resource because it's a property of a node?
    # My classifier says: /sequence/1 -> Topology?
    # /sequence/1/id -> Resource?
    # Let's check classifier logic:
    # if "/sequence" in path:
    #    parts = path.split("/") # "", "sequence", "1", "id" -> len 4
    #    if len(parts) == 3: return "topology" # /sequence/1
    #    return "resource"

    assert isinstance(op, ResourceMutation)


def test_diff_topology_replace_entry_point() -> None:
    """Test replacing a primitive field in Topology domain (entry_point)."""
    # Create GraphFlows
    graph1 = Graph(nodes={}, edges=[], entry_point="a")
    graph2 = Graph(nodes={}, edges=[], entry_point="b")

    # We need full GraphFlow to satisfy validation
    # Use model_construct to avoid validation errors for missing nodes
    f1 = GraphFlow.model_construct(
        kind="GraphFlow", metadata=FlowMetadata(name="T", version="1.0.0", description="d", tags=[]), graph=graph1
    )
    f2 = GraphFlow.model_construct(
        kind="GraphFlow", metadata=FlowMetadata(name="T", version="1.0.0", description="d", tags=[]), graph=graph2
    )

    report = compare_flows(f1, f2)
    diff = report.changes
    # path: /graph/entry_point
    # op: replace
    # domain: topology

    mutation = next((d for d in diff if d.path == "/graph/entry_point"), None)
    assert mutation is not None
    assert mutation.op == "replace"
    assert mutation.mutation_type == "topology"
    assert mutation.category == "BREAKING"
    assert report.has_breaking is True


def test_diff_identity_list_behavior() -> None:
    """Test identity-based diffing logic (remove+add vs replace)."""
    n1 = AgentNode(id="a1", type="agent", metadata={}, profile="p1", tools=[])
    n2 = AgentNode(id="a2", type="agent", metadata={}, profile="p1", tools=[])
    n3 = AgentNode(id="a3", type="agent", metadata={}, profile="p1", tools=[])

    # Case: [A, B] -> [A, C]
    # Naive: replace /1
    # Identity: remove B, add C (since B and C have different IDs)
    f1 = create_flow(nodes=[n1, n2])
    f2 = create_flow(nodes=[n1, n3])

    report = compare_flows(f1, f2)
    diff = report.changes

    # We expect remove and add, OR replace if identity fallback triggered (but here IDs are unique)
    # len(dict) == len(list) -> Identity logic used.

    # Order of iteration in set(all_ids) is undefined.
    # Logic:
    # a1 matches -> no diff.
    # a2 not in new -> remove /sequence/1 (idx in old)
    # a3 not in old -> add /sequence/1 (idx in new)

    ops = {d.op for d in diff}
    assert "remove" in ops
    assert "add" in ops
    # Depending on implementation details, replace might NOT be generated.
    assert "replace" not in ops

    # Verify paths
    rem_op = next(d for d in diff if d.op == "remove")
    add_op = next(d for d in diff if d.op == "add")

    # Remove index might be 1 (index in old)
    assert rem_op.path.endswith("/1")
    # Add index might be 1 (index in new)
    assert add_op.path.endswith("/1")


def test_diff_reordering_ignored() -> None:
    """Test that reordering of identified items generates minimal/no diff."""
    n1 = AgentNode(id="a1", type="agent", metadata={}, profile="p1", tools=[])
    n2 = AgentNode(id="a2", type="agent", metadata={}, profile="p1", tools=[])

    # Case: [A, B] -> [B, A]
    f1 = create_flow(nodes=[n1, n2])
    f2 = create_flow(nodes=[n2, n1])

    report = compare_flows(f1, f2)
    diff = report.changes

    # Identity logic:
    # a1 in both. Diff(a1, a1) -> None.
    # a2 in both. Diff(a2, a2) -> None.
    # Result: Empty diff.
    assert len(diff) == 0


def test_diff_topology_remove_edge() -> None:
    """Test removing an item from a Topology list (edges)."""
    e1 = Edge(source="a", target="b")
    graph1 = Graph(nodes={}, edges=[e1], entry_point="a")
    graph2 = Graph(nodes={}, edges=[], entry_point="a")

    f1 = GraphFlow.model_construct(
        kind="GraphFlow", metadata=FlowMetadata(name="T", version="1.0.0", description="d", tags=[]), graph=graph1
    )
    f2 = GraphFlow.model_construct(
        kind="GraphFlow", metadata=FlowMetadata(name="T", version="1.0.0", description="d", tags=[]), graph=graph2
    )

    report = compare_flows(f1, f2)
    diff = report.changes
    # path: /graph/edges/0
    # op: remove
    # domain: topology

    mutation = next((d for d in diff if d.path == "/graph/edges/0"), None)
    assert mutation is not None
    assert mutation.op == "remove"
    assert mutation.mutation_type == "topology"
    assert mutation.category == "BREAKING"
    assert report.has_breaking is True
