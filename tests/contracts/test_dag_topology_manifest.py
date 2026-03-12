import hypothesis.strategies as st
from hypothesis import HealthCheck, given, settings

from coreason_manifest.spec.ontology import DAGTopologyManifest

# NodeIdentifierState uses regex: "^did:[a-z0-9]+:[a-zA-Z0-9.\-_:]+$"
did_strategy = st.from_regex(r"^did:[a-z0-9]+:[a-zA-Z0-9.\-_:]+$", fullmatch=True)


@given(edges=st.lists(st.tuples(did_strategy, did_strategy), max_size=100))
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_dag_topology_manifest_causal_preservation(edges: list[tuple[str, str]]) -> None:
    """
    AGENT INSTRUCTION: Prove that under no mathematical conditions are DAG edges ever sorted or mutated.
    Causal edges are structurally ordered sequences (Topological DAG edges) and MUST NOT be sorted,
    as defined by Paradigm 2 of the Cryptographic Determinism rule in AGENTS.md.
    """
    manifest = DAGTopologyManifest(
        type="dag",
        max_depth=10,
        max_fan_out=10,
        lifecycle_phase="draft",
        nodes={},
        edges=edges,
    )
    # The output array must be an exact isomorphic match to the input array
    assert manifest.edges == edges, "CRITICAL: DAG causality mathematically breached."
