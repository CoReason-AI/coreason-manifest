import uuid
from datetime import datetime, timezone

from coreason_manifest.definitions.audit import AuditEventType, AuditLog


def test_audit_tamper_evidence() -> None:
    """Verify that changing data in an AuditLog instance invalidates its integrity_hash."""
    log_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    log = AuditLog(
        id=log_id,
        timestamp=now,
        actor="user_1",
        event_type=AuditEventType.PREDICTION,
        safety_metadata={"safe": True},
        previous_hash="0000",
        integrity_hash="placeholder",
    )

    # Compute correct hash
    correct_hash = log.compute_hash()

    # Update the log with the correct hash
    log.integrity_hash = correct_hash

    # Verify it matches
    assert log.compute_hash() == log.integrity_hash

    # Tamper with the data (e.g. change actor)
    log.actor = "malicious_actor"

    # Verify hash no longer matches
    assert log.compute_hash() != log.integrity_hash
