# Prosperity-3.0
import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from coreason_manifest.errors import PolicyViolationError
from coreason_manifest.models import (
    AgentDefinition,
    AgentDependencies,
    AgentInterface,
    AgentMetadata,
    AgentTopology,
    ModelConfig,
    Step,
)
from coreason_manifest.policy import PolicyEnforcer


# Helper to create a dummy agent definition
def create_agent_def(**kwargs):
    return AgentDefinition(
        metadata=AgentMetadata(
            id="123e4567-e89b-12d3-a456-426614174000",
            version="1.0.0",
            name="Test Agent",
            author="Tester",
            created_at="2023-10-27T10:00:00Z",
        ),
        interface=AgentInterface(inputs={}, outputs={}),
        topology=AgentTopology(steps=[Step(id="step1")], model_config=ModelConfig(model="gpt-4", temperature=0.7)),
        dependencies=AgentDependencies(tools=kwargs.get("tools", []), libraries=kwargs.get("libraries", [])),
    )


@pytest.fixture
def policy_file(tmp_path):
    p = tmp_path / "compliance.rego"
    p.write_text("""
    package compliance

    deny[msg] {
        input.dependencies.libraries[_] == "pickle"
        msg := "Security Risk: 'pickle' library is strictly forbidden."
    }
    """)
    return p


def test_policy_enforcer_init(policy_file):
    enforcer = PolicyEnforcer(policy_path=policy_file)
    assert enforcer.policy_path == policy_file


def test_policy_enforcer_init_missing_policy():
    with pytest.raises(FileNotFoundError):
        PolicyEnforcer(policy_path="non_existent.rego")


def test_evaluate_compliant(policy_file):
    # Mock subprocess.run to return empty result (no deny)
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            stdout=json.dumps({"result": [{"expressions": [{"value": []}]}]}).encode("utf-8"), returncode=0
        )

        enforcer = PolicyEnforcer(policy_path=policy_file)
        agent = create_agent_def(libraries=["requests"])
        enforcer.evaluate(agent)


def test_evaluate_violation(policy_file):
    # Mock subprocess.run to return violation
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            stdout=json.dumps(
                {"result": [{"expressions": [{"value": ["Security Risk: 'pickle' library is strictly forbidden."]}]}]}
            ).encode("utf-8"),
            returncode=0,
        )

        enforcer = PolicyEnforcer(policy_path=policy_file)
        agent = create_agent_def(libraries=["pickle"])

        with pytest.raises(PolicyViolationError) as excinfo:
            enforcer.evaluate(agent)

        assert "pickle" in excinfo.value.violations[0]


def test_evaluate_opa_execution_error(policy_file):
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, ["opa"], stderr=b"Error")

        enforcer = PolicyEnforcer(policy_path=policy_file)
        agent = create_agent_def()

        with pytest.raises(RuntimeError, match="OPA execution failed"):
            enforcer.evaluate(agent)


def test_evaluate_opa_not_found(policy_file):
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError()

        enforcer = PolicyEnforcer(policy_path=policy_file)
        agent = create_agent_def()

        with pytest.raises(RuntimeError, match="OPA binary not found"):
            enforcer.evaluate(agent)


def test_evaluate_opa_json_error(policy_file):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=b"Not JSON", returncode=0)

        enforcer = PolicyEnforcer(policy_path=policy_file)
        agent = create_agent_def()

        with pytest.raises(RuntimeError, match="Failed to parse OPA output"):
            enforcer.evaluate(agent)


# Integration test with actual OPA binary if available
@pytest.mark.skipif(not Path("tools/opa").exists(), reason="OPA binary not found at tools/opa")
def test_evaluate_integration(policy_file):
    opa_path = Path("tools/opa").resolve()
    enforcer = PolicyEnforcer(policy_path=policy_file, opa_path=opa_path)

    # Compliant
    agent_compliant = create_agent_def(libraries=["requests"])
    enforcer.evaluate(agent_compliant)

    # Violation
    agent_violation = create_agent_def(libraries=["pickle"])
    with pytest.raises(PolicyViolationError) as excinfo:
        enforcer.evaluate(agent_violation)

    assert "pickle" in excinfo.value.violations[0]
