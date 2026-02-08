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

from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    FailureBehavior,
    GraphTopology,
    RecoveryConfig,
)


def test_edge_case_zero_retries() -> None:
    """Edge Case: max_retries set to 0 (fail immediately)."""
    config = RecoveryConfig(max_retries=0)
    assert config.max_retries == 0


def test_edge_case_large_negative_retries() -> None:
    """Edge Case: max_retries set to large negative number."""
    config = RecoveryConfig(max_retries=-100)
    assert config.max_retries == -100


def test_edge_case_zero_delay() -> None:
    """Edge Case: retry_delay_seconds set to 0.0."""
    config = RecoveryConfig(retry_delay_seconds=0.0)
    assert config.retry_delay_seconds == 0.0


def test_edge_case_negative_delay() -> None:
    """Edge Case: retry_delay_seconds set to negative value."""
    config = RecoveryConfig(retry_delay_seconds=-1.0)
    assert config.retry_delay_seconds == -1.0


def test_edge_case_default_output_none() -> None:
    """Edge Case: continue_with_default with None default_output."""
    config = RecoveryConfig(
        behavior=FailureBehavior.CONTINUE_WITH_DEFAULT,
        default_output=None
    )
    assert config.behavior == FailureBehavior.CONTINUE_WITH_DEFAULT
    assert config.default_output is None


def test_complex_cyclic_fallback() -> None:
    """Complex Case: Cyclic fallback (A -> B, B fallback -> A)."""
    node_a = AgentNode(
        id="A",
        agent_ref="agent-a",
        recovery=RecoveryConfig(behavior=FailureBehavior.ROUTE_TO_FALLBACK, fallback_node_id="B")
    )
    node_b = AgentNode(
        id="B",
        agent_ref="agent-b",
        recovery=RecoveryConfig(behavior=FailureBehavior.ROUTE_TO_FALLBACK, fallback_node_id="A")
    )

    # Structurally valid, though runtime might loop infinitely
    topo = GraphTopology(nodes=[node_a, node_b], edges=[], entry_point="A")
    assert topo.status == "valid"


def test_complex_self_fallback() -> None:
    """Complex Case: Self fallback (A fallback -> A)."""
    node_a = AgentNode(
        id="A",
        agent_ref="agent-a",
        recovery=RecoveryConfig(behavior=FailureBehavior.ROUTE_TO_FALLBACK, fallback_node_id="A")
    )

    topo = GraphTopology(nodes=[node_a], edges=[], entry_point="A")
    assert topo.status == "valid"


def test_complex_fallback_chain() -> None:
    """Complex Case: Long fallback chain (A -> B -> C -> D)."""
    nodes = []
    # Create A, B, C pointing to next
    chars = ["A", "B", "C", "D"]
    for i in range(3):
        nodes.append(AgentNode(
            id=chars[i],
            agent_ref=f"agent-{chars[i]}",
            recovery=RecoveryConfig(
                behavior=FailureBehavior.ROUTE_TO_FALLBACK,
                fallback_node_id=chars[i+1]
            )
        ))
    # D fails workflow
    nodes.append(AgentNode(
        id="D",
        agent_ref="agent-d",
        recovery=RecoveryConfig(behavior=FailureBehavior.FAIL_WORKFLOW)
    ))

    topo = GraphTopology(nodes=nodes, edges=[], entry_point="A")
    assert topo.status == "valid"


def test_validation_fallback_missing_node() -> None:
    """Complex Case: Fallback node does not exist in graph."""
    node_a = AgentNode(
        id="A",
        agent_ref="agent-a",
        recovery=RecoveryConfig(
            behavior=FailureBehavior.ROUTE_TO_FALLBACK,
            fallback_node_id="MISSING_NODE"
        )
    )

    with pytest.raises(ValidationError, match="Invalid fallback_node_id 'MISSING_NODE'"):
        GraphTopology(nodes=[node_a], edges=[], entry_point="A")
