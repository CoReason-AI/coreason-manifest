import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest

from coreason_manifest.spec.common.observability import AuditLog
from coreason_manifest.spec.v2.definitions import ManifestV2
from coreason_manifest.utils.audit import compute_audit_hash, compute_audit_hash_async, verify_chain_async
from coreason_manifest.utils.loader import load_agent_from_ref_async

# --- Loader Tests ---


@pytest.fixture
def temp_agent_file(tmp_path: Path) -> Path:
    d = tmp_path / "async_agents"
    d.mkdir()
    p = d / "my_async_agent.py"
    p.write_text("""
from coreason_manifest.builder import AgentBuilder

builder = AgentBuilder(name="AsyncAgent")
agent = builder.build()
""")
    return p


@pytest.mark.asyncio
async def test_load_agent_from_ref_async(temp_agent_file: Path) -> None:
    ref = f"{temp_agent_file}:agent"
    agent = await load_agent_from_ref_async(ref)
    assert isinstance(agent, ManifestV2)
    assert agent.metadata.name == "AsyncAgent"


@pytest.mark.asyncio
async def test_load_agent_from_ref_async_error() -> None:
    with pytest.raises(ValueError, match="File not found"):
        await load_agent_from_ref_async("non_existent_file.py:agent")


# --- Audit Tests ---


def create_audit_log(prev_hash: str | None = None) -> AuditLog:
    req_id = uuid.uuid4()
    entry = {
        "id": uuid.uuid4(),
        "request_id": req_id,
        "root_request_id": req_id,
        "timestamp": datetime.now(UTC),
        "actor": "system",
        "action": "test_action",
        "outcome": "success",
        "previous_hash": prev_hash,
    }
    # Compute hash synchronously to set it
    integrity_hash = compute_audit_hash(entry)
    entry["integrity_hash"] = integrity_hash
    return AuditLog(**entry)


@pytest.mark.asyncio
async def test_compute_audit_hash_async() -> None:
    req_id = uuid.uuid4()
    entry = {
        "id": uuid.uuid4(),
        "request_id": req_id,
        "root_request_id": req_id,
        "timestamp": datetime.now(UTC),
        "actor": "system",
        "action": "test_action",
        "outcome": "success",
    }

    # Sync computation
    sync_hash = compute_audit_hash(entry)

    # Async computation
    async_hash = await compute_audit_hash_async(entry)

    assert async_hash == sync_hash
    assert isinstance(async_hash, str)
    assert len(async_hash) == 64  # SHA-256 hex digest length


@pytest.mark.asyncio
async def test_verify_chain_async() -> None:
    chain = []
    prev_hash: str | None = None
    for _ in range(10):
        log = create_audit_log(prev_hash)
        chain.append(log)
        prev_hash = log.integrity_hash

    result = await verify_chain_async(chain)
    assert result is True


@pytest.mark.asyncio
async def test_verify_chain_async_tampered() -> None:
    chain = []
    prev_hash: str | None = None
    for _ in range(10):
        log = create_audit_log(prev_hash)
        chain.append(log)
        prev_hash = log.integrity_hash

    # Tamper with the chain
    # We can't easily modify AuditLog because it's frozen (pydantic frozen=True).
    # But we can replace an item in the list with a forged one.

    # Create a new log that doesn't match the previous hash of the next one
    # Or modify a log so its hash doesn't match its integrity_hash.

    # Let's tamper with the middle element's integrity hash (by replacing it with one that has wrong hash)
    # But AuditLog calculates hash from fields. If we change fields, hash changes.
    # We need to manually construct an AuditLog with a mismatching integrity_hash.

    # Since AuditLog validates nothing about the hash on creation (it's just a field),
    # we can create one with wrong hash.

    tampered_log_dict = chain[5].model_dump()
    tampered_log_dict["integrity_hash"] = "0" * 64  # Wrong hash

    tampered_log = AuditLog(**tampered_log_dict)
    chain[5] = tampered_log

    result = await verify_chain_async(chain)
    assert result is False


@pytest.mark.asyncio
async def test_verify_chain_async_broken_link() -> None:
    chain = []
    prev_hash: str | None = None
    for _ in range(10):
        log = create_audit_log(prev_hash)
        chain.append(log)
        prev_hash = log.integrity_hash

    # Break the link: chain[6].previous_hash != chain[5].integrity_hash

    # Create a new log for position 6 that points to wrong previous hash
    bad_link_log_dict = chain[6].model_dump()
    bad_link_log_dict["previous_hash"] = "1" * 64

    # We must also update its integrity_hash because previous_hash changed!
    # Otherwise it fails self-integrity check first.
    # To test chain link failure specifically, we need valid self-integrity but invalid link.

    new_integrity_hash = compute_audit_hash(bad_link_log_dict)  # Compute hash with the BAD previous_hash
    bad_link_log_dict["integrity_hash"] = new_integrity_hash

    bad_link_log = AuditLog(**bad_link_log_dict)
    chain[6] = bad_link_log

    result = await verify_chain_async(chain)
    assert result is False
