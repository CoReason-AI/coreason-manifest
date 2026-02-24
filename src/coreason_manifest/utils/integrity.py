# src/coreason_manifest/utils/integrity.py

import hashlib
import json
import math
import uuid
from abc import ABC, abstractmethod
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
    parent_hashes: list[str]


class HashingStrategy(ABC):
    """
    Abstract base class for hashing strategies.
    Ensures verification capability across different protocol versions.
    """

    @abstractmethod
    def compute_hash(self, obj: Any) -> str:
        """Computes the deterministic hash of the object."""


class CanonicalHashingStrategy(HashingStrategy):
    """
    Canonical hashing strategy enforcing RFC 8785 compliance.
    Note: This implementation approximates true JCS (RFC 8785) compliance.
    Specific ECMA-262 double-precision float formatting is approximated by Python's
    standard library. Full compliance would require a custom dtoa implementation.
    - Strict float formatting (no NaN/Inf).
    - Strips None values.
    - Deterministic key sorting.
    - UTF-8 enforcement (no escapes).
    """

    def _recursive_sort_and_sanitize(self, obj: Any) -> Any:
        """
        Prepares an object for RFC 8785 Canonical JSON serialization.
        """
        if isinstance(obj, dict):
            # Universal Hash Sanitization:
            # Strip modern keys (execution_hash, signature, __*)
            # Also strip None values (Architectural requirement)
            return {
                k: self._recursive_sort_and_sanitize(v)
                for k, v in sorted(obj.items())
                if v is not None
                and k not in {"execution_hash", "signature", "integrity_hash"}
                and not k.startswith("__")
            }
        if isinstance(obj, (list, tuple)):
            return [self._recursive_sort_and_sanitize(x) for x in obj]
        if isinstance(obj, (set, frozenset)):
            # Sets should be sorted lists
            return sorted([self._recursive_sort_and_sanitize(x) for x in obj], key=str)
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return to_canonical_timestamp(obj)
        if isinstance(obj, BaseModel):
            # Pydantic v2
            excludes = getattr(obj, "_hash_exclude_", None)
            return self._recursive_sort_and_sanitize(obj.model_dump(exclude_none=True, exclude=excludes, mode="python"))
        if hasattr(obj, "model_dump"):
            # Pydantic v2 or compatible
            return self._recursive_sort_and_sanitize(obj.model_dump(exclude_none=True, mode="python"))
        if isinstance(obj, float):
            # RFC 8785: If number is integer, represent as integer.
            if obj.is_integer():
                return int(obj)
            # For other floats, verify finiteness.
            if not math.isfinite(obj):
                raise ValueError("NaN and Infinity are not allowed in Canonical JSON")
            return obj

        # Architectural Note: Enforce strict deterministic types.
        if isinstance(obj, (int, str, bool)) or obj is None:
            return obj

        raise TypeError(f"Object of type {type(obj)} is not deterministically serializable.")

    def compute_hash(self, obj: Any) -> str:
        if hasattr(obj, "compute_hash"):
            # Self-hashing objects (avoid infinite recursion if they call back here)
            return str(obj.compute_hash())

        sanitized = self._recursive_sort_and_sanitize(obj)

        # RFC 8785 approximation:
        # - separators=(',', ':') removes whitespace
        # - sort_keys=True
        # - ensure_ascii=False (UTF-8)
        # - allow_nan=False
        json_bytes = json.dumps(
            sanitized, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")

        return hashlib.sha256(json_bytes).hexdigest()


def compute_hash(obj: Any) -> str:
    """
    Computes a SHA-256 hash of a JSON-serializable object using the CanonicalHashingStrategy (RFC 8785).
    """
    # Inherently use CanonicalHashingStrategy
    return CanonicalHashingStrategy().compute_hash(obj)


def reconstruct_payload(node: Any) -> dict[str, Any]:
    """
    Reconstructs the payload dictionary used for hashing from a NodeExecution object.
    Automatically handles SOTA fields by using model_dump if available.
    """
    if isinstance(node, BaseModel):
        return node.model_dump()

    if isinstance(node, dict):
        return node

    # Strict Design Rule: No implicit casting.
    raise TypeError(f"Could not reconstruct payload from {type(node)}. Must be dict or Pydantic model.")


def verify_merkle_proof(trace: list[Any], trusted_root_hash: str | None = None) -> bool:
    """
    Verifies the cryptographic integrity of a DAG trace.
    Mathematically reconstructs the DAG topology to prove absence of parallel hallucinations.
    """
    if not trace:
        return False

    verified_hashes = set()

    for i, node in enumerate(trace):
        # 1. Verify Content Integrity
        try:
            payload = reconstruct_payload(node)
        except TypeError:
            return False

        # Design Rule: Always use v2
        computed_hash = compute_hash(payload)

        stored_hash = payload.get("execution_hash")

        if not stored_hash or stored_hash != computed_hash:
            return False

        # 2. Extract declared parents (Topology Verification)
        # Support both Linear (parent_hash) and DAG (parent_hashes)
        parent_hashes = payload.get("parent_hashes", [])
        parent_hash = payload.get("parent_hash")

        expected_parents = set()
        if parent_hashes:
            expected_parents.update(parent_hashes)
        if parent_hash:
            expected_parents.add(parent_hash)

        # 3. Verify Linkage
        if not expected_parents:
            # Genesis Node
            if i == 0 and trusted_root_hash and stored_hash != trusted_root_hash:
                return False
        else:
            # Child Node: Every declared parent must be present in the VERIFIED pool.
            for prev_hash in expected_parents:
                if trusted_root_hash and prev_hash == trusted_root_hash:
                    continue
                if prev_hash not in verified_hashes:
                    # Topology Violation: Node claims a parent that hasn't been verified.
                    return False

        # 4. Add to verified set (Topological Progress)
        verified_hashes.add(stored_hash)

    return True
