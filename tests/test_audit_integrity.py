# tests/test_audit_integrity.py

import uuid
from datetime import UTC, datetime, timedelta

from coreason_manifest.spec.common.observability import AuditLog
from coreason_manifest.utils.audit import compute_audit_hash, verify_chain


def test_deterministic_hashing() -> None:
    """Verify that hashing is deterministic regardless of key order in dict."""
    uid = uuid.uuid4()
    req_id = uuid.uuid4()
    root_id = uuid.uuid4()
    now = datetime.now(UTC)

    data1 = {
        "id": uid,
        "request_id": req_id,
        "root_request_id": root_id,
        "timestamp": now,
        "actor": "user-1",
        "action": "login",
        "outcome": "success",
        "previous_hash": None,
        "safety_metadata": {"score": 0.9},
    }

    data2 = {
        "outcome": "success",
        "action": "login",
        "actor": "user-1",
        "timestamp": now,
        "root_request_id": root_id,
        "request_id": req_id,
        "id": uid,
        "safety_metadata": {"score": 0.9},
        "previous_hash": None,
    }

    hash1 = compute_audit_hash(data1)
    hash2 = compute_audit_hash(data2)

    assert hash1 == hash2


def test_tamper_detection() -> None:
    """Verify that changing any field changes the hash."""
    uid = uuid.uuid4()
    req_id = uuid.uuid4()
    root_id = uuid.uuid4()
    now = datetime.now(UTC)

    base_data = {
        "id": uid,
        "request_id": req_id,
        "root_request_id": root_id,
        "timestamp": now,
        "actor": "user-1",
        "action": "login",
        "outcome": "success",
        "previous_hash": None,
    }

    original_hash = compute_audit_hash(base_data)

    # Modify outcome
    tampered_data = base_data.copy()
    tampered_data["outcome"] = "failed"
    assert compute_audit_hash(tampered_data) != original_hash

    # Modify timestamp
    tampered_data = base_data.copy()
    tampered_data["timestamp"] = now + timedelta(seconds=1)
    assert compute_audit_hash(tampered_data) != original_hash


def test_integrity_hash_exclusion() -> None:
    """Verify that integrity_hash field is excluded from calculation."""
    uid = uuid.uuid4()
    req_id = uuid.uuid4()
    root_id = uuid.uuid4()
    now = datetime.now(UTC)

    data = {
        "id": uid,
        "request_id": req_id,
        "root_request_id": root_id,
        "timestamp": now,
        "actor": "user-1",
        "action": "login",
        "outcome": "success",
        "previous_hash": None,
    }

    hash1 = compute_audit_hash(data)

    # Add integrity_hash to input dict (simulating a record that already has it)
    data_with_hash = data.copy()
    data_with_hash["integrity_hash"] = "fake_hash"

    hash2 = compute_audit_hash(data_with_hash)

    assert hash1 == hash2


def test_verify_chain_valid() -> None:
    """Verify a valid chain of logs."""
    chain: list[AuditLog] = []

    root_id = uuid.uuid4()
    prev_hash = None

    for i in range(3):
        entry_data = {
            "id": uuid.uuid4(),
            "request_id": uuid.uuid4(),
            "root_request_id": root_id,
            "timestamp": datetime.now(UTC),
            "actor": "system",
            "action": f"step-{i}",
            "outcome": "success",
            "previous_hash": prev_hash,
        }

        # Compute hash
        integrity = compute_audit_hash(entry_data)

        # Create object
        log = AuditLog(**entry_data, integrity_hash=integrity)
        chain.append(log)
        prev_hash = integrity

    assert verify_chain(chain) is True


