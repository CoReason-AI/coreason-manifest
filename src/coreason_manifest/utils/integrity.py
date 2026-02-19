# src/coreason_manifest/utils/integrity.py

import hashlib
import json
import math
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
    Prepares an object for RFC 8785 Canonical JSON serialization.
    - Dicts: Sorted by key. None values removed. Keys sanitized.
    - Lists: Processed recursively.
    - Datetime: Converted to canonical string.
    - Numbers: strict formatting (1.0 -> 1).
    - Pydantic Models: Dumped to dict.
    """
    if isinstance(obj, dict):
        # Universal Hash Sanitization:
        # Strip legacy keys (integrity_hash) and modern keys (execution_hash, signature, __*)
        # Also strip None values (SOTA requirement)
        return {
            k: _recursive_sort_and_sanitize(v)
            for k, v in sorted(obj.items())
            if v is not None and k not in {"integrity_hash", "execution_hash", "signature"} and not k.startswith("__")
        }
    if isinstance(obj, (list, tuple)):
        return [_recursive_sort_and_sanitize(x) for x in obj]
    if isinstance(obj, set):
        # Sets should be sorted lists
        return sorted([_recursive_sort_and_sanitize(x) for x in obj])
    if isinstance(obj, datetime):
        return to_canonical_timestamp(obj)
    if isinstance(obj, BaseModel):
        # Pydantic v2
        excludes = getattr(obj, "_hash_exclude_", None)
        return _recursive_sort_and_sanitize(obj.model_dump(exclude_none=True, exclude=excludes, mode="json"))
    if hasattr(obj, "model_dump"):
        # Pydantic v2 or compatible
        return _recursive_sort_and_sanitize(obj.model_dump(exclude_none=True, mode="json"))
    if isinstance(obj, float):
        # RFC 8785: If number is integer, represent as integer.
        if obj.is_integer():
            return int(obj)
        # For other floats, we rely on json.dumps later, but we can verify finiteness
        if not math.isfinite(obj):
            raise ValueError("NaN and Infinity are not allowed in Canonical JSON")
        return obj

    # SOTA Fix: Enforce strict deterministic types.
    if isinstance(obj, (int, str, bool)) or obj is None:
        return obj

    # Fallback for objects that might have a dict method but aren't Pydantic models (legacy compat)
    if hasattr(obj, "dict") and callable(obj.dict):
        return _recursive_sort_and_sanitize(obj.dict(exclude_none=True))

    if hasattr(obj, "json") and callable(obj.json):
        # Pydantic v1 or compatible (serialized string)
        try:
            return _recursive_sort_and_sanitize(json.loads(obj.json()))
        except (ValueError, TypeError):
            pass

    raise TypeError(f"Object of type {type(obj)} is not deterministically serializable.")


def compute_hash(obj: Any) -> str:
    """
    Computes a SHA-256 hash of a JSON-serializable object using RFC 8785 Canonical JSON rules.
    1. Prepares object (strip None, sort keys, format numbers).
    2. Serializes to JSON with no whitespace.
    3. Computes SHA-256.
    """
    if hasattr(obj, "compute_hash"):
        return str(obj.compute_hash())

    # 1. Prepare
    sanitized = _recursive_sort_and_sanitize(obj)

    # 2. Serialize (RFC 8785 approximation)
    # - separators=(',', ':') removes whitespace
    # - sort_keys=True ensures key order (redundant as we sorted in prepare, but safe)
    # - ensure_ascii=False allows UTF-8 characters (RFC 8785 requires UTF-8)
    # - allow_nan=False forbids NaN/Infinity

    # Note: json.dumps in Python uses "shortest" float representation usually, which matches JCS mostly.
    # The integer check in _prepare_for_canonical_json handles the 1.0 -> 1 case.

    json_bytes = json.dumps(
        sanitized,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False
    ).encode("utf-8")

    # 3. Hash
    return hashlib.sha256(json_bytes).hexdigest()


def reconstruct_payload(node: Any) -> dict[str, Any]:
    """
    Reconstructs the payload dictionary used for hashing from a NodeExecution object.
    Automatically handles SOTA fields by using model_dump if available.
    """
    if isinstance(node, BaseModel):
        return node.model_dump()

    if isinstance(node, dict):
        return node

    # SOTA Fix: Handle list of tuples (as seen in tests)
    if isinstance(node, (list, tuple)):
         try:
             return dict(node)
         except (ValueError, TypeError):
             pass

    # Fallback for other objects (shouldn't happen with strict types)
    try:
        return dict(node)
    except (ValueError, TypeError):
        # Mypy: Returning Any from function declared to return "dict[str, Any]"
        # If conversion fails, we return an empty dict or raise?
        # The prompt "Return as is" causes Mypy error.
        # But if it fails hashing later, we might as well raise or return something valid.
        # Returning `node` as is implies `Any`.
        # We'll cast it to satisfy Mypy, knowing it might be invalid at runtime but handled by caller?
        # Or better: raise TypeError since `reconstruct_payload` expects something dict-like.
        raise TypeError(f"Could not reconstruct payload from {type(node)}")


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
