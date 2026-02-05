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

from coreason_manifest import AdapterHints, AgentDefinition, AgentRuntimeConfig


def test_adapter_hint_serialization():
    """Test that AdapterHints correctly serializes settings."""
    settings = {"recursion_limit": 50, "experimental": True}
    hint = AdapterHints(framework="langgraph", adapter_type="ReActNode", settings=settings)

    dumped = hint.dump()
    assert dumped["framework"] == "langgraph"
    assert dumped["adapter_type"] == "ReActNode"
    assert dumped["settings"] == settings


def test_runtime_config_integration():
    """Test integration of AgentRuntimeConfig with AgentDefinition."""
    langgraph_hint = AdapterHints(
        framework="langgraph", adapter_type="ReActNode", settings={"recursion_limit": 50}
    )
    autogen_hint = AdapterHints(
        framework="autogen", adapter_type="AssistantAgent", settings={"llm_config": {"seed": 42}}
    )

    runtime_config = AgentRuntimeConfig(adapters=[langgraph_hint, autogen_hint])

    agent = AgentDefinition(
        id="agent-1",
        name="Test Agent",
        role="Tester",
        goal="Test integration",
        runtime=runtime_config,
    )

    assert agent.runtime is not None
    assert len(agent.runtime.adapters) == 2
    assert agent.runtime.adapters[0].framework == "langgraph"
    assert agent.runtime.adapters[1].framework == "autogen"


def test_immutability():
    """Test that models are immutable."""
    hint = AdapterHints(framework="langgraph", adapter_type="ReActNode")

    with pytest.raises(ValidationError):
        hint.settings = {"new": "value"}  # type: ignore

    runtime_config = AgentRuntimeConfig(adapters=[hint])

    with pytest.raises(ValidationError):
        runtime_config.adapters = []  # type: ignore

    agent = AgentDefinition(
        id="agent-1",
        name="Test Agent",
        role="Tester",
        goal="Test immutability",
        runtime=runtime_config,
    )

    with pytest.raises(ValidationError):
        agent.runtime.adapters = []  # type: ignore
