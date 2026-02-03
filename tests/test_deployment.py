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
        config.scaling_strategy = "dedicated"

    with pytest.raises(ValidationError):
        config.resources.cpu_cores = 2.0
