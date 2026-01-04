# Prosperity-3.0
import re
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch
from uuid import uuid4

import pytest
import yaml

from coreason_manifest.engine import ManifestConfig, ManifestEngine
from coreason_manifest.errors import PolicyViolationError
from coreason_manifest.integrity import IntegrityChecker
from coreason_manifest.utils.logger import logger


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
    }


def test_policy_check_logging_pass(
    manifest_config: ManifestConfig,
    valid_agent_data: Dict[str, Any],
    tmp_path: Path,
) -> None:
    """Verify logging of policy check duration on success."""
    engine = ManifestEngine(manifest_config)
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "main.py").write_text("print('ok')")

    valid_agent_data["integrity_hash"] = IntegrityChecker.calculate_hash(src_dir)

    manifest_path = tmp_path / "agent.yaml"
    with open(manifest_path, "w") as f:
        yaml.dump(valid_agent_data, f)

    # Capture logs
    log_messages = []
    handler_id = logger.add(lambda msg: log_messages.append(msg))

    try:
        # Mock PolicyEnforcer to pass
        with patch.object(engine.policy_enforcer, "evaluate") as mock_eval:
            engine.load_and_validate(manifest_path, src_dir)
            mock_eval.assert_called_once()
    finally:
        logger.remove(handler_id)

    # Check for specific log messages
    found_pass = False
    found_validate = False

    agent_id = valid_agent_data["metadata"]["id"]
    agent_version = valid_agent_data["metadata"]["version"]
    expected_validate = f"Validating Agent {agent_id} v{agent_version}"

    for msg in log_messages:
        # Check raw message content
        raw_msg = msg.record["message"]
        if re.match(r"Policy Check: Pass - \d+(\.\d+)?ms", raw_msg):
            found_pass = True
        if raw_msg == expected_validate:
            found_validate = True

    assert found_pass, "Expected log message 'Policy Check: Pass - <time>ms' not found."
    assert found_validate, f"Expected log message '{expected_validate}' not found."


def test_policy_check_logging_fail(
    manifest_config: ManifestConfig,
    valid_agent_data: Dict[str, Any],
    tmp_path: Path,
) -> None:
    """Verify logging of policy check duration on failure."""
    engine = ManifestEngine(manifest_config)
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "main.py").write_text("print('ok')")

    valid_agent_data["integrity_hash"] = IntegrityChecker.calculate_hash(src_dir)

    manifest_path = tmp_path / "agent.yaml"
    with open(manifest_path, "w") as f:
        yaml.dump(valid_agent_data, f)

    # Capture logs
    log_messages = []
    handler_id = logger.add(lambda msg: log_messages.append(msg))

    try:
        # Mock PolicyEnforcer to fail
        with patch.object(
            engine.policy_enforcer,
            "evaluate",
            side_effect=PolicyViolationError("Violation"),
        ):
            with pytest.raises(PolicyViolationError):
                engine.load_and_validate(manifest_path, src_dir)
    finally:
        logger.remove(handler_id)

    found = False
    for msg in log_messages:
        raw_msg = msg.record["message"]
        if re.match(r"Policy Check: Fail - \d+(\.\d+)?ms", raw_msg):
            found = True
            break

    assert found, "Expected log message 'Policy Check: Fail - <time>ms' not found."
