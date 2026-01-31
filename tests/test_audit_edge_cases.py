import uuid
from datetime import datetime, timezone

from coreason_manifest.definitions.audit import AuditEventType, AuditLog


def test_audit_hash_stability() -> None:
    """Test that dictionary key order does not affect the hash."""
    log_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    # Same data, different key order in safety_metadata
    log1 = AuditLog(
        id=log_id,
        timestamp=now,
        actor="system",
        event_type=AuditEventType.SYSTEM_CHANGE,
        safety_metadata={"a": 1, "b": 2},
        previous_hash="abc",
        integrity_hash="placeholder",
    )

    log2 = AuditLog(
        id=log_id,
        timestamp=now,
        actor="system",
        event_type=AuditEventType.SYSTEM_CHANGE,
        safety_metadata={"b": 2, "a": 1},
        previous_hash="abc",
        integrity_hash="placeholder",
    )

    assert log1.compute_hash() == log2.compute_hash()


def test_audit_complex_types_serialization() -> None:
    """Test that compute_hash handles complex types like UUID and datetime."""
    log = AuditLog(
        id=uuid.uuid4(),
        timestamp=datetime.now(timezone.utc),
        actor="system",
        event_type=AuditEventType.SYSTEM_CHANGE,
        safety_metadata={"related_id": uuid.uuid4(), "detected_at": datetime.now(timezone.utc)},
        previous_hash="abc",
        integrity_hash="placeholder",
    )

    # Should not raise TypeError
    hash_val = log.compute_hash()
    assert isinstance(hash_val, str)
    assert len(hash_val) == 64  # SHA256 hex digest length


def test_audit_integrity_sensitivity() -> None:
    """Test that modifying any field changes the hash."""
    log = AuditLog(
        id=uuid.uuid4(),
        timestamp=datetime.now(timezone.utc),
        actor="actor_1",
        event_type=AuditEventType.PREDICTION,
        safety_metadata={"safe": True},
        previous_hash="prev_hash",
        integrity_hash="placeholder",
    )

    original_hash = log.compute_hash()

    # Modify actor
    log.actor = "actor_2"
    assert log.compute_hash() != original_hash
    log.actor = "actor_1"  # restore
    assert log.compute_hash() == original_hash

    # Modify metadata
    log.safety_metadata["safe"] = False
    assert log.compute_hash() != original_hash
    log.safety_metadata["safe"] = True  # restore

    # Modify event type
    log.event_type = AuditEventType.GUARDRAIL_TRIGGER
    assert log.compute_hash() != original_hash
