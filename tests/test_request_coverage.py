from uuid import uuid4

import pytest

from coreason_manifest.spec.interop.request import AgentRequest


# --- test_request_coverage.py content ---


def test_trace_integrity_rule2_root_consistency() -> None:
    """
    Test Rule 2: Root Consistency (If root == self, parent must be None)
    """
    req_id = str(uuid4())
    parent_id = str(uuid4())

    with pytest.raises(ExceptionGroup) as excinfo:
        AgentRequest(
            agent_id="agent1",
            session_id="session1",
            inputs={},
            request_id=req_id,
            parent_request_id=parent_id,
            root_request_id=req_id,
        )

    assert any("Root request cannot imply a parent" in str(e) for e in excinfo.value.exceptions)


def test_trace_integrity_rule3_self_parenting() -> None:
    """
    Test Rule 3: Self-Parenting Cycle
    """
    req_id = str(uuid4())
    # parent = self
    # root must be set to something else to avoid Rule 2 trigger (or rule 1 if missing)
    # If root is missing, it's rule 1.
    # If root == self, it's rule 2.
    # So root must be some other ID.
    root_id = str(uuid4())

    with pytest.raises(ExceptionGroup) as excinfo:
        AgentRequest(
            agent_id="agent1",
            session_id="session1",
            inputs={},
            request_id=req_id,
            parent_request_id=req_id,
            root_request_id=root_id,
        )

    assert any("Self-referential parent_request_id detected" in str(e) for e in excinfo.value.exceptions)


def test_trace_integrity_multiple_violations() -> None:
    """
    Test multiple violations aggregating in ExceptionGroup.
    """
    req_id = str(uuid4())

    # Rule 2 (Root=Self but Parent set) AND Rule 3 (Parent=Self)
    # parent = self, root = self
    with pytest.raises(ExceptionGroup) as excinfo:
        AgentRequest(
            agent_id="agent1",
            session_id="session1",
            inputs={},
            request_id=req_id,
            parent_request_id=req_id,
            root_request_id=req_id,
        )

    errors = excinfo.value.exceptions
    assert len(errors) >= 2
    assert any("Root request cannot imply a parent" in str(e) for e in errors)
    assert any("Self-referential parent_request_id detected" in str(e) for e in errors)
