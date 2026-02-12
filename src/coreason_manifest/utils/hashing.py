from __future__ import annotations

import hashlib
import json
from typing import Any


def canonicalize(data: Any) -> bytes:
    """
    Implements RFC 8785 (JSON Canonicalization Scheme).
    """
    processed_data = _prepare_for_jcs(data)

    return json.dumps(
        processed_data, separators=(",", ":"), sort_keys=True, ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def _prepare_for_jcs(data: Any) -> Any:
    """
    Prepares data for JCS, handling Pydantic aliasing and float normalization.
    """
    if hasattr(data, "model_dump"):
        # CRITICAL FIX: Use by_alias=True to match the wire protocol/YAML contract
        return _prepare_for_jcs(data.model_dump(mode="json", by_alias=True))

    if isinstance(data, dict):
        return {k: _prepare_for_jcs(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_prepare_for_jcs(v) for v in data]
    if isinstance(data, float):
        # RFC 8785: Integers represented as floats must be stripped of .0
        if data.is_integer():
            return int(data)
        return data
    return data


def compute_integrity_hash(entry: Any, exclude_fields: set[str] | None = None) -> str:
    """
    Computes the SHA256 integrity hash.
    Automatically excludes 'integrity_hash' and 'integrityHash' (alias).
    """
    if hasattr(entry, "model_dump"):
        # CRITICAL FIX: by_alias=True
        payload = entry.model_dump(mode="json", by_alias=True)
    elif isinstance(entry, dict):
        payload = entry.copy()
    else:
        payload = entry

    if isinstance(payload, dict):
        fields_to_remove = {"integrity_hash", "integrityHash"}
        if exclude_fields:
            fields_to_remove.update(exclude_fields)

        for field in fields_to_remove:
            if field in payload:
                del payload[field]

    return hashlib.sha256(canonicalize(payload)).hexdigest()


def verify_chain(chain: list[Any]) -> bool:
    """
    Verifies the Merkle-Linear Chain.
    """
    for i, entry in enumerate(chain):
        # Handle both snake_case (internal) and camelCase (serialized) access
        if isinstance(entry, dict):
            stored_hash = entry.get("integrity_hash") or entry.get("integrityHash")
            previous_hash = entry.get("previous_hash") or entry.get("previousHash")
        else:
            stored_hash = getattr(entry, "integrity_hash", None)
            previous_hash = getattr(entry, "previous_hash", None)

        if not stored_hash:
            return False

        if compute_integrity_hash(entry) != stored_hash:
            return False

        if i > 0:
            prev_entry = chain[i - 1]
            if isinstance(prev_entry, dict):
                prev_stored_hash = prev_entry.get("integrity_hash") or prev_entry.get("integrityHash")
            else:
                prev_stored_hash = getattr(prev_entry, "integrity_hash", None)

            if previous_hash != prev_stored_hash:
                return False
    return True
