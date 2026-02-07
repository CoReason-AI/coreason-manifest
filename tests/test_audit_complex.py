# tests/test_audit_complex.py

import random
import uuid
from datetime import UTC, datetime, timedelta, timezone

from coreason_manifest.spec.common.observability import AuditLog
from coreason_manifest.utils.audit import compute_audit_hash, verify_chain


def test_edge_null_vs_missing() -> None:
    """Verify that an explicit None value hashes identically to a missing field."""
    uid = uuid.uuid4()
    req_id = uuid.uuid4()
    root_id = uuid.uuid4()
    now = datetime.now(UTC)

    # Dict with 'safety_metadata' missing
    data_missing = {
        "id": uid,
        "request_id": req_id,
        "root_request_id": root_id,
        "timestamp": now,
        "actor": "user-1",
        "action": "login",
        "outcome": "success",
        "previous_hash": None,
        # safety_metadata missing
    }

    # Dict with 'safety_metadata' explicitly None
    data_none = {
        "id": uid,
        "request_id": req_id,
        "root_request_id": root_id,
        "timestamp": now,
        "actor": "user-1",
        "action": "login",
        "outcome": "success",
        "previous_hash": None,
        "safety_metadata": None,
    }

    hash1 = compute_audit_hash(data_missing)
    hash2 = compute_audit_hash(data_none)

    assert hash1 == hash2


def test_edge_timezone_conversion() -> None:
    """Verify that equivalent instants in different timezones hash identically."""
    uid = uuid.uuid4()
    req_id = uuid.uuid4()
    root_id = uuid.uuid4()

    # Create a time in UTC
    dt_utc = datetime(2023, 10, 27, 12, 0, 0, tzinfo=UTC)

    # Create the same instant in EST (UTC-5)
    # 12:00 UTC = 07:00 EST
    est = timezone(timedelta(hours=-5))
    dt_est = datetime(2023, 10, 27, 7, 0, 0, tzinfo=est)

    assert dt_utc == dt_est  # Python equality check

    data_utc = {
        "id": uid,
        "request_id": req_id,
        "root_request_id": root_id,
        "timestamp": dt_utc,
        "actor": "system",
        "action": "check",
        "outcome": "ok",
        "previous_hash": None,
    }

    data_est = {
        "id": uid,
        "request_id": req_id,
        "root_request_id": root_id,
        "timestamp": dt_est,
        "actor": "system",
        "action": "check",
        "outcome": "ok",
        "previous_hash": None,
    }

    hash1 = compute_audit_hash(data_utc)
    hash2 = compute_audit_hash(data_est)

    assert hash1 == hash2


def test_complex_mixed_metadata() -> None:
    """Verify determinism with deep, mixed-type safety_metadata."""
    uid = uuid.uuid4()
    req_id = uuid.uuid4()
    root_id = uuid.uuid4()
    now = datetime.now(UTC)

    complex_metadata = {
        "metrics": {
            "latency": 0.123,
            "tokens": 42,
            "flags": [True, False, True],
        },
        "annotations": {
            "reviewer": None,  # Should be ignored
            "tags": ["alpha", "beta", "gamma"],  # List order matters in JSON
            "nested": {"deep": {"val": 100}},
        },
        "user_id": 12345,
    }

    data1 = {
        "id": uid,
        "request_id": req_id,
        "root_request_id": root_id,
        "timestamp": now,
        "actor": "system",
        "action": "complex_op",
        "outcome": "success",
        "previous_hash": None,
        "safety_metadata": complex_metadata,
    }

    hash1 = compute_audit_hash(data1)

    # Create a logically identical structure but constructed differently
    complex_metadata2 = {
        "user_id": 12345,
        "annotations": {"nested": {"deep": {"val": 100}}, "tags": ["alpha", "beta", "gamma"], "reviewer": None},
        "metrics": {"flags": [True, False, True], "tokens": 42, "latency": 0.123},
    }

    data2 = data1.copy()
    data2["safety_metadata"] = complex_metadata2

    hash2 = compute_audit_hash(data2)

    assert hash1 == hash2


def test_complex_large_chain_random_tamper() -> None:
    """
    Generate a large chain (50 items).
    Randomly tamper with 3 distinct items.
    Verify chain is invalid.
    """
    chain: list[AuditLog] = []
    root_id = uuid.uuid4()
    prev_hash = None

    # 1. Build valid chain
    for i in range(50):
        entry_data = {
            "id": uuid.uuid4(),
            "request_id": uuid.uuid4(),
            "root_request_id": root_id,
            "timestamp": datetime.now(UTC),
            "actor": f"user-{i}",
            "action": f"step-{i}",
            "outcome": "success",
            "previous_hash": prev_hash,
            "hash_algorithm": "v2",
        }
        integrity = compute_audit_hash(entry_data)
        log = AuditLog(**entry_data, integrity_hash=integrity)
        chain.append(log)
        prev_hash = integrity

    assert verify_chain(chain) is True

    # 2. Tamper
    # We will modify the 'action' of 3 distinct logs
    indices = random.sample(range(50), 3)

    for idx in indices:
        original = chain[idx]
        # Just creating a new object with different data but same hash
        # This simulates a "content tamper" where the attacker tries to hide the change
        # but cannot forge the signature (integrity_hash)
        tampered = AuditLog(
            id=original.id,
            request_id=original.request_id,
            root_request_id=original.root_request_id,
            timestamp=original.timestamp,
            actor=original.actor,
            action="TAMPERED",  # changed
            outcome=original.outcome,
            previous_hash=original.previous_hash,
            integrity_hash=original.integrity_hash,  # old hash
        )
        chain[idx] = tampered

    assert verify_chain(chain) is False


def test_edge_empty_chain() -> None:
    """Verify behavior with empty chain."""
    assert verify_chain([]) is True


def test_edge_single_item_chain() -> None:
    """Verify behavior with single item chain."""
    entry_data = {
        "id": uuid.uuid4(),
        "request_id": uuid.uuid4(),
        "root_request_id": uuid.uuid4(),
        "timestamp": datetime.now(UTC),
        "actor": "system",
        "action": "solo",
        "outcome": "success",
        "previous_hash": None,
        "hash_algorithm": "v2",
    }
    integrity = compute_audit_hash(entry_data)
    log = AuditLog(**entry_data, integrity_hash=integrity)

    assert verify_chain([log]) is True

    # Tamper single item
    tampered = AuditLog(
        **{**entry_data, "action": "BAD"},
        integrity_hash=integrity,
    )
    assert verify_chain([tampered]) is False
