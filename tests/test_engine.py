# Prosperity-3.0
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest
import yaml

from coreason_manifest.engine import ManifestConfig, ManifestEngine
from coreason_manifest.errors import (
    IntegrityCompromisedError,
    ManifestError,
    ManifestSyntaxError,
    PolicyViolationError,
    SchemaValidationError,
)
from coreason_manifest.models import AgentDefinition


@pytest.fixture
def valid_manifest_dict() -> Dict[str, Any]:
    return {
        "metadata": {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "version": "1.0.0",
            "name": "Test Agent",
            "author": "Tester",
            "created_at": "2023-10-27T10:00:00Z",
        },
        "interface": {"inputs": {"type": "object"}, "outputs": {"type": "object"}},
        "topology": {"steps": [{"id": "step1"}], "model_config": {"model": "gpt-4", "temperature": 0.7}},
        "dependencies": {"tools": [], "libraries": ["requests"]},
        "integrity_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",  # Empty hash for simplicity
    }


@pytest.fixture
def manifest_file(tmp_path: Path, valid_manifest_dict: Dict[str, Any]) -> Path:
    p = tmp_path / "agent.yaml"
    with open(p, "w") as f:
        yaml.dump(valid_manifest_dict, f)
    return p


@pytest.fixture
def source_dir(tmp_path: Path) -> Path:
    d = tmp_path / "src"
    d.mkdir()
    return d


@pytest.fixture
def policy_file(tmp_path: Path) -> Path:
    p = tmp_path / "policy.rego"
    p.touch()
    return p


@pytest.fixture
def config(policy_file: Path) -> ManifestConfig:
    return ManifestConfig(policy_path=policy_file, verify_integrity=False, enforce_policy=False)


def test_engine_initialization(config: ManifestConfig) -> None:
    engine = ManifestEngine(config)
    assert engine.config == config
    assert engine.validator is not None
    assert engine.policy_enforcer is None


def test_engine_initialization_with_policy(policy_file: Path) -> None:
    config = ManifestConfig(policy_path=policy_file, enforce_policy=True)
    engine = ManifestEngine(config)
    assert engine.policy_enforcer is not None


def test_load_and_validate_success(manifest_file: Path, source_dir: Path, config: ManifestConfig) -> None:
    engine = ManifestEngine(config)
    agent_def = engine.load_and_validate(manifest_file, source_dir)
    assert isinstance(agent_def, AgentDefinition)
    assert agent_def.metadata.name == "Test Agent"


def test_load_and_validate_file_not_found(source_dir: Path, config: ManifestConfig) -> None:
    engine = ManifestEngine(config)
    with pytest.raises(FileNotFoundError):
        engine.load_and_validate("non_existent.yaml", source_dir)


def test_load_and_validate_schema_error(
    manifest_file: Path, source_dir: Path, config: ManifestConfig, valid_manifest_dict: Dict[str, Any]
) -> None:
    # Make manifest invalid (missing required field)
    valid_manifest_dict.pop("metadata")
    with open(manifest_file, "w") as f:
        yaml.dump(valid_manifest_dict, f)

    engine = ManifestEngine(config)
    with pytest.raises(SchemaValidationError):
        engine.load_and_validate(manifest_file, source_dir)


def test_load_and_validate_manifest_not_dict(manifest_file: Path, source_dir: Path, config: ManifestConfig) -> None:
    # Case where YAML loads but is not a dict (e.g., list or string)
    with open(manifest_file, "w") as f:
        f.write("- item1\n- item2")

    engine = ManifestEngine(config)
    with pytest.raises(ManifestSyntaxError):
        engine.load_and_validate(manifest_file, source_dir)


def test_load_and_validate_policy_violation(manifest_file: Path, source_dir: Path, policy_file: Path) -> None:
    config = ManifestConfig(policy_path=policy_file, enforce_policy=True)
    engine = ManifestEngine(config)

    # Mock PolicyEnforcer.evaluate to raise exception
    assert engine.policy_enforcer is not None
    with patch.object(engine.policy_enforcer, "evaluate", side_effect=PolicyViolationError("Violation")):
        with pytest.raises(PolicyViolationError):
            engine.load_and_validate(manifest_file, source_dir)


def test_load_and_validate_policy_success(manifest_file: Path, source_dir: Path, policy_file: Path) -> None:
    """Test successful policy validation to cover the success path line."""
    config = ManifestConfig(policy_path=policy_file, enforce_policy=True)
    engine = ManifestEngine(config)

    # Mock PolicyEnforcer.evaluate to succeed (return None)
    assert engine.policy_enforcer is not None
    with patch.object(engine.policy_enforcer, "evaluate", return_value=None) as mock_eval:
        engine.load_and_validate(manifest_file, source_dir)
        mock_eval.assert_called_once()


