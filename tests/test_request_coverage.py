from uuid import uuid4

import pytest

from coreason_manifest.spec.interop.exceptions import LineageIntegrityError
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


def test_create_child() -> None:
    req = AgentRequest(
        agent_id="agent1",
        session_id="session1",
        inputs={},
    )
    child = req.create_child(metadata={"foo": "bar"})
    assert child.parent_request_id == req.request_id
    assert child.root_request_id == req.root_request_id
    assert child.metadata["foo"] == "bar"
    assert child.request_id != req.request_id


def test_auto_root_generation_missing_id() -> None:
    req = AgentRequest(
        agent_id="agent1",
        session_id="session1",
        inputs={},
        # request_id missing
    )
    assert req.request_id is not None
    assert req.root_request_id == req.request_id
    assert req.parent_request_id is None


def test_trace_integrity_rule1_orphaned() -> None:
    """
    Test Rule 1: Parent exists but Root is missing.
    """
    parent_id = str(uuid4())

    # We must suppress the default factory for root_request_id if it existed (it defaults to None)
    # But enforce_lineage_rooting might interfere?
    # enforce_lineage_rooting only sets root if parent is also missing.
    # Here parent is present, so enforce_lineage_rooting does nothing.

    with pytest.raises(ExceptionGroup) as excinfo:
        AgentRequest(
            agent_id="agent1",
            session_id="session1",
            inputs={},
            parent_request_id=parent_id,
            # root_request_id is None by default
        )

    errors = excinfo.value.exceptions
    assert any("Orphaned request" in str(e) for e in errors)
    assert any(isinstance(e, LineageIntegrityError) for e in errors)
