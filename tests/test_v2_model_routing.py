# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest


from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.recipe import AgentNode, GraphTopology, RecipeDefinition, RecipeInterface
from coreason_manifest.spec.v2.resources import ComplianceTier, ModelSelectionPolicy, RoutingStrategy


def test_model_selection_policy() -> None:
    policy = ModelSelectionPolicy(
        strategy=RoutingStrategy.LOWEST_COST,
        min_context_window=16000,
        max_input_cost_per_m=10.0,
        compliance=[ComplianceTier.HIPAA],
        provider_whitelist=["azure"],
        allow_fallback=True,
    )
    assert policy.strategy == RoutingStrategy.LOWEST_COST
    assert policy.min_context_window == 16000
    assert policy.max_input_cost_per_m == 10.0
    assert ComplianceTier.HIPAA in policy.compliance
    assert "azure" in policy.provider_whitelist
    assert policy.allow_fallback is True


def test_agent_node_with_model_policy_inline() -> None:
    policy = ModelSelectionPolicy(strategy=RoutingStrategy.PERFORMANCE)
    node = AgentNode(id="agent-1", agent_ref="agent-a", model_policy=policy)
    assert isinstance(node.model_policy, ModelSelectionPolicy)
    assert node.model_policy.strategy == RoutingStrategy.PERFORMANCE


def test_agent_node_with_model_policy_ref() -> None:
    node = AgentNode(id="agent-1", agent_ref="agent-a", model_policy="gpt-4-turbo")
    assert isinstance(node.model_policy, str)
    assert node.model_policy == "gpt-4-turbo"


def test_recipe_definition_with_default_model_policy() -> None:
    policy = ModelSelectionPolicy(strategy=RoutingStrategy.ROUND_ROBIN)
    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Test Recipe"),
        interface=RecipeInterface(),
        topology=GraphTopology(nodes=[AgentNode(id="start", agent_ref="agent-1")], edges=[], entry_point="start"),
        default_model_policy=policy,
    )
    assert recipe.default_model_policy is not None
    assert recipe.default_model_policy.strategy == RoutingStrategy.ROUND_ROBIN


def test_serialization() -> None:
    policy = ModelSelectionPolicy(strategy=RoutingStrategy.LOWEST_LATENCY)
    node = AgentNode(id="agent-1", agent_ref="agent-a", model_policy=policy)
    dumped = node.model_dump(mode="json")
    assert dumped["model_policy"]["strategy"] == "lowest_latency"

    loaded = AgentNode.model_validate(dumped)
    assert isinstance(loaded.model_policy, ModelSelectionPolicy)
    assert loaded.model_policy.strategy == RoutingStrategy.LOWEST_LATENCY
