# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest


from coreason_manifest.spec.v2.agent import (
    CognitiveProfile,
    ComponentPriority,
    ContextDependency,
)
from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    GraphTopology,
    PolicyConfig,
    RecipeDefinition,
    RecipeInterface,
)


def test_cognitive_profile_creation() -> None:
    """Test creating a CognitiveProfile."""
    profile = CognitiveProfile(
        role="data_analyst",
        reasoning_mode="analytical",
        knowledge_contexts=[ContextDependency(name="sql_knowledge", priority=ComponentPriority.HIGH)],
        task_primitive="extract_metrics",
    )
    assert profile.role == "data_analyst"
    assert profile.reasoning_mode == "analytical"
    assert len(profile.knowledge_contexts) == 1
    assert profile.knowledge_contexts[0].name == "sql_knowledge"
    assert profile.knowledge_contexts[0].priority == ComponentPriority.HIGH
    assert profile.task_primitive == "extract_metrics"


def test_agent_node_with_construct() -> None:
    """Test AgentNode with inline construct."""
    profile = CognitiveProfile(role="assistant")
    node = AgentNode(
        id="agent-1",
        cognitive_profile=profile,
        agent_ref=None,  # Explicitly None
    )
    assert node.cognitive_profile == profile
    assert node.agent_ref is None


def test_agent_node_construct_overrides_agent_ref_in_logic() -> None:
    """
    The spec says 'If provided, this overrides agent_ref lookup'.
    We just test that both can be present in the object,
    and it's up to the runtime to prioritize.
    """
    profile = CognitiveProfile(role="assistant")
    node = AgentNode(
        id="agent-1",
        cognitive_profile=profile,
        agent_ref="some-catalog-id",
    )
    assert node.cognitive_profile == profile
    assert node.agent_ref == "some-catalog-id"


def test_policy_config_token_budget() -> None:
    """Test new token_budget field in PolicyConfig."""
    policy = PolicyConfig(
        max_retries=3,
        token_budget=10000,
        budget_cap_usd=5.0,
    )
    assert policy.token_budget == 10000
    assert policy.budget_cap_usd == 5.0


def test_full_recipe_with_construct() -> None:
    """Test full recipe serialization with construct."""
    profile = CognitiveProfile(
        role="writer",
        knowledge_contexts=[ContextDependency(name="style_guide", priority=ComponentPriority.CRITICAL)],
    )

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Construct Recipe"),
        interface=RecipeInterface(),
        policy=PolicyConfig(token_budget=5000),
        topology=GraphTopology(
            nodes=[
                AgentNode(id="writer", cognitive_profile=profile),
            ],
            edges=[],
            entry_point="writer",
        ),
    )

    # Roundtrip
    json_str = recipe.model_dump_json(by_alias=True, exclude_none=True)
    loaded = RecipeDefinition.model_validate_json(json_str)

    node = loaded.topology.nodes[0]
    assert isinstance(node, AgentNode)
    assert node.cognitive_profile is not None
    assert node.cognitive_profile.role == "writer"
    assert node.cognitive_profile.knowledge_contexts[0].priority == ComponentPriority.CRITICAL

    assert loaded.policy is not None
    assert loaded.policy.token_budget == 5000
