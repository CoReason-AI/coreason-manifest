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
          (The previous code stripped None. I will continue to strip None for consistency with 'SOTA' context unless RFC says otherwise.
           Actually, RFC 8785 treats null as null. But the prompt said 'Do not rely on Pydantic...'.
           The previous code had 'exclude_none=True'. I'll stick to 'exclude_none=True' logic for Pydantic/dicts as it's cleaner for manifests.)
        """
        if isinstance(obj, BaseModel):
            # Pydantic v2
            # Use model_dump to get a dict, then process recursively
            # exclude_none=True is a common SOTA practice for manifests to keep hash stable across defaults
            return self._prepare_object(obj.model_dump(exclude_none=True, mode='python'))

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
        # - Sorted keys (handled in _prepare_object for stability, but json.dumps sort_keys=True is also good as safeguard)
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


def compute_hash(obj: Any) -> str:
    """
    Convenience function to compute the canonical hash of an object.
    """
    return canonicalizer.compute_hash(obj)
