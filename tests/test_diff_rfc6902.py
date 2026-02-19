from coreason_manifest.spec.core.flow import AnyNode, FlowMetadata, LinearFlow
from coreason_manifest.spec.core.nodes import AgentNode
from coreason_manifest.utils.diff import GovernanceMutation, ResourceMutation, TopologyMutation, compare_flows


def create_flow(name: str = "test", nodes: list[AnyNode] | None = None) -> LinearFlow:
    return LinearFlow(
        kind="LinearFlow",
        metadata=FlowMetadata(name=name, version="1.0", description="desc", tags=[]),
        sequence=nodes or [],
    )


def test_diff_metadata_resource() -> None:
    f1 = create_flow(name="A")
    f2 = create_flow(name="B")

    diff = compare_flows(f1, f2)
    assert len(diff) == 1
    op = diff[0]
    assert isinstance(op, ResourceMutation)
    assert op.op == "replace"
    assert op.path == "/metadata/name"
    assert op.value == "B"


def test_diff_topology_add_node() -> None:
    n1 = AgentNode(id="a1", type="agent", metadata={}, profile="p1", tools=[])
    f1 = create_flow(nodes=[])
    f2 = create_flow(nodes=[n1])

    diff = compare_flows(f1, f2)
    assert len(diff) == 1
    op = diff[0]
    assert isinstance(op, TopologyMutation)  # /sequence/0 -> Topology?
    assert op.op == "add"
    assert op.path == "/sequence/0"
    assert op.value["id"] == "a1"


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

    diff = compare_flows(f1_gov, f2_gov)
    assert len(diff) == 1
    op = diff[0]
    assert isinstance(op, GovernanceMutation)
    assert op.op == "add"
    assert op.path == "/governance/allowed_domains/1"
    assert op.value == "foo.com"


def test_diff_list_replace() -> None:
    # List: [A, B] -> [A, C]
    # Expect: replace /1
    # Logic in _generate_diff handles list elements recursively if index matches.
    # So index 1 differs.

    n1 = AgentNode(id="a1", type="agent", metadata={}, profile="p1", tools=[])
    n2 = AgentNode(id="a2", type="agent", metadata={}, profile="p1", tools=[])

    f1 = create_flow(nodes=[n1, n1])
    f2 = create_flow(nodes=[n1, n2])

    diff = compare_flows(f1, f2)
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
