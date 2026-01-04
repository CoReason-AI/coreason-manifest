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
TBOM_PATH = Path("src/coreason_manifest/policies/tbom.json")
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
        "dependencies": {"tools": [], "libraries": ["requests==2.31.0"]},
    }


def test_tbom_enforcement_mock(valid_agent_data: Dict[str, Any], tmp_path: Path) -> None:
    """Test TBOM enforcement with mock OPA output."""
    policy_file = tmp_path / "test.rego"
    policy_file.touch()
    tbom_file = tmp_path / "tbom.json"
    tbom_file.touch()

    enforcer = PolicyEnforcer(policy_path=policy_file, opa_path="opa", data_paths=[tbom_file])

    # Case 1: Library allowed (Mocked success)
    mock_result_success = MagicMock()
    mock_result_success.returncode = 0
    mock_result_success.stdout = json.dumps({"result": [{"expressions": [{"value": []}]}]})

    with patch("subprocess.run", return_value=mock_result_success) as mock_run:
        enforcer.evaluate(valid_agent_data)
        args, _ = mock_run.call_args
        # Verify -d flags were passed
        cmd = args[0]
        assert "-d" in cmd
        assert str(tbom_file) in cmd

    # Case 2: Library not in TBOM (Mocked failure)
    valid_agent_data["dependencies"]["libraries"] = ["malicious-lib==1.0.0"]

    mock_result_fail = MagicMock()
    mock_result_fail.returncode = 0
    mock_result_fail.stdout = json.dumps(
        {
            "result": [
                {
                    "expressions": [
                        {
                            "value": [
                                "Compliance Violation: Library 'malicious-lib' is not in the Trusted Bill of Materials (TBOM)."  # noqa: E501
                            ]
                        }
                    ]
                }
            ]
        }
    )

    with patch("subprocess.run", return_value=mock_result_fail):
        with pytest.raises(PolicyViolationError) as excinfo:
            enforcer.evaluate(valid_agent_data)
        # Check violations attribute instead of string representation of exception
        # as the message is generic "Policy violations found."
        assert "not in the Trusted Bill of Materials" in str(excinfo.value.violations)


@pytest.mark.skipif(not OPA_BINARY, reason="OPA binary not found")
def test_tbom_real_opa_integration(valid_agent_data: Dict[str, Any]) -> None:
    """Integration test with real OPA binary to verify regex parsing and TBOM lookup."""
    assert OPA_BINARY is not None
    # We use the real policy and tbom file
    assert POLICY_PATH.exists()
    assert TBOM_PATH.exists()

    enforcer = PolicyEnforcer(policy_path=POLICY_PATH, opa_path=OPA_BINARY, data_paths=[TBOM_PATH])

    # 1. Valid Case: requests is in TBOM
    # valid_agent_data has "requests==2.31.0"
    enforcer.evaluate(valid_agent_data)

    # 2. Invalid Case: Library not in TBOM
    valid_agent_data["dependencies"]["libraries"].append("unknown-lib==1.0.0")
    with pytest.raises(PolicyViolationError) as excinfo:
        enforcer.evaluate(valid_agent_data)
    assert "is not in the Trusted Bill of Materials" in str(excinfo.value.violations)

    # 3. Invalid Case: Library in TBOM but not pinned (Rule 1 still active)
    valid_agent_data["dependencies"]["libraries"] = ["requests"]
    with pytest.raises(PolicyViolationError) as excinfo:
        enforcer.evaluate(valid_agent_data)
    # This might fail Rule 1 or Rule 2 depending on how regex handles "requests" (no ==)
    # Rule 1 explicitly checks for "==" so it should fail Rule 1.
    violations = str(excinfo.value.violations)
    assert "must be strictly pinned with '=='" in violations
