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

from coreason_manifest.definitions import (
    AgentDefinition,
    AgentRuntimeConfig,
    DeploymentConfig,
    Protocol,
)
from coreason_manifest.definitions.agent import (
    AgentCapability,
    AgentDependencies,
    AgentMetadata,
    CapabilityType,
    ModelConfig,
)


def test_deployment_defaults() -> None:
    config = DeploymentConfig()
    assert config.protocol == Protocol.HTTP_SSE
    assert config.port == 8000
    assert config.route_prefix == "/assist"
    assert config.scaling_min_instances == 0
    assert config.scaling_max_instances == 1
    assert config.timeout_seconds == 60
    assert config.env_vars == {}


def test_deployment_custom_values() -> None:
    config = DeploymentConfig(
        protocol=Protocol.GRPC,
        port=9090,
        route_prefix="/api/v1/agent",
        scaling_min_instances=2,
        scaling_max_instances=10,
        timeout_seconds=120,
        env_vars={"KEY": "VALUE"},
    )
    assert config.protocol == Protocol.GRPC
    assert config.port == 9090
    assert config.route_prefix == "/api/v1/agent"
    assert config.scaling_min_instances == 2
    assert config.scaling_max_instances == 10
    assert config.timeout_seconds == 120
    assert config.env_vars == {"KEY": "VALUE"}


def test_agent_definition_with_deployment() -> None:
    agent = AgentDefinition(
        metadata=AgentMetadata(
            id=uuid4(),
            version="1.0.0",
            name="Test Agent",
            author="Tester",
            created_at=datetime.now(timezone.utc),
        ),
        capabilities=[
            AgentCapability(
                name="chat",
                type=CapabilityType.ATOMIC,
                description="Chat capability",
                inputs={"type": "object"},
                outputs={"type": "object"},
            )
        ],
        config=AgentRuntimeConfig(
            llm_config=ModelConfig(
                model="gpt-4",
                temperature=0.7,
                system_prompt="You are a helper.",
            )
        ),
        dependencies=AgentDependencies(),
        integrity_hash="a" * 64,
        deployment=DeploymentConfig(port=8080),
    )

    assert agent.deployment is not None
    assert agent.deployment.port == 8080
    assert agent.deployment.protocol == Protocol.HTTP_SSE


def test_agent_definition_without_deployment() -> None:
    agent = AgentDefinition(
        metadata=AgentMetadata(
            id=uuid4(),
            version="1.0.0",
            name="Test Agent",
            author="Tester",
            created_at=datetime.now(timezone.utc),
        ),
        capabilities=[
            AgentCapability(
                name="chat",
                type=CapabilityType.ATOMIC,
                description="Chat capability",
                inputs={"type": "object"},
                outputs={"type": "object"},
            )
        ],
        config=AgentRuntimeConfig(
            llm_config=ModelConfig(
                model="gpt-4",
                temperature=0.7,
                system_prompt="You are a helper.",
            )
        ),
        dependencies=AgentDependencies(),
        integrity_hash="a" * 64,
    )

    assert agent.deployment is None
