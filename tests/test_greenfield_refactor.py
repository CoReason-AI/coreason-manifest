import logging
import sys
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.core.flow import DataSchema

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

    # Setup capturing logger
    caplog.set_level(logging.WARNING, logger="coreason_manifest")

    # Run load_agent_from_ref
    # Must catch RuntimeSecurityWarning
    with pytest.warns(RuntimeSecurityWarning, match="Dynamic Code Execution"):
        load_agent_from_ref(f"{agent_file.name}:TestAgent", root_dir=tmp_path)


# ------------------------------------------------------------------------
# Task 3: Tolerant Ingress via Smart Discriminators
# ------------------------------------------------------------------------


def test_stream_error_duck_typing() -> None:
    """
    Inject a raw, untyped dictionary into the stream packet parser.
    Assert that it is successfully deserialized into a frozen StreamError object.
    """
    raw_payload = {"code": 500, "message": "Failure", "severity": "high"}

    # Simulate receiving this payload in a StreamPacket container
    # We need a model that uses StreamPacket
    try:
        # If StreamPacket is a Union, we might need a container to trigger validation
        container = PacketContainer(packet=raw_payload)
        packet = container.packet

        assert isinstance(packet, StreamError)
        assert packet.code == 500
        assert packet.message == "Failure"
        assert packet.severity == "high"

        # Verify frozen
        with pytest.raises(ValidationError):
            packet.code = 200  # type: ignore[misc]

    except ValidationError as e:
        pytest.fail(f"Duck typing failed: {e}")


def test_stream_error_duck_typing_fallback() -> None:
    """
    Inject a dictionary that matches signature but has wrong types.
    Should fallback to dict.
    """
    # 'code' is string, but StreamError requires int. strict=True means no coercion?
    # Actually Pydantic v2 strict=True might allow str->int if it looks like int?
    # No, strict=True means strict types.
    raw_payload = {"code": "500", "message": "Failure", "severity": "high"}

    container = PacketContainer(packet=raw_payload)
    packet = container.packet

    # Should remain a dict because StreamError validation failed (strict)
    # OR if Pydantic casts it?
    # If the validator code does StreamError.model_validate(raw_pkt), it raises ValidationError.
    # The except block catches it and passes.
    # So it remains a dict.
    assert isinstance(packet, dict)
    assert packet["code"] == "500"


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
    Test that invalid schema (not fixed by repair) raises ValueError wrapping SchemaError.
    """
    # 'type' must be string or list of strings. Integer is invalid.
    invalid_schema = {"type": 123}

    with pytest.raises(ValueError, match="Invalid JSON Schema"):
        DataSchema(json_schema=invalid_schema)


def test_unexpected_exception_handling(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Test catch-all exception handler in validate_meta_schema.
    """
    import jsonschema

    def mock_check_schema(_schema: Any) -> None:
        raise RuntimeError("Unexpected boom")

    monkeypatch.setattr(jsonschema.Draft7Validator, "check_schema", mock_check_schema)

    with pytest.raises(ValueError, match="Invalid JSON Schema definition: Unexpected boom"):
        DataSchema(json_schema={"type": "string"})


# ------------------------------------------------------------------------
# Final Hardening Tests (New Directives)
# ------------------------------------------------------------------------


def test_boolean_schema() -> None:
    """
    Test support for boolean schemas (Draft 7 allows true/false).
    """
    # True is a valid schema (always passes)
    ds_true = DataSchema(json_schema=True)
    assert ds_true.json_schema is True

    # False is a valid schema (always fails)
    ds_false = DataSchema(json_schema=False)
    assert ds_false.json_schema is False


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

    with pytest.raises(ValueError, match="Invalid JSON Schema") as excinfo:
        DataSchema(json_schema=schema)

    msg = str(excinfo.value)
    # The path should be present in the error message
    # Path: /properties/user/properties/age/minimum
    # Note: jsonschema might report path slightly differently depending on where it stops.
    # But it should contain 'minimum' or 'age'.
    assert "Invalid JSON Schema" in msg
    assert "at '/properties/user/properties/age/minimum'" in msg or "at '/properties/user/properties/age'" in msg
