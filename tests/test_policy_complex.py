# Prosperity-3.0
import os
import shutil
from pathlib import Path
from typing import Any, Dict

import pytest
from coreason_manifest.errors import PolicyViolationError
from coreason_manifest.policy import PolicyEnforcer

POLICY_PATH = Path("src/coreason_manifest/policies/compliance.rego")
TBOM_PATH = Path("src/coreason_manifest/policies/tbom.json")
# Use the locally installed OPA if available
OPA_BINARY: str = "./opa" if os.path.exists("./opa") else (shutil.which("opa") or "")


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
            "steps": [{"id": "s1", "description": "valid description"}],
            "model_config": {"model": "gpt-4", "temperature": 0.7},
        },
        "dependencies": {"tools": [], "libraries": []},
    }


@pytest.mark.skipif(not OPA_BINARY, reason="OPA binary not found")
def test_complex_dependency_pinning(base_agent_data: Dict[str, Any]) -> None:
    """Test various dependency pinning scenarios against Rego policy."""
    enforcer = PolicyEnforcer(policy_path=POLICY_PATH, opa_path=OPA_BINARY, data_paths=[TBOM_PATH])

    # 1. Valid: Standard pinning (in TBOM)
    base_agent_data["dependencies"]["libraries"] = ["requests==2.31.0"]
    enforcer.evaluate(base_agent_data)  # Should pass

    # 2. Valid: Extras (in TBOM: requests)
    # Note: Rego parses 'requests[security]' -> lib name 'requests'.
    base_agent_data["dependencies"]["libraries"] = ["requests[security]==2.31.0"]
    enforcer.evaluate(base_agent_data)  # Should pass

    # 3. Valid: Build Metadata
    base_agent_data["dependencies"]["libraries"] = ["requests==2.31.0+build.123"]
    enforcer.evaluate(base_agent_data)  # Should pass

    # 4. Invalid: Mixed constraints
    base_agent_data["dependencies"]["libraries"] = ["requests==2.31.0,>=2.30.0"]
    with pytest.raises(PolicyViolationError) as e:
        enforcer.evaluate(base_agent_data)
    assert "must be strictly pinned" in str(e.value.violations)

    # 5. Invalid: Unpinned (>=)
    base_agent_data["dependencies"]["libraries"] = ["requests>=2.31.0"]
    with pytest.raises(PolicyViolationError) as e:
        enforcer.evaluate(base_agent_data)
    assert "must be strictly pinned" in str(e.value.violations)

    # 6. Invalid: No version
    base_agent_data["dependencies"]["libraries"] = ["requests"]
    with pytest.raises(PolicyViolationError) as e:
        enforcer.evaluate(base_agent_data)
    assert "must be strictly pinned" in str(e.value.violations)


@pytest.mark.skipif(not OPA_BINARY, reason="OPA binary not found")
def test_tbom_case_insensitivity(base_agent_data: Dict[str, Any]) -> None:
    """Test TBOM case insensitivity."""
    enforcer = PolicyEnforcer(policy_path=POLICY_PATH, opa_path=OPA_BINARY, data_paths=[TBOM_PATH])

    # TBOM contains "requests" (lowercase)

    # 1. Valid: Uppercase input "Requests"
    base_agent_data["dependencies"]["libraries"] = ["Requests==2.31.0"]
    enforcer.evaluate(base_agent_data)  # Should pass

    # 2. Valid: Mixed case "ReQuEsTs"
    base_agent_data["dependencies"]["libraries"] = ["ReQuEsTs==2.31.0"]
    enforcer.evaluate(base_agent_data)  # Should pass

    # 3. Invalid: Not in TBOM "UnknownLib"
    base_agent_data["dependencies"]["libraries"] = ["UnknownLib==1.0.0"]
    with pytest.raises(PolicyViolationError) as e:
        enforcer.evaluate(base_agent_data)
    assert "not in the Trusted Bill of Materials" in str(e.value.violations)


@pytest.mark.skipif(not OPA_BINARY, reason="OPA binary not found")
def test_malformed_tbom_file(base_agent_data: Dict[str, Any], tmp_path: Path) -> None:
    """Test behavior when TBOM file is malformed JSON."""
    bad_tbom = tmp_path / "bad_tbom.json"
    bad_tbom.write_text("{ not valid json }")

    # Init should pass (only checks existence)
    enforcer = PolicyEnforcer(policy_path=POLICY_PATH, opa_path=OPA_BINARY, data_paths=[bad_tbom])

    # Evaluate should fail due to OPA error parsing data
    with pytest.raises(RuntimeError) as e:
        enforcer.evaluate(base_agent_data)
    assert "OPA execution failed" in str(e.value)


@pytest.mark.skipif(not OPA_BINARY, reason="OPA binary not found")
def test_incorrect_tbom_structure(base_agent_data: Dict[str, Any], tmp_path: Path) -> None:
    """Test behavior when TBOM structure is incorrect (not a list)."""
    weird_tbom = tmp_path / "weird_tbom.json"
    # Valid JSON, but 'tbom' is a string, not a list
    weird_tbom.write_text('{"tbom": "just a string"}')

    enforcer = PolicyEnforcer(policy_path=POLICY_PATH, opa_path=OPA_BINARY, data_paths=[weird_tbom])

    # Rego: `some tbom_lib in data.tbom`
    # If data.tbom is a string "just a string", it iterates characters.
    # So "j", "u", "s", ...
    # If we request library "requests", it won't match any character.
    # So it should be denied as "not in TBOM".

    base_agent_data["dependencies"]["libraries"] = ["requests==2.31.0"]

    with pytest.raises(PolicyViolationError) as e:
        enforcer.evaluate(base_agent_data)
    assert "not in the Trusted Bill of Materials" in str(e.value.violations)
