
import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from coreason_manifest.definitions.agent import (
    AgentConfig,
    AgentDefinition,
)
from coreason_manifest.definitions.audit import AuditEventType, AuditLog, GenAIOperation
from coreason_manifest.recipes import RecipeManifest


def test_audit_log_legacy_key_rejection() -> None:
    """Test that instantiating AuditLog with legacy 'id' field fails."""
    now = datetime.now(timezone.utc)
    with pytest.raises(ValidationError) as exc:
        AuditLog(
            id=uuid.uuid4(),  # Legacy key  # type: ignore[call-arg]
            trace_id="trace-123",
            timestamp=now,
            actor="user",
            event_type=AuditEventType.SYSTEM_CHANGE,
            safety_metadata={},
            previous_hash="abc",
            integrity_hash="def",
        )  # type: ignore[call-arg]
    # Pydantic v2 error for extra fields (if extra="forbid" which is default for these models usually)
    # or missing required field 'audit_id'
    error_str = str(exc.value)
    assert "audit_id" in error_str and "Field required" in error_str


def test_audit_log_trace_id_requirement() -> None:
    """Test that trace_id is mandatory for AuditLog."""
    now = datetime.now(timezone.utc)
    with pytest.raises(ValidationError) as exc:
        AuditLog(
            audit_id=uuid.uuid4(),
            # trace_id missing
            timestamp=now,
            actor="user",
            event_type=AuditEventType.SYSTEM_CHANGE,
            safety_metadata={},
            previous_hash="abc",
            integrity_hash="def",
        )  # type: ignore[call-arg]
    assert "trace_id" in str(exc.value)


def test_gen_ai_operation_legacy_key_rejection() -> None:
    """Test that instantiating GenAIOperation with legacy 'id' field fails."""
    with pytest.raises(ValidationError) as exc:
        GenAIOperation(
            id="span-123",  # Legacy  # type: ignore[call-arg]
            trace_id="trace-123",
            operation_name="test",
            provider="openai",
            model="gpt-4",
        )  # type: ignore[call-arg]
    error_str = str(exc.value)
    assert "span_id" in error_str and "Field required" in error_str


def test_agent_definition_legacy_key_rejection() -> None:
    """Test that AgentDefinition rejects 'topology' key in favor of 'config'."""
    data = {
        "metadata": {
            "id": str(uuid.uuid4()),
            "version": "1.0.0",
            "name": "Test",
            "author": "Me",
            "created_at": "2023-01-01T00:00:00Z",
        },
        "interface": {"inputs": {}, "outputs": {}},
        "topology": {  # Legacy key
            "nodes": [],
            "edges": [],
            "entry_point": "start",
            "model_config": {"model": "gpt-4", "temperature": 0.1},
        },
        "dependencies": {},
        "integrity_hash": "a" * 64,
    }
    with pytest.raises(ValidationError) as exc:
        AgentDefinition(**data)

    error_str = str(exc.value)
    assert "config" in error_str and "Field required" in error_str
    assert "topology" in error_str and "Extra inputs are not permitted" in error_str


def test_recipe_manifest_legacy_key_rejection() -> None:
    """Test that RecipeManifest rejects 'graph' key in favor of 'topology'."""
    data = {
        "id": "recipe-1",
        "version": "1.0.0",
        "name": "Test Recipe",
        "interface": {"inputs": {}, "outputs": {}},
        "state": {"schema": {}, "persistence": "ephemeral"},
        "parameters": {},
        "graph": {"nodes": [], "edges": []},  # Legacy key
    }
    with pytest.raises(ValidationError) as exc:
        RecipeManifest(**data)

    error_str = str(exc.value)
    assert "topology" in error_str and "Field required" in error_str
    assert "graph" in error_str and "Extra inputs are not permitted" in error_str


def test_agent_config_validation() -> None:
    """Test that AgentConfig (new name) works correctly."""
    config = AgentConfig(nodes=[], edges=[], entry_point="start", model_config={"model": "gpt-4", "temperature": 0.5})
    assert config.model_config.get("extra") == "forbid"
    assert hasattr(config, "nodes")
