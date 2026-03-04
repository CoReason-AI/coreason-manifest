from coreason_manifest.compute.reasoning import GraphReasoning
from coreason_manifest.spec.graph_contracts import GraphEdge, GraphNode, SemanticTraversalRequest, SubgraphResponse
from coreason_manifest.state.events import EventType, GraphRetrievalTrace


def test_graph_reasoning() -> None:
    gr = GraphReasoning(
        semantic_intent="Find concepts", anchor_nodes=["A"], max_hops=2, allowed_edge_types=["MAPS_TO"], model="gpt-4o"
    )
    assert gr.type == "graph"
    assert gr.semantic_intent == "Find concepts"


def test_semantic_traversal_request() -> None:
    req = SemanticTraversalRequest(
        semantic_intent="Explore", anchor_nodes=["B"], max_hops=1, allowed_edge_types=["IS_A"]
    )
    assert req.semantic_intent == "Explore"
    assert req.max_hops == 1


def test_subgraph_response() -> None:
    node = GraphNode(id="A", properties={"name": "Alice"})
    edge = GraphEdge(source="A", target="B", edge_type="KNOWS")
    resp = SubgraphResponse(nodes=[node], edges=[edge])
    assert len(resp.nodes) == 1
    assert len(resp.edges) == 1


def test_graph_retrieval_trace() -> None:
    trace = GraphRetrievalTrace(
        traversal_request_hash="hash1",
        subgraph_topology_hash="hash2",
        nodes_retrieved_count=10,
        edges_retrieved_count=5,
    )
    assert trace.nodes_retrieved_count == 10
    assert EventType.GRAPH_RETRIEVAL_TRACE == "GRAPH_RETRIEVAL_TRACE"
