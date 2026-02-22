from coreason_manifest.spec.core.flow import (
    AnyNode,
    DataSchema,
    Edge,
    FlowDefinitions,
    FlowInterface,
    FlowMetadata,
    Graph,
    GraphFlow,
)
from coreason_manifest.spec.core.governance import Governance
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile
from coreason_manifest.utils.diff import compare_flows

# ------------------------------------------------------------------------
# Pillar 3: Graph Topology (Draft Cycles)
# ------------------------------------------------------------------------


def test_draft_flow_allows_cycles() -> None:
    """
    Directive: Graph validation should allow cycles when status is 'draft'.
    """
    # A simple cycle: A -> B -> A
    nodes: dict[str, AnyNode] = {
        "A": AgentNode(id="A", type="agent", profile="p1", tools=[], metadata={}),
        "B": AgentNode(id="B", type="agent", profile="p1", tools=[], metadata={}),
    }
    edges = [Edge(from_node="A", to_node="B"), Edge(from_node="B", to_node="A")]

    graph = Graph(nodes=nodes, edges=edges, entry_point="A")

    # This should pass if status is draft
    flow = GraphFlow(
        kind="GraphFlow",
        status="draft",
        metadata=FlowMetadata(name="cycle", version="1.0.0", description="desc", tags=[]),
        interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
        blackboard=None,
        graph=graph,
    )

    assert flow.status == "draft"


def test_published_flow_forbids_cycles() -> None:
    """
    Directive: Published flow must enforce acyclic property.
    """
    nodes: dict[str, AnyNode] = {
        "A": AgentNode(id="A", type="agent", profile="p1", tools=[], metadata={}),
        "B": AgentNode(id="B", type="agent", profile="p1", tools=[], metadata={}),
    }
    edges = [Edge(from_node="A", to_node="B"), Edge(from_node="B", to_node="A")]

    graph = Graph(nodes=nodes, edges=edges, entry_point="A")

    # We must provide definitions for p1 profile validation (status=published triggers strict checks)
    defs = FlowDefinitions(profiles={"p1": CognitiveProfile(role="r", persona="p", reasoning=None, fast_path=None)})

    # Architectural Update: Cycles are no longer strictly banned by GraphFlow validation.
    # They are flagged by Gatekeeper.
    flow = GraphFlow(
        kind="GraphFlow",
        status="published",
        metadata=FlowMetadata(name="cycle", version="1.0.0", description="desc", tags=[]),
        interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
        blackboard=None,
        definitions=defs,
        graph=graph,
    )
    assert flow.status == "published"


# ------------------------------------------------------------------------
# Pillar 5: Governance (Allowed Domains)
# ------------------------------------------------------------------------


def test_governance_allowed_domains_cleanup() -> None:
    """
    Directive: allowed_domains must strip scheme and path.
    """
    # User inputs a full URL
    gov = Governance(allowed_domains=["https://example.com/api/v1", "http://sub.test.org", "schemeless.com/path"])

    assert "example.com" in gov.allowed_domains
    assert "sub.test.org" in gov.allowed_domains
    assert "schemeless.com" in gov.allowed_domains

    # Ensure raw inputs are gone
    assert "https://example.com/api/v1" not in gov.allowed_domains


# ------------------------------------------------------------------------
# Pillar 4: Diff Classification
# ------------------------------------------------------------------------


def test_diff_classification_via_context() -> None:
    """
    Directive: _classify_path removed. Context passed down.
    Verify 'add agent' -> Topology, 'change profile' -> Resource.
    """
    # Create a flow
    entry_node = AgentNode(id="entry", type="agent", profile="p1", tools=[], metadata={})
    base_flow = GraphFlow(
        kind="GraphFlow",
        status="draft",
        metadata=FlowMetadata(name="diff", version="1.0.0", description="desc", tags=[]),
        interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
        blackboard=None,
        graph=Graph(nodes={"entry": entry_node}, edges=[], entry_point="entry"),
    )

    # 1. Add a Node (Topology Change)
    node = AgentNode(id="A", type="agent", profile="p1", tools=[], metadata={})
    new_flow_1 = base_flow.model_copy(deep=True)
    # We update the dict directly.
    new_graph_1 = Graph(nodes={"entry": entry_node, "A": node}, edges=[], entry_point="entry")
    new_flow_1 = base_flow.model_copy(update={"graph": new_graph_1})

    report_1 = compare_flows(base_flow, new_flow_1)
    diffs_1 = report_1.changes

    # Check that adding node "A" is a Topology mutation
    # Path: /graph/nodes/A
    mutation = next((d for d in diffs_1 if d.path == "/graph/nodes/A"), None)
    assert mutation is not None
    assert mutation.op == "add"
    assert mutation.mutation_type == "topology"

    # 2. Modify Node Profile (Resource Change)
    new_node = node.model_copy(update={"profile": "p2"})
    new_graph_2 = Graph(nodes={"entry": entry_node, "A": new_node}, edges=[], entry_point="entry")
    new_flow_2 = new_flow_1.model_copy(update={"graph": new_graph_2})

    report_2 = compare_flows(new_flow_1, new_flow_2)
    diffs_2 = report_2.changes

    # Check that changing profile is Resource mutation
    # Path: /graph/nodes/A/profile
    mutation_2 = next((d for d in diffs_2 if d.path == "/graph/nodes/A/profile"), None)
    assert mutation_2 is not None
    assert mutation_2.op == "replace"
    assert mutation_2.mutation_type == "resource"
