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


def verify_merkle_proof(chain: list[Any], trusted_root_hash: str | None = None) -> bool:
    """
    Verifies the cryptographic integrity of a state DAG (Merkle Proof).

    1. Headless Chain Check: If trusted_root_hash is provided, validates the genesis block.
    2. DAG Continuity: Validates that each block's previous_hashes point to known, verified blocks.
    """
    if not chain:
        return False

    # 1. Headless Chain Check
    genesis_hash = compute_hash(chain[0])
    if trusted_root_hash and genesis_hash != trusted_root_hash:
        return False

    # Initialize verified hashes with genesis
    verified_hashes = {genesis_hash}

    # 2. DAG Continuity
    for i in range(1, len(chain)):
        curr = chain[i]

        # Extract previous_hashes
        previous_hashes: list[str] = []
        if isinstance(curr, dict):
            previous_hashes = curr.get("previous_hashes", [])
        elif hasattr(curr, "previous_hashes"):
            previous_hashes = curr.previous_hashes
        else:
            # If structure doesn't support DAG chaining (missing field), fail strict validation
            return False

        # Strictness: All referenced hashes must be verified
        if not previous_hashes:
            # Disconnected node or multiple roots are not standard in this context
            # expecting at least one previous hash for non-genesis nodes
            return False

        for ph in previous_hashes:
            if ph not in verified_hashes:
                return False

        # Compute and store current hash
        current_hash = compute_hash(curr)
        verified_hashes.add(current_hash)

    return True
