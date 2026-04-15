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
    CryptographicProvenancePolicy,
    HypothesisSuperpositionState,
    TargetTopologyProfile,
    TopologicalProjectionIntent,
)


class MockDeterministicExecutionNode(CryptographicProvenancePolicy):
    """
    AGENT INSTRUCTION: A local mock execution node to test cryptographic lineage traversals.

    CAUSAL AFFORDANCE: Does nothing, exists purely to simulate a deterministic node execution graph.

    EPISTEMIC BOUNDS: Follows CoreasonBaseState rules and tests string payload parsing.

    MCP ROUTING TRIGGERS: Mock Execution, Cryptographic Lineage, Serialization Isomorphism
    """

    payload: str


MockDeterministicExecutionNode.model_rebuild()


@given(
    st.builds(
        HypothesisSuperpositionState,
        superposition_cid=st.uuids().map(str),
        competing_manifolds=st.just({}),
        wave_collapse_function=st.just("deterministic_compiler"),
        residual_entropy_vectors=st.lists(st.text(min_size=1, max_size=10)),
    ),
    st.uuids().map(str),
    st.floats(min_value=0.85, max_value=1.0),
    st.sampled_from(TargetTopologyProfile),
    st.text(min_size=1, max_size=50),
)
def test_cryptographic_lineage_and_serialization(
    superposition: HypothesisSuperpositionState,
    projection_cid: str,
    confidence: float,
    topology: TargetTopologyProfile,
    mock_payload: str,
) -> None:
    intent = TopologicalProjectionIntent(
        projection_cid=projection_cid,
        source_superposition_cid=superposition.superposition_cid,
        target_topology=topology,
        isomorphism_confidence=confidence,
        lossy_translation_divergence=[],
    )
    node = MockDeterministicExecutionNode(provenance_trace_cid=intent.projection_cid, payload=mock_payload)
    assert node.provenance_trace_cid == intent.projection_cid
    assert intent.source_superposition_cid == superposition.superposition_cid

    superposition_json = superposition.model_dump_canonical()
    intent_json = intent.model_dump_canonical()
    node_json = node.model_dump_canonical()

    superposition_restored = HypothesisSuperpositionState.model_validate_json(superposition_json)
    intent_restored = TopologicalProjectionIntent.model_validate_json(intent_json)
    node_restored = MockDeterministicExecutionNode.model_validate_json(node_json)

    assert node_restored.provenance_trace_cid == intent_restored.projection_cid
    assert intent_restored.source_superposition_cid == superposition_restored.superposition_cid
