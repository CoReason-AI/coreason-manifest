# src/coreason_manifest/utils/integrity.py

import hashlib
import json
from typing import Any


def compute_hash(obj: Any) -> str:
    """
    Computes a SHA-256 hash of a JSON-serializable object.
    If the object has a .compute_hash() method, it uses that.
    """
    if hasattr(obj, "compute_hash"):
        return str(obj.compute_hash())

    # Standardize serialization for hashing
    if hasattr(obj, "model_dump_json"):
        # Pydantic v2
        data = obj.model_dump_json(exclude_none=True)
    elif hasattr(obj, "json"):
        # Pydantic v1 or similar
        data = obj.json()
    elif isinstance(obj, dict):
        data = json.dumps(obj, sort_keys=True, default=str)
    else:
        # Fallback
        data = str(obj)

    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def reconstruct_payload(node: Any) -> dict[str, Any]:
    """
    Reconstructs the payload dictionary used for hashing from a NodeExecution object.
    """
    # Extract fields assuming node is NodeExecution or dict
    d = node if isinstance(node, dict) else node.model_dump()

    # Replicate recorder.py payload construction
    timestamp = d.get("timestamp")
    if timestamp and hasattr(timestamp, "isoformat"):
        timestamp = timestamp.isoformat()
    elif timestamp and not isinstance(timestamp, str):
        timestamp = str(timestamp)

    return {
        "node_id": d.get("node_id"),
        "state": d.get("state"),
        "inputs": d.get("inputs"),
        "outputs": d.get("outputs"),
        "error": d.get("error"),
        "timestamp": timestamp,
        "duration_ms": d.get("duration_ms"),
        "attributes": d.get("attributes", {}),
        "previous_hashes": sorted(d.get("previous_hashes", [])),
    }


def verify_merkle_proof(trace: list[Any], trusted_root_hash: str | None = None) -> bool:
    """
    Verifies the cryptographic integrity of a DAG trace (Merkle DAG).

    1. Content Integrity: Recomputes the hash of each node and compares with its `execution_hash`.
    2. Link Integrity: Each node's declared `previous_hashes` must exist in the verified history.
    """
    if not trace:
        return False

    verified_hashes = set()

    for i, node in enumerate(trace):
        # 1. Verify Content Integrity
        # We must recompute the hash exactly as the recorder did
        payload = reconstruct_payload(node)
        computed_hash = compute_hash(payload)

        stored_hash = None
        if hasattr(node, "execution_hash"):
            stored_hash = node.execution_hash
        elif isinstance(node, dict):
            stored_hash = node.get("execution_hash")

        if stored_hash != computed_hash:
            # Hash mismatch implies tampering or corruption
            return False

        # 2. Extract declared parents
        previous_hashes = payload["previous_hashes"]

        # 3. Verify Linkage
        if not previous_hashes:
            # Genesis Node (No parents in this trace)
            if i == 0 and trusted_root_hash and stored_hash != trusted_root_hash:
                return False
        else:
            # Child Node
            # Ensure ALL hash strings in node.previous_hashes exist in verified_hashes.
            for prev_hash in previous_hashes:
                # If trusted_root_hash acts as an external parent
                if trusted_root_hash and prev_hash == trusted_root_hash:
                    continue

                if prev_hash not in verified_hashes:
                    return False

        # 4. Add to verified set
        verified_hashes.add(stored_hash)

    return True
