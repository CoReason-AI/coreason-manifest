# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import asyncio
import hashlib
import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from ..spec.common.observability import AuditLog


def _safe_serialize(obj: Any) -> Any:
    """
    Recursively serializes an object into a JSON-safe structure with strict type allowing.

    Allowed types: dict, list, tuple, str, int, float, bool, None.
    Converted types: UUID -> str, datetime -> ISO 8601 str.
    All other types are redacted.
    """
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, (list, tuple)):
        return [_safe_serialize(item) for item in obj]
    if isinstance(obj, dict):
        # Sort keys for determinism
        return {k: _safe_serialize(v) for k, v in sorted(obj.items())}
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, datetime):
        # Ensure UTC and ISO format
        dt = obj
        dt = dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)
        return dt.isoformat()

    # Fail-Safe Redaction
    return f"<REDACTED_TYPE: {type(obj).__name__}>"


def compute_audit_hash(entry: AuditLog | dict[str, Any]) -> str:
    """
    Computes a deterministic SHA-256 hash of the audit entry.

    The hash is computed over all fields present in the entry, except `integrity_hash`.
    This uses introspection to ensure all current and future fields are
    automatically included in the integrity check.

    Fields are canonicalized (UUID -> str, datetime -> ISO 8601 UTC) and
    serialized to JSON with sorted keys. `integrity_hash` is explicitly excluded.
    None values are excluded from the payload.
    """
    # Fields to extract: Use introspection to get all fields
    fields = list(type(entry).model_fields.keys()) if isinstance(entry, BaseModel) else list(entry.keys())

    # Explicitly exclude integrity_hash
    if "integrity_hash" in fields:
        fields.remove("integrity_hash")

    payload: dict[str, Any] = {}

    for field in fields:
        val: Any = entry.get(field) if isinstance(entry, dict) else getattr(entry, field, None)

        if val is None:
            continue

        payload[field] = val

    # Serialize using safe serializer
    safe_payload = _safe_serialize(payload)

    # Serialize to JSON bytes
    # ensure_ascii=False to support Unicode characters in names/actions
    # sort_keys=True for determinism
    json_bytes = json.dumps(safe_payload, sort_keys=True, ensure_ascii=False).encode("utf-8")

    return hashlib.sha256(json_bytes).hexdigest()


async def compute_audit_hash_async(entry: AuditLog | dict[str, Any]) -> str:
    """
    Asynchronously computes a deterministic SHA-256 hash of the audit entry.
    Offloads the CPU-bound hashing to a thread pool.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, compute_audit_hash, entry)


def verify_chain(chain: list[AuditLog]) -> bool:
    """
    Verifies the cryptographic integrity of a chain of audit logs.

    Checks:
    1. Each log's integrity_hash matches the re-computed hash.
    2. Each log's previous_hash matches the preceding log's integrity_hash.
    """
    if not chain:
        return True

    for i, log in enumerate(chain):
        # 1. Verify self integrity
        computed = compute_audit_hash(log)
        if computed != log.integrity_hash:
            return False

        # 2. Verify chain link
        if i > 0:
            prev_log = chain[i - 1]
            if log.previous_hash != prev_log.integrity_hash:
                return False

    return True


async def verify_chain_async(chain: list[AuditLog]) -> bool:
    """
    Asynchronously verifies the cryptographic integrity of a chain of audit logs.
    Offloads the CPU-bound verification loop to a thread pool.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, verify_chain, chain)
