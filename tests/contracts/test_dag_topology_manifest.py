
from coreason_manifest.spec.ontology import DAGTopologyManifest


def test_dag_topology_manifest_edges_are_not_sorted() -> None:
    # Creating a valid DAG topology
    manifest = DAGTopologyManifest(
        type="dag",
        max_depth=10,
        max_fan_out=10,
        lifecycle_phase="draft",
        nodes={},
        edges=[
            ("did:example:nodeC", "did:example:nodeA"),
            ("did:example:nodeB", "did:example:nodeC"),
            ("did:example:nodeA", "did:example:nodeD"),
        ],
    )

    # It should strictly preserve the causal edge order defined above
    assert manifest.edges == [
        ("did:example:nodeC", "did:example:nodeA"),
        ("did:example:nodeB", "did:example:nodeC"),
        ("did:example:nodeA", "did:example:nodeD"),
    ], "DAG topology edges MUST NOT be sorted. It destroys epistemic value."
