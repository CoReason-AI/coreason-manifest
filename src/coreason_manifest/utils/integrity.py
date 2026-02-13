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
    Verifies the cryptographic integrity of a chain or DAG trace.

    Supports two modes:
    1. NodeExecution DAG (Strict): Verifies content integrity (re-hashing) and DAG linkage.
    2. Generic/Legacy Chain (Loose): Verifies simple hash linkage via `prev_hash`.
    """
    if not trace:
        return False

    verified_hashes = set()

    for i, node in enumerate(trace):
        # Determine verification mode
        # Check if it looks like a NodeExecution (has execution_hash and previous_hashes)
        is_node_exec = False
        if (hasattr(node, "execution_hash") and hasattr(node, "previous_hashes")) or (
            isinstance(node, dict) and "execution_hash" in node and "previous_hashes" in node
        ):
            is_node_exec = True

        if is_node_exec:
            # --- Strict NodeExecution Verification ---

            # 1. Verify Content Integrity
            payload = reconstruct_payload(node)
            computed_hash = compute_hash(payload)

            stored_hash = None
            if hasattr(node, "execution_hash"):
                stored_hash = node.execution_hash
            elif isinstance(node, dict):
                stored_hash = node.get("execution_hash")

            if stored_hash != computed_hash:
                return False

            # 2. Extract declared parents
            previous_hashes = payload["previous_hashes"]

            # 3. Verify Linkage
            if not previous_hashes:
                # Genesis Node
                if i == 0 and trusted_root_hash and stored_hash != trusted_root_hash:
                    return False
            else:
                # Child Node
                for prev_hash in previous_hashes:
                    if trusted_root_hash and prev_hash == trusted_root_hash:
                        continue
                    if prev_hash not in verified_hashes:
                        return False

            current_hash_for_set = stored_hash

        else:
            # --- Legacy/Generic Verification ---

            # 1. Compute Hash
            current_hash_for_set = compute_hash(node)

            # 2. Extract Previous Hash
            prev_hash = None
            if isinstance(node, dict):
                prev_hash = node.get("prev_hash")
            elif hasattr(node, "prev_hash"):
                prev_hash = node.prev_hash

            # 3. Verify Linkage
            if prev_hash is None:
                # Genesis check
                if i == 0:
                    if trusted_root_hash and current_hash_for_set != trusted_root_hash:
                        return False
                else:
                    # Missing prev_hash in non-genesis node -> Fail
                    return False
            else:
                # Chain check
                # For legacy, previous block hash is expected_prev_hash
                # But here we verify if prev_hash points to a KNOWN hash in verified_hashes.
                # However, the legacy verify_merkle_proof (from step 1) logic was:
                # prev = chain[i-1]; expected = compute_hash(prev); actual == expected.
                # This assumes LINEAR chain order.
                # If we want to support the test cases which are linear chains:

                if i > 0:
                    prev_node = trace[i - 1]
                    expected_prev_hash = compute_hash(prev_node)
                    if prev_hash != expected_prev_hash:
                        return False
                elif trusted_root_hash:
                    if prev_hash != trusted_root_hash:
                        return False
                elif prev_hash:
                    # Has prev_hash but is index 0 and no trusted root to match.
                    # Allow loosely for generic objects/partial chains.
                    pass

        # 4. Add to verified set
        verified_hashes.add(current_hash_for_set)

    return True