def test_verify_chain_broken_content() -> None:
    """Verify that tampering with content breaks the chain verification."""
    chain: list[AuditLog] = []
    root_id = uuid.uuid4()
    prev_hash = None

    for i in range(3):
        entry_data = {
            "id": uuid.uuid4(),
            "request_id": uuid.uuid4(),
            "root_request_id": root_id,
            "timestamp": datetime.now(UTC),
            "actor": "system",
            "action": f"step-{i}",
            "outcome": "success",
            "previous_hash": prev_hash,
        }
        integrity = compute_audit_hash(entry_data)
        log = AuditLog(**entry_data, integrity_hash=integrity)
        chain.append(log)
        prev_hash = integrity

    # Tamper with the second log (index 1)
    original_log = chain[1]
    # Create a log with same hash but different content
    tampered_log = AuditLog(
        id=original_log.id,
        request_id=original_log.request_id,
        root_request_id=original_log.root_request_id,
        timestamp=original_log.timestamp,
        actor=original_log.actor,
        action="tampered_action",  # Changed
        outcome=original_log.outcome,
        previous_hash=original_log.previous_hash,
        integrity_hash=original_log.integrity_hash,  # Kept old hash
    )
    chain[1] = tampered_log

    assert verify_chain(chain) is False


def test_verify_chain_broken_link() -> None:
    """Verify that breaking the hash link breaks the chain verification."""
    chain: list[AuditLog] = []
    root_id = uuid.uuid4()
    prev_hash = None

    for i in range(3):
        entry_data = {
            "id": uuid.uuid4(),
            "request_id": uuid.uuid4(),
            "root_request_id": root_id,
            "timestamp": datetime.now(UTC),
            "actor": "system",
            "action": f"step-{i}",
            "outcome": "success",
            "previous_hash": prev_hash,
        }
        integrity = compute_audit_hash(entry_data)
        log = AuditLog(**entry_data, integrity_hash=integrity)
        chain.append(log)
        prev_hash = integrity

    # Break the link between 1 and 2
    # Modify log 2's previous_hash
    original_log = chain[2]
    broken_link_log = AuditLog(
        id=original_log.id,
        request_id=original_log.request_id,
        root_request_id=original_log.root_request_id,
        timestamp=original_log.timestamp,
        actor=original_log.actor,
        action=original_log.action,
        outcome=original_log.outcome,
        previous_hash="wrong_hash",  # Broken link
        integrity_hash=compute_audit_hash(
            {
                "id": original_log.id,
                "request_id": original_log.request_id,
                "root_request_id": original_log.root_request_id,
                "timestamp": original_log.timestamp,
                "actor": original_log.actor,
                "action": original_log.action,
                "outcome": original_log.outcome,
                "previous_hash": "wrong_hash",
            }
        ),
    )

    chain[2] = broken_link_log

    assert verify_chain(chain) is False


def test_safety_metadata_inclusion() -> None:
    """Verify that safety_metadata is included in hash calculation."""
    uid = uuid.uuid4()
    req_id = uuid.uuid4()
    root_id = uuid.uuid4()
    now = datetime.now(UTC)

    data = {
        "id": uid,
        "request_id": req_id,
        "root_request_id": root_id,
        "timestamp": now,
        "actor": "user-1",
        "action": "login",
        "outcome": "success",
        "previous_hash": None,
    }

    hash_without = compute_audit_hash(data)

    data_with = data.copy()
    data_with["safety_metadata"] = {"flag": True}

    hash_with = compute_audit_hash(data_with)

    assert hash_without != hash_with


def test_unicode_consistency() -> None:
    """Verify that hashing works consistently with Unicode characters."""
    uid = uuid.uuid4()
    req_id = uuid.uuid4()
    root_id = uuid.uuid4()
    now = datetime.now(UTC)

    # Test with emojis and non-ASCII script
    data = {
        "id": uid,
        "request_id": req_id,
        "root_request_id": root_id,
        "timestamp": now,
        "actor": "user-🚀",
        "action": "acción_crítica",
        "outcome": "成功",  # Success in Chinese
        "previous_hash": None,
        "safety_metadata": None,
    }

    hash1 = compute_audit_hash(data)
    hash2 = compute_audit_hash(data)

    assert hash1 == hash2
    assert isinstance(hash1, str)
    assert len(hash1) == 64


