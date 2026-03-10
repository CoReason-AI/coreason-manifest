from coreason_manifest.spec.ontology import DAGTopology
from coreason_manifest.utils.algebra import align_semantic_manifolds, compute_topology_hash


def test_align_semantic_manifolds_dense() -> None:
    res = align_semantic_manifolds("task1", ["text"], ["text", "raster_image"], "ev1")
    assert res is not None
    assert res.compression_sla.required_grounding_density == "dense"


def test_compute_topology_hash() -> None:
    topology = DAGTopology(
        nodes={}, edges=[], max_depth=10, max_fan_out=10, allow_cycles=False, architectural_intent="test"
    )
    hash_val = compute_topology_hash(topology)
    assert isinstance(hash_val, str)
    assert len(hash_val) == 64
