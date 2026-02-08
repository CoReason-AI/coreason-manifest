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

from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    FailureBehavior,
    GraphTopology,
    RecipeNode,
    RecoveryConfig,
)


def test_recovery_config_defaults() -> None:
    """Ensure default recovery strategy is fail-fast."""
    config = RecoveryConfig()
    assert config.behavior == FailureBehavior.FAIL_WORKFLOW
    assert config.max_retries is None
    assert config.retry_delay_seconds == 1.0


def test_recovery_retry_logic() -> None:
    """Test valid retry configurations."""
    config = RecoveryConfig(max_retries=3, retry_delay_seconds=0.5)
    assert config.max_retries == 3
    assert config.retry_delay_seconds == 0.5


def test_fallback_node_validation() -> None:
    """Test routing to a fallback node."""
    config = RecoveryConfig(
        behavior=FailureBehavior.ROUTE_TO_FALLBACK,
        fallback_node_id="agent_supervisor",
    )
    assert config.fallback_node_id == "agent_supervisor"
    assert config.behavior == "route_to_fallback"


def test_node_integration() -> None:
    """Ensure a node can carry a recovery config."""
    node = RecipeNode(id="step_1", recovery=RecoveryConfig(max_retries=5))
    assert node.recovery is not None
    assert node.recovery.max_retries == 5


def test_serialization() -> None:
    """Verify JSON persistence."""
    node = RecipeNode(id="step_1", recovery=RecoveryConfig(behavior=FailureBehavior.IGNORE))
    data = node.model_dump(mode="json")
    assert data["recovery"]["behavior"] == "ignore"


# --- Edge Cases (Negative/Zero Values) ---


def test_edge_case_negative_retries() -> None:
    """
    Edge Case: Negative max_retries.
    Previously forbidden (ge=0), now allowed by schema but logically questionable.
    We test that the model accepts it without raising ValidationError.
    """
    config = RecoveryConfig(max_retries=-1)
    assert config.max_retries == -1


def test_edge_case_negative_delay() -> None:
    """
    Edge Case: Negative retry_delay_seconds.
    Previously forbidden (ge=0.0), now allowed by schema.
    """
    config = RecoveryConfig(retry_delay_seconds=-5.0)
    assert config.retry_delay_seconds == -5.0


def test_edge_case_zero_retries() -> None:
    """Edge Case: Zero retries (effectively no retries)."""
    config = RecoveryConfig(max_retries=0)
    assert config.max_retries == 0


def test_edge_case_route_to_fallback_missing_id() -> None:
    """
    Edge Case: behavior is ROUTE_TO_FALLBACK but fallback_node_id is None.
    The Schema itself doesn't enforce this relationship in RecoveryConfig validation,
    but GraphTopology validation logic does.
    This test confirms the isolated config object allows it (loose coupling).
    """
    config = RecoveryConfig(behavior=FailureBehavior.ROUTE_TO_FALLBACK)
    assert config.behavior == FailureBehavior.ROUTE_TO_FALLBACK
    assert config.fallback_node_id is None  # Allowed here


# --- Complex Cases (Graph Validation) ---


def test_complex_graph_validation_valid_fallback() -> None:
    """
    Complex Case: Verify GraphTopology correctly validates that fallback_node_id exists.
    Scenario: Node A fails -> Fallback to Node B. Both exist.
    """
    node_a = AgentNode(
        id="node_a",
        agent_ref="agent-1",
        recovery=RecoveryConfig(behavior=FailureBehavior.ROUTE_TO_FALLBACK, fallback_node_id="node_b"),
    )
    node_b = AgentNode(id="node_b", agent_ref="agent-2")

    # Valid Topology
    GraphTopology(
        nodes=[node_a, node_b],
        edges=[],
        entry_point="node_a",
    )


def test_complex_graph_validation_invalid_fallback() -> None:
    """
    Complex Case: Verify GraphTopology RAISES error if fallback_node_id does not exist.
    Scenario: Node A fails -> Fallback to 'ghost_node' (missing).
    """
    node_a = AgentNode(
        id="node_a",
        agent_ref="agent-1",
        recovery=RecoveryConfig(behavior=FailureBehavior.ROUTE_TO_FALLBACK, fallback_node_id="ghost_node"),
    )

    with pytest.raises(ValueError, match="Invalid fallback_node_id 'ghost_node'"):
        GraphTopology(
            nodes=[node_a],
            edges=[],
            entry_point="node_a",
        )


def test_complex_graph_validation_fallback_is_self() -> None:
    """
    Complex Case: Fallback node is the node itself (Infinite Loop Potential).
    The validator currently only checks existence, not cycles, so this should PASS validation.
    """
    node_a = AgentNode(
        id="node_a",
        agent_ref="agent-1",
        recovery=RecoveryConfig(behavior=FailureBehavior.ROUTE_TO_FALLBACK, fallback_node_id="node_a"),
    )

    GraphTopology(
        nodes=[node_a],
        edges=[],
        entry_point="node_a",
    )


def test_complex_serialization_full_structure() -> None:
    """
    Complex Case: Serialize a full structure with various recovery configs.
    """
    node_a = AgentNode(
        id="node_a",
        agent_ref="agent-1",
        recovery=RecoveryConfig(
            max_retries=2,
            retry_delay_seconds=0.1,
            behavior=FailureBehavior.CONTINUE_WITH_DEFAULT,
            default_output={"status": "mocked"},
        ),
    )

    dumped = node_a.model_dump(mode="json")
    assert dumped["recovery"]["max_retries"] == 2
    assert dumped["recovery"]["retry_delay_seconds"] == 0.1
    assert dumped["recovery"]["default_output"] == {"status": "mocked"}
