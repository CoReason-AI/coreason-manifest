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

from coreason_manifest.spec.v2.agent import CognitiveProfile
from coreason_manifest.spec.v2.knowledge import (
    KnowledgeScope,
    RetrievalConfig,
    RetrievalStrategy,
)


def test_retrieval_strategy_enum() -> None:
    """Ensure RetrievalStrategy values are correct."""
    assert RetrievalStrategy.DENSE.value == "dense"
    assert RetrievalStrategy.SPARSE.value == "sparse"
    assert RetrievalStrategy.HYBRID.value == "hybrid"
    assert RetrievalStrategy.GRAPH.value == "graph"
    assert RetrievalStrategy.GRAPH_RAG.value == "graph_rag"


def test_knowledge_scope_enum() -> None:
    """Ensure KnowledgeScope values are correct."""
    assert KnowledgeScope.SHARED.value == "shared"
    assert KnowledgeScope.USER.value == "user"
    assert KnowledgeScope.SESSION.value == "session"


def test_retrieval_config_defaults() -> None:
    """Test defaults for RetrievalConfig."""
    config = RetrievalConfig(collection_name="test_collection")
    assert config.strategy == RetrievalStrategy.HYBRID
    assert config.top_k == 5
    assert config.score_threshold == 0.7
    assert config.scope == KnowledgeScope.SHARED
    assert config.collection_name == "test_collection"


def test_retrieval_config_custom() -> None:
    """Test custom values for RetrievalConfig."""
    config = RetrievalConfig(
        strategy=RetrievalStrategy.GRAPH,
        collection_name="legal_docs",
        top_k=10,
        score_threshold=0.5,
        scope=KnowledgeScope.USER,
    )
    assert config.strategy == RetrievalStrategy.GRAPH
    assert config.collection_name == "legal_docs"
    assert config.top_k == 10
    assert config.score_threshold == 0.5
    assert config.scope == KnowledgeScope.USER


def test_retrieval_config_validation() -> None:
    """Test validation constraints."""
    # Test top_k < 1
    with pytest.raises(ValidationError) as exc:
        RetrievalConfig(collection_name="test", top_k=0)
    assert "Input should be greater than or equal to 1" in str(exc.value)

    # Test score_threshold < 0
    with pytest.raises(ValidationError) as exc:
        RetrievalConfig(collection_name="test", score_threshold=-0.1)
    assert "Input should be greater than or equal to 0" in str(exc.value)

    # Test score_threshold > 1
    with pytest.raises(ValidationError) as exc:
        RetrievalConfig(collection_name="test", score_threshold=1.1)
    assert "Input should be less than or equal to 1" in str(exc.value)


def test_retrieval_config_edge_cases() -> None:
    """Test boundary values for RetrievalConfig."""
    # Test boundary score_threshold = 0.0
    config_low = RetrievalConfig(collection_name="test", score_threshold=0.0)
    assert config_low.score_threshold == 0.0

    # Test boundary score_threshold = 1.0
    config_high = RetrievalConfig(collection_name="test", score_threshold=1.0)
    assert config_high.score_threshold == 1.0

    # Test top_k = 1
    config_k1 = RetrievalConfig(collection_name="test", top_k=1)
    assert config_k1.top_k == 1

    # Test very large top_k
    config_k_large = RetrievalConfig(collection_name="test", top_k=10000)
    assert config_k_large.top_k == 10000


def test_cognitive_profile_with_memory() -> None:
    """Test integration of RetrievalConfig into CognitiveProfile."""
    memory_config = RetrievalConfig(strategy=RetrievalStrategy.DENSE, collection_name="history")
    profile = CognitiveProfile(
        role="archivist",
        memory_read=[memory_config],
    )
    assert len(profile.memory_read) == 1
    assert profile.memory_read[0].collection_name == "history"
    assert profile.memory_read[0].strategy == RetrievalStrategy.DENSE


def test_cognitive_profile_complex_memory() -> None:
    """Test multiple memory configurations with different strategies/scopes."""
    memory_configs = [
        RetrievalConfig(
            strategy=RetrievalStrategy.DENSE,
            collection_name="global_knowledge",
            scope=KnowledgeScope.SHARED,
            top_k=5,
        ),
        RetrievalConfig(
            strategy=RetrievalStrategy.SPARSE,
            collection_name="user_notes",
            scope=KnowledgeScope.USER,
            top_k=10,
            score_threshold=0.5,
        ),
        RetrievalConfig(
            strategy=RetrievalStrategy.GRAPH,
            collection_name="ontology",
            scope=KnowledgeScope.SHARED,
        ),
    ]

    profile = CognitiveProfile(
        role="researcher",
        memory_read=memory_configs,
    )

    assert len(profile.memory_read) == 3
    assert profile.memory_read[0].strategy == RetrievalStrategy.DENSE
    assert profile.memory_read[1].scope == KnowledgeScope.USER
    assert profile.memory_read[2].strategy == RetrievalStrategy.GRAPH
    assert profile.memory_read[1].score_threshold == 0.5


def test_cognitive_profile_redundant_memory() -> None:
    """Test adding the same configuration multiple times (should be allowed)."""
    # While logically redundant, the schema shouldn't block it.
    config = RetrievalConfig(collection_name="test")
    profile = CognitiveProfile(
        role="tester",
        memory_read=[config, config],
    )
    assert len(profile.memory_read) == 2
    assert profile.memory_read[0] == profile.memory_read[1]


def test_serialization() -> None:
    """Test serialization of RetrievalConfig."""
    config = RetrievalConfig(collection_name="test", top_k=3)
    dumped = config.model_dump(mode='json', by_alias=True, exclude_none=True)
    assert dumped["collection_name"] == "test"
    assert dumped["top_k"] == 3
    assert dumped["strategy"] == "hybrid"  # Default
