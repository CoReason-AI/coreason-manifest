# src/coreason_manifest/utils/integrity.py

import hashlib
import json
from datetime import UTC, datetime
from typing import Any, TypedDict

from pydantic import BaseModel


def to_canonical_timestamp(dt: datetime) -> str:
    """
    Converts a datetime to a strict UTC string format: YYYY-MM-DDTHH:MM:SSZ
    """
    if dt.tzinfo is None:
        # Assume UTC if naive
        dt = dt.replace(tzinfo=UTC)

    # Convert to UTC
    dt_utc = dt.astimezone(UTC)

    # Format as YYYY-MM-DDTHH:MM:SSZ (no microseconds)
    return dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")


class MerkleNode(TypedDict):
    """
    Standard structure for verifiable execution blocks.
    """

    execution_hash: str
    previous_hashes: list[str]


def _recursive_sort_and_sanitize(obj: Any) -> Any:
    """
    Recursively sorts dictionary keys and sanitizes values for consistent hashing.
    - Dicts: Sorted by key. None values removed. Keys sanitized.
    - Lists: Processed recursively.
    - Datetime: Converted to canonical string.
    - Models: Converted to dicts.
    """
    if isinstance(obj, dict):
        # Universal Hash Sanitization:
        # Strip legacy keys (integrity_hash) and modern keys (execution_hash, signature, __*)
        return {
            k: _recursive_sort_and_sanitize(v)
            for k, v in sorted(obj.items())
            if v is not None and k not in {"integrity_hash", "execution_hash", "signature"} and not k.startswith("__")
        }
    if isinstance(obj, (list, tuple)):
        return [_recursive_sort_and_sanitize(x) for x in obj]
    if isinstance(obj, set):
        return sorted([_recursive_sort_and_sanitize(x) for x in obj])
    if isinstance(obj, datetime):
        return to_canonical_timestamp(obj)
    if isinstance(obj, BaseModel):
        # Pydantic v2
        excludes = getattr(obj, "_hash_exclude_", None)
        return _recursive_sort_and_sanitize(obj.model_dump(exclude_none=True, exclude=excludes))
    if hasattr(obj, "model_dump"):
        # Pydantic v2 or compatible
        return _recursive_sort_and_sanitize(obj.model_dump(exclude_none=True))
    if hasattr(obj, "dict"):
        # Pydantic v1
        return _recursive_sort_and_sanitize(obj.dict(exclude_none=True))
    if hasattr(obj, "json") and callable(obj.json):
        # Pydantic v1 or compatible (serialized string)
        try:
            return _recursive_sort_and_sanitize(json.loads(obj.json()))
        except (ValueError, TypeError):  # pragma: no cover
            pass
    return obj


def compute_hash(obj: Any) -> str:
    """
    Computes a SHA-256 hash of a JSON-serializable object.
    If the object has a .compute_hash() method, it uses that.
    """
    if hasattr(obj, "compute_hash"):
        return str(obj.compute_hash())

    # Standardize serialization for hashing
    sanitized = _recursive_sort_and_sanitize(obj)

    # json.dumps with sort_keys=True ensures consistent ordering (redundant but safe)
    data = json.dumps(sanitized, sort_keys=True, default=str)

    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def reconstruct_payload(node: Any) -> dict[str, Any]:
    """
    Reconstructs the payload dictionary used for hashing from a NodeExecution object.
    Automatically handles SOTA fields by using model_dump if available.
    """
    if isinstance(node, BaseModel):
        return node.model_dump()

    if isinstance(node, dict):
        return node

    # Fallback for other objects (shouldn't happen with strict types)
    return dict(node)


def verify_merkle_proof(trace: list[Any], trusted_root_hash: str | None = None) -> bool:
    """
    Verifies the cryptographic integrity of a DAG trace.
    Strictly enforcing NodeExecution structure.
    """
    if not trace:
        return False

    verified_hashes = set()

    for i, node in enumerate(trace):
        # 1. Verify Content Integrity
        payload = reconstruct_payload(node)
        computed_hash = compute_hash(payload)

        stored_hash = None
        if hasattr(node, "execution_hash"):
            stored_hash = node.execution_hash
        elif isinstance(node, dict):
            stored_hash = node.get("execution_hash")

        if not stored_hash or stored_hash != computed_hash:
            return False

        # 2. Extract declared parents
        previous_hashes = payload.get("previous_hashes", [])

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

        # 4. Add to verified set
        verified_hashes.add(stored_hash)

    return True
