# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

from hypothesis import given
from hypothesis import strategies as st

from coreason_manifest.spec.ontology import (
    CryptographicProvenanceMixin,
    StochasticConsensus,
    TargetTopologyEnum,
    TopologicalProjectionIntent,
)


class MockDeterministicExecutionNode(CryptographicProvenanceMixin):
    """
    AGENT INSTRUCTION: A local mock execution node to test cryptographic lineage traversals.

    CAUSAL AFFORDANCE: Does nothing, exists purely to simulate a deterministic node execution graph.

    EPISTEMIC BOUNDS: Follows CoreasonBaseState rules and tests string payload parsing.

    MCP ROUTING TRIGGERS: Mock Execution, Cryptographic Lineage, Serialization Isomorphism
    """

    payload: str


# Rebuild the model so it can be instantiated
MockDeterministicExecutionNode.model_rebuild()


@given(
    st.builds(
        StochasticConsensus,
        proposed_manifold=st.text(min_size=1, max_size=50),
        convergence_confidence=st.floats(min_value=0.0, max_value=1.0),
        residual_entropy_vectors=st.lists(st.text(min_size=1, max_size=10)),
    ),
    st.floats(min_value=0.85, max_value=1.0),
    st.sampled_from(TargetTopologyEnum),
    st.text(min_size=1, max_size=50),
)
def test_cryptographic_lineage_and_serialization(
    consensus: StochasticConsensus, confidence: float, topology: TargetTopologyEnum, mock_payload: str
) -> None:
    """Test 1 & 2: Cryptographic Lineage Traversal and Serialization Isomorphism"""

    # 1. Build Projection Intent from Consensus
    intent = TopologicalProjectionIntent(
        source_consensus_cid=consensus.consensus_cid,
        target_topology=topology,
        isomorphism_confidence=confidence,
        lossy_translation_divergence=[],
    )

    # 2. Build Mock Node from Projection Intent
    node = MockDeterministicExecutionNode(provenance_trace_cid=intent.projection_cid, payload=mock_payload)

    # Validate Linkage
    assert node.provenance_trace_cid == intent.projection_cid
    assert intent.source_consensus_cid == consensus.consensus_cid

    # Test Serialization Isomorphism
    consensus_json = consensus.model_dump_canonical()
    intent_json = intent.model_dump_canonical()
    node_json = node.model_dump_canonical()

    # Deserialization
    consensus_restored = StochasticConsensus.model_validate_json(consensus_json)
    intent_restored = TopologicalProjectionIntent.model_validate_json(intent_json)
    node_restored = MockDeterministicExecutionNode.model_validate_json(node_json)

    # Assert CIDs match across Serialization perturbation
    assert node_restored.provenance_trace_cid == intent_restored.projection_cid
    assert intent_restored.source_consensus_cid == consensus_restored.consensus_cid
