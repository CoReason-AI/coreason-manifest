from datetime import UTC, datetime

import pytest

from coreason_manifest.spec.core.exceptions import DomainValidationError, Severity
from coreason_manifest.spec.interop.antibody import DataAnomaly
from coreason_manifest.spec.interop.compliance import ComplianceReport, ErrorCatalog, RemediationAction
from coreason_manifest.spec.interop.telemetry import NodeExecution, NodeState

# --- TELEMETRY TESTS ---\n


def test_telemetry_parent_hash_auto_init() -> None:
    # Case: parent_hash provided, parent_hashes missing (None)
    raw_data = {
        "node_id": "test_node_init",
        "state": NodeState.COMPLETED,
        "inputs": {},
        "outputs": {},
        "timestamp": datetime.now(UTC),
        "duration_ms": 1.0,
        "parent_hash": "hash123",
        # parent_hashes is missing/None
    }

    node = NodeExecution(**raw_data)
    assert node.parent_hash == "hash123"
    assert node.parent_hashes == ["hash123"]


def test_telemetry_parent_hash_append() -> None:
    # Case: parent_hash provided, parent_hashes exists but does not contain parent_hash
    raw_data = {
        "node_id": "test_node_append",
        "state": NodeState.COMPLETED,
        "inputs": {},
        "outputs": {},
        "timestamp": datetime.now(UTC),
        "duration_ms": 1.0,
        "parent_hash": "hash_new",
        "parent_hashes": ["hash_old"],
    }

    node = NodeExecution(**raw_data)
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
        NodeExecution(
            node_id="n1",
            state=NodeState.COMPLETED,
            inputs={},
            outputs={},
            timestamp=datetime.now(UTC),
            duration_ms=1.0,
            parent_request_id="p1",
            root_request_id=None,  # Explicitly None to bypass auto-rooting if any
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

    node = NodeExecution(**raw_data)

    assert isinstance(node.inputs["bad_val"], DataAnomaly)
    assert node.inputs["bad_val"].code == "CRSN-ANTIBODY-FLOAT"
    assert node.outputs["good_val"] == 1.0


# --- EXCEPTIONS TESTS ---


def test_exception_severity_mapping() -> None:
    # Case: Warning severity
    report_warn = ComplianceReport(code=ErrorCatalog.ERR_CAP_MISSING_TOOL_001, severity="warning", message="warn msg")

    err = DomainValidationError("msg", report=report_warn)
    assert err.fault.severity == Severity.WARNING

    # Case: Info severity
    report_info = ComplianceReport(code=ErrorCatalog.ERR_CAP_MISSING_TOOL_001, severity="info", message="info msg")

    err_info = DomainValidationError("msg", report=report_info)
    # Assuming info maps to warning or handled similarly in current logic
    assert err_info.fault.severity == Severity.WARNING


def test_exception_remediation_payload() -> None:
    # Case: With remediation
    remediation = RemediationAction(
        type="update_field", description="Fix it", patch_data=[{"op": "replace", "path": "/foo", "value": "bar"}]
    )

    err = DomainValidationError("error msg", remediation=remediation)

    # Check context population
    assert err.fault.context["remediation"]["type"] == "update_field"

    # Check __str__ serialization
    str_repr = str(err)
    assert "Remediation: Fix it" in str_repr
    assert "Payload:" in str_repr
    assert "update_field" in str_repr


def test_exception_str_fallback() -> None:
    # Case: No remediation
    err = DomainValidationError("simple error")
    assert str(err) == "[CRSN-VAL-GENERIC] simple error"
