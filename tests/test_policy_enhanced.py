# Prosperity-3.0
import json
import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from coreason_manifest.errors import PolicyViolationError
from coreason_manifest.policy import PolicyEnforcer


def test_policy_regex_pinning_strictness() -> None:
    """
    Test the strictness of the regex used in PolicyEnforcer.
    """
    # Matching the regex from compliance.rego
    # Using raw string and escaping backslash for dash inside [] correctly for Python regex engine
    pattern = r"^[a-zA-Z0-9_\-\.]+(\[[a-zA-Z0-9_\-\.,]+\])?==[a-zA-Z0-9_\-\.\+]+$"

    valid_cases = [
        "pandas==2.0.1",
        "requests==2.31.0",
        "mypkg==1.0.0+build.1",
        "pkg-name==1.0",
        "pkg.name==1.0",
        "pkg_name==1.0",
        "pkg[extra]==1.0",
        "pkg[extra1,extra2]==1.0",
        "pkg[extra-1]==1.0",
    ]

    invalid_cases = [
        "pandas>=2.0",
        "pandas>2.0",
        "pandas~=2.0",
        "pandas==2.0,>=1.0",
        "pandas==2.0,!=2.1",
        "pandas",
        "==1.0",
        "pandas==",
        "pandas[extra]>=1.0",
        "pandas==2.0; python_version<'3.10'",
    ]

    for case in valid_cases:
        assert re.match(pattern, case), f"Should match: {case}"

    for case in invalid_cases:
        assert not re.match(pattern, case), f"Should NOT match: {case}"


def test_policy_enforcer_evaluate_success(tmp_path: Path) -> None:
    """Test evaluate success path with mocked subprocess."""
    policy_path = tmp_path / "policy.rego"
    policy_path.touch()

    enforcer = PolicyEnforcer(policy_path, opa_path="opa")

    # Mock subprocess.run to return clean result
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = json.dumps({"result": []})  # No violations

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        enforcer.evaluate({"some": "data"})

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "opa"
        assert "eval" in args


def test_policy_enforcer_evaluate_failure(tmp_path: Path) -> None:
    """Test evaluate failure path (violations found)."""
    policy_path = tmp_path / "policy.rego"
    policy_path.touch()

    enforcer = PolicyEnforcer(policy_path)

    # Mock subprocess.run to return violations
    mock_result = MagicMock()
    mock_result.returncode = 0
    # OPA output format structure
    mock_result.stdout = json.dumps({"result": [{"expressions": [{"value": ["Violation 1", "Violation 2"]}]}]})

    with patch("subprocess.run", return_value=mock_result):
        with pytest.raises(PolicyViolationError) as excinfo:
            enforcer.evaluate({"some": "data"})

        assert "Violation 1" in excinfo.value.violations
        assert "Violation 2" in excinfo.value.violations


def test_policy_enforcer_opa_error(tmp_path: Path) -> None:
    """Test OPA execution error (non-zero return code)."""
    policy_path = tmp_path / "policy.rego"
    policy_path.touch()

    enforcer = PolicyEnforcer(policy_path)

    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "OPA Error"

    with patch("subprocess.run", return_value=mock_result):
        with pytest.raises(RuntimeError, match="OPA execution failed: OPA Error"):
            enforcer.evaluate({})


def test_policy_enforcer_opa_not_found(tmp_path: Path) -> None:
    """Test OPA executable not found."""
    policy_path = tmp_path / "policy.rego"
    policy_path.touch()

    enforcer = PolicyEnforcer(policy_path, opa_path="non_existent_opa")

    with patch("subprocess.run", side_effect=FileNotFoundError):
        with pytest.raises(RuntimeError, match="OPA executable not found"):
            enforcer.evaluate({})


def test_policy_enforcer_json_error(tmp_path: Path) -> None:
    """Test invalid JSON output from OPA."""
    policy_path = tmp_path / "policy.rego"
    policy_path.touch()

    enforcer = PolicyEnforcer(policy_path)

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Invalid JSON"

    with patch("subprocess.run", return_value=mock_result):
        with pytest.raises(RuntimeError, match="Failed to parse OPA output"):
            enforcer.evaluate({})


def test_policy_enforcer_init_files_not_found() -> None:
    """Test initialization file checks."""
    with pytest.raises(FileNotFoundError, match="Policy file not found"):
        PolicyEnforcer("non_existent.rego")

    # Create valid policy file but invalid data file
    import tempfile

    with tempfile.NamedTemporaryFile() as f:
        with pytest.raises(FileNotFoundError, match="Data file not found"):
            PolicyEnforcer(f.name, data_paths=["non_existent.json"])


def test_policy_enforcer_evaluate_with_data_paths(tmp_path: Path) -> None:
    """Test evaluate includes data paths in command."""
    policy_path = tmp_path / "policy.rego"
    policy_path.touch()
    data_path = tmp_path / "data.json"
    data_path.touch()

    enforcer = PolicyEnforcer(policy_path, data_paths=[data_path])

    # Mock subprocess
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = json.dumps({"result": []})

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        enforcer.evaluate({})

        args = mock_run.call_args[0][0]
        assert "-d" in args
        # Check that data_path is in args after -d
        # args is a list, we can just check if str(data_path) is in it
        assert str(data_path) in args


def test_policy_enforcer_opa_error_empty_stderr(tmp_path: Path) -> None:
    """Test OPA error with empty stderr (fallback to stdout or default)."""
    policy_path = tmp_path / "policy.rego"
    policy_path.touch()

    enforcer = PolicyEnforcer(policy_path)

    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = ""
    mock_result.stdout = "Stdout Error"

    with patch("subprocess.run", return_value=mock_result):
        with pytest.raises(RuntimeError, match="OPA execution failed: Stdout Error"):
            enforcer.evaluate({})

    # Test completely empty
    mock_result.stdout = ""
    with patch("subprocess.run", return_value=mock_result):
        with pytest.raises(RuntimeError, match="OPA execution failed: Unknown error"):
            enforcer.evaluate({})
