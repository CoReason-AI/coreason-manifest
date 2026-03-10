from pydantic import BaseModel, Field, ValidationError

from coreason_manifest.spec.ontology import DAGTopologyManifest
from coreason_manifest.utils.algebra import align_semantic_manifolds, compute_topology_hash, generate_correction_prompt


def test_align_semantic_manifolds_dense() -> None:
    res = align_semantic_manifolds("task1", ["text"], ["text", "raster_image"], "ev1")
    assert res is not None
    assert res.compression_sla.required_grounding_density == "dense"


def test_compute_topology_hash() -> None:
    topology = DAGTopologyManifest(
        nodes={}, edges=[], max_depth=10, max_fan_out=10, allow_cycles=False, architectural_intent="test"
    )
    hash_val = compute_topology_hash(topology)
    assert isinstance(hash_val, str)
    assert len(hash_val) == 64


class MockStrictSchema(BaseModel):
    name: str = Field(min_length=5)
    age: int


def test_generate_correction_prompt_translation() -> None:
    try:
        MockStrictSchema(name="Bob", age="not_an_int")
    except ValidationError as e:
        prompt = generate_correction_prompt(error=e, target_node_id="did:web:node-1", fault_id="fault-001")
        assert prompt.fault_id == "fault-001"
        assert prompt.target_node_id == "did:web:node-1"
        assert "/name" in prompt.failing_pointers
        assert "/age" in prompt.failing_pointers
        assert "CRITICAL CONTRACT BREACH" in prompt.remediation_prompt