def test_nested_safety_metadata() -> None:
    """Verify determinism with nested dictionaries in safety_metadata."""
    uid = uuid.uuid4()
    req_id = uuid.uuid4()
    root_id = uuid.uuid4()
    now = datetime.now(UTC)

    metadata = {"policy": {"name": "PII", "checks": ["email", "phone"]}, "score": 0.05}

    data = {
        "id": uid,
        "request_id": req_id,
        "root_request_id": root_id,
        "timestamp": now,
        "actor": "system",
        "action": "scan",
        "outcome": "success",
        "previous_hash": None,
        "safety_metadata": metadata,
    }

    hash1 = compute_audit_hash(data)

    # Create copy with different key order in nested dict
    metadata2 = {"score": 0.05, "policy": {"checks": ["email", "phone"], "name": "PII"}}

    data2 = data.copy()
    data2["safety_metadata"] = metadata2

    hash2 = compute_audit_hash(data2)

    assert hash1 == hash2


def test_long_chain_verification() -> None:
    """Verify a longer chain of logs."""
    chain: list[AuditLog] = []
    root_id = uuid.uuid4()
    prev_hash = None

    # Chain of 15 items
    for i in range(15):
        entry_data = {
            "id": uuid.uuid4(),
            "request_id": uuid.uuid4(),
            "root_request_id": root_id,
            "timestamp": datetime.now(UTC),
            "actor": "system",
            "action": f"step-{i}",
            "outcome": "success",
            "previous_hash": prev_hash,
        }
        integrity = compute_audit_hash(entry_data)
        log = AuditLog(**entry_data, integrity_hash=integrity)
        chain.append(log)
        prev_hash = integrity

    assert verify_chain(chain) is True


def test_chain_domino_effect() -> None:
    """
    Verify that if a middle node is tampered (and re-hashed),
    the chain verification fails at the NEXT node because of link mismatch.
    """
    chain: list[AuditLog] = []
    root_id = uuid.uuid4()
    prev_hash = None

    for i in range(5):
        entry_data = {
            "id": uuid.uuid4(),
            "request_id": uuid.uuid4(),
            "root_request_id": root_id,
            "timestamp": datetime.now(UTC),
            "actor": "system",
            "action": f"step-{i}",
            "outcome": "success",
            "previous_hash": prev_hash,
        }
        integrity = compute_audit_hash(entry_data)
        log = AuditLog(**entry_data, integrity_hash=integrity)
        chain.append(log)
        prev_hash = integrity

    # Tamper with index 2 (the 3rd item)
    # We change the content AND recompute the hash so the node itself is valid.
    target_idx = 2
    original_log = chain[target_idx]

    tampered_data = {
        "id": original_log.id,
        "request_id": original_log.request_id,
        "root_request_id": original_log.root_request_id,
        "timestamp": original_log.timestamp,
        "actor": original_log.actor,
        "action": "MALICIOUS_ACTION",  # Changed
        "outcome": original_log.outcome,
        "previous_hash": original_log.previous_hash,  # Valid link to previous
        "safety_metadata": None,
    }

    new_integrity = compute_audit_hash(tampered_data)
    tampered_log = AuditLog(**tampered_data, integrity_hash=new_integrity)

    chain[target_idx] = tampered_log

    # Now:
    # chain[0]: Valid
    # chain[1]: Valid
    # chain[2]: Valid (self-integrity check passes)
    # chain[3]: INVALID (chain[3].previous_hash != chain[2].integrity_hash)

    assert verify_chain(chain) is False

    # Verify manually that the break is where we expect
    assert compute_audit_hash(chain[target_idx]) == chain[target_idx].integrity_hash
    assert chain[target_idx + 1].previous_hash != chain[target_idx].integrity_hash
