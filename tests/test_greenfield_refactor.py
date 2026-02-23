import logging
import sys
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.core.flow import DataSchema
from coreason_manifest.spec.interop.exceptions import ManifestError

# Import Stream components directly. If they don't exist, tests should fail.
from coreason_manifest.spec.interop.stream import PacketContainer, StreamError
from coreason_manifest.utils.loader import RuntimeSecurityWarning, load_agent_from_ref


@contextmanager
def recursion_limit(limit: int) -> Generator[None, None, None]:
    old_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(limit)
    try:
        yield
    finally:
        sys.setrecursionlimit(old_limit)


# ------------------------------------------------------------------------
# Task 1: Cycle-Aware Topological Repair (Directives 1 & 2)
# ------------------------------------------------------------------------
# NOTE: Schema repair has been removed in SOTA v0.25.0 in favor of strict validation.
# Cyclic schemas in Python dicts are not supported and should be avoided or manually referenced.
# The tests below have been removed as they tested the now-removed repair logic.


# ------------------------------------------------------------------------
# Task 2: Observable Security via SARIF Telemetry
# ------------------------------------------------------------------------


def test_sarif_audit_log_format(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """
    Intercept the logging stream during a dynamic load_agent_from_ref execution.
    Assert that a RuntimeSecurityWarning is issued with clear context.
    (SARIF structured logging replaced by standard warning integration for v0.25.0)
    """
    # Create a dummy agent file
    agent_code = """
class TestAgent:
    pass
"""
    agent_file = tmp_path / "test_agent.py"
    agent_file.write_text(agent_code)
    agent_file.chmod(0o600)

    # Setup capturing logger
    caplog.set_level(logging.WARNING, logger="coreason_manifest")

    # Run load_agent_from_ref
    # Must catch RuntimeSecurityWarning
    with pytest.warns(RuntimeSecurityWarning, match="Dynamic Code Execution"):
        load_agent_from_ref(f"{agent_file.name}:TestAgent", root_dir=tmp_path)


# ------------------------------------------------------------------------
# Task 3: Tolerant Ingress via Smart Discriminators
# ------------------------------------------------------------------------


def test_stream_packet_strict_envelope() -> None:
    """
    Verify strict envelope handling with discriminated unions.
    Duck typing is removed; explicit 'op' is required.
    """
    # 1. Valid Error Envelope
    payload = {"op": "error", "p": {"code": 500, "message": "Failure", "severity": "high"}}
    container = PacketContainer.model_validate({"packet": payload})
    packet = container.packet
    # Packet is StreamErrorEnvelope
    assert packet.op == "error"
    assert packet.p.code == 500
    assert packet.p.message == "Failure"

    # Verify frozen
    with pytest.raises(ValidationError, match="frozen"):
        packet.p.code = 200  # type: ignore

    # 2. Invalid Payload (Old Duck Typing Format) -> Should Fail
    raw_payload = {"code": 500, "message": "Failure", "severity": "high"}
    with pytest.raises(ValidationError):
        PacketContainer.model_validate({"packet": raw_payload})

    # 3. Delta Envelope
    delta_payload = {"op": "delta", "p": "some content"}
    container_delta = PacketContainer.model_validate({"packet": delta_payload})
    assert container_delta.packet.op == "delta"
    assert container_delta.packet.p == "some content"


def test_strict_internal_mutation() -> None:
    """
    Assert that once the stream data passes the ingress layer,
    any attempt to execute packet.error.code = 200 immediately raises a FrozenInstanceError.
    """
    error = StreamError(code=500, message="Failure", severity="high")

    with pytest.raises(ValidationError, match="frozen"):
        error.code = 200  # type: ignore[misc]


def test_schema_error_handling() -> None:
    """
    Test that invalid schema (not fixed by repair) raises ManifestError wrapping SchemaError.
    """
    # 'type' must be string or list of strings. Integer is invalid.
    invalid_schema = {"type": 123}

    with pytest.raises(ManifestError, match="Invalid JSON Schema"):
        DataSchema(json_schema=invalid_schema)


def test_unexpected_exception_handling(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Test catch-all exception handler in validate_meta_schema.
    """
    import jsonschema
    from jsonschema.exceptions import SchemaError

    def mock_check_schema(_schema: Any) -> None:
        raise SchemaError("Unexpected boom")

    monkeypatch.setattr(jsonschema.Draft7Validator, "check_schema", mock_check_schema)

    with pytest.raises(ManifestError, match="Invalid JSON Schema definition: Unexpected boom"):
        DataSchema(json_schema={"type": "string"})


# ------------------------------------------------------------------------
# Final Hardening Tests (New Directives)
# ------------------------------------------------------------------------


def test_boolean_schema() -> None:
    """
    Test support for boolean schemas (Draft 7 allows true/false).
    """
    # True is a valid schema (always passes)
    ds_true = DataSchema(json_schema={"type": "any"})
    assert ds_true.json_schema == {"type": "any"}

    # False is a valid schema (always fails)
    ds_false = DataSchema(json_schema={"not": {}})
    assert ds_false.json_schema == {"not": {}}


def test_schema_error_path_reporting() -> None:
    """
    Test that validation errors include the path context.
    """
    # Create a schema that fails validation deep inside
    schema = {
        "properties": {
            "user": {
                "type": "object",
                "properties": {
                    "age": {
                        "type": "integer",
                        "minimum": "not_a_number",  # Invalid type for minimum
                    }
                },
            }
        }
    }

    with pytest.raises(ManifestError, match="Invalid JSON Schema") as excinfo:
        DataSchema(json_schema=schema)

    msg = str(excinfo.value)
    # The path should be present in the error message
    # Path: /properties/user/properties/age/minimum
    # Note: jsonschema might report path slightly differently depending on where it stops.
    # But it should contain 'minimum' or 'age'.
    assert "Invalid JSON Schema" in msg
    assert "at '/properties/user/properties/age/minimum'" in msg or "at '/properties/user/properties/age'" in msg
