# Copyright (c) 2025 CoReason, Inc.

from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.recipe import AgentNode, GraphEdge, GraphTopology, RecipeDefinition, RecipeInterface
from coreason_manifest.spec.v2.resources import ComplianceTier, ModelSelectionPolicy, RoutingStrategy


def test_complex_recipe_mixed_policies() -> None:
    """Test a recipe with mixed policy types: global default, inline override, and string override."""

    # 1. Define Global Default
    default_policy = ModelSelectionPolicy(strategy=RoutingStrategy.PRIORITY, compliance=[ComplianceTier.STANDARD])

    # 2. Define Nodes

    # Node 1: Inherits default (policy is None)
    node1 = AgentNode(id="node-1", agent_ref="agent-1")

    # Node 2: Overrides with inline policy (high performance)
    node2_policy = ModelSelectionPolicy(
        strategy=RoutingStrategy.PERFORMANCE, min_context_window=32000, provider_whitelist=["openai", "anthropic"]
    )
    node2 = AgentNode(id="node-2", agent_ref="agent-2", model_policy=node2_policy)

    # Node 3: Overrides with string ID (legacy/specific model)
    node3 = AgentNode(id="node-3", agent_ref="agent-3", model_policy="gpt-4-turbo-preview")

    # 3. Create Recipe
    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Complex Routing Recipe"),
        interface=RecipeInterface(),
        topology=GraphTopology(
            nodes=[node1, node2, node3],
            edges=[GraphEdge(source="node-1", target="node-2"), GraphEdge(source="node-2", target="node-3")],
            entry_point="node-1",
        ),
        default_model_policy=default_policy,
    )

    # 4. Verify Structure

    # Check Default
    assert recipe.default_model_policy is not None
    assert recipe.default_model_policy.strategy == RoutingStrategy.PRIORITY

    # Check Node 1 (None policy)
    n1 = next(n for n in recipe.topology.nodes if n.id == "node-1")
    assert isinstance(n1, AgentNode)
    assert n1.model_policy is None

    # Check Node 2 (Inline policy)
    n2 = next(n for n in recipe.topology.nodes if n.id == "node-2")
    assert isinstance(n2, AgentNode)
    assert isinstance(n2.model_policy, ModelSelectionPolicy)
    assert n2.model_policy.strategy == RoutingStrategy.PERFORMANCE
    assert n2.model_policy.min_context_window == 32000

    # Check Node 3 (String policy)
    n3 = next(n for n in recipe.topology.nodes if n.id == "node-3")
    assert isinstance(n3, AgentNode)
    assert n3.model_policy == "gpt-4-turbo-preview"


def test_large_provider_whitelist() -> None:
    """Test handling of a large list of providers."""
    providers = [f"provider-{i}" for i in range(100)]
    policy = ModelSelectionPolicy(strategy=RoutingStrategy.ROUND_ROBIN, provider_whitelist=providers)
    assert len(policy.provider_whitelist) == 100
    assert "provider-50" in policy.provider_whitelist


def test_boundary_values() -> None:
    """Test boundary values for numeric constraints."""
    policy = ModelSelectionPolicy(strategy=RoutingStrategy.LOWEST_COST, min_context_window=0, max_input_cost_per_m=0.0)
    assert policy.min_context_window == 0
    assert policy.max_input_cost_per_m == 0.0

    # Max integer validation handled by Pydantic/Python int size,
    # but let's test a reasonable large number
    large_window = 1_000_000_000
    policy_large = ModelSelectionPolicy(min_context_window=large_window)
    assert policy_large.min_context_window == large_window


def test_redundant_policy_structure() -> None:
    """Test creating identical policies multiple times (redundancy check)."""
    p1 = ModelSelectionPolicy(strategy=RoutingStrategy.PERFORMANCE)
    p2 = ModelSelectionPolicy(strategy=RoutingStrategy.PERFORMANCE)

    assert p1 == p2  # Pydantic models with same data should be equal

    node1 = AgentNode(id="n1", agent_ref="a1", model_policy=p1)
    node2 = AgentNode(id="n2", agent_ref="a1", model_policy=p2)

    assert node1.model_policy == node2.model_policy
