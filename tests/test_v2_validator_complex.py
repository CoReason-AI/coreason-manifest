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

from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.evaluation import EvaluationProfile, SuccessCriterion
from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    EvaluatorNode,
    FailureBehavior,
    GraphTopology,
    HumanNode,
    RecipeDefinition,
    RecipeInterface,
    RecipeStatus,
    RecoveryConfig,
    RouterNode,
)


def test_fallback_chain() -> None:
    """Test a chain of fallbacks: A -> B -> C."""
    node_c = AgentNode(id="Agent_C", agent_ref="agent-3")
    node_b = AgentNode(
        id="Agent_B",
        agent_ref="agent-2",
        recovery=RecoveryConfig(
            behavior=FailureBehavior.ROUTE_TO_FALLBACK,
            fallback_node_id="Agent_C",
        ),
    )
    node_a = AgentNode(
        id="Agent_A",
        agent_ref="agent-1",
        recovery=RecoveryConfig(
            behavior=FailureBehavior.ROUTE_TO_FALLBACK,
            fallback_node_id="Agent_B",
        ),
    )

    topology = GraphTopology(
        nodes=[node_a, node_b, node_c],
        edges=[],
        entry_point="Agent_A",
        status="valid",
    )

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Chain Topology"),
        interface=RecipeInterface(),
        topology=topology,
        status=RecipeStatus.DRAFT,
    )

    assert recipe.topology.nodes[0].recovery is not None
    assert recipe.topology.nodes[0].recovery.fallback_node_id == "Agent_B"
    assert recipe.topology.nodes[1].recovery is not None
    assert recipe.topology.nodes[1].recovery.fallback_node_id == "Agent_C"


def test_fallback_cycle() -> None:
    """Test a fallback cycle: A -> B -> A."""
    node_b = AgentNode(
        id="Agent_B",
        agent_ref="agent-2",
        recovery=RecoveryConfig(
            behavior=FailureBehavior.ROUTE_TO_FALLBACK,
            fallback_node_id="Agent_A",
        ),
    )
    node_a = AgentNode(
        id="Agent_A",
        agent_ref="agent-1",
        recovery=RecoveryConfig(
            behavior=FailureBehavior.ROUTE_TO_FALLBACK,
            fallback_node_id="Agent_B",
        ),
    )

    topology = GraphTopology(
        nodes=[node_a, node_b],
        edges=[],
        entry_point="Agent_A",
        status="valid",
    )

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Cycle Topology"),
        interface=RecipeInterface(),
        topology=topology,
        status=RecipeStatus.DRAFT,
    )

    assert recipe.topology.nodes[0].recovery is not None
    assert recipe.topology.nodes[0].recovery.fallback_node_id == "Agent_B"


def test_complex_broken_topology() -> None:
    """Test a mix of nodes where one has a broken link."""
    node_agent = AgentNode(id="Worker", agent_ref="worker-v1")
    node_human = HumanNode(id="Manager", prompt="Approve?")

    # Broken Router
    node_router = RouterNode(
        id="Decider",
        input_key="score",
        routes={"high": "Worker"},
        default_route="Manager",
        recovery=RecoveryConfig(
            behavior=FailureBehavior.ROUTE_TO_FALLBACK,
            fallback_node_id="Missing_Node",  # This is the error
        ),
    )

    topology = GraphTopology(
        nodes=[node_agent, node_human, node_router],
        edges=[],
        entry_point="Decider",
        status="draft",
    )

    with pytest.raises(ValueError, match="Missing_Node"):
        RecipeDefinition(
            metadata=ManifestMetadata(name="Complex Broken"),
            interface=RecipeInterface(),
            topology=topology,
            status=RecipeStatus.DRAFT,
        )


def test_mixed_node_types() -> None:
    """Verify different node types with valid fallbacks."""
    node_fallback = HumanNode(id="Human_Help", prompt="Fix it")

    node_router = RouterNode(
        id="Router",
        input_key="x",
        routes={},
        default_route="Human_Help",
        recovery=RecoveryConfig(behavior=FailureBehavior.ROUTE_TO_FALLBACK, fallback_node_id="Human_Help"),
    )

    node_evaluator = EvaluatorNode(
        id="Judge",
        target_variable="output",
        evaluator_agent_ref="gpt-4",
        evaluation_profile=EvaluationProfile(
            grading_rubric=[SuccessCriterion(name="accuracy", description="Must be accurate", threshold=0.9)]
        ),
        pass_threshold=0.9,
        max_refinements=1,
        pass_route="Human_Help",
        fail_route="Human_Help",
        feedback_variable="feedback",
        recovery=RecoveryConfig(behavior=FailureBehavior.ROUTE_TO_FALLBACK, fallback_node_id="Human_Help"),
    )

    topology = GraphTopology(
        nodes=[node_fallback, node_router, node_evaluator],
        edges=[],
        entry_point="Router",
        status="valid",
    )

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Mixed Nodes"),
        interface=RecipeInterface(),
        topology=topology,
        status=RecipeStatus.DRAFT,
    )

    # Check Router
    router = next(n for n in recipe.topology.nodes if n.id == "Router")
    assert router.recovery is not None
    assert router.recovery.fallback_node_id == "Human_Help"

    # Check Evaluator
    evaluator = next(n for n in recipe.topology.nodes if n.id == "Judge")
    assert evaluator.recovery is not None
    assert evaluator.recovery.fallback_node_id == "Human_Help"
