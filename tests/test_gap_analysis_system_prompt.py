import uuid

import pytest
from pydantic import ValidationError

from coreason_manifest.definitions.agent import AgentDefinition, AgentRuntimeConfig, ModelConfig


def test_system_prompt_in_runtime_config() -> None:
    """Verify that system_prompt exists in AgentRuntimeConfig and can be set."""
    llm_config = ModelConfig(model="gpt-4", temperature=0.7)

    config = AgentRuntimeConfig(llm_config=llm_config, system_prompt="You are a global agent.")

    assert config.system_prompt == "You are a global agent."
    assert config.llm_config.system_prompt is None


def test_atomic_agent_requires_system_prompt_if_published() -> None:
    """Verify that Atomic Agents (no nodes) require a system prompt only when published."""
    llm_config = ModelConfig(model="gpt-4", temperature=0.7)

    # RuntimeConfig does not validate anymore
    config = AgentRuntimeConfig(
        llm_config=llm_config,
        nodes=[],
    )
    assert config.system_prompt is None

    # AgentDefinition DOES validate if PUBLISHED
    data = {
        "metadata": {
            "id": str(uuid.uuid4()),
            "version": "1.0.0",
            "name": "Atomic Agent",
            "author": "Me",
            "created_at": "2023-10-27T10:00:00Z",
        },
        "capabilities": [{"name": "default", "type": "atomic", "description": "Default", "inputs": {}, "outputs": {}}],
        "config": config,
        "dependencies": {},
        "status": "published",
        "integrity_hash": "a" * 64,
    }

    with pytest.raises(ValidationError) as exc:
        AgentDefinition(**data)
    assert "Atomic Agents require a system_prompt" in str(exc.value)


def test_atomic_agent_valid_with_model_prompt() -> None:
    """Verify that Atomic Agents are valid if prompt is in model_config."""
    llm_config = ModelConfig(model="gpt-4", temperature=0.7, system_prompt="Model prompt")

    config = AgentRuntimeConfig(llm_config=llm_config, nodes=[])

    assert config.llm_config.system_prompt == "Model prompt"
    assert config.system_prompt is None


def test_graph_agent_does_not_require_system_prompt() -> None:
    """Verify that Graph Agents (with nodes) do NOT strictly require a global system prompt."""
    from coreason_manifest.definitions.topology import LogicNode

    llm_config = ModelConfig(model="gpt-4", temperature=0.7)
    nodes = [LogicNode(id="n1", code="pass")]

    # Validation requires entry_point for graph
    config = AgentRuntimeConfig(llm_config=llm_config, nodes=nodes, entry_point="n1")

    assert config.system_prompt is None
    # Should not raise validation error
