from coreason_manifest.state.federated import FederatedStatePatch, FederatedSuspenseEnvelope, VectorClock
from coreason_manifest.state.persistence import JSONPatchOperation, PatchOp


def test_vector_clock() -> None:
    vc = VectorClock(ticks={"inst_a": 1, "inst_b": 2})
    assert vc.ticks["inst_a"] == 1
    assert vc.ticks["inst_b"] == 2


def test_federated_state_patch() -> None:
    vc = VectorClock(ticks={"inst_a": 1})
    op = JSONPatchOperation(op=PatchOp.ADD, path="/foo", value="bar", from_=None)
    patch = FederatedStatePatch(
        patch_id="123e4567-e89b-12d3-a456-426614174000",
        originating_institution_id="inst_a",
        target_workflow_id="123e4567-e89b-12d3-a456-426614174001",
        vector_clock=vc,
        operations=[op],
        cryptographic_signature="sha256:abc123def456",
    )
    assert patch.patch_id == "123e4567-e89b-12d3-a456-426614174000"
    assert len(patch.operations) == 1
    assert patch.operations[0].op == PatchOp.ADD


def test_federated_suspense_envelope() -> None:
    envelope = FederatedSuspenseEnvelope(
        envelope_id="123e4567-e89b-12d3-a456-426614174002",
        required_signatures=["inst_a", "inst_b"],
        current_signatures=["inst_a"],
    )
    assert envelope.envelope_id == "123e4567-e89b-12d3-a456-426614174002"
    assert len(envelope.required_signatures) == 2
    assert len(envelope.current_signatures) == 1
