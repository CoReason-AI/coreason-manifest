import os
import shutil
from pathlib import Path
from typing import Generator

import pytest

from coreason_manifest.errors import PolicyViolationError
from coreason_manifest.policy import PolicyEnforcer

POLICY_PATH = Path("src/coreason_manifest/policies/compliance.rego")
TBOM_PATH = Path("src/coreason_manifest/policies/tbom.json")
OPA_BINARY = "./opa" if os.path.exists("./opa") else shutil.which("opa")


@pytest.fixture
def enforcer() -> Generator[PolicyEnforcer, None, None]:
    # OPA binary check removed as we use mock
    # We must yield, even though we don't need teardown, to match typical fixture patterns if needed,
    # but strictly returning is fine if typed as PolicyEnforcer.
    # However, generator is standard for pytest fixtures.
    yield PolicyEnforcer(policy_path=POLICY_PATH, opa_path="opa", data_paths=[TBOM_PATH])


def test_mixed_pinning_fails(enforcer: PolicyEnforcer) -> None:
    """Test that mixed constraints like 'requests==2.31.0,>=2.0' are NOW REJECTED."""
    data = {
        "metadata": {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "version": "1.0.0",
            "name": "A",
            "author": "B",
            "created_at": "2023-01-01",
        },
        "interface": {"inputs": {}, "outputs": {}},
        "topology": {
            "steps": [{"id": "s1", "description": "valid desc"}],
            "model_config": {"model": "m", "temperature": 0.1},
        },
        "dependencies": {"tools": [], "libraries": ["requests==2.31.0,>=2.0"]},
    }
    with pytest.raises(PolicyViolationError) as excinfo:
        enforcer.evaluate(data)
    assert "must be strictly pinned with '=='" in str(excinfo.value.violations)


def test_extras_pinning_passes(enforcer: PolicyEnforcer) -> None:
    """Test that strict pinning allows extras."""
    # Ensure requests is in TBOM for this to pass Rule 2 as well
    data = {
        "metadata": {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "version": "1.0.0",
            "name": "A",
            "author": "B",
            "created_at": "2023-01-01",
        },
        "interface": {"inputs": {}, "outputs": {}},
        "topology": {
            "steps": [{"id": "s1", "description": "valid desc"}],
            "model_config": {"model": "m", "temperature": 0.1},
        },
        "dependencies": {"tools": [], "libraries": ["requests[security]==2.31.0"]},
    }
    enforcer.evaluate(data)


def test_case_sensitivity_passes(enforcer: PolicyEnforcer) -> None:
    """Test that 'Requests==2.31.0' matches 'requests' in TBOM (case-insensitive)."""
    data = {
        "metadata": {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "version": "1.0.0",
            "name": "A",
            "author": "B",
            "created_at": "2023-01-01",
        },
        "interface": {"inputs": {}, "outputs": {}},
        "topology": {
            "steps": [{"id": "s1", "description": "valid desc"}],
            "model_config": {"model": "m", "temperature": 0.1},
        },
        "dependencies": {"tools": [], "libraries": ["Requests==2.31.0"]},
    }
    enforcer.evaluate(data)


def test_complex_version_passes(enforcer: PolicyEnforcer) -> None:
    """Test that versions with build metadata are allowed."""
    # We use a lib in TBOM: pandas
    data = {
        "metadata": {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "version": "1.0.0",
            "name": "A",
            "author": "B",
            "created_at": "2023-01-01",
        },
        "interface": {"inputs": {}, "outputs": {}},
        "topology": {
            "steps": [{"id": "s1", "description": "valid desc"}],
            "model_config": {"model": "m", "temperature": 0.1},
        },
        "dependencies": {"tools": [], "libraries": ["pandas==2.0.1+cpu"]},
    }
    enforcer.evaluate(data)


def test_loose_pinning_fails(enforcer: PolicyEnforcer) -> None:
    """Test that 'pandas>=2.0.1' is rejected."""
    data = {
        "metadata": {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "version": "1.0.0",
            "name": "A",
            "author": "B",
            "created_at": "2023-01-01",
        },
        "interface": {"inputs": {}, "outputs": {}},
        "topology": {
            "steps": [{"id": "s1", "description": "valid desc"}],
            "model_config": {"model": "m", "temperature": 0.1},
        },
        "dependencies": {"tools": [], "libraries": ["pandas>=2.0.1"]},
    }
    with pytest.raises(PolicyViolationError) as excinfo:
        enforcer.evaluate(data)
    assert "must be strictly pinned" in str(excinfo.value.violations)
