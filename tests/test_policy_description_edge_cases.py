# Prosperity-3.0
import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict

import pytest

from coreason_manifest.errors import PolicyViolationError
from coreason_manifest.policy import PolicyEnforcer

POLICY_PATH = Path("src/coreason_manifest/policies/compliance.rego")
TBOM_PATH = Path("src/coreason_manifest/policies/tbom.json")
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
            "steps": [],
            "model_config": {"model": "gpt-4", "temperature": 0.5},
        },
        "dependencies": {"tools": [], "libraries": []},
    }

@pytest.mark.skipif(not OPA_BINARY, reason="OPA binary not found")
def test_description_boundary_conditions(base_agent_data: Dict[str, Any]) -> None:
    """Test description length boundary conditions."""
    enforcer = PolicyEnforcer(policy_path=POLICY_PATH, opa_path=OPA_BINARY, data_paths=[TBOM_PATH])

    # 1. Length 4 (Fail)
    base_agent_data["topology"]["steps"] = [{"id": "s1", "description": "abcd"}]
    with pytest.raises(PolicyViolationError) as e:
        enforcer.evaluate(base_agent_data)
    assert "Step description is too short" in str(e.value.violations)

    # 2. Length 5 (Pass)
    base_agent_data["topology"]["steps"] = [{"id": "s1", "description": "abcde"}]
    enforcer.evaluate(base_agent_data)

    # 3. Empty (Fail)
    base_agent_data["topology"]["steps"] = [{"id": "s1", "description": ""}]
    with pytest.raises(PolicyViolationError) as e:
        enforcer.evaluate(base_agent_data)
    assert "Step description is too short" in str(e.value.violations)

@pytest.mark.skipif(not OPA_BINARY, reason="OPA binary not found")
def test_unicode_description_length(base_agent_data: Dict[str, Any]) -> None:
    """Test how OPA counts unicode characters."""
    enforcer = PolicyEnforcer(policy_path=POLICY_PATH, opa_path=OPA_BINARY, data_paths=[TBOM_PATH])

    # 5 emojis
    # Python len("😊"*5) is 5.
    # OPA `count()` on string usually counts codepoints.
    base_agent_data["topology"]["steps"] = [{"id": "s1", "description": "😊😊😊😊😊"}]
    enforcer.evaluate(base_agent_data)

    # 4 emojis (Fail)
    base_agent_data["topology"]["steps"] = [{"id": "s1", "description": "😊😊😊😊"}]
    with pytest.raises(PolicyViolationError) as e:
        enforcer.evaluate(base_agent_data)
    assert "Step description is too short" in str(e.value.violations)

@pytest.mark.skipif(not OPA_BINARY, reason="OPA binary not found")
def test_multiple_steps_validation(base_agent_data: Dict[str, Any]) -> None:
    """Test that all steps are checked."""
    enforcer = PolicyEnforcer(policy_path=POLICY_PATH, opa_path=OPA_BINARY, data_paths=[TBOM_PATH])

    # Step 1: Good, Step 2: Good, Step 3: Bad
    base_agent_data["topology"]["steps"] = [
        {"id": "s1", "description": "Good Description 1"},
        {"id": "s2", "description": "Good Description 2"},
        {"id": "s3", "description": "Bad"},
    ]
    with pytest.raises(PolicyViolationError) as e:
        enforcer.evaluate(base_agent_data)
    assert "Step description is too short" in str(e.value.violations)
