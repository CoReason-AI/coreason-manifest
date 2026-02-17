from typing import Any
import pytest
from coreason_manifest.utils.integrity import compute_hash, verify_merkle_proof, reconstruct_payload
from pydantic import BaseModel

def test_compute_hash_determinism() -> None:
    data1 = {"b": 2, "a": 1}
    data2 = {"a": 1, "b": 2}
    assert compute_hash(data1) == compute_hash(data2)

def test_verify_merkle_proof_valid() -> None:
    # Use reconstruct_payload to ensure hash consistency
    n1_raw = {"node_id": "genesis", "state": "ok", "previous_hashes": []}
    h1 = compute_hash(reconstruct_payload(n1_raw))
    n1 = {**n1_raw, "execution_hash": h1}

    n2_raw = {"node_id": "child", "state": "ok", "previous_hashes": [h1]}
    h2 = compute_hash(reconstruct_payload(n2_raw))
    n2 = {**n2_raw, "execution_hash": h2}

    assert verify_merkle_proof([n1, n2]) is True

def test_verify_merkle_proof_tampered() -> None:
    n1_raw = {"node_id": "genesis", "state": "ok", "previous_hashes": []}
    h1 = compute_hash(reconstruct_payload(n1_raw))
    n1 = {**n1_raw, "execution_hash": h1}

    # Tamper with n1 after hash computation
    n1_tampered = {**n1, "state": "corrupted"}

    assert verify_merkle_proof([n1_tampered]) is False

def test_verify_merkle_legacy_object_attributes() -> None:
    """
    Updated to use Pydantic model for strict verification compatibility.
    """
    class NodeModel(BaseModel):
        node_id: str
        state: str
        previous_hashes: list[str] = []
        attributes: dict[str, Any] = {}
        # fields needed for reconstruct_payload

    # Genesis
    n1_model = NodeModel(node_id="gen", state="ok")
    # compute_hash handles models by dumping them
    # verify_merkle_proof -> reconstruct_payload -> model_dump
    # We must ensure the hash matches what reconstruct_payload produces.

    # Manually compute hash of the reconstructed payload
    payload1 = reconstruct_payload(n1_model)
    h1 = compute_hash(payload1)

    # Helper wrapper to simulate node with execution_hash
    class SignedNode(NodeModel):
        execution_hash: str

    n1 = SignedNode(**n1_model.model_dump(), execution_hash=h1)

    # Child
    n2_model = NodeModel(node_id="child", state="ok", previous_hashes=[h1])
    payload2 = reconstruct_payload(n2_model)
    h2 = compute_hash(payload2)
    n2 = SignedNode(**n2_model.model_dump(), execution_hash=h2)

    assert verify_merkle_proof([n1, n2]) is True

def test_integrity_legacy_trusted_root_mismatch_at_genesis_continuation() -> None:
    # Valid continuation
    n1_raw = {"node_id": "cont", "state": "ok", "previous_hashes": ["some_hash"]}
    h1 = compute_hash(reconstruct_payload(n1_raw))
    n1 = {**n1_raw, "execution_hash": h1}

    # Mismatch (provided root doesn't match prev_hash)
    assert verify_merkle_proof([n1], trusted_root_hash="other_hash") is False

    # Match (trusted root matches prev_hash)
    assert verify_merkle_proof([n1], trusted_root_hash="some_hash") is True

def test_verify_merkle_legacy_genesis_continuation_loose() -> None:
    # Chain start with prev_hash but no trusted root
    # In strict mode, if prev_hash is present, it must be verified.
    # But for the first node in trace, we can't verify its parent unless we have trusted_root_hash
    # OR if we just accept it as valid genesis.
    # Current logic:
    # if i == 0 and trusted_root_hash and stored_hash != trusted_root_hash: ...
    # if i == 0 and not trusted_root_hash: logic falls through loop?

    # Logic in verify_merkle_proof:
    # 3. Verify Linkage
    # if not previous_hashes: ... (Genesis)
    # else: (Child Node)
    #    for prev_hash in previous_hashes:
    #       if trusted_root_hash and prev_hash == trusted_root_hash: continue
    #       if prev_hash not in verified_hashes: return False

    # So if previous_hashes is set, but trusted_root_hash is None, and verified_hashes is empty (i=0),
    # it returns False. This is STRICT mode. Loose mode would allow this.
    # The previous test asserted True, meaning it was testing loose mode.
    # Since we are strict now, this should fail.

    n1_raw = {"node_id": "cont", "state": "ok", "previous_hashes": ["some_hash"]}
    h1 = compute_hash(reconstruct_payload(n1_raw))
    n1 = {**n1_raw, "execution_hash": h1}

    # Strict mode forbids unanchored continuations
    assert verify_merkle_proof([n1], trusted_root_hash=None) is False
