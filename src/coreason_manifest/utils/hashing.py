from __future__ import annotations

import hashlib
import json
from typing import Any


def canonicalize(data: Any) -> bytes:
    """
    Implements RFC 8785 (JSON Canonicalization Scheme) logic.
    - Dictionaries: Keys sorted lexicographically.
    - Whitespace: Compact representation (no whitespace).
    - Floats: Strip trailing zeros if integer (e.g. 20.0 -> 20).
    """
    processed_data = _prepare_for_jcs(data)

    # separators=(',', ':') removes whitespace
    # sort_keys=True sorts dictionary keys
    # ensure_ascii=False ensures UTF-8 characters are not escaped
    return json.dumps(
        processed_data,
        separators=(',', ':'),
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False
    ).encode('utf-8')

def _prepare_for_jcs(data: Any) -> Any:
    """
    Recursively prepares data for JCS serialization.
    - Converts integer-like floats to ints.
    - Handles Pydantic models if passed directly.
    """
    if hasattr(data, "model_dump"):
        # If it's a Pydantic model, dump it first
        return _prepare_for_jcs(data.model_dump(mode='json'))

    if isinstance(data, dict):
        return {k: _prepare_for_jcs(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_prepare_for_jcs(v) for v in data]
    if isinstance(data, float):
        if data.is_integer():
            return int(data)
        return data
    return data

def compute_integrity_hash(entry: Any, exclude_fields: set[str] | None = None) -> str:
    """
    Computes the SHA256 integrity hash of a log entry or object.
    Automatically excludes 'integrity_hash' to avoid self-reference.
    """
    # Create a mutable payload
    if hasattr(entry, "model_dump"):
        payload = entry.model_dump(mode='json')
    elif isinstance(entry, dict):
        payload = entry.copy()
    else:
        # If it's a primitive or list, we can't exclude fields easily,
        # but also lists don't have named fields. Just use as is.
        payload = entry

    # Remove excluded fields only if payload is a dict
    if isinstance(payload, dict):
        fields_to_remove = set()
        if exclude_fields:
            fields_to_remove.update(exclude_fields)
        fields_to_remove.add("integrity_hash")

        for field in fields_to_remove:
            if field in payload:
                del payload[field]

    # Canonicalize
    canonical_bytes = canonicalize(payload)

    # Hash
    return hashlib.sha256(canonical_bytes).hexdigest()

def verify_chain(chain: list[Any]) -> bool:
    """
    Verifies a Merkle-Linear Chain of audit logs.
    Checks:
    1. entry.integrity_hash matches the computed hash of the entry.
    2. entry.previous_hash matches the previous entry's integrity_hash.
    """
    for i, entry in enumerate(chain):
        # Access attributes
        if isinstance(entry, dict):
            stored_hash = entry.get("integrity_hash")
            previous_hash = entry.get("previous_hash")
        else:
            stored_hash = getattr(entry, "integrity_hash", None)
            previous_hash = getattr(entry, "previous_hash", None)

        if not stored_hash:
            # Missing hash implies broken chain or invalid entry
            return False

        # Re-compute hash (this automatically excludes 'integrity_hash' from calculation)
        computed = compute_integrity_hash(entry)

        if stored_hash != computed:
            return False

        # Verify link to previous
        if i > 0:
            prev_entry = chain[i-1]
            if isinstance(prev_entry, dict):
                prev_stored_hash = prev_entry.get("integrity_hash")
            else:
                prev_stored_hash = getattr(prev_entry, "integrity_hash", None)

            if previous_hash != prev_stored_hash:
                return False
        # Genesis block (i=0) has no previous link to check

    return True
