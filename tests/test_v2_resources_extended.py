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

from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    PolicyConfig,
    RecipeDefinition,
    RecipeInterface,
    TaskSequence,
)
from coreason_manifest.spec.v2.resources import (
    McpServerRequirement,
    RuntimeEnvironment,
    ToolDefinition,
)

# -----------------------------------------------------------------------------
# 1. ToolDefinition Edge Cases & Complexity
# -----------------------------------------------------------------------------


def test_tool_definition_empty_params() -> None:
    """Edge Case: ToolDefinition with empty parameters dict should be valid."""
    tool = ToolDefinition(name="simple_tool", description="Does nothing", parameters={})
    assert tool.parameters == {}
    assert tool.is_consequential is False  # Default


def test_tool_definition_complex_nested_params() -> None:
    """Complex Case: deeply nested JSON schema in parameters."""
    complex_schema = {
        "type": "object",
        "properties": {
            "config": {"type": "object", "properties": {"nested": {"type": "array", "items": {"type": "string"}}}}
        },
    }
    tool = ToolDefinition(
        name="complex_tool",
        description="Complex params",
        parameters=complex_schema,
        is_consequential=True,
        namespace="complex-ns",
    )

    # Verify structure matches input
    assert tool.parameters["properties"]["config"]["properties"]["nested"]["type"] == "array"

    # Verify serialization
    dumped = tool.model_dump(mode='json', by_alias=True, exclude_none=True)
    assert dumped["parameters"]["type"] == "object"


def test_tool_definition_validation_error() -> None:
    """Validation: Missing required fields."""
    with pytest.raises(ValidationError) as exc:
        ToolDefinition(
            # Missing name, description, parameters
            is_consequential=True
        )  # type: ignore[call-arg]

    errors = exc.value.errors()
    missing_fields = [e["loc"][0] for e in errors]
    assert "name" in missing_fields
    assert "description" in missing_fields
    assert "parameters" in missing_fields


# -----------------------------------------------------------------------------
# 2. RuntimeEnvironment & McpServerRequirement Edge Cases
# -----------------------------------------------------------------------------


def test_mcp_requirement_empty_tools() -> None:
    """Edge Case: Server requirement with no specific tools."""
    req = McpServerRequirement(name="brave")
    assert req.name == "brave"
    assert req.required_tools == []
    assert req.version_constraint is None


def test_runtime_env_multiple_servers() -> None:
    """Complex Case: Multiple servers with mixed constraints."""
    req1 = McpServerRequirement(name="github", required_tools=["create_issue"], version_constraint=">=1.0.0")
    req2 = McpServerRequirement(name="slack", required_tools=[])

    env = RuntimeEnvironment(mcp_servers=[req1, req2], python_version="3.11")

    assert len(env.mcp_servers) == 2
    assert env.mcp_servers[0].name == "github"
    assert env.mcp_servers[1].name == "slack"


def test_runtime_env_defaults() -> None:
    """Edge Case: Default initialization."""
    env = RuntimeEnvironment()
    assert env.mcp_servers == []
    assert env.python_version == "3.12"  # Check default value


# -----------------------------------------------------------------------------
# 3. PolicyConfig & RecipeDefinition Integration
# -----------------------------------------------------------------------------


def test_policy_config_defaults() -> None:
    """Edge Case: PolicyConfig defaults."""
    policy = PolicyConfig()
    assert policy.allowed_mcp_servers == []
    assert policy.sensitive_tools == []


def test_policy_config_explicit_empty_list() -> None:
    """Edge Case: Explicit empty list vs None (Pydantic handles None -> list if default factory?).
    Actually fields are usually required or have defaults.
    """
    policy = PolicyConfig(allowed_mcp_servers=[])
    assert policy.allowed_mcp_servers == []


def test_full_recipe_integration() -> None:
    """Complex Case: Full integration of Recipe with Environment and Policy."""

    # 1. Environment
    mcp_req = McpServerRequirement(name="github", required_tools=["create_issue"])
    env = RuntimeEnvironment(mcp_servers=[mcp_req])

    # 2. Policy
    policy = PolicyConfig(allowed_mcp_servers=["github"], sensitive_tools=["github.delete_repo"], max_retries=5)

    # 3. Topology (Minimal)
    node = AgentNode(id="step1", agent_ref="agent-v1", inputs_map={"q": "q"})

    # 4. Recipe
    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Integration Test Recipe"),
        interface=RecipeInterface(inputs={"q": {"type": "string"}}),
        environment=env,
        policy=policy,
        topology=TaskSequence(steps=[node]).to_graph(),
    )

    # Assertions
    assert recipe.environment is not None
    assert recipe.environment.mcp_servers[0].name == "github"

    assert recipe.policy is not None
    assert "github" in recipe.policy.allowed_mcp_servers
    assert recipe.policy.max_retries == 5

    # Test Serialization
    dumped = recipe.model_dump(mode='json', by_alias=True, exclude_none=True)
    assert dumped["environment"]["mcp_servers"][0]["name"] == "github"
    assert dumped["policy"]["allowed_mcp_servers"] == ["github"]


def test_recipe_hashing() -> None:
    """Verify hash computation works with new fields."""
    env = RuntimeEnvironment(mcp_servers=[McpServerRequirement(name="github")])
    recipe1 = RecipeDefinition(
        metadata=ManifestMetadata(name="Recipe"),
        interface=RecipeInterface(),
        topology=TaskSequence(steps=[AgentNode(id="a", agent_ref="b")]).to_graph(),
        environment=env,
    )

    # Create identical recipe
    recipe2 = RecipeDefinition(
        metadata=ManifestMetadata(name="Recipe"),
        interface=RecipeInterface(),
        topology=TaskSequence(steps=[AgentNode(id="a", agent_ref="b")]).to_graph(),
        environment=env.model_copy(),
    )

    assert recipe1.compute_hash() == recipe2.compute_hash()

    # Create different recipe (different env)
    env_diff = RuntimeEnvironment(mcp_servers=[McpServerRequirement(name="gitlab")])
    recipe3 = RecipeDefinition(
        metadata=ManifestMetadata(name="Recipe"),
        interface=RecipeInterface(),
        topology=TaskSequence(steps=[AgentNode(id="a", agent_ref="b")]).to_graph(),
        environment=env_diff,
    )

    assert recipe1.compute_hash() != recipe3.compute_hash()
