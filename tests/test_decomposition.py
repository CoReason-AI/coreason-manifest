# Copyright (c) 2026 CoReason, Inc.
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

from coreason_manifest.spec.ontology import (
    CognitiveUncertaintyProfile,
    DecomposedSubQueryState,
    QueryDecompositionManifest,
    SemanticDiscoveryIntent,
    VectorEmbeddingState,
)


def test_cognitive_uncertainty_profile() -> None:
    profile = CognitiveUncertaintyProfile(
        decomposition_entropy_threshold=1.5,
        aleatoric_entropy=0.5,
        epistemic_uncertainty=0.2,
        semantic_consistency_score=0.9,
        requires_abductive_escalation=False,
    )
    assert profile.decomposition_entropy_threshold == 1.5


def test_decomposed_sub_query_state() -> None:
    vector = VectorEmbeddingState(vector_base64="aA==", dimensionality=1, model_name="test-model")
    sub_query = DecomposedSubQueryState(
        sub_query_id="query-1",
        latent_target_vector=vector,
        expected_information_gain=0.8,
        required_surface_capabilities=["b-capability", "a-capability"],
    )
    assert sub_query.required_surface_capabilities == ["a-capability", "b-capability"]


def test_semantic_discovery_intent() -> None:
    vector = VectorEmbeddingState(vector_base64="aA==", dimensionality=1, model_name="test-model")
    intent = SemanticDiscoveryIntent(
        parent_decomposition_id="manifest-1",
        query_vector=vector,
        min_isometry_score=0.5,
        required_structural_types=["type-a"],
    )
    assert intent.parent_decomposition_id == "manifest-1"


def test_query_decomposition_manifest_success() -> None:
    vector = VectorEmbeddingState(vector_base64="aA==", dimensionality=1, model_name="test-model")
    sub_query_1 = DecomposedSubQueryState(
        sub_query_id="q1",
        latent_target_vector=vector,
        expected_information_gain=0.5,
        required_surface_capabilities=["cap1"],
    )
    sub_query_2 = DecomposedSubQueryState(
        sub_query_id="q2",
        latent_target_vector=vector,
        expected_information_gain=0.6,
        required_surface_capabilities=["cap2"],
    )

    manifest = QueryDecompositionManifest(
        manifest_id="manifest-1",
        root_intent_hash="0" * 64,
        surface_projection_id="proj-1",
        sub_queries={"q1": sub_query_1, "q2": sub_query_2},
        execution_dag_edges=[("q1", "q2")],
    )
    assert manifest.execution_dag_edges == [("q1", "q2")]


def test_query_decomposition_manifest_ghost_node_source() -> None:
    vector = VectorEmbeddingState(vector_base64="aA==", dimensionality=1, model_name="test-model")
    sub_query_2 = DecomposedSubQueryState(
        sub_query_id="q2",
        latent_target_vector=vector,
        expected_information_gain=0.6,
        required_surface_capabilities=["cap2"],
    )
    with pytest.raises(ValidationError, match="Ghost node referenced in execution_dag_edges source: q1"):
        QueryDecompositionManifest(
            manifest_id="manifest-1",
            root_intent_hash="0" * 64,
            surface_projection_id="proj-1",
            sub_queries={"q2": sub_query_2},
            execution_dag_edges=[("q1", "q2")],
        )


def test_query_decomposition_manifest_ghost_node_target() -> None:
    vector = VectorEmbeddingState(vector_base64="aA==", dimensionality=1, model_name="test-model")
    sub_query_1 = DecomposedSubQueryState(
        sub_query_id="q1",
        latent_target_vector=vector,
        expected_information_gain=0.6,
        required_surface_capabilities=["cap1"],
    )
    with pytest.raises(ValidationError, match="Ghost node referenced in execution_dag_edges target: q2"):
        QueryDecompositionManifest(
            manifest_id="manifest-1",
            root_intent_hash="0" * 64,
            surface_projection_id="proj-1",
            sub_queries={"q1": sub_query_1},
            execution_dag_edges=[("q1", "q2")],
        )


def test_query_decomposition_manifest_cycle() -> None:
    vector = VectorEmbeddingState(vector_base64="aA==", dimensionality=1, model_name="test-model")
    sub_query_1 = DecomposedSubQueryState(
        sub_query_id="q1",
        latent_target_vector=vector,
        expected_information_gain=0.5,
        required_surface_capabilities=["cap1"],
    )
    sub_query_2 = DecomposedSubQueryState(
        sub_query_id="q2",
        latent_target_vector=vector,
        expected_information_gain=0.6,
        required_surface_capabilities=["cap2"],
    )

    with pytest.raises(ValidationError, match="Execution DAG contains cycles"):
        QueryDecompositionManifest(
            manifest_id="manifest-1",
            root_intent_hash="0" * 64,
            surface_projection_id="proj-1",
            sub_queries={"q1": sub_query_1, "q2": sub_query_2},
            execution_dag_edges=[("q1", "q2"), ("q2", "q1")],
        )
