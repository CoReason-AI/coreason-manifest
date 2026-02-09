# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest.spec.simulation import SimulationScenario, ValidationLogic
from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.provenance import ProvenanceData, ProvenanceType
from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    CollaborationConfig,
    CollaborationMode,
    OptimizationIntent,
    PolicyConfig,
    RecipeDefinition,
    RecipeRecommendation,
    SemanticRef,
    TaskSequence,
)


def test_optimization_harvesting() -> None:
    """Verify Foundry attributes."""
    intent = OptimizationIntent(
        base_ref="old-v1",
        improvement_goal="Fix bugs",
        metric_name="faithfulness",
        teacher_model="gpt-4-turbo",
        max_demonstrations=3,
    )
    assert intent.metric_name == "faithfulness"
    assert intent.max_demonstrations == 3
    assert intent.teacher_model == "gpt-4-turbo"


def test_optimization_harvesting_defaults() -> None:
    """Verify Foundry attributes defaults."""
    intent = OptimizationIntent(
        base_ref="old-v1",
        improvement_goal="Fix bugs",
    )
    assert intent.metric_name == "exact_match"
    assert intent.teacher_model is None
    assert intent.max_demonstrations == 5


def test_collaboration_harvesting() -> None:
    """Verify Human-Layer attributes."""
    collab = CollaborationConfig(
        mode=CollaborationMode.INTERACTIVE,
        channels=["slack", "email"],
        timeout_seconds=3600,
        fallback_behavior="escalate",
    )
    assert "slack" in collab.channels
    assert collab.timeout_seconds == 3600
    assert collab.fallback_behavior == "escalate"


def test_collaboration_harvesting_defaults() -> None:
    """Verify Human-Layer attributes defaults."""
    collab = CollaborationConfig(
        mode=CollaborationMode.COMPLETION,
    )
    assert collab.channels == []
    assert collab.timeout_seconds is None
    assert collab.fallback_behavior == "fail"


def test_policy_harvesting() -> None:
    """Verify Connect attributes."""
    policy = PolicyConfig(budget_cap_usd=50.00, sensitive_tools=["buy_stock", "delete_db"])
    assert policy.budget_cap_usd == 50.0
    assert "delete_db" in policy.sensitive_tools


def test_policy_harvesting_defaults() -> None:
    """Verify Connect attributes defaults."""
    policy = PolicyConfig()
    assert policy.budget_cap_usd is None
    assert policy.sensitive_tools == []


def test_simulation_harvesting() -> None:
    """Verify Simulacrum attributes embedded in Recipe."""
    scenario = SimulationScenario(
        id="test-1", description="Basic happy path", inputs={"q": "hello"}, validation_logic=ValidationLogic.EXACT_MATCH
    )

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Test Recipe", provenance=ProvenanceData(type=ProvenanceType.HUMAN)),
        interface={},
        tests=[scenario],
        topology=TaskSequence(steps=[AgentNode(id="step-1", agent_ref="agent-1")]).to_graph(),
    )

    assert len(recipe.tests) == 1
    assert recipe.tests[0].id == "test-1"


def test_simulation_harvesting_multiple_scenarios() -> None:
    """Verify multiple Simulation attributes embedded in Recipe."""
    scenario1 = SimulationScenario(
        id="test-1", description="Scenario 1", inputs={"q": "hello"}, validation_logic=ValidationLogic.EXACT_MATCH
    )
    scenario2 = SimulationScenario(
        id="test-2", description="Scenario 2", inputs={"q": "world"}, validation_logic=ValidationLogic.FUZZY
    )

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Test Recipe", provenance=ProvenanceData(type=ProvenanceType.HUMAN)),
        interface={},
        tests=[scenario1, scenario2],
        topology=TaskSequence(steps=[AgentNode(id="step-1", agent_ref="agent-1")]).to_graph(),
    )

    assert len(recipe.tests) == 2
    assert recipe.tests[0].id == "test-1"
    assert recipe.tests[1].id == "test-2"
    assert recipe.tests[1].validation_logic == ValidationLogic.FUZZY


def test_complex_harvesting_scenario() -> None:
    """Verify a complex recipe combining all new harvesting features."""

    # 1. Optimization Intent
    opt_intent = OptimizationIntent(
        base_ref="base-agent",
        improvement_goal="Make it faster",
        metric_name="latency",
        teacher_model="claude-3-opus",
        max_demonstrations=10,
    )

    # 2. Semantic Reference using Optimization Intent
    semantic_ref = SemanticRef(
        intent="Process data",
        optimization=opt_intent,
        candidates=[RecipeRecommendation(ref="candidate-1", score=0.9, rationale="Fast", warnings=[])],
    )

    # 3. Collaboration Config
    collab_config = CollaborationConfig(
        mode=CollaborationMode.CO_EDIT,
        channels=["slack"],
        timeout_seconds=1800,
        fallback_behavior="proceed_with_default",
    )

    # 4. Agent Node with new configs
    node = AgentNode(id="processor", agent_ref=semantic_ref, collaboration=collab_config)

    # 5. Policy Config
    policy = PolicyConfig(max_retries=5, budget_cap_usd=100.0, sensitive_tools=["deployment_tool"])

    # 6. Recipe Definition
    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Complex Recipe", provenance=ProvenanceData(type=ProvenanceType.AI)),
        interface={},
        policy=policy,
        topology=TaskSequence(steps=[node]).to_graph(),
        # Note: status defaults to DRAFT, which allows SemanticRef
    )

    # Assertions
    assert recipe.policy is not None
    assert recipe.policy.budget_cap_usd == 100.0
    assert "deployment_tool" in recipe.policy.sensitive_tools

    assert len(recipe.topology.nodes) == 1
    node_chk = recipe.topology.nodes[0]
    assert isinstance(node_chk, AgentNode)
    assert isinstance(node_chk.agent_ref, SemanticRef)
    assert node_chk.agent_ref.optimization is not None
    assert node_chk.agent_ref.optimization.metric_name == "latency"
    assert node_chk.agent_ref.optimization.teacher_model == "claude-3-opus"

    assert node_chk.collaboration is not None
    assert node_chk.collaboration.fallback_behavior == "proceed_with_default"
