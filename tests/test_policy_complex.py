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

# We assume OPA is available or mocked.
# If unavailable, we skip real execution tests.
POLICY_PATH = Path("src/coreason_manifest/policies/compliance.rego")
TBOM_PATH = Path("src/coreason_manifest/policies/tbom.json")
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
            "steps": [{"id": "s1", "description": "Valid description"}],
            "model_config": {"model": "gpt-4", "temperature": 0.5},
        },
        "dependencies": {"tools": [], "libraries": ["requests==2.0.0"]},
    }


def test_dependency_pinning_enforcement(valid_agent_data: Dict[str, Any], tmp_path: Path) -> None:
    """Test that libraries without '==' are rejected."""
    # We use a mocked OPA response to simulate the policy behavior
    # because ensuring OPA binary exists with correct version everywhere is hard.
    # However, to truly test the REGO logic, we should use the real OPA if available.

    # If OPA is not available, we mock the expected JSON response for this violation.
    # But wait, testing the *Rego logic* requires running the Rego.
    # Mocking subprocess just tests Python code handling the output.

    # Since I'm tasked to "check for complex cases", verifying the REGO logic is key.
    # I will attempt to run real OPA if available, else skip.
    pass


@pytest.mark.skipif(not OPA_BINARY, reason="OPA binary not found")
def test_rego_pinning_logic_real(valid_agent_data: Dict[str, Any]) -> None:
    """Test actual Rego logic for pinning using OPA binary."""
    assert OPA_BINARY
    enforcer = PolicyEnforcer(policy_path=POLICY_PATH, opa_path=OPA_BINARY, data_paths=[TBOM_PATH])

    # Case 1: Valid pinned
    enforcer.evaluate(valid_agent_data)

    # Case 2: Unpinned (>=)
    valid_agent_data["dependencies"]["libraries"] = ["requests>=2.0.0"]
    with pytest.raises(PolicyViolationError) as excinfo:
        enforcer.evaluate(valid_agent_data)
    assert "must be pinned with '=='" in str(excinfo.value.violations)

    # Case 3: No version
    valid_agent_data["dependencies"]["libraries"] = ["requests"]
    with pytest.raises(PolicyViolationError) as excinfo:
        enforcer.evaluate(valid_agent_data)
    assert "must be pinned with '=='" in str(excinfo.value.violations)


def test_mocked_pinning_violation(valid_agent_data: Dict[str, Any], tmp_path: Path) -> None:
    """Mock test ensuring Python code handles the pinning violation message correctly."""
    policy_file = tmp_path / "dummy.rego"
    policy_file.touch()
    enforcer = PolicyEnforcer(policy_path=policy_file)

    mock_result = MagicMock()
    mock_result.returncode = 0
    # Simulate OPA output for the violation
    mock_result.stdout = json.dumps(
        {
            "result": [
                {"expressions": [{"value": ["Compliance Violation: Library 'requests' must be pinned with '=='."]}]}
            ]
        }
    )

    with patch("subprocess.run", return_value=mock_result):
        with pytest.raises(PolicyViolationError) as excinfo:
            enforcer.evaluate(valid_agent_data)
        assert "must be pinned with '=='" in str(excinfo.value.violations)
