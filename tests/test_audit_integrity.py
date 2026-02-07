from datetime import UTC, datetime
from uuid import uuid4

from coreason_manifest.spec.common.observability import AuditLog
from coreason_manifest.utils.audit import compute_audit_hash


def test_audit_dict_behavior() -> None:
    """Verify compute_audit_hash includes extra fields in dict (security behavior)."""
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
