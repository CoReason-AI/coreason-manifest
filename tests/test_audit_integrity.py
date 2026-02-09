# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from datetime import UTC, datetime
from uuid import uuid4

from coreason_manifest.spec.common.observability import AuditLog
from coreason_manifest.utils.audit import compute_audit_hash, verify_chain


def test_audit_dict_behavior() -> None:
    """Verify compute_audit_hash includes extra fields in dict."""
    entry_id = uuid4()
    req_id = uuid4()
    root_req_id = uuid4()
    ts = datetime.now(UTC)

    base_data = {
        "id": entry_id,
        "request_id": req_id,
        "root_request_id": root_req_id,
        "timestamp": ts,
        "actor": "user",
        "action": "login",
        "outcome": "success",
        "extra_field": "secret",
    }

    hash1 = compute_audit_hash(base_data)

    tampered_data = base_data.copy()
    tampered_data["extra_field"] = "changed"
    hash2 = compute_audit_hash(tampered_data)

    assert hash1 != hash2


def test_audit_model_behavior() -> None:
    """Verify compute_audit_hash includes extra fields in Pydantic model subclass."""

    class ExtendedAuditLog(AuditLog):
        user_ip: str

    entry_id = uuid4()
    req_id = uuid4()
    root_req_id = uuid4()
    ts = datetime.now(UTC)

    log1 = ExtendedAuditLog(
        id=entry_id,
        request_id=req_id,
        root_request_id=root_req_id,
        timestamp=ts,
        actor="user",
        action="login",
        outcome="success",
        integrity_hash="placeholder",
        user_ip="1.1.1.1",
    )

    hash1 = compute_audit_hash(log1)

    log2 = ExtendedAuditLog(
        id=entry_id,
        request_id=req_id,
        root_request_id=root_req_id,
        timestamp=ts,
        actor="user",
        action="login",
        outcome="success",
        integrity_hash="placeholder",
        user_ip="2.2.2.2",
    )

    hash2 = compute_audit_hash(log2)

    assert hash1 != hash2


def test_verify_chain_valid() -> None:
    """Verify a valid chain of audit logs."""
    entry_id_1 = uuid4()
    entry_id_2 = uuid4()
    req_id = uuid4()
    root_req_id = uuid4()
    ts = datetime.now(UTC)

    # 1. Create first log
    log1 = AuditLog(
        id=entry_id_1,
        request_id=req_id,
        root_request_id=root_req_id,
        timestamp=ts,
        actor="user",
        action="login",
        outcome="success",
        integrity_hash="placeholder",
    )
    # Compute valid hash
    hash1 = compute_audit_hash(log1)
    # Update log with valid hash (using model_copy to be safe/immutable-ish)
    log1 = log1.model_copy(update={"integrity_hash": hash1})

    # 2. Create second log linked to first
    log2 = AuditLog(
        id=entry_id_2,
        request_id=req_id,
        root_request_id=root_req_id,
        timestamp=ts,
        actor="user",
        action="logout",
        outcome="success",
        previous_hash=hash1,
        integrity_hash="placeholder",
    )
    # Compute valid hash
    hash2 = compute_audit_hash(log2)
    # Update log with valid hash
    log2 = log2.model_copy(update={"integrity_hash": hash2})

    # 3. Verify chain
    assert verify_chain([log1, log2]) is True

    # 4. Verify tampering fails chain
    log1_tampered = log1.model_copy(update={"actor": "hacker"})
    # Re-computing hash for tampered log wouldn't match integrity_hash if we don't update it
    # But verify_chain checks: computed == log.integrity_hash
    # So if we tamper with data but NOT hash, it fails self-integrity
    # This covers the line: if computed != log.integrity_hash: return False
    assert verify_chain([log1_tampered, log2]) is False

    # 5. Verify broken link
    # If we update log1's hash to be valid for the tampered data...
    hash1_tampered = compute_audit_hash(log1_tampered)
    log1_tampered_valid_hash = log1_tampered.model_copy(update={"integrity_hash": hash1_tampered})
    # ... then self-integrity passes for log1
    # But log2.previous_hash will still be hash1 (original), which != hash1_tampered
    assert verify_chain([log1_tampered_valid_hash, log2]) is False


def test_verify_chain_empty() -> None:
    """Verify empty chain is valid."""
    assert verify_chain([]) is True
