# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from coreason_manifest.definitions import (
    AgentDefinition,
    DeploymentConfig,
    ResourceLimits,
    SecretReference,
)


def test_deployment_serialization() -> None:
    """Test serialization of a full DeploymentConfig."""
    config = DeploymentConfig(
        env_vars=[
            SecretReference(key="OPENAI_API_KEY", description="LLM Key"),
            SecretReference(key="DB_PASS", description="Database Password", required=False, provider_hint="vault"),
        ],
        resources=ResourceLimits(cpu_cores=2.0, memory_mb=2048, timeout_seconds=120),
        scaling_strategy="dedicated",
        concurrency_limit=50,
    )

    dumped = config.dump()
    assert dumped["scaling_strategy"] == "dedicated"
    assert dumped["concurrency_limit"] == 50
    assert len(dumped["env_vars"]) == 2
    assert dumped["resources"]["cpu_cores"] == 2.0


def test_agent_definition_parsing() -> None:
    """Verify that AgentDefinition correctly parses the deployment field."""
    agent_data = {
        "metadata": {
            "id": str(uuid4()),
            "version": "1.0.0",
            "name": "Test Agent",
            "author": "Tester",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        "capabilities": [
            {
                "name": "chat",
                "type": "atomic",
                "description": "Chat capability",
                "inputs": {"type": "object"},
                "outputs": {"type": "object"},
            }
        ],
        "config": {
            "model_config": {
                "model": "gpt-4",
                "temperature": 0.7,
                "system_prompt": "You are a helper.",
            }
        },
        "dependencies": {},
        "deployment": {
            "env_vars": [{"key": "API_KEY", "description": "Key"}],
            "resources": {"cpu_cores": 1.0, "memory_mb": 512},
        },
        "integrity_hash": "a" * 64,
    }

    agent = AgentDefinition.model_validate(agent_data)
    assert agent.deployment is not None
    assert len(agent.deployment.env_vars) == 1
    assert agent.deployment.env_vars[0].key == "API_KEY"
    assert agent.deployment.resources is not None
    assert agent.deployment.resources.cpu_cores == 1.0


def test_deployment_immutability() -> None:
    """Verify immutability."""
    config = DeploymentConfig(
        env_vars=[SecretReference(key="KEY", description="Desc")],
        resources=ResourceLimits(cpu_cores=1.0),
    )

    with pytest.raises(ValidationError):
        config.scaling_strategy = "dedicated"  # type: ignore[misc]

    # Ensure resources is not None for mypy before attempting assignment
    assert config.resources is not None
    with pytest.raises(ValidationError):
        config.resources.cpu_cores = 2.0  # type: ignore[misc]


def test_deployment_edge_cases() -> None:
    """Test edge cases: empty lists, defaults, and None values."""
    # 1. Empty env_vars
    config = DeploymentConfig(env_vars=[])
    assert config.env_vars == []
    assert config.resources is None
    assert config.scaling_strategy == "serverless"  # Default
    assert config.concurrency_limit is None

    # 2. Resource limits with mixed fields
    limits = ResourceLimits(timeout_seconds=300)
    assert limits.cpu_cores is None
    assert limits.memory_mb is None
    assert limits.timeout_seconds == 300

    # 3. SecretReference defaults
    secret = SecretReference(key="TEST_KEY", description="Test Description")
    assert secret.required is True  # Default
    assert secret.provider_hint is None


def test_deployment_complex() -> None:
    """Test complex scenarios: maximal nested configuration."""
    config = DeploymentConfig(
        env_vars=[
            SecretReference(key="MANDATORY", description="Must have", required=True),
            SecretReference(
                key="OPTIONAL_VAULT", description="Maybe", required=False, provider_hint="aws-secrets-manager"
            ),
            SecretReference(key="LEGACY", description="Env var", provider_hint="env"),
        ],
        resources=ResourceLimits(
            cpu_cores=4.5,
            memory_mb=16384,
            timeout_seconds=3600,
        ),
        scaling_strategy="dedicated",
        concurrency_limit=1000,
    )

    # Serialize
    json_str = config.to_json()
    assert "MANDATORY" in json_str
    assert "OPTIONAL_VAULT" in json_str
    assert "dedicated" in json_str
    assert "16384" in json_str

    # Deserialize back
    restored = DeploymentConfig.model_validate_json(json_str)
    assert restored == config
    assert len(restored.env_vars) == 3
    assert restored.resources is not None
    assert restored.resources.cpu_cores == 4.5
