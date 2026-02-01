# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import uuid

import pytest
from coreason_manifest.definitions.agent import (
    AgentDefinition,
    AgentDependencies,
    ModelConfig,
)
from pydantic import ValidationError


def test_model_config_immutability() -> None:
    """Test that ModelConfig is immutable."""
    config = ModelConfig(model="gpt-4", temperature=0.7)

    with pytest.raises(ValidationError):
        config.temperature = 0.8  # type: ignore[misc]

    with pytest.raises(ValidationError):
        config.model = "gpt-3.5"  # type: ignore[misc]


def test_agent_definition_immutability() -> None:
    """Test that AgentDefinition (root) is immutable."""
    agent_data = {
        "metadata": {
            "id": str(uuid.uuid4()),
            "version": "1.0.0",
            "name": "Immutable Agent",
            "author": "Tester",
            "created_at": "2023-10-27T10:00:00Z",
        },
        "interface": {"inputs": {}, "outputs": {}},
        "config": {
            "nodes": [],
            "edges": [],
            "entry_point": "start",
            "model_config": {"model": "gpt-4", "temperature": 0.7},
            "system_prompt": "Dummy",
        },
        "dependencies": {"tools": [], "libraries": []},
        "integrity_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    }

    agent = AgentDefinition(**agent_data)

    # Try to modify a direct field
    with pytest.raises(ValidationError):
        agent.integrity_hash = "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"  # type: ignore[misc]

    # Try to replace a nested model
    with pytest.raises(ValidationError):
        agent.dependencies = AgentDependencies(tools=[], libraries=[])  # type: ignore[misc]


def test_nested_model_immutability() -> None:
    """Test that nested models accessed through the root are immutable."""
    agent_data = {
        "metadata": {
            "id": str(uuid.uuid4()),
            "version": "1.0.0",
            "name": "Immutable Agent",
            "author": "Tester",
            "created_at": "2023-10-27T10:00:00Z",
        },
        "interface": {"inputs": {}, "outputs": {}},
        "config": {
            "nodes": [],
            "edges": [],
            "entry_point": "start",
            "model_config": {"model": "gpt-4", "temperature": 0.7},
            "system_prompt": "Dummy",
        },
        "dependencies": {"tools": [], "libraries": []},
        "integrity_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    }

    agent = AgentDefinition(**agent_data)

    # Try to modify a field on a nested object
    with pytest.raises(ValidationError):
        agent.config.llm_config.temperature = 0.9  # type: ignore[misc]

    with pytest.raises(ValidationError):
        agent.metadata.name = "New Name"  # type: ignore[misc]
