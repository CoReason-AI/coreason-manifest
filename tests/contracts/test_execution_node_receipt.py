import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import ExecutionNodeReceipt


def test_execution_node_receipt_comprehensive() -> None:
    # 1. Valid receipt initialization
    receipt = ExecutionNodeReceipt(
        request_id="req-1",
        root_request_id="root-1",
        parent_request_id="req-0",
        inputs={"key": "val"},
        outputs={"res": 1},
        parent_hashes=["hash1", "hash2"],
    )
    assert receipt.request_id == "req-1"
    assert receipt.node_hash is not None

    # 2. Lineage validation
    with pytest.raises(ValidationError, match="Orphaned Lineage"):
        ExecutionNodeReceipt(request_id="req-1", parent_request_id="req-0", root_request_id=None, inputs={}, outputs={})

    # 3. Hash determinism with unsorted dicts
    r1 = ExecutionNodeReceipt(
        request_id="req-1", inputs={"a": 1, "b": {"c": 2, "d": [1, 2]}}, outputs=[{"e": 3}, {"f": 4}]
    )
    r2 = ExecutionNodeReceipt(
        request_id="req-1", inputs={"b": {"d": [1, 2], "c": 2}, "a": 1}, outputs=[{"e": 3}, {"f": 4}]
    )
    assert r1.node_hash == r2.node_hash

    # 4. Hash determinism ignores None values
    r3 = ExecutionNodeReceipt(request_id="req-1", inputs={"a": 1, "b": None}, outputs=None)
    r4 = ExecutionNodeReceipt(request_id="req-1", inputs={"a": 1}, outputs=None)
    assert r3.node_hash == r4.node_hash
