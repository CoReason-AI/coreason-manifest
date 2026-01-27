# Prosperity-3.0
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch
from uuid import uuid4

import pytest
import yaml

from coreason_manifest.engine import ManifestConfig, ManifestEngine, ManifestEngineAsync
from coreason_manifest.errors import (
    IntegrityCompromisedError,
    ManifestSyntaxError,
    PolicyViolationError,
)
from coreason_manifest.integrity import IntegrityChecker
from coreason_manifest.models import AgentDefinition


@pytest.fixture
def manifest_config(tmp_path: Path) -> ManifestConfig:
    policy_path = tmp_path / "policy.rego"
    policy_path.touch()
    return ManifestConfig(policy_path=policy_path)


@pytest.fixture
def valid_agent_data() -> Dict[str, Any]:
    return {
        "metadata": {
            "id": str(uuid4()),
            "version": "1.0.0",
            "name": "Test Agent",
            "author": "Test Author",
            "created_at": "2023-10-27T10:00:00Z",
        },
        "interface": {"inputs": {}, "outputs": {}},
        "topology": {
            "steps": [{"id": "s1", "description": "desc"}],
            "model_config": {"model": "gpt-4", "temperature": 0.5},
        },
        "dependencies": {"tools": [], "libraries": ["requests==2.0.0"]},
        # Hash will be set in test
    }


def test_engine_init(manifest_config: ManifestConfig) -> None:
    """Test Engine initialization."""
    engine = ManifestEngine(manifest_config)
    assert engine._async.config == manifest_config
    assert engine._async.schema_validator is not None
    assert engine._async.policy_enforcer is not None

    # Test getattr proxying
    assert engine.config == manifest_config
    assert engine.schema_validator is not None
    assert engine.policy_enforcer is not None


def test_engine_init_with_tbom(tmp_path: Path) -> None:
    """Test Engine initialization with TBOM path."""
    policy_path = tmp_path / "policy.rego"
    policy_path.touch()
    tbom_path = tmp_path / "tbom.json"
    tbom_path.touch()

    config = ManifestConfig(policy_path=policy_path, tbom_path=tbom_path)
    engine = ManifestEngine(config)

    # Check if TBOM path is in PolicyEnforcer's data_paths
    assert tbom_path in engine._async.policy_enforcer.data_paths


def test_load_and_validate_success(
    manifest_config: ManifestConfig,
    valid_agent_data: Dict[str, Any],
    tmp_path: Path,
) -> None:
    """Test full successful flow (Sync Facade)."""
    engine = ManifestEngine(manifest_config)
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "main.py").write_text("print('ok')")

    # Calculate hash and add to manifest
    valid_agent_data["integrity_hash"] = IntegrityChecker.calculate_hash(src_dir)

    manifest_path = tmp_path / "agent.yaml"
    with open(manifest_path, "w") as f:
        yaml.dump(valid_agent_data, f)

    # Mock PolicyEnforcer to pass
    with patch.object(engine._async.policy_enforcer, "evaluate") as mock_eval:
        with engine:
            agent = engine.load_and_validate(manifest_path, src_dir)

        assert isinstance(agent, AgentDefinition)
        # Mock eval is called inside anyio thread, so we check called
        mock_eval.assert_called_once()


@pytest.mark.asyncio
async def test_load_and_validate_success_async(
    manifest_config: ManifestConfig,
    valid_agent_data: Dict[str, Any],
    tmp_path: Path,
) -> None:
    """Test full successful flow (Async Core)."""
    engine = ManifestEngineAsync(manifest_config)
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "main.py").write_text("print('ok')")

    # Calculate hash and add to manifest
    valid_agent_data["integrity_hash"] = IntegrityChecker.calculate_hash(src_dir)

    manifest_path = tmp_path / "agent.yaml"
    with open(manifest_path, "w") as f:
        yaml.dump(valid_agent_data, f)

    # Mock PolicyEnforcer to pass
    with patch.object(engine.policy_enforcer, "evaluate") as mock_eval:
        async with engine as svc:
            agent = await svc.load_and_validate(manifest_path, src_dir)

        assert isinstance(agent, AgentDefinition)
        mock_eval.assert_called_once()


def test_load_and_validate_schema_error(
    manifest_config: ManifestConfig,
    valid_agent_data: Dict[str, Any],
    tmp_path: Path,
) -> None:
    """Test failure at schema validation step."""
    engine = ManifestEngine(manifest_config)
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    # Invalid data (missing required field)
    del valid_agent_data["metadata"]

    manifest_path = tmp_path / "agent.yaml"
    with open(manifest_path, "w") as f:
        yaml.dump(valid_agent_data, f)

    with pytest.raises(ManifestSyntaxError):
        engine.load_and_validate(manifest_path, src_dir)


def test_load_and_validate_policy_error(
    manifest_config: ManifestConfig,
    valid_agent_data: Dict[str, Any],
    tmp_path: Path,
) -> None:
    """Test failure at policy enforcement step."""
    engine = ManifestEngine(manifest_config)
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "main.py").write_text("print('ok')")
    valid_agent_data["integrity_hash"] = IntegrityChecker.calculate_hash(src_dir)

    manifest_path = tmp_path / "agent.yaml"
    with open(manifest_path, "w") as f:
        yaml.dump(valid_agent_data, f)

    # Mock PolicyEnforcer to fail
    with patch.object(
        engine._async.policy_enforcer,
        "evaluate",
        side_effect=PolicyViolationError("Violation"),
    ):
        with pytest.raises(PolicyViolationError):
            engine.load_and_validate(manifest_path, src_dir)


def test_load_and_validate_integrity_error(
    manifest_config: ManifestConfig,
    valid_agent_data: Dict[str, Any],
    tmp_path: Path,
) -> None:
    """Test failure at integrity check step."""
    engine = ManifestEngine(manifest_config)
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "main.py").write_text("print('ok')")

    # Wrong hash
    valid_agent_data["integrity_hash"] = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"

    manifest_path = tmp_path / "agent.yaml"
    with open(manifest_path, "w") as f:
        yaml.dump(valid_agent_data, f)

    # Mock PolicyEnforcer to pass
    with patch.object(engine._async.policy_enforcer, "evaluate"):
        with pytest.raises(IntegrityCompromisedError):
            engine.load_and_validate(manifest_path, src_dir)


def test_validate_manifest_dict_sync(
    manifest_config: ManifestConfig,
    valid_agent_data: Dict[str, Any],
) -> None:
    """Test validate_manifest_dict sync method."""
    engine = ManifestEngine(manifest_config)

    # Needs valid integrity hash format for Pydantic validation,
    # even if integrity check is skipped in this method.
    valid_agent_data["integrity_hash"] = "a" * 64

    # Mock PolicyEnforcer to pass
    with patch.object(engine._async.policy_enforcer, "evaluate") as mock_eval:
        agent = engine.validate_manifest_dict(valid_agent_data)

        assert isinstance(agent, AgentDefinition)
        mock_eval.assert_called_once()
