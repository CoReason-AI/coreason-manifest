from typing import Any

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    AgentNodeProfile,
    NeurosymbolicVerificationTopologyManifest,
    SystemNodeProfile,
)


def test_bipartite_identity_violation() -> None:
    # Setup standard agent and system
    nodes: dict[str, Any] = {
        "did:coreason:node-1": AgentNodeProfile(description="Test Proposer", type="agent"),
    }

    with pytest.raises(ValidationError) as exc_info:
        NeurosymbolicVerificationTopologyManifest(
            nodes=nodes,
            proposer_node_id="did:coreason:node-1",
            verifier_node_id="did:coreason:node-1",
            max_revision_loops=10,
        )
    assert "Topological Contradiction" in str(exc_info.value)
    assert "Proposer and Verifier cannot be the same node" in str(exc_info.value)


def test_bipartite_type_violation_both_agents() -> None:
    nodes: dict[str, Any] = {
        "did:coreason:agent-1": AgentNodeProfile(description="Agent 1", type="agent"),
        "did:coreason:agent-2": AgentNodeProfile(description="Agent 2", type="agent"),
    }
    with pytest.raises(ValidationError) as exc_info:
        NeurosymbolicVerificationTopologyManifest(
            nodes=nodes,
            proposer_node_id="did:coreason:agent-1",
            verifier_node_id="did:coreason:agent-2",
            max_revision_loops=10,
        )
    assert "Topological Contradiction" in str(exc_info.value)
    assert "Proposer must be a Connectionist Agent, and the Verifier must be a Deterministic System" in str(
        exc_info.value
    )


def test_bipartite_type_violation_both_systems() -> None:
    nodes: dict[str, Any] = {
        "did:coreason:system-1": SystemNodeProfile(description="System 1", type="system"),
        "did:coreason:system-2": SystemNodeProfile(description="System 2", type="system"),
    }
    with pytest.raises(ValidationError) as exc_info:
        NeurosymbolicVerificationTopologyManifest(
            nodes=nodes,
            proposer_node_id="did:coreason:system-1",
            verifier_node_id="did:coreason:system-2",
            max_revision_loops=10,
        )
    assert "Topological Contradiction" in str(exc_info.value)


def test_cycle_bound_enforcement_too_high() -> None:
    nodes: dict[str, Any] = {
        "did:coreason:agent-1": AgentNodeProfile(description="Agent 1", type="agent"),
        "did:coreason:system-1": SystemNodeProfile(description="System 1", type="system"),
    }
    with pytest.raises(ValidationError) as exc_info:
        NeurosymbolicVerificationTopologyManifest(
            nodes=nodes,
            proposer_node_id="did:coreason:agent-1",
            verifier_node_id="did:coreason:system-1",
            max_revision_loops=1000,
        )
    assert "100" in str(exc_info.value)


def test_cycle_bound_enforcement_too_low() -> None:
    nodes: dict[str, Any] = {
        "did:coreason:agent-1": AgentNodeProfile(description="Agent 1", type="agent"),
        "did:coreason:system-1": SystemNodeProfile(description="System 1", type="system"),
    }
    with pytest.raises(ValidationError) as exc_info:
        NeurosymbolicVerificationTopologyManifest(
            nodes=nodes,
            proposer_node_id="did:coreason:agent-1",
            verifier_node_id="did:coreason:system-1",
            max_revision_loops=-5,
        )
    assert "1" in str(exc_info.value)


def test_successful_compilation() -> None:
    nodes: dict[str, Any] = {
        "did:coreason:agent-1": AgentNodeProfile(description="Agent 1", type="agent"),
        "did:coreason:system-1": SystemNodeProfile(description="System 1", type="system"),
    }
    macro = NeurosymbolicVerificationTopologyManifest(
        nodes=nodes,
        proposer_node_id="did:coreason:agent-1",
        verifier_node_id="did:coreason:system-1",
        max_revision_loops=42,
    )

    dag = macro.compile_to_base_topology()
    assert dag.type == "dag"
    assert dag.allow_cycles is True
    assert dag.max_depth == 42
    # Verify the edges exactly match the bidirectional Proposer-Verifier loop
    assert ("did:coreason:agent-1", "did:coreason:system-1") in dag.edges
    assert ("did:coreason:system-1", "did:coreason:agent-1") in dag.edges
    assert len(dag.edges) == 2
