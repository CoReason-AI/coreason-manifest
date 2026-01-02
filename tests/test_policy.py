# Prosperity-3.0
import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from coreason_manifest.errors import PolicyViolationError
from coreason_manifest.policy import PolicyEnforcer

# Path to the default policy
POLICY_PATH = Path("src/coreason_manifest/policies/compliance.rego")
# Path to the OPA binary downloaded in the setup phase (assumed to be in repo root)
OPA_BINARY = "./opa" if os.path.exists("./opa") else shutil.which("opa")


@pytest.fixture
def valid_agent_data() -> Dict[str, Any]:
    return {
        "metadata": {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "version": "1.0.0",
            "name": "Test Agent",
            "author": "Test Author",
            "created_at": "2023-10-27T10:00:00Z",
        },
        "interface": {"inputs": {}, "outputs": {}},
        "topology": {
            "steps": [{"id": "step1", "description": "Long enough description"}],
            "model_config": {"model": "gpt-4", "temperature": 0.7},
        },
        "dependencies": {"tools": [], "libraries": ["requests"]},
    }


def test_policy_enforcer_init_error() -> None:
    """Test that PolicyEnforcer raises FileNotFoundError if policy file missing."""
    with pytest.raises(FileNotFoundError):
        PolicyEnforcer(policy_path="non_existent.rego")


def test_evaluate_success_mock(valid_agent_data: Dict[str, Any], tmp_path: Path) -> None:
    """Test successful evaluation with mocked OPA."""
    policy_file = tmp_path / "test.rego"
    policy_file.touch()

    enforcer = PolicyEnforcer(policy_path=policy_file, opa_path="opa")

    # Mock subprocess.run to return clean result
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = json.dumps({"result": [{"expressions": [{"value": []}]}]})

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        enforcer.evaluate(valid_agent_data)
        mock_run.assert_called_once()


def test_evaluate_violation_mock(valid_agent_data: Dict[str, Any], tmp_path: Path) -> None:
    """Test evaluation with violations using mocked OPA."""
    policy_file = tmp_path / "test.rego"
    policy_file.touch()

    enforcer = PolicyEnforcer(policy_path=policy_file, opa_path="opa")

    # Mock subprocess.run to return violations
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = json.dumps({"result": [{"expressions": [{"value": ["Violation 1"]}]}]})

    with patch("subprocess.run", return_value=mock_result):
        with pytest.raises(PolicyViolationError) as excinfo:
            enforcer.evaluate(valid_agent_data)
        assert "Violation 1" in excinfo.value.violations


def test_opa_execution_failure(valid_agent_data: Dict[str, Any], tmp_path: Path) -> None:
    """Test handling of OPA execution failure (non-zero return code)."""
    policy_file = tmp_path / "test.rego"
    policy_file.touch()

    enforcer = PolicyEnforcer(policy_path=policy_file, opa_path="opa")

    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "OPA Error"

    with patch("subprocess.run", return_value=mock_result):
        with pytest.raises(RuntimeError) as excinfo:
            enforcer.evaluate(valid_agent_data)
        assert "OPA execution failed" in str(excinfo.value)


def test_opa_not_found(valid_agent_data: Dict[str, Any], tmp_path: Path) -> None:
    """Test handling when OPA executable is not found."""
    policy_file = tmp_path / "test.rego"
    policy_file.touch()

    enforcer = PolicyEnforcer(policy_path=policy_file, opa_path="non_existent_opa")

    with patch("subprocess.run", side_effect=FileNotFoundError):
        with pytest.raises(RuntimeError) as excinfo:
            enforcer.evaluate(valid_agent_data)
        assert "OPA executable not found" in str(excinfo.value)


def test_opa_invalid_json_output(valid_agent_data: Dict[str, Any], tmp_path: Path) -> None:
    """Test handling when OPA returns invalid JSON."""
    policy_file = tmp_path / "test.rego"
    policy_file.touch()
    enforcer = PolicyEnforcer(policy_path=policy_file, opa_path="opa")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Not JSON"

    with patch("subprocess.run", return_value=mock_result):
        with pytest.raises(RuntimeError) as excinfo:
            enforcer.evaluate(valid_agent_data)
        assert "Failed to parse OPA output" in str(excinfo.value)


@pytest.mark.skipif(not OPA_BINARY, reason="OPA binary not found")
def test_real_opa_integration(valid_agent_data: Dict[str, Any]) -> None:
    """Integration test with real OPA binary."""
    assert OPA_BINARY is not None
    enforcer = PolicyEnforcer(policy_path=POLICY_PATH, opa_path=OPA_BINARY)

    # 1. Valid Case
    enforcer.evaluate(valid_agent_data)

    # 2. Violation Case (pickle)
    valid_agent_data["dependencies"]["libraries"].append("pickle")
    with pytest.raises(PolicyViolationError) as excinfo:
        enforcer.evaluate(valid_agent_data)
    assert "pickle' library is strictly forbidden" in str(excinfo.value.violations)
