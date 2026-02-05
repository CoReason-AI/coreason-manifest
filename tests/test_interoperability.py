# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.common.interoperability import AdapterHints, AgentRuntimeConfig
from coreason_manifest.spec.v2.definitions import AgentDefinition


def test_adapter_hints_serialization() -> None:
    """Test serialization of AdapterHints."""
    hints = AdapterHints(
        target="langchain",
        version="0.1.0",
        config={"experimental": "true"},
    )
    payload = hints.dump()
    assert payload["target"] == "langchain"
    assert payload["version"] == "0.1.0"
    assert payload["config"] == {"experimental": "true"}


def test_agent_runtime_config_serialization() -> None:
    """Test serialization of AgentRuntimeConfig."""
    config = AgentRuntimeConfig(
        env_vars={"API_KEY": "secret"},
        adapter_hints=AdapterHints(target="autogen"),
    )
    payload = config.dump()
    assert payload["env_vars"] == {"API_KEY": "secret"}
    assert payload["adapter_hints"]["target"] == "autogen"


def test_immutability() -> None:
    """Test that models are frozen."""
    hints = AdapterHints(target="test")
    with pytest.raises(ValidationError):
        hints.target = "modified"  # type: ignore

    config = AgentRuntimeConfig()
    with pytest.raises(ValidationError):
        config.env_vars = {"NEW": "val"}  # type: ignore


def test_integration_with_agent_definition() -> None:
    """Test embedding RuntimeConfig in AgentDefinition."""
    agent = AgentDefinition(
        id="agent-1",
        name="Test Agent",
        role="Tester",
        goal="Test things",
        runtime=AgentRuntimeConfig(
            env_vars={"DEBUG": "1"},
        ),
    )
    payload = agent.dump()
    assert "runtime" in payload
    assert payload["runtime"]["env_vars"] == {"DEBUG": "1"}

    # Test default is None (excluded by exclude_none=True in dump())
    agent_minimal = AgentDefinition(
        id="agent-2",
        name="Minimal Agent",
        role="Tester",
        goal="Test things",
    )
    assert "runtime" not in agent_minimal.dump()
