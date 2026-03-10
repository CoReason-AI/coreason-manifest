from coreason_manifest.spec.ontology import DAGTopology
from coreason_manifest.utils.algebra import align_semantic_manifolds, compute_topology_hash


def test_align_semantic_manifolds_subset() -> None:
    # If target is subset of source, returns None
    res = align_semantic_manifolds("task1", ["text", "raster_image"], ["text"], "ev1")
    assert res is None


def test_align_semantic_manifolds_dense() -> None:
    # Target requires raster_image
    res = align_semantic_manifolds("task1", ["text"], ["text", "raster_image"], "ev1")
    assert res is not None
    assert res.compression_sla.required_grounding_density == "dense"


def test_align_semantic_manifolds_sparse() -> None:
    # Target requires text and vector_graphics
    res = align_semantic_manifolds("task1", ["text"], ["text", "vector_graphics"], "ev1")
    assert res is not None
    assert res.compression_sla.required_grounding_density == "sparse"


def test_compute_topology_hash() -> None:
    topology = DAGTopology(
        nodes={},
        edges=[],
        max_depth=10,
        max_fan_out=10,
        allow_cycles=False,
        architectural_intent="test",
        justification="test",
    )
    hash_val = compute_topology_hash(topology)
    assert isinstance(hash_val, str)
    assert len(hash_val) == 64
