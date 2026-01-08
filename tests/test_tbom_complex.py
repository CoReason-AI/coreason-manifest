# Prosperity-3.0
import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict

import pytest

from coreason_manifest.errors import PolicyViolationError
from coreason_manifest.policy import PolicyEnforcer

# Path to the default policy
POLICY_PATH = Path("src/coreason_manifest/policies/compliance.rego")
OPA_BINARY = "./opa" if os.path.exists("./opa") else shutil.which("opa")


@pytest.fixture
def complex_tbom_file(tmp_path: Path) -> Path:
    """Creates a temporary TBOM file with a variety of package names."""
    tbom_path = tmp_path / "complex_tbom.json"
    tbom_data = {
        "tbom": ["requests", "zope.interface", "google-cloud-storage", "pandas", "hyphen-ated", "under_scored"]
    }
    with open(tbom_path, "w") as f:
        json.dump(tbom_data, f)
    return tbom_path


@pytest.fixture
def agent_data() -> Dict[str, Any]:
    return {
        "metadata": {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "version": "1.0.0",
            "name": "Complex Agent",
            "author": "Tester",
            "created_at": "2023-10-27T10:00:00Z",
        },
        "interface": {"inputs": {}, "outputs": {}},
        "topology": {
            "steps": [],
            "model_config": {"model": "gpt-4", "temperature": 0.5},
        },
        "dependencies": {"tools": [], "libraries": []},
    }


# @pytest.mark.skipif removed
class TestTBOMComplex:
    def test_dotted_package_name(self, complex_tbom_file: Path, agent_data: Dict[str, Any]) -> None:
        """Test that packages with dots (namespace packages) are correctly parsed and allowed."""

        enforcer = PolicyEnforcer(policy_path=POLICY_PATH, opa_path="opa", data_paths=[complex_tbom_file])

        # Allowed dotted package
        agent_data["dependencies"]["libraries"] = ["zope.interface==5.0.0"]
        enforcer.evaluate(agent_data)  # Should pass

        # Disallowed dotted package
        agent_data["dependencies"]["libraries"] = ["zope.component==5.0.0"]
        with pytest.raises(PolicyViolationError) as excinfo:
            enforcer.evaluate(agent_data)
        assert "is not in the Trusted Bill of Materials" in str(excinfo.value.violations)

    def test_package_with_extras(self, complex_tbom_file: Path, agent_data: Dict[str, Any]) -> None:
        """Test that packages with extras (brackets) are correctly matched against base name in TBOM."""

        enforcer = PolicyEnforcer(policy_path=POLICY_PATH, opa_path="opa", data_paths=[complex_tbom_file])

        # 'requests' is in TBOM. 'requests[security]' should be allowed.
        agent_data["dependencies"]["libraries"] = ["requests[security]==2.31.0"]
        enforcer.evaluate(agent_data)

        # 'pandas' is in TBOM.
        agent_data["dependencies"]["libraries"] = ["pandas[excel,plot]==2.0.0"]
        enforcer.evaluate(agent_data)

    def test_similar_package_names(self, complex_tbom_file: Path, agent_data: Dict[str, Any]) -> None:
        """Test strict matching to avoid prefix/suffix confusion."""

        enforcer = PolicyEnforcer(policy_path=POLICY_PATH, opa_path="opa", data_paths=[complex_tbom_file])

        # 'google-cloud-storage' is allowed.
        # 'google-cloud' (prefix) should NOT be allowed unless explicitly in TBOM (it's not).
        agent_data["dependencies"]["libraries"] = ["google-cloud==1.0.0"]
        with pytest.raises(PolicyViolationError) as excinfo:
            enforcer.evaluate(agent_data)
        assert "is not in the Trusted Bill of Materials" in str(excinfo.value.violations)

        # 'requests' is allowed. 'requests-toolbelt' should NOT be allowed.
        agent_data["dependencies"]["libraries"] = ["requests-toolbelt==1.0.0"]
        with pytest.raises(PolicyViolationError) as excinfo:
            enforcer.evaluate(agent_data)
        assert "is not in the Trusted Bill of Materials" in str(excinfo.value.violations)

    def test_case_sensitivity(self, complex_tbom_file: Path, agent_data: Dict[str, Any]) -> None:
        """Test handling of case sensitivity. TBOM is lowercase. Input might be mixed."""

        enforcer = PolicyEnforcer(policy_path=POLICY_PATH, opa_path="opa", data_paths=[complex_tbom_file])

        # Python packages are generally case-insensitive in pip, but best practice is lowercase.
        # If input is 'Pandas==2.0.0', and TBOM has 'pandas', it ideally should pass if we normalize,
        # or fail if we are strict. Given standard pip usage, normalization is safer, but strictly matching
        # TBOM is more secure.
        # UPDATE: Policy now normalizes case, so 'Pandas' should pass.

        agent_data["dependencies"]["libraries"] = ["Pandas==2.0.0"]
        enforcer.evaluate(agent_data)

    def test_no_dependencies(self, complex_tbom_file: Path, agent_data: Dict[str, Any]) -> None:
        """Test that empty dependencies list passes."""

        enforcer = PolicyEnforcer(policy_path=POLICY_PATH, opa_path="opa", data_paths=[complex_tbom_file])

        agent_data["dependencies"]["libraries"] = []
        enforcer.evaluate(agent_data)  # Should pass

    def test_malformed_tbom_structure(self, tmp_path: Path, agent_data: Dict[str, Any]) -> None:
        """Test behavior when TBOM file exists but has wrong structure (missing 'tbom' key)."""
        bad_tbom = tmp_path / "bad_tbom.json"
        with open(bad_tbom, "w") as f:
            json.dump({"allowed_libs": ["requests"]}, f)  # Wrong key

        enforcer = PolicyEnforcer(policy_path=POLICY_PATH, opa_path="opa", data_paths=[bad_tbom])

        # 'requests' is requested. It should fail because 'tbom' array is undefined/empty in the policy context.
        agent_data["dependencies"]["libraries"] = ["requests==2.0.0"]
        with pytest.raises(PolicyViolationError) as excinfo:
            enforcer.evaluate(agent_data)
        assert "is not in the Trusted Bill of Materials" in str(excinfo.value.violations)