def test_load_and_validate_integrity_check_failure(
    manifest_file: Path, source_dir: Path, config: ManifestConfig
) -> None:
    config.verify_integrity = True
    engine = ManifestEngine(config)

    # Mock IntegrityChecker.verify to raise exception
    with patch(
        "coreason_manifest.engine.IntegrityChecker.verify", side_effect=IntegrityCompromisedError("Integrity error")
    ):
        with pytest.raises(IntegrityCompromisedError):
            engine.load_and_validate(manifest_file, source_dir)


def test_load_and_validate_integrity_check_success(
    manifest_file: Path, source_dir: Path, config: ManifestConfig
) -> None:
    config.verify_integrity = True
    engine = ManifestEngine(config)

    with patch("coreason_manifest.engine.IntegrityChecker.verify") as mock_verify:
        engine.load_and_validate(manifest_file, source_dir)
        mock_verify.assert_called_once()


def test_integrity_check_logging_exception(manifest_file: Path, source_dir: Path, config: ManifestConfig) -> None:
    config.verify_integrity = True
    engine = ManifestEngine(config)

    # We want to verify that the exception is logged.
    with patch("coreason_manifest.engine.IntegrityChecker.verify", side_effect=IntegrityCompromisedError("Fail")):
        with patch("coreason_manifest.engine.logger") as mock_logger:
            with pytest.raises(IntegrityCompromisedError):
                engine.load_and_validate(manifest_file, source_dir)

            mock_logger.error.assert_called()
            assert any(
                "Integrity Check: Fail" in str(arg) for call in mock_logger.error.call_args_list for arg in call[0]
            )


def test_policy_check_logging_exception(manifest_file: Path, source_dir: Path, policy_file: Path) -> None:
    config = ManifestConfig(policy_path=policy_file, enforce_policy=True)
    engine = ManifestEngine(config)

    assert engine.policy_enforcer is not None
    with patch.object(engine.policy_enforcer, "evaluate", side_effect=PolicyViolationError("Violation")):
        with patch("coreason_manifest.engine.logger") as mock_logger:
            with pytest.raises(PolicyViolationError):
                engine.load_and_validate(manifest_file, source_dir)

            mock_logger.error.assert_called()
            assert any("Policy Check: Fail" in str(arg) for call in mock_logger.error.call_args_list for arg in call[0])


def test_policy_check_generic_manifest_error(manifest_file: Path, source_dir: Path, policy_file: Path) -> None:
    """Test catching generic ManifestError during policy check."""
    config = ManifestConfig(policy_path=policy_file, enforce_policy=True)
    engine = ManifestEngine(config)

    assert engine.policy_enforcer is not None
    with patch.object(engine.policy_enforcer, "evaluate", side_effect=ManifestError("Generic Error")):
        with patch("coreason_manifest.engine.logger") as mock_logger:
            with pytest.raises(ManifestError):
                engine.load_and_validate(manifest_file, source_dir)

            mock_logger.error.assert_called()
            # This should cover line 128
            assert any("Policy Check: Fail" in str(arg) for call in mock_logger.error.call_args_list for arg in call[0])


def test_integrity_check_generic_manifest_error(manifest_file: Path, source_dir: Path, config: ManifestConfig) -> None:
    """Test catching generic ManifestError during integrity check."""
    config.verify_integrity = True
    engine = ManifestEngine(config)

    with patch("coreason_manifest.engine.IntegrityChecker.verify", side_effect=ManifestError("Generic Error")):
        with patch("coreason_manifest.engine.logger") as mock_logger:
            with pytest.raises(ManifestError):
                engine.load_and_validate(manifest_file, source_dir)

            mock_logger.error.assert_called()
            # This should cover line 140
            assert any(
                "Integrity Check: Fail" in str(arg) for call in mock_logger.error.call_args_list for arg in call[0]
            )


def test_validation_works_with_valid_dict(
    manifest_file: Path, source_dir: Path, config: ManifestConfig, valid_manifest_dict: Dict[str, Any]
) -> None:
    """Explicitly verify that when dict is valid, we proceed."""
    engine = ManifestEngine(config)
    # Using real file which contains a dict
    agent_def = engine.load_and_validate(manifest_file, source_dir)
    assert agent_def is not None


def test_validation_skipped_if_not_dict_but_loader_handles_it(
    manifest_file: Path, source_dir: Path, config: ManifestConfig
) -> None:
    """
    If raw_data is not dict, validation is skipped.
    Then loader is called.
    """
    engine = ManifestEngine(config)

    with open(manifest_file, "w") as f:
        f.write("- list\n- item")

    with patch("coreason_manifest.engine.ManifestLoader.load_from_dict") as mock_loader:
        # Mock loader to return a valid agent definition
        mock_agent = MagicMock()
        # Mock attributes accessed by logging
        mock_agent.metadata.name = "Mock Agent"
        mock_agent.metadata.version = "1.0.0"

        mock_loader.return_value = mock_agent

        # NOTE: Ensure the 'pass' line (104) is hit.
        # This test ensures that when isinstance(dict) is false, we fall through to pass
        # and then continue to load_from_dict.

        agent_def = engine.load_and_validate(manifest_file, source_dir)

        assert agent_def == mock_agent
