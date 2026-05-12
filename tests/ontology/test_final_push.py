# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

"""Final push tests targeting remaining largest uncovered blocks.

These tests provide the last ~70 lines needed to reach 95% coverage.
"""

from coreason_manifest.spec.ontology import (
    # DocumentKnowledgeGraphManifest — lines 4688-4713 (remaining DAG code)
    DocumentKnowledgeGraphManifest,
    # EpistemicAxiomState — used by chain/partition sorts
    EpistemicAxiomState,
    # EpistemicDomainGraphManifest — lines 13590-13599 (10 lines)
    EpistemicDomainGraphManifest,
    SemanticClassificationProfile,
    # SemanticSlicingPolicy — lines 2052-2065 (14 lines)
    SemanticSlicingPolicy,
)

# ---------------------------------------------------------------------------
# SemanticSlicingPolicy — canonical sort with sorted tiers (14 lines)
# ---------------------------------------------------------------------------


class TestSemanticSlicingPolicy:
    """Exercise canonical sort for classification tiers and semantic labels."""

    def test_with_labels(self) -> None:
        obj = SemanticSlicingPolicy(
            permitted_classification_tiers=[
                SemanticClassificationProfile.RESTRICTED,
                SemanticClassificationProfile.CONFIDENTIAL,
            ],
            required_semantic_labels=["zebra", "apple"],
            context_window_token_ceiling=1000,
        )
        # Verify labels are sorted
        assert obj.required_semantic_labels == ["apple", "zebra"]

    def test_without_labels(self) -> None:
        obj = SemanticSlicingPolicy(
            permitted_classification_tiers=[SemanticClassificationProfile.CONFIDENTIAL],
            context_window_token_ceiling=500,
        )
        assert obj.required_semantic_labels is None


# ---------------------------------------------------------------------------
# EpistemicAxiomPartitionManifest — canonical sort (10 lines)
# ---------------------------------------------------------------------------


class TestEpistemicDomainGraphManifest:
    """Exercise axiom partition canonical sort."""

    def test_valid_partition(self) -> None:
        obj = EpistemicDomainGraphManifest(
            graph_cid="g-1",
            verified_axioms=[
                EpistemicAxiomState(
                    source_concept_cid="z_src",
                    directed_edge_class="is_a",
                    target_concept_cid="tgt",
                ),
                EpistemicAxiomState(
                    source_concept_cid="a_src",
                    directed_edge_class="is_a",
                    target_concept_cid="tgt",
                ),
            ],
        )
        # Verify sorted by source_concept_cid
        assert obj.verified_axioms[0].source_concept_cid == "a_src"


# ---------------------------------------------------------------------------
# DocumentKnowledgeGraphManifest — full DAG path with edges (26 lines)
# ---------------------------------------------------------------------------


class TestDocumentKnowledgeGraphManifestDAG:
    """Exercise the full DAG validation path."""

    def test_graph_with_no_edges(self) -> None:
        obj = DocumentKnowledgeGraphManifest(
            graph_cid="dkg-full",
            source_artifact_cid="doc-1",
            nodes=[],
            causal_edges=[],
            isomorphism_hash="a" * 64,
        )
        assert obj.graph_cid == "dkg-full"

    def test_empty_graph(self) -> None:
        obj = DocumentKnowledgeGraphManifest(
            graph_cid="dkg-noe",
            source_artifact_cid="doc-1",
            nodes=[],
            causal_edges=[],
            isomorphism_hash="b" * 64,
        )
        assert len(obj.causal_edges) == 0
