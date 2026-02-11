# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import uuid
from datetime import UTC, datetime
from typing import Any

from coreason_manifest.spec.common.observability import AuditLog
from coreason_manifest.utils.audit import _safe_serialize, compute_audit_hash, verify_chain


def test_audit_log_safety_metadata_roundtrip() -> None:
    """
    Security Test: Verify that AuditLog correctly preserves safety_metadata
    and that the integrity hash matches between dict source and model instance.
    """
    log_id = uuid.uuid4()
    req_id = uuid.uuid4()

    # Source data with security context
    data: dict[str, Any] = {
        "id": log_id,
        "request_id": req_id,
        "root_request_id": req_id,
        "timestamp": datetime.now(UTC),
        "actor": "admin",
        "action": "override_policy",
        "outcome": "success",
        "safety_metadata": {"reason": "emergency", "approved_by": "CISO"},
        "previous_hash": None,
    }

    # 1. Compute hash from raw data (simulating storage/transport)
    expected_hash = compute_audit_hash(data)

    # 2. Load into AuditLog model (simulating verification)
    log = AuditLog(**data, integrity_hash=expected_hash)

    # 3. Verify that the model retained the metadata
    assert log.safety_metadata == data["safety_metadata"]

    # 4. Verify that re-computing hash from model matches expected hash
    computed_hash = compute_audit_hash(log)
    assert computed_hash == expected_hash, "Hash mismatch: AuditLog lost security context!"

    # 5. Verify chain validation passes
    assert verify_chain([log]) is True


def test_audit_log_safety_metadata_tamper() -> None:
    """Verify that modifying safety_metadata invalidates the hash."""
    log_id = uuid.uuid4()
    req_id = uuid.uuid4()

    data: dict[str, Any] = {
        "id": log_id,
        "request_id": req_id,
        "root_request_id": req_id,
        "timestamp": datetime.now(UTC),
        "actor": "admin",
        "action": "override_policy",
        "outcome": "success",
        "safety_metadata": {"reason": "valid"},
        "previous_hash": None,
    }

    initial_hash = compute_audit_hash(data)
    log = AuditLog(**data, integrity_hash=initial_hash)

    # Create a tampered log with different metadata but same hash
    tampered_log = AuditLog(
        id=log.id,
        request_id=log.request_id,
        root_request_id=log.root_request_id,
        timestamp=log.timestamp,
        actor=log.actor,
        action=log.action,
        outcome=log.outcome,
        previous_hash=log.previous_hash,
        safety_metadata={"reason": "malicious"},  # Tampered
        integrity_hash=log.integrity_hash,
    )

    # Verify chain should fail
    assert verify_chain([tampered_log]) is False


def test_audit_sensitive_data_redaction() -> None:
    """Test that sensitive objects are redacted in audit logs."""

    class SecretKey:
        def __repr__(self) -> str:
            return "SECRET_API_KEY_12345"

        def __str__(self) -> str:
            return "SECRET_API_KEY_12345"

    entry = {
        "id": uuid.uuid4(),
        "action": "login",
        "timestamp": datetime.now(UTC),
        "details": {
            "username": "admin",
            "key": SecretKey(),  # This should be redacted
            "safe_val": 123,
        },
    }

    # Compute hash
    hash_val = compute_audit_hash(entry)

    # Verify via _safe_serialize
    serialized = _safe_serialize(entry)

    assert serialized["details"]["key"] == "<REDACTED_TYPE: SecretKey>"
    assert serialized["details"]["username"] == "admin"
    assert serialized["details"]["safe_val"] == 123

    # Ensure it doesn't crash
    assert isinstance(hash_val, str)
    assert len(hash_val) == 64
