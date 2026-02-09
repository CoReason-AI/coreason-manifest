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

from coreason_manifest.spec.v2.agent import (
    CognitiveProfile,
    ComponentPriority,
    ContextDependency,
)
from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    GraphEdge,
    GraphTopology,
    PolicyConfig,
    RecipeDefinition,
    RecipeInterface,
    RecipeStatus,
)

# ==========================================
# Edge Cases
# ==========================================


def test_agent_node_no_ref_no_construct() -> None:
    """
    Test AgentNode with neither agent_ref nor construct.
    Technically valid by schema (both Optional), but Runtime should handle it.
    """
    node = AgentNode(id="ghost-agent")
    assert node.agent_ref is None
    assert node.cognitive_profile is None
    # This node is essentially empty, waiting for runtime logic or injection.


def test_cognitive_profile_minimal() -> None:
    """Test CognitiveProfile with only required fields."""
    profile = CognitiveProfile(role="observer")
    assert profile.role == "observer"
    assert profile.reasoning_mode == "standard"  # Default
    assert profile.knowledge_contexts == []  # Default
    assert profile.task_primitive is None  # Default


def test_context_dependency_minimal() -> None:
    """Test ContextDependency with defaults."""
    dep = ContextDependency(name="basic_context")
    assert dep.name == "basic_context"
    assert dep.priority == ComponentPriority.MEDIUM  # Default
    assert dep.parameters == {}  # Default


def test_policy_config_extreme_values() -> None:
    """Test PolicyConfig with extreme/boundary values."""
    policy = PolicyConfig(
        token_budget=0,  # Zero budget
        budget_cap_usd=999999.99,  # Large budget
    )
    assert policy.token_budget == 0
    assert policy.budget_cap_usd == 999999.99

    policy_none = PolicyConfig(token_budget=None)
    assert policy_none.token_budget is None


# ==========================================
# Complex Cases
# ==========================================


def test_hybrid_recipe_topology() -> None:
    """
    Test a graph that mixes:
    1. Agent with inline construct.
    2. Agent with semantic reference.
    3. Agent with concrete reference.
    """
    # 1. Inline Agent
    node_inline = AgentNode(
        id="step-1-inline", cognitive_profile=CognitiveProfile(role="analyst", task_primitive="analyze")
    )

    # 2. Concrete Agent
    node_concrete = AgentNode(id="step-2-concrete", agent_ref="summarizer-v1")

    # 3. Hybrid (Both - construct takes precedence logic wise, but both exist in model)
    node_hybrid = AgentNode(
        id="step-3-hybrid", cognitive_profile=CognitiveProfile(role="reviewer"), agent_ref="reviewer-base-v1"
    )

    topology = GraphTopology(
        nodes=[node_inline, node_concrete, node_hybrid],
        edges=[
            GraphEdge(source="step-1-inline", target="step-2-concrete"),
            GraphEdge(source="step-2-concrete", target="step-3-hybrid"),
        ],
        entry_point="step-1-inline",
    )

    assert len(topology.nodes) == 3
    assert topology.verify_completeness()


def test_complex_context_dependencies() -> None:
    """Test a profile with many context dependencies and parameters."""
    profile = CognitiveProfile(
        role="legal_expert",
        knowledge_contexts=[
            ContextDependency(name="constitution", priority=ComponentPriority.CRITICAL),
            ContextDependency(
                name="case_law_2024",
                priority=ComponentPriority.HIGH,
                parameters={"year": 2024, "region": "US"},
            ),
            ContextDependency(
                name="internal_memos",
                priority=ComponentPriority.LOW,
                parameters={"tags": ["confidential"]},
            ),
        ],
    )

    assert len(profile.knowledge_contexts) == 3
    # Verify sorting or access
    critical = [c for c in profile.knowledge_contexts if c.priority == ComponentPriority.CRITICAL]
    assert len(critical) == 1
    assert critical[0].name == "constitution"


def test_full_recipe_serialization_roundtrip_complex() -> None:
    """Test full serialization of a complex recipe with new features."""
    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Complex Assembler Recipe"),
        interface=RecipeInterface(),
        policy=PolicyConfig(token_budget=128000, sensitive_tools=["exec_code"]),
        topology=GraphTopology(
            nodes=[
                AgentNode(
                    id="start",
                    cognitive_profile=CognitiveProfile(
                        role="orchestrator",
                        reasoning_mode="six_hats",
                        knowledge_contexts=[ContextDependency(name="project_specs", priority=ComponentPriority.HIGH)],
                    ),
                ),
                AgentNode(id="end", agent_ref="finalizer"),
            ],
            edges=[GraphEdge(source="start", target="end")],
            entry_point="start",
        ),
    )

    # Dump
    json_str = recipe.model_dump_json(by_alias=True, exclude_none=True)

    # Load
    loaded = RecipeDefinition.model_validate_json(json_str)

    # Verify
    assert loaded.policy is not None
    assert loaded.policy.token_budget == 128000

    start_node = next(n for n in loaded.topology.nodes if n.id == "start")
    assert isinstance(start_node, AgentNode)
    assert start_node.cognitive_profile is not None
    assert start_node.cognitive_profile.reasoning_mode == "six_hats"


def test_lifecycle_validation_incomplete_node() -> None:
    """Test that PUBLISHED status rejects nodes without agent_ref or construct."""
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Incomplete Recipe"},
        "interface": {},
        "status": RecipeStatus.PUBLISHED,
        "topology": {
            "nodes": [
                {"type": "agent", "id": "ghost"}  # missing agent_ref and construct
            ],
            "edges": [],
            "entry_point": "ghost",
        },
    }

    with pytest.raises(ValidationError) as excinfo:
        RecipeDefinition.model_validate(data)

    assert "Nodes ['ghost'] are incomplete" in str(excinfo.value)
