# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import json
from typing import Any, Dict

import pytest
from pydantic import ValidationError

from coreason_manifest import AdapterHints, AgentDefinition, AgentRuntimeConfig


def test_adapter_hint_serialization() -> None:
    """Test that AdapterHints correctly serializes settings."""
    settings = {"recursion_limit": 50, "experimental": True}
    hint = AdapterHints(framework="langgraph", adapter_type="ReActNode", settings=settings)

    dumped = hint.dump()
    assert dumped["framework"] == "langgraph"
    assert dumped["adapter_type"] == "ReActNode"
    assert dumped["settings"] == settings


def test_runtime_config_integration() -> None:
    """Test integration of AgentRuntimeConfig with AgentDefinition."""
    langgraph_hint = AdapterHints(framework="langgraph", adapter_type="ReActNode", settings={"recursion_limit": 50})
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


def test_immutability() -> None:
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

    # Note: AgentDefinition fields might be mutable depending on its config,
    # but AgentRuntimeConfig fields are frozen.
    # Trying to replace the entire runtime object on the agent is allowed if AgentDefinition is not frozen,
    # but modifying the internals of the runtime object should fail.
    # AgentRuntimeConfig is frozen, so:
    with pytest.raises(ValidationError):
        agent.runtime.adapters = []  # type: ignore


# --- Edge Cases ---


def test_edge_case_empty_values() -> None:
    """Test AdapterHints with empty strings and dictionaries."""
    hint = AdapterHints(framework="", adapter_type="", settings={})
    assert hint.framework == ""
    assert hint.adapter_type == ""
    assert hint.settings == {}

    dumped = hint.dump()
    assert dumped["framework"] == ""
    assert dumped["adapter_type"] == ""
    assert dumped["settings"] == {}


def test_edge_case_nested_settings() -> None:
    """Test AdapterHints with deeply nested mixed-type settings."""
    complex_settings: Dict[str, Any] = {
        "level1": {
            "level2": [
                {"level3": "value"},
                123,
                None,
                True,
            ]
        },
        "unicode": "🤖",
        "empty_list": [],
    }
    hint = AdapterHints(framework="test", adapter_type="Deep", settings=complex_settings)

    # Verify structure is preserved in dump
    dumped = hint.dump()
    assert dumped["settings"]["level1"]["level2"][0]["level3"] == "value"
    assert dumped["settings"]["unicode"] == "🤖"

    # Verify JSON serialization works
    json_str = hint.to_json()
    loaded = json.loads(json_str)
    assert loaded["settings"]["unicode"] == "🤖"


def test_edge_case_large_payload() -> None:
    """Test serialization with a large settings payload."""
    large_list = list(range(1000))
    large_settings = {"data": large_list, "meta": "x" * 1000}
    hint = AdapterHints(framework="loadtest", adapter_type="Heavy", settings=large_settings)

    dumped = hint.dump()
    assert len(dumped["settings"]["data"]) == 1000
    assert len(dumped["settings"]["meta"]) == 1000


# --- Complex Cases ---


def test_complex_langgraph_config() -> None:
    """Test a realistic complex LangGraph configuration."""
    langgraph_settings = {
        "checkpointer": "MemorySaver",
        "interrupt_before": ["human_review"],
        "nodes": {
            "agent": {"type": "runnable", "model": "gpt-4"},
            "tools": {"type": "tool_node", "tools": ["search", "calc"]},
        },
        "edges": [
            {"from": "agent", "to": "tools", "condition": "has_tools"},
            {"from": "tools", "to": "agent"},
        ],
        "recursion_limit": 100,
    }

    hint = AdapterHints(framework="langgraph", adapter_type="CompiledGraph", settings=langgraph_settings)

    config = AgentRuntimeConfig(adapters=[hint])
    agent = AgentDefinition(id="lg-agent", name="LG Agent", role="Graph", goal="Run graph", runtime=config)

    assert agent.runtime is not None
    assert agent.runtime.adapters[0].settings["nodes"]["agent"]["model"] == "gpt-4"
    assert "human_review" in agent.runtime.adapters[0].settings["interrupt_before"]


def test_complex_redundant_adapters() -> None:
    """Test multiple adapters for the same framework (valid case)."""
    # A user might want to generate both a Node and a full Graph for the same agent
    hint_node = AdapterHints(framework="langgraph", adapter_type="Node", settings={"style": "functional"})
    hint_graph = AdapterHints(framework="langgraph", adapter_type="Graph", settings={"style": "compiled"})

    config = AgentRuntimeConfig(adapters=[hint_node, hint_graph])
    assert len(config.adapters) == 2
    assert config.adapters[0].adapter_type == "Node"
    assert config.adapters[1].adapter_type == "Graph"
