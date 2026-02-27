from datetime import datetime

import pytest

from coreason_manifest.spec.interop.telemetry import NodeExecution, NodeState
from coreason_manifest.utils.integrity import compute_hash, verify_merkle_proof


def test_telemetry_parent_hash_consistency() -> None:
    # 1. parent_hash added to parent_hashes if not present
    ne = NodeExecution(
        node_id="n1",
        state=NodeState.COMPLETED,
        inputs={},
        outputs={},
        timestamp=datetime.now(),
        duration_ms=100,
        parent_hash="abc",
        parent_hashes=["def"],
    )
    assert "abc" in ne.parent_hashes
    assert "def" in ne.parent_hashes


def test_integrity_verify_merkle_proof_exception() -> None:
    # verify_merkle_proof(chain)
    # chain is list of dicts.
    # We want to trigger Exception inside loop.
    # e.g. missing 'execution_hash' key or 'parent_hashes' key or something.

    # Passing something that is not dict? verify_merkle_proof takes list[dict].
    # But inside:
    # current_hash = node.get("execution_hash")
    # If node is not dict?

    # If we pass a list containing something that raises exception on .get()
    class BadObj:
        def get(self, _k: object) -> object:
            raise RuntimeError("Boom")

    assert verify_merkle_proof([BadObj()]) is False


def test_telemetry_orphan_trace() -> None:
    # parent_request_id without root_request_id
    with pytest.raises(ValueError, match="Orphaned trace detected"):
        NodeExecution(
            node_id="n",
            state=NodeState.COMPLETED,
            inputs={},
            outputs={},
            timestamp=datetime.now(),
            duration_ms=1,
            parent_request_id="p",
            root_request_id=None,
        )


def test_integrity_nan_inf() -> None:
    with pytest.raises(ValueError, match="NaN and Infinity are not allowed"):
        compute_hash(float("nan"))
    with pytest.raises(ValueError, match="NaN and Infinity are not allowed"):
        compute_hash(float("inf"))
