import uuid
from datetime import datetime

import pytest
from pydantic import ValidationError

from coreason_manifest.definitions.audit import AuditLog, AuditEventType, ReasoningTrace

def test_trace_auto_rooting():
    """Test Case 1: Trace Auto-Rooting"""
    req_id = uuid.uuid4()
    trace = ReasoningTrace(
        trace_id="trace-123",
        agent_id="agent-007",
        request_id=req_id,
        start_time=datetime.now()
    )

    assert trace.request_id == req_id
    assert trace.root_request_id == req_id
    assert trace.parent_request_id is None

def test_broken_lineage():
    """Test Case 2: Broken Lineage (Validation Error)"""
    req_id = uuid.uuid4()
    parent_id = uuid.uuid4()

    # Attempt to instantiate with parent but no root (and explicitly passing None or implicit default)
    # The validator logic is: if root is None: check parent. If parent is NOT None, raise ValueError.

    with pytest.raises(ValidationError) as exc_info:
        ReasoningTrace(
            trace_id="trace-123",
            agent_id="agent-007",
            request_id=req_id,
            parent_request_id=parent_id,
            # root_request_id defaults to None
            start_time=datetime.now()
        )

    assert "Root ID missing while Parent ID is present" in str(exc_info.value)

    # Also verify if we explicitly set root_request_id=None
    with pytest.raises(ValidationError) as exc_info:
        ReasoningTrace(
            trace_id="trace-123",
            agent_id="agent-007",
            request_id=req_id,
            parent_request_id=parent_id,
            root_request_id=None,
            start_time=datetime.now()
        )
    assert "Root ID missing while Parent ID is present" in str(exc_info.value)


def test_audit_log_compliance():
    """Test Case 3: Audit Log Compliance"""
    req_id = uuid.uuid4()
    root_id = uuid.uuid4()
    audit_id = uuid.uuid4()

    log = AuditLog(
        audit_id=audit_id,
        trace_id="trace-123",
        request_id=req_id,
        root_request_id=root_id,
        timestamp=datetime.now(),
        actor="user-1",
        event_type=AuditEventType.SYSTEM_CHANGE,
        safety_metadata={"safe": True},
        previous_hash="hash-000",
        integrity_hash="temp-hash" # Required field, though usually computed later
    )

    # compute_hash excludes integrity_hash, so it should work
    computed = log.compute_hash()
    assert isinstance(computed, str)
    assert len(computed) > 0

    # Verify that changing request_id changes the hash
    log2 = log.model_copy(update={"request_id": uuid.uuid4()})
    assert log.compute_hash() != log2.compute_hash()


def test_hierarchy_logic():
    """Test Case 4: Hierarchy Logic"""
    root_id = uuid.uuid4()
    parent_id = uuid.uuid4()
    child_req_id = uuid.uuid4()

    trace = ReasoningTrace(
        trace_id="trace-child",
        agent_id="agent-child",
        request_id=child_req_id,
        root_request_id=root_id,
        parent_request_id=parent_id,
        start_time=datetime.now()
    )

    assert trace.request_id == child_req_id
    assert trace.root_request_id == root_id
    assert trace.parent_request_id == parent_id
