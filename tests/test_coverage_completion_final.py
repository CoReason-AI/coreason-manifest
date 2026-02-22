from datetime import UTC, datetime
from typing import Any

import pytest

from coreason_manifest.spec.interop.exceptions import (
    FaultSeverity,
    LineageIntegrityError,
    ManifestError,
    RecoveryAction,
    SemanticFault,
)
from coreason_manifest.spec.interop.telemetry import NodeExecution, NodeState

# --- TELEMETRY TESTS ---


def test_telemetry_parent_hash_auto_init() -> None:
    # Case: parent_hash provided, parent_hashes missing (None)
    raw_data: dict[str, Any] = {
        "node_id": "test_node_init",
        "state": NodeState.COMPLETED,
        "inputs": {},
        "outputs": {},
        "timestamp": datetime.now(UTC),
        "duration_ms": 1.0,
        "parent_hash": "hash123",
        # parent_hashes is missing/None
    }

    node = NodeExecution.model_validate(raw_data)
    assert node.parent_hash == "hash123"
    assert node.parent_hashes == ["hash123"]


def test_telemetry_parent_hash_append() -> None:
    # Case: parent_hash provided, parent_hashes exists but does not contain parent_hash
    raw_data: dict[str, Any] = {
        "node_id": "test_node_append",
        "state": NodeState.COMPLETED,
        "inputs": {},
        "outputs": {},
        "timestamp": datetime.now(UTC),
        "duration_ms": 1.0,
        "parent_hash": "hash_new",
        "parent_hashes": ["hash_old"],
    }

    node = NodeExecution.model_validate(raw_data)
    assert node.parent_hash == "hash_new"
    assert "hash_old" in node.parent_hashes
    assert "hash_new" in node.parent_hashes


def test_telemetry_orphaned_trace() -> None:
    # Case: parent provided but root is missing (orphaned trace)
    # We must explicitly prevent auto-rooting (enforce_lineage_rooting) from fixing it,
    # but enforce_lineage_rooting only fixes if (not parent AND not root).
    # Here we have parent, so it won't auto-root. It will leave root as None.
    # Then validate_trace_integrity runs and sees parent but no root -> ERROR.

    with pytest.raises(ValueError, match="Orphaned trace detected"):
        NodeExecution.model_validate(
            {
                "node_id": "n1",
                "state": NodeState.COMPLETED,
                "inputs": {},
                "outputs": {},
                "timestamp": datetime.now(UTC),
                "duration_ms": 1.0,
                "parent_request_id": "p1",
                "root_request_id": None,  # Explicitly None to bypass auto-rooting if any
            }
        )


def test_node_execution_antibody_integration() -> None:
    # Case: Inputs contain NaN -> Should be quarantined into DataAnomaly
    raw_data = {
        "node_id": "test_node_antibody",
        "state": NodeState.COMPLETED,
        "inputs": {"bad_val": float("nan")},
        "outputs": {"good_val": 1.0},
        "timestamp": datetime.now(UTC),
        "duration_ms": 1.0,
    }

    node = NodeExecution.model_validate(raw_data)

    # Check that the input was converted to a dict (via .model_dump())
    assert isinstance(node.inputs["bad_val"], dict)
    assert node.inputs["bad_val"]["code"] == "CRSN-ANTIBODY-FLOAT"
    assert node.outputs["good_val"] == 1.0


# --- EXCEPTIONS TESTS ---


def test_exception_structure() -> None:
    # Verify semantic fault fields
    fault = SemanticFault(
        error_code="TEST-ERR-001",
        message="Test Message",
        severity=FaultSeverity.WARNING,
        recovery_action=RecoveryAction.RETRY,
        context={"foo": "bar"},
    )
    assert fault.severity == FaultSeverity.WARNING
    assert fault.context["foo"] == "bar"


def test_manifest_error_wrapping() -> None:
    # Verify exception wrapping
    fault = SemanticFault(
        error_code="TEST-ERR-002",
        message="Wrapped Error",
        severity=FaultSeverity.CRITICAL,
        recovery_action=RecoveryAction.HALT,
    )
    err = ManifestError(fault)
    assert "Wrapped Error" in str(err)
    assert err.fault.error_code == "TEST-ERR-002"


def test_lineage_error_defaults() -> None:
    # Verify specialized error defaults
    err = LineageIntegrityError("Broken chain")
    assert err.fault.error_code == "CRSN-SEC-LINEAGE-001"
    assert err.fault.severity == FaultSeverity.CRITICAL
    assert err.fault.recovery_action == RecoveryAction.HALT
