# src/coreason_manifest/utils/integrity.py

import hashlib
import json
import math
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel


def to_canonical_timestamp(dt: datetime) -> str:
    """
    Converts a datetime to a strict UTC string format: YYYY-MM-DDTHH:MM:SSZ
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    dt_utc = dt.astimezone(UTC)
    return dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")


class Canonicalizer:
    """
    Sovereign implementation of RFC 8785 (JSON Canonicalization Scheme).
    Enforces strict serialization rules for cryptographic integrity.
    """

    def _prepare_object(self, obj: Any) -> Any:
        """
        Recursively prepares an object for canonical serialization.
        - Dicts: Keys sorted.
        - Pydantic: Dumped to dict.
        - Datetime: ISO formatted.
        - Floats: Integer check.
        - None: Stripped (SOTA requirement from context, though RFC 8785 handles null).
        """
        if isinstance(obj, BaseModel):
            # Pydantic v2
            # Use model_dump to get a dict, then process recursively
            # exclude_none=True is a common SOTA practice for manifests to keep hash stable across defaults
            return self._prepare_object(obj.model_dump(exclude_none=True, mode="python"))

        if isinstance(obj, dict):
            # Sort keys and recurse
            return {
                k: self._prepare_object(v)
                for k, v in sorted(obj.items())
                if v is not None  # Strip None values
            }

        if isinstance(obj, (list, tuple)):
            # Recurse
            return [self._prepare_object(x) for x in obj]

        if isinstance(obj, datetime):
            return to_canonical_timestamp(obj)

        if isinstance(obj, float):
            # RFC 8785: Integers as integers
            if obj.is_integer():
                return int(obj)
            # No NaN/Inf
            if not math.isfinite(obj):
                raise ValueError("NaN and Infinity are not allowed in Canonical JSON")
            return obj

        # Primitive types (str, int, bool) are returned as is
        return obj

    def to_json(self, obj: Any) -> bytes:
        """
        Serializes an object to a canonical JSON byte string (RFC 8785).
        """
        prepared = self._prepare_object(obj)

        # RFC 8785:
        # - UTF-8 (ensure_ascii=False)
        # - No whitespace (separators=(',', ':'))
        # - Sorted keys (handled in _prepare_object, but sort_keys=True is a safeguard)
        return json.dumps(
            prepared,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")

    def compute_hash(self, obj: Any) -> str:
        """
        Computes the SHA-256 hash of the canonical JSON representation.
        """
        json_bytes = self.to_json(obj)
        return hashlib.sha256(json_bytes).hexdigest()


# Singleton instance for easy access
canonicalizer = Canonicalizer()


def compute_hash(obj: Any, **_kwargs: Any) -> str:
    """
    Convenience function to compute the canonical hash of an object.
    Accepts kwargs to maintain compatibility with legacy tests passing 'version'.
    """
    return canonicalizer.compute_hash(obj)


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

        # SOTA: Always use canonicalizer v2 (Greenfield)
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
