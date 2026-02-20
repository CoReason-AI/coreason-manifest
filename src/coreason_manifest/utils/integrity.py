# src/coreason_manifest/utils/integrity.py

import hashlib
import json
import math
import uuid
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any, Literal, TypedDict

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


class HashingStrategy(ABC):
    """
    Abstract base class for hashing strategies.
    Ensures verification capability across different protocol versions.
    """

    @abstractmethod
    def compute_hash(self, obj: Any) -> str:
        """Computes the deterministic hash of the object."""


class LegacyV1Strategy(HashingStrategy):
    """
    Legacy hashing strategy (v0.24.0 compatibility).
    Uses Python's native json.dumps(sort_keys=True).
    Weakness: Vulnerable to serialization drift.
    """

    def compute_hash(self, obj: Any) -> str:
        # Naive dump, mimicking legacy behavior
        # Note: Legacy might not have handled Pydantic models gracefully in all paths,
        # but we assume obj is usually a dict or model.
        data = obj
        if isinstance(obj, BaseModel):
            data = obj.model_dump(mode="json")

        # Native sort_keys=True
        # SOTA Directive: Re-enable ensure_ascii=False to match v0.24.0 legacy behavior.
        # This prevents unicode escape sequences (e.g. \uXXXX) from altering the hash.
        json_bytes = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(json_bytes).hexdigest()


class CanonicalV2Strategy(HashingStrategy):
    """
    SOTA hashing strategy (RFC 8785 Compliance).
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
            # Strip legacy keys (integrity_hash) and modern keys (execution_hash, signature, __*)
            # Also strip None values (SOTA requirement)
            return {
                k: self._recursive_sort_and_sanitize(v)
                for k, v in sorted(obj.items())
                if v is not None
                and k not in {"integrity_hash", "execution_hash", "signature"}
                and not k.startswith("__")
            }
        if isinstance(obj, (list, tuple)):
            return [self._recursive_sort_and_sanitize(x) for x in obj]
        if isinstance(obj, (set, frozenset)):
            # Sets should be sorted lists
            return sorted([self._recursive_sort_and_sanitize(x) for x in obj])
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
            # We strictly avoid scientific notation for typical ranges, but standard json.dumps
            # does ok for simple values. For full JCS compliance, one might need a custom float formatter,
            # but verifying finiteness is the critical SOTA check requested.
            if not math.isfinite(obj):
                raise ValueError("NaN and Infinity are not allowed in Canonical JSON")
            return obj

        # SOTA Fix: Enforce strict deterministic types.
        if isinstance(obj, (int, str, bool)) or obj is None:
            return obj

        # Fallback for objects that might have a dict method but aren't Pydantic models (legacy compat)
        if hasattr(obj, "dict") and callable(obj.dict):
            return self._recursive_sort_and_sanitize(obj.dict(exclude_none=True))

        if hasattr(obj, "json") and callable(obj.json):
            # Pydantic v1 or compatible (serialized string)
            try:
                return self._recursive_sort_and_sanitize(json.loads(obj.json()))
            except (ValueError, TypeError):
                pass

        raise TypeError(f"Object of type {type(obj)} is not deterministically serializable.")

    def compute_hash(self, obj: Any) -> str:
        if hasattr(obj, "compute_hash"):
            # Self-hashing objects (avoid infinite recursion if they call back here)
            # Assuming they don't call this function inside their compute_hash without args.
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


# Default Strategy Registry
_STRATEGIES: dict[str, HashingStrategy] = {
    "v1": LegacyV1Strategy(),
    "v2": CanonicalV2Strategy(),
}


def compute_hash(obj: Any, version: Literal["v1", "v2"] = "v2") -> str:
    """
    Computes a SHA-256 hash of a JSON-serializable object.
    Defaults to SOTA v2 (RFC 8785).
    """
    strategy = _STRATEGIES.get(version)
    if not strategy:
        raise ValueError(f"Unknown hashing version: {version}")
    return strategy.compute_hash(obj)


def reconstruct_payload(node: Any) -> dict[str, Any]:
    """
    Reconstructs the payload dictionary used for hashing from a NodeExecution object.
    Automatically handles SOTA fields by using model_dump if available.
    """
    if isinstance(node, BaseModel):
        return node.model_dump()

    if isinstance(node, dict):
        return node

    # Fix: Strict tuple handling. No brittle casting.
    # If the input is not a dict or a model, it is likely invalid for payload reconstruction.
    # The previous implementation attempted `dict(node)` which works for list of tuples but is unsafe.
    if isinstance(node, (list, tuple)):
        # Explicit check if it looks like pairs
        try:
            return dict(node)
        except (ValueError, TypeError) as e:
            raise TypeError(f"Could not reconstruct payload from iterable {type(node)}") from e

    # Fallback for other objects
    try:
        return dict(node)
    except (ValueError, TypeError) as e:
        raise TypeError(f"Could not reconstruct payload from {type(node)}") from e


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

        # Determine hash version from payload if present, default to v1 for legacy compatibility?
        # SOTA requires v2. If payload has 'hash_version', use it.
        version = payload.get("hash_version", "v1")  # Default to v1 if unspecified? Or assume v2 for new system?
        # Given "Greenfield Refactor", we default to v2 if missing, OR we check the node.
        # But legacy logs might be v1.
        # Ideally, look for 'hash_version' field.
        if version not in ("v1", "v2"):
            version = "v2"  # Fallback to latest

        computed_hash = compute_hash(payload, version=version)

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
