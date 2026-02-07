
import pytest
from datetime import datetime, timezone
from uuid import uuid4
from coreason_manifest.spec.common.observability import AuditLog
from coreason_manifest.utils.audit import compute_audit_hash

def test_audit_v1_legacy_behavior():
    """Verify V1 ignores extra fields in dict."""
    entry_id = uuid4()
    req_id = uuid4()
    root_req_id = uuid4()
    ts = datetime.now(timezone.utc)

    base_data = {
        "id": entry_id,
        "request_id": req_id,
        "root_request_id": root_req_id,
        "timestamp": ts,
        "actor": "user",
        "action": "login",
        "outcome": "success",
        "hash_algorithm": 1,
        "extra_field": "secret"
    }

    hash1 = compute_audit_hash(base_data)

    tampered_data = base_data.copy()
    tampered_data["extra_field"] = "changed"
    hash2 = compute_audit_hash(tampered_data)

    assert hash1 == hash2

def test_audit_v2_dict_behavior():
    """Verify V2 includes extra fields in dict."""
    entry_id = uuid4()
    req_id = uuid4()
    root_req_id = uuid4()
    ts = datetime.now(timezone.utc)

    base_data = {
        "id": entry_id,
        "request_id": req_id,
        "root_request_id": root_req_id,
        "timestamp": ts,
        "actor": "user",
        "action": "login",
        "outcome": "success",
        "hash_algorithm": 2,
        "extra_field": "secret"
    }

    hash1 = compute_audit_hash(base_data)

    tampered_data = base_data.copy()
    tampered_data["extra_field"] = "changed"
    hash2 = compute_audit_hash(tampered_data)

    assert hash1 != hash2

def test_audit_v2_model_behavior():
    """Verify V2 includes extra fields in Pydantic model subclass."""
    class ExtendedAuditLog(AuditLog):
        user_ip: str

    entry_id = uuid4()
    req_id = uuid4()
    root_req_id = uuid4()
    ts = datetime.now(timezone.utc)

    log1 = ExtendedAuditLog(
        id=entry_id,
        request_id=req_id,
        root_request_id=root_req_id,
        timestamp=ts,
        actor="user",
        action="login",
        outcome="success",
        hash_algorithm=2,
        integrity_hash="placeholder",
        user_ip="1.1.1.1"
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
        hash_algorithm=2,
        integrity_hash="placeholder",
        user_ip="2.2.2.2"
    )

    hash2 = compute_audit_hash(log2)

    assert hash1 != hash2

def test_audit_invalid_algorithm():
    """Verify invalid algorithm raises ValueError."""
    entry_id = uuid4()
    req_id = uuid4()
    root_req_id = uuid4()
    ts = datetime.now(timezone.utc)

    data = {
        "id": entry_id,
        "request_id": req_id,
        "root_request_id": root_req_id,
        "timestamp": ts,
        "actor": "user",
        "action": "login",
        "outcome": "success",
        "hash_algorithm": 99
    }

    with pytest.raises(ValueError, match="Unsupported hash_algorithm: 99"):
        compute_audit_hash(data)

def test_audit_v1_ignores_hash_algorithm_field_value():
    """Verify V1 hash is same regardless of hash_algorithm field presence/value in dict if it defaults to 1."""

    entry_id = uuid4()
    req_id = uuid4()
    root_req_id = uuid4()
    ts = datetime.now(timezone.utc)

    data1 = {
        "id": entry_id,
        "request_id": req_id,
        "root_request_id": root_req_id,
        "timestamp": ts,
        "actor": "user",
        "action": "login",
        "outcome": "success",
        # Missing hash_algorithm -> defaults to 1
    }

    hash1 = compute_audit_hash(data1)

    data2 = data1.copy()
    data2["hash_algorithm"] = 1

    hash2 = compute_audit_hash(data2)

    assert hash1 == hash2
