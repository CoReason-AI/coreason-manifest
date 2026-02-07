# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import hashlib
import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from ..spec.common.observability import AuditLog


def compute_audit_hash(entry: AuditLog | dict[str, Any]) -> str:
    """
    Computes a deterministic SHA-256 hash of the audit entry.

    The hash is computed over the following fields (if present):
    - id
    - request_id
    - root_request_id
    - timestamp
    - actor
    - action
    - outcome
    - previous_hash
    - safety_metadata

    Fields are canonicalized (UUID -> str, datetime -> ISO 8601 UTC) and
    serialized to JSON with sorted keys. `integrity_hash` is explicitly excluded.
    None values are excluded from the payload.
    """
    V1_FIELDS = [
        "id",
        "request_id",
        "root_request_id",
        "timestamp",
        "actor",
        "action",
        "outcome",
        "previous_hash",
        "safety_metadata",
    ]

    # Determine version
    version: str
    if isinstance(entry, dict):
        version = str(entry.get("hash_algorithm", "v2"))
    else:
        version = str(getattr(entry, "hash_algorithm", "v2"))

    fields: list[str]
    if version == "v1":
        fields = V1_FIELDS
    else:
        # v2: Introspection
        fields = (
            list(entry.keys())
            if isinstance(entry, dict)
            else list(type(entry).model_fields.keys())
        )

        # Exclude technical fields
        # Note: hash_algorithm IS included in the payload for v2 to prevent version downgrade attacks
        if "integrity_hash" in fields:
            fields.remove("integrity_hash")

    payload: dict[str, Any] = {}

    for field in fields:
        val: Any = entry.get(field) if isinstance(entry, dict) else getattr(entry, field, None)

        if val is None:
            continue

        if isinstance(val, UUID):
            payload[field] = str(val)
        elif isinstance(val, datetime):
            # Ensure UTC and ISO format
            dt = val
            dt = dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)
            payload[field] = dt.isoformat()
        else:
            payload[field] = val

    # Serialize to JSON bytes
    # ensure_ascii=False to support Unicode characters in names/actions
    # sort_keys=True for determinism
    # default=str to handle non-serializable objects (like sets or custom classes) safely
    json_bytes = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")

    return hashlib.sha256(json_bytes).hexdigest()


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
