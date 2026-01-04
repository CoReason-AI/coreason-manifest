# Prosperity-3.0
import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict

import pytest

from coreason_manifest.errors import PolicyViolationError
from coreason_manifest.policy import PolicyEnforcer

# Setup paths
POLICY_PATH = Path("src/coreason_manifest/policies/compliance.rego")
OPA_BINARY = "./opa" if os.path.exists("./opa") else shutil.which("opa")


@pytest.fixture
def base_agent_data() -> Dict[str, Any]:
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
        "dependencies": {"tools": [], "libraries": []},
    }


@pytest.mark.skipif(not OPA_BINARY, reason="OPA binary not found")
def test_complex_library_names(base_agent_data: Dict[str, Any], tmp_path: Path) -> None:
    """
    Test edge cases for library name parsing in Rego.
    - Names with dots (e.g., zope.interface)
    - Names with hyphens (e.g., google-cloud-storage)
    - Names with underscores (e.g., my_lib)
    """
    assert OPA_BINARY is not None

    # Create a custom TBOM for this test
    tbom_data = {"tbom": ["zope.interface", "google-cloud-storage", "my_lib"]}
    tbom_file = tmp_path / "tbom.json"
    with open(tbom_file, "w") as f:
        json.dump(tbom_data, f)

    enforcer = PolicyEnforcer(policy_path=POLICY_PATH, opa_path=OPA_BINARY, data_paths=[tbom_file])

    # Case 1: All valid complex names
    base_agent_data["dependencies"]["libraries"] = [
        "zope.interface==5.0.0",
        "google-cloud-storage==2.0.0",
        "my_lib==1.0.0",
    ]
    enforcer.evaluate(base_agent_data)

    # Case 2: Violation - Name with dot not in TBOM
    base_agent_data["dependencies"]["libraries"].append("other.lib==1.0")
    with pytest.raises(PolicyViolationError) as excinfo:
        enforcer.evaluate(base_agent_data)

    violations = str(excinfo.value.violations)
    assert "Library 'other.lib' is not in the Trusted Bill of Materials" in violations


@pytest.mark.skipif(not OPA_BINARY, reason="OPA binary not found")
def test_multiple_violations(base_agent_data: Dict[str, Any], tmp_path: Path) -> None:
    """Test that multiple violations are reported accurately."""
    assert OPA_BINARY is not None

    tbom_file = tmp_path / "tbom.json"
    with open(tbom_file, "w") as f:
        json.dump({"tbom": ["allowed-lib"]}, f)

    enforcer = PolicyEnforcer(policy_path=POLICY_PATH, opa_path=OPA_BINARY, data_paths=[tbom_file])

    base_agent_data["dependencies"]["libraries"] = [
        "pickle==1.0",  # Forbidden explicitly (in compliance.rego)
        "banned-lib==1.0",  # Not in TBOM
        "allowed-lib",  # Unpinned
    ]

    with pytest.raises(PolicyViolationError) as excinfo:
        enforcer.evaluate(base_agent_data)

    violations = excinfo.value.violations
    assert len(violations) >= 3

    # Check for specific messages
    # 1. pickle forbidden
    assert any("'pickle' library is strictly forbidden" in v for v in violations)
    # 2. banned-lib not in TBOM
    assert any("Library 'banned-lib' is not in the Trusted Bill of Materials" in v for v in violations)
    # 3. allowed-lib unpinned
    assert any("Library 'allowed-lib' must be strictly pinned with '=='" in v for v in violations)


@pytest.mark.skipif(not OPA_BINARY, reason="OPA binary not found")
def test_extras_handling(base_agent_data: Dict[str, Any], tmp_path: Path) -> None:
    """Test libraries with extras, e.g., fastapi[all]==0.95.0."""
    assert OPA_BINARY is not None

    # Note: The current Rego regex `^[a-zA-Z0-9_\-\.]+` might not handle `[` correctly if it stops early.
    # It parses the NAME.
    # If the string is `fastapi[all]==0.95.0`, the regex matches `fastapi`.
    # Then `[` causes it to stop matching name.
    # Then it checks if `fastapi` is in TBOM.

    tbom_file = tmp_path / "tbom.json"
    with open(tbom_file, "w") as f:
        json.dump({"tbom": ["fastapi"]}, f)

    enforcer = PolicyEnforcer(policy_path=POLICY_PATH, opa_path=OPA_BINARY, data_paths=[tbom_file])

    base_agent_data["dependencies"]["libraries"] = ["fastapi[all]==0.95.0"]

    # This should Pass if the regex correctly extracts "fastapi" as the name.
    enforcer.evaluate(base_agent_data)
