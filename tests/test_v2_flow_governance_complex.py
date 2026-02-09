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
    FailureBehavior,
    GraphTopology,
    RecipeDefinition,
    RecipeInterface,
    RecoveryConfig,
)


def test_validation_negative_retries() -> None:
    """Test that max_retries can be negative (flexible runtime)."""
    config = RecoveryConfig(max_retries=-1)
    assert config.max_retries == -1


def test_validation_negative_delay() -> None:
    """Test that retry_delay_seconds can be negative (flexible runtime)."""
    config = RecoveryConfig(retry_delay_seconds=-0.5)
    assert config.retry_delay_seconds == -0.5


def test_validation_fallback_integrity() -> None:
    """Test that defining a fallback_node_id that doesn't exist raises validation error."""
    # A points to B (fallback), but B is missing
    node_a = AgentNode(
        id="A",
        agent_ref="agent-a",
        recovery=RecoveryConfig(behavior=FailureBehavior.ROUTE_TO_FALLBACK, fallback_node_id="B"),
    )

    with pytest.raises(ValidationError, match="Invalid fallback_node_id 'B' in node 'A'"):
        GraphTopology(
            nodes=[node_a],
            edges=[],
            entry_point="A",  # No node B
        )


def test_validation_fallback_integrity_valid() -> None:
    """Test that a valid fallback reference passes validation."""
    node_a = AgentNode(
        id="A",
        agent_ref="agent-a",
        recovery=RecoveryConfig(behavior=FailureBehavior.ROUTE_TO_FALLBACK, fallback_node_id="B"),
    )
    node_b = AgentNode(id="B", agent_ref="agent-b")

    # This should pass
    topo = GraphTopology(
        nodes=[node_a, node_b],
        edges=[],  # No explicit edge needed for fallback
        entry_point="A",
    )
    assert topo.status == "valid"


def test_complex_fallback_chain() -> None:
    """Test a chain: A -> B (fallback) -> C (fallback)."""
    node_a = AgentNode(
        id="A",
        agent_ref="agent-a",
        recovery=RecoveryConfig(behavior=FailureBehavior.ROUTE_TO_FALLBACK, fallback_node_id="B"),
    )
    node_b = AgentNode(
        id="B",
        agent_ref="agent-b",
        recovery=RecoveryConfig(behavior=FailureBehavior.ROUTE_TO_FALLBACK, fallback_node_id="C"),
    )
    node_c = AgentNode(
        id="C",
        agent_ref="agent-c",
        recovery=RecoveryConfig(behavior=FailureBehavior.FAIL_WORKFLOW),
    )

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Chain Test"),
        interface=RecipeInterface(),
        topology=GraphTopology(nodes=[node_a, node_b, node_c], edges=[], entry_point="A"),
    )
    # Just ensuring it validates successfully
    assert recipe.topology.verify_completeness()


def test_self_fallback_validation() -> None:
    """Test A -> A (fallback). Valid in schema, might loop in runtime."""
    node_a = AgentNode(
        id="A",
        agent_ref="agent-a",
        recovery=RecoveryConfig(behavior=FailureBehavior.ROUTE_TO_FALLBACK, fallback_node_id="A"),
    )
    # Should be valid structurally
    GraphTopology(nodes=[node_a], edges=[], entry_point="A")


def test_fallback_missing_but_behavior_ignore() -> None:
    """Test that checking for fallback_node_id only happens if behavior is ROUTE_TO_FALLBACK."""
    # Here fallback_node_id is "B" (missing), but behavior is IGNORE.
    # Logic in validate_integrity checks `behavior == ROUTE_TO_FALLBACK`.
    # So this should technically pass if the validator is strict about the condition.
    # However, setting a fallback_id without using it is weird but maybe allowed.
    node_a = AgentNode(
        id="A",
        agent_ref="agent-a",
        recovery=RecoveryConfig(behavior=FailureBehavior.IGNORE, fallback_node_id="B"),
    )
    # This should pass because the validator only checks if behavior is ROUTE_TO_FALLBACK
    GraphTopology(nodes=[node_a], edges=[], entry_point="A")
