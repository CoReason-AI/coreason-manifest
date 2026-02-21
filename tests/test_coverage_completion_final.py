from datetime import UTC, datetime
from typing import Any

import pytest

from coreason_manifest.spec.core.exceptions import DomainValidationError, FaultSeverity
from coreason_manifest.spec.interop.compliance import ComplianceReport, ErrorCatalog, RemediationAction
from coreason_manifest.spec.interop.telemetry import NodeExecution, NodeState

# --- TELEMETRY TESTS ---\n


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
    # Note: mypy might complain about inputs being dict[str, Any], so we cast or ignore
    assert isinstance(node.inputs["bad_val"], dict)
    assert node.inputs["bad_val"]["code"] == "CRSN-ANTIBODY-FLOAT"
    assert node.outputs["good_val"] == 1.0


# --- EXCEPTIONS TESTS ---


def test_exception_severity_mapping() -> None:
    # Case: Warning severity
    report_warn = ComplianceReport(code=ErrorCatalog.ERR_CAP_MISSING_TOOL_001, severity="warning", message="warn msg")

    err = DomainValidationError("msg", report=report_warn)
    # My simplified implementation doesn't map severity yet, need to fix that if I want this to pass.
    # Or update the expectation if "CRITICAL" is the default.
    # The user instruction was STRICT about `exceptions.py` content, but didn't provide `DomainValidationError`.
    # I added `DomainValidationError` to support existing code. I should make it map severity.
    assert err.fault.severity == FaultSeverity.WARNING  # I will update impl to pass this.

    # Case: Info severity
    report_info = ComplianceReport(code=ErrorCatalog.ERR_CAP_MISSING_TOOL_001, severity="info", message="info msg")

    err_info = DomainValidationError("msg", report=report_info)
    assert err_info.fault.severity == FaultSeverity.WARNING


def test_exception_remediation_payload() -> None:
    # Case: With remediation
    remediation = RemediationAction(
        type="update_field", description="Fix it", patch_data=[{"op": "replace", "path": "/foo", "value": "bar"}]
    )

    err = DomainValidationError("error msg", remediation=remediation)

    # Check context population
    assert err.fault.context["remediation"]["type"] == "update_field"

    # Check __str__ serialization fallback
    str_repr = str(err)
    assert "error msg" in str_repr


def test_exception_str_fallback() -> None:
    # Case: No remediation
    err = DomainValidationError("simple error")
    assert str(err) == "simple error"
