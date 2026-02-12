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
    Verifies the cryptographic integrity of a state chain (Merkle Proof).

    1. Headless Chain Check: If trusted_root_hash is provided, validates the genesis block.
    2. Chain Continuity: Validates that each block's prev_hash matches the hash of the previous block.
    """
    if not chain:
        return False

    # 1. Headless Chain Check (The Fix)
    if trusted_root_hash:
        # Using the prompt's specific requirement: check chain[0].compute_hash() == trusted_root_hash
        # We use our helper which delegates to .compute_hash() if present.
        genesis_hash = compute_hash(chain[0])
        if genesis_hash != trusted_root_hash:
            return False

    # 2. Chain Continuity
    for i in range(1, len(chain)):
        curr = chain[i]
        prev = chain[i - 1]

        expected_prev_hash = compute_hash(prev)

        # Access prev_hash from current block
        actual_prev_hash = None
        if isinstance(curr, dict):
            actual_prev_hash = curr.get("prev_hash")
        elif hasattr(curr, "prev_hash"):
            actual_prev_hash = curr.prev_hash
        else:
            # If structure doesn't support chaining, we can't verify continuity
            # But the task focuses on "The Headless Chain", so we prioritize the root check.
            # We fail closed if we can't verify links?
            # Or maybe just return True if trusted root passed and no links to check?
            # Assuming standard behavior: fail if prev_hash is missing.
            return False

        if actual_prev_hash != expected_prev_hash:
            return False

    return True
