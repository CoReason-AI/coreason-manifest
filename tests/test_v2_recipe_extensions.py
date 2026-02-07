# Copyright (c) 2025 CoReason, Inc.

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    GraphTopology,
    PolicyConfig,
    RecipeDefinition,
    RecipeInterface,
    StateDefinition,
)


def test_recipe_interface_defaults() -> None:
    """Test that RecipeInterface defaults to empty dicts."""
    interface = RecipeInterface()
    assert interface.inputs == {}
    assert interface.outputs == {}


def test_recipe_interface_validation() -> None:
    """Test RecipeInterface validation."""
    interface = RecipeInterface(
        inputs={"arg": {"type": "string"}},
        outputs={"result": {"type": "integer"}}
    )
    assert interface.inputs["arg"]["type"] == "string"
    assert interface.outputs["result"]["type"] == "integer"

    # Test extra fields forbidden
    with pytest.raises(ValidationError):
        RecipeInterface(extra_field="invalid")  # type: ignore[call-arg]


def test_state_definition_validation() -> None:
    """Test StateDefinition validation."""
    # Test valid
    state = StateDefinition(
        properties={"count": {"type": "integer"}},
        persistence="redis"
    )
    assert state.persistence == "redis"
    assert state.properties["count"]["type"] == "integer"

    # Test default persistence
    state_default = StateDefinition(properties={})
    assert state_default.persistence == "ephemeral"

    # Test invalid persistence
    with pytest.raises(ValidationError):
        StateDefinition(properties={}, persistence="invalid_mode")

    # Test missing properties
    with pytest.raises(ValidationError):
        StateDefinition(persistence="ephemeral")  # type: ignore[call-arg]


def test_policy_config_defaults() -> None:
    """Test PolicyConfig defaults."""
    policy = PolicyConfig()
    assert policy.max_retries == 0
    assert policy.timeout_seconds is None
    assert policy.execution_mode == "sequential"


def test_policy_config_validation() -> None:
    """Test PolicyConfig validation."""
    policy = PolicyConfig(
        max_retries=5,
        timeout_seconds=30,
        execution_mode="parallel"
    )
    assert policy.max_retries == 5
    assert policy.timeout_seconds == 30
    assert policy.execution_mode == "parallel"

    # Test invalid execution_mode
    with pytest.raises(ValidationError):
        PolicyConfig(execution_mode="random")


def test_full_recipe_with_extensions() -> None:
    """Test RecipeDefinition with all new components."""
    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Extended Recipe"),
        interface=RecipeInterface(
            inputs={"query": {"type": "string"}},
            outputs={"answer": {"type": "string"}}
        ),
        state=StateDefinition(
            properties={"memory": {"type": "array"}},
            persistence="postgres"
        ),
        policy=PolicyConfig(
            max_retries=3,
            timeout_seconds=60
        ),
        topology=GraphTopology(
            nodes=[
                AgentNode(id="start", agent_ref="agent-1"),
            ],
            edges=[],
            entry_point="start",
        ),
    )

    assert recipe.interface.inputs["query"]["type"] == "string"
    assert recipe.state is not None
    assert recipe.state.persistence == "postgres"
    assert recipe.policy is not None
    assert recipe.policy.max_retries == 3

    # Test serialization
    dumped = recipe.dump()
    assert dumped["interface"]["inputs"]["query"]["type"] == "string"
    assert dumped["state"]["persistence"] == "postgres"
    assert dumped["policy"]["max_retries"] == 3
