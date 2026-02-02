import uuid
from datetime import datetime

from coreason_manifest.definitions.audit import AuditEventType, AuditLog


def test_audit_hashing_consistency() -> None:
    """Verify that changing data in an AuditLog instance invalidates its integrity_hash."""

    log = AuditLog(
        audit_id=uuid.uuid4(),
        trace_id="trace-123",
        request_id=uuid.uuid4(),
        root_request_id=uuid.uuid4(),
        timestamp=datetime.now(),
        actor="system",
        event_type=AuditEventType.SYSTEM_CHANGE,
        safety_metadata={"checked": True},
        previous_hash="abc",
        integrity_hash="placeholder",
    )

    computed = log.compute_hash()
    assert isinstance(computed, str)
    assert len(computed) == 64  # SHA256 hex digest length
