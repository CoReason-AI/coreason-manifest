import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import BoundedJSONRPCIntent


def test_bounded_json_rpc_intent_valid() -> None:
    intent = BoundedJSONRPCIntent(
        jsonrpc="2.0", method="test.method", params={"key": "value", "nested": [1, 2, 3]}, id=1
    )
    assert intent.method == "test.method"
    assert intent.params == {"key": "value", "nested": [1, 2, 3]}


def test_bounded_json_rpc_intent_none_params() -> None:
    intent = BoundedJSONRPCIntent(jsonrpc="2.0", method="test.method", params=None, id="abc")
    assert intent.params == {}


def test_bounded_json_rpc_intent_valid_list_params() -> None:
    intent = BoundedJSONRPCIntent(jsonrpc="2.0", method="test.method", params=["a", "list", "is", "fine"], id=2)
    assert intent.params == ["a", "list", "is", "fine"]


def test_bounded_json_rpc_intent_invalid_params_type() -> None:
    with pytest.raises(ValidationError, match="params must be a dictionary or a list"):
        BoundedJSONRPCIntent(
            jsonrpc="2.0",
            method="test.method",
            params="this is neither a dict nor a list",  # type: ignore
        )


def test_bounded_json_rpc_intent_exceeds_depth() -> None:
    # Create a dictionary nested 11 levels deep
    nested_dict = {}
    current = nested_dict
    for _ in range(11):
        current["child"] = {}
        current = current["child"]

    with pytest.raises(ValidationError, match="JSON payload exceeds maximum depth of 10"):
        BoundedJSONRPCIntent(jsonrpc="2.0", method="test.method", params=nested_dict)


def test_bounded_json_rpc_intent_exceeds_dict_keys() -> None:
    # Create a dictionary with 101 keys
    large_dict = {f"key_{i}": i for i in range(101)}

    with pytest.raises(ValidationError, match="Dictionary exceeds maximum of 100 keys"):
        BoundedJSONRPCIntent(jsonrpc="2.0", method="test.method", params=large_dict)


def test_bounded_json_rpc_intent_exceeds_dict_key_length() -> None:
    # Create a dictionary with a key > 1000 chars
    long_key = "a" * 1001
    bad_dict = {long_key: "value"}

    with pytest.raises(ValidationError, match="Dictionary key exceeds maximum length of 1000"):
        BoundedJSONRPCIntent(jsonrpc="2.0", method="test.method", params=bad_dict)


def test_bounded_json_rpc_intent_exceeds_list_length() -> None:
    # Create a list with 1001 elements
    large_list = list(range(1001))

    with pytest.raises(ValidationError, match="List exceeds maximum of 1000 elements"):
        BoundedJSONRPCIntent(jsonrpc="2.0", method="test.method", params={"data": large_list})


def test_bounded_json_rpc_intent_exceeds_string_length() -> None:
    # Create a string with > 10000 characters
    long_string = "a" * 10001

    with pytest.raises(ValidationError, match="String exceeds maximum length of 10000 characters"):
        BoundedJSONRPCIntent(jsonrpc="2.0", method="test.method", params={"data": long_string})
from coreason_manifest.spec.ontology import (
    DefeasibleCascadeEvent,
    EphemeralNamespacePartitionState,
    LatentScratchpadReceipt,
    SecureSubSessionState,
    ThoughtBranchState,
)


def test_secure_sub_session_state_sort_arrays() -> None:
    session = SecureSubSessionState(
        session_id="session-1",
        allowed_vault_keys=["z-key", "a-key", "m-key"],
        max_ttl_seconds=3600,
        description="Test session",
    )
    assert session.allowed_vault_keys == ["a-key", "m-key", "z-key"]


def test_defeasible_cascade_event_sort_arrays() -> None:
    event = DefeasibleCascadeEvent(
        cascade_id="c1",
        root_falsified_event_id="e1",
        propagated_decay_factor=0.5,
        quarantined_event_ids=["e3", "e1", "e2"],
        cross_boundary_quarantine_issued=True,
    )
    assert event.quarantined_event_ids == ["e1", "e2", "e3"]


def test_latent_scratchpad_receipt_referential_integrity_valid() -> None:
    tb1 = ThoughtBranchState(branch_id="b1", latent_content_hash="a" * 64)
    tb2 = ThoughtBranchState(branch_id="b2", latent_content_hash="b" * 64)
    receipt = LatentScratchpadReceipt(
        trace_id="t1",
        explored_branches=[tb2, tb1],
        discarded_branches=["b2"],
        resolution_branch_id="b1",
        total_latent_tokens=100,
    )
    assert receipt.resolution_branch_id == "b1"
    assert receipt.discarded_branches == ["b2"]
    # Verify sorting
    assert receipt.explored_branches[0].branch_id == "b1"
    assert receipt.explored_branches[1].branch_id == "b2"


def test_latent_scratchpad_receipt_invalid_resolution_branch() -> None:
    tb1 = ThoughtBranchState(branch_id="b1", latent_content_hash="a" * 64)
    with pytest.raises(ValidationError, match="resolution_branch_id 'b99' not found in explored_branches"):
        LatentScratchpadReceipt(
            trace_id="t1",
            explored_branches=[tb1],
            discarded_branches=[],
            resolution_branch_id="b99",
            total_latent_tokens=100,
        )


def test_latent_scratchpad_receipt_invalid_discarded_branch() -> None:
    tb1 = ThoughtBranchState(branch_id="b1", latent_content_hash="a" * 64)
    with pytest.raises(ValidationError, match="discarded branch 'b99' not found in explored_branches"):
        LatentScratchpadReceipt(
            trace_id="t1",
            explored_branches=[tb1],
            discarded_branches=["b99"],
            resolution_branch_id="b1",
            total_latent_tokens=100,
        )


def test_latent_scratchpad_receipt_sort_discarded_branches() -> None:
    tb1 = ThoughtBranchState(branch_id="b1", latent_content_hash="a" * 64)
    tb2 = ThoughtBranchState(branch_id="b2", latent_content_hash="b" * 64)
    tb3 = ThoughtBranchState(branch_id="b3", latent_content_hash="c" * 64)
    receipt = LatentScratchpadReceipt(
        trace_id="t1",
        explored_branches=[tb1, tb2, tb3],
        discarded_branches=["b3", "b1"],
        resolution_branch_id="b2",
        total_latent_tokens=100,
    )
    assert receipt.discarded_branches == ["b1", "b3"]


def test_ephemeral_namespace_partition_state_valid() -> None:
    hash1 = "a" * 64
    hash2 = "b" * 64
    state = EphemeralNamespacePartitionState(
        partition_id="p1",
        execution_runtime="wasm32-wasi",
        authorized_bytecode_hashes=[hash2, hash1],
        max_ttl_seconds=3600,
        max_vram_mb=1024,
    )
    assert state.authorized_bytecode_hashes == [hash1, hash2]


def test_ephemeral_namespace_partition_state_invalid_hash() -> None:
    with pytest.raises(ValidationError, match="Invalid SHA-256 hash in whitelist: invalid-hash"):
        EphemeralNamespacePartitionState(
            partition_id="p1",
            execution_runtime="wasm32-wasi",
            authorized_bytecode_hashes=["invalid-hash"],
            max_ttl_seconds=3600,
            max_vram_mb=1024,
        )
